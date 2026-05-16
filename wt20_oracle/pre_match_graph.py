"""
Pre-Match Pipeline
==================

LangGraph-style sequential pipeline for generating pre-match recommendations.

Architecture:
  DataNode → ScenarioNode → OpponentAnalysisNode
           → SquadSelectorNode → BattingOrderNode
           → BowlingPlanNode → PredictionNode
           → StrategyNode → Output

ScenarioNode is intentionally placed early: every downstream node
(runs estimate, win probability, batting order) reads `scenario` from state.
This was the root cause of the India vs SA April 27 failure — scenario
was never set, so batting-first assumptions propagated through all nodes.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from wt20_oracle.state import PreMatchState
from wt20_oracle.io.loader import load_match_context, venue_pace_score, avg_first_innings_score
from wt20_oracle.io.analyst_loader import AnalystInsightEnricher
from wt20_oracle.optimisation.monte_carlo import (
    estimate_win_probability,
    squad_batting_strength,
    squad_bowling_strength,
)
from wt20_oracle.agents.pre_match.squad_selector_node import squad_selector_node
from wt20_oracle.agents.pre_match.batting_order_node import batting_order_node
from wt20_oracle.agents.pre_match.bowling_plan_node import bowling_plan_node
from wt20_oracle.agents.pre_match.strategy_node import strategy_node

# Retraining framework — ScenarioHandler is the critical new integration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from testing.prediction_pipeline.scenario_handler import ScenarioHandler


# ---------------------------------------------------------------------------
# Individual pipeline nodes
# ---------------------------------------------------------------------------

def data_node(state: PreMatchState) -> Dict[str, Any]:
    """Load all reference data into state."""
    context = load_match_context(
        team_id=state["team_id"],
        opponent_id=state["opponent_id"],
        venue_id=state["venue_id"],
    )
    return context  # merges our_squad, opponent_squad, venue_data, etc.


def scenario_node(state: PreMatchState) -> Dict[str, Any]:
    """
    CRITICAL NODE: Set toss-aware scenario before any prediction is made.

    Reads toss_winner and toss_decision from state (set by CLI or live input).
    If toss is not yet known, scenario defaults to "unknown" — predictions
    will carry wider confidence intervals.

    This node was the missing piece that caused the India vs SA failure.
    Old pipeline: assumed India batting first unconditionally.
    New pipeline: reads toss outcome, classifies scenario, sets chase penalty.
    """
    handler = ScenarioHandler()

    toss_winner = state.get("toss_winner")
    toss_decision = state.get("toss_decision")

    if toss_winner and toss_decision:
        handler.set_toss(winner=toss_winner, decision=toss_decision)

    team_id = state["team_id"]
    opponent_id = state["opponent_id"]
    scenario = handler.identify_scenario(team_id, opponent_id)

    venue_data = state.get("venue_data", {})
    pace_score = venue_pace_score(venue_data)
    pitch_difficulty = handler.classify_pitch_difficulty(pace_score)
    chase_penalty = handler.get_chase_penalty(pitch_difficulty) if scenario == "chasing" else 0

    return {
        "scenario": scenario,
        "pitch_difficulty": pitch_difficulty,
        "chase_penalty": chase_penalty,
        "scenario_report": handler.generate_scenario_report(),
    }


def opponent_analysis_node(state: PreMatchState) -> Dict[str, Any]:
    """Analyse opponent strengths, weaknesses, key players."""
    opponent_squad = state.get("opponent_squad", [])
    opponent_data = state.get("opponent_data", {})
    venue_data = state.get("venue_data", {})
    pitch_type = venue_data.get("pitch", {}).get("type", "balanced")

    strengths = []
    weaknesses = []
    key_batters = []
    key_bowlers = []

    for player in opponent_squad:
        role = player.get("role", "")
        bowl_stats = player.get("t20i_stats", {}).get("bowling") or {}
        bat_stats = player.get("t20i_stats", {}).get("batting") or {}

        # Key batters: high SR / average
        if role in ("batter", "wk_batter", "all_rounder"):
            sr = bat_stats.get("strike_rate", 0) or 0
            avg = bat_stats.get("average", 0) or 0
            if sr > 125 or avg > 30:
                key_batters.append(player["id"])

        # Key bowlers: good economy
        if role in ("bowler", "all_rounder"):
            economy = bowl_stats.get("economy", 99) or 99
            innings = bowl_stats.get("innings", 0) or 0
            if economy < 7.5 and innings >= 5:
                key_bowlers.append(player["id"])
                # Check for pitch-type match
                style = player.get("bowling_style", "")
                if pitch_type == "spin_friendly" and "spin" in style:
                    strengths.append(f"Spin bowler {player['id']} will be effective on this pitch")
                elif pitch_type in ("seam_friendly", "flat") and "pace" in style:
                    strengths.append(f"Pace bowler {player['id']} will benefit from conditions")

    # Structural patterns from team data
    batting_first_data = opponent_data.get("batting_first", {})
    chasing_data = opponent_data.get("chasing", {})

    bf_wins = batting_first_data.get("wins") or 0
    bf_matches = batting_first_data.get("matches") or 1
    bf_win_pct = bf_wins / max(bf_matches, 1)

    if bf_win_pct > 0.65:
        strengths.append(f"Strong when batting first ({bf_win_pct:.0%} win rate)")
    elif bf_win_pct < 0.40:
        weaknesses.append(f"Weak when batting first ({bf_win_pct:.0%} win rate)")

    chase_wins = chasing_data.get("wins") or 0
    chase_matches = chasing_data.get("matches") or 1
    chase_win_pct = chase_wins / max(chase_matches, 1)

    if chase_win_pct > 0.65:
        strengths.append(f"Strong chasers ({chase_win_pct:.0%} win rate)")

    # Weak batting positions
    weak_links = opponent_data.get("weak_links", [])
    if weak_links:
        weaknesses.append(f"Batting collapses at: {', '.join(weak_links)}")

    return {
        "opponent_strengths": strengths,
        "opponent_weaknesses": weaknesses,
        "opponent_key_batters": key_batters[:5],
        "opponent_key_bowlers": key_bowlers[:5],
    }


def _calculate_batter_bowler_boost(
    our_squad: List[Dict],
    opponent_squad: List[Dict],
    matchups: Dict[str, Any],
    scenario: str,
) -> float:
    """
    Calculate a runs boost based on elite batter-vs-bowler matchups.

    Identifies top-4 batters from our team vs top-3 bowlers from opponent.
    If batters have high strike rates (>120) vs these bowlers, apply +2-5 run bonus.

    Returns: Bonus runs to add to prediction (0-5 runs typical)
    """
    if scenario != "chasing":
        return 0.0  # Only enhance chase scenarios where we specifically face their bowlers

    from wt20_oracle.io.loader import get_player, get_matchup

    # Get top batters (high SR or average)
    our_batters = []
    for p in our_squad:
        if p.get("role") in ("batter", "wk_batter", "all_rounder"):
            bat_stats = p.get("t20i_stats", {}).get("batting", {}) or {}
            sr = bat_stats.get("strike_rate", 0) or 0
            avg = bat_stats.get("average", 0) or 0
            if sr > 110 or avg > 25:
                our_batters.append((p["id"], sr, avg, p.get("name", "")))

    # Get top bowlers from opponent (good economy)
    opp_bowlers = []
    for p in opponent_squad:
        if p.get("role") in ("bowler", "all_rounder"):
            bowl_stats = p.get("t20i_stats", {}).get("bowling", {}) or {}
            economy = bowl_stats.get("economy", 99) or 99
            innings = bowl_stats.get("innings", 0) or 0
            if economy < 7.5 and innings >= 5:
                opp_bowlers.append((p["id"], economy, p.get("name", "")))

    # Sort by quality
    our_batters.sort(key=lambda x: x[1], reverse=True)  # By strike rate
    opp_bowlers.sort(key=lambda x: x[1])  # By economy (lower is better)

    our_batters = our_batters[:4]  # Top 4
    opp_bowlers = opp_bowlers[:3]  # Top 3

    bonus = 0.0

    # Fallback: find matchups with loose matching (case-insensitive search in keys)
    def find_matchup_loose(matchups: Dict, batter_id: str, bowler_id: str) -> Optional[Dict]:
        """Try multiple matching strategies to find batter-vs-bowler matchup."""
        # Strategy 1: Exact match (most common case)
        key = f"{batter_id}::{bowler_id}"
        if key in matchups:
            return matchups[key]

        # Strategy 2: Try with underscores/spaces variations
        # The database might have "arundhati_reddy" stored as "Arundhati Reddy"
        batter_parts = batter_id.lower().replace("_", " ").split()
        bowler_parts = bowler_id.lower().replace("_", " ").split()

        for k, v in matchups.items():
            k_lower = k.lower()
            # Check if key contains the player names (allow flexible matching)
            if all(part in k_lower for part in batter_parts) and all(part in k_lower for part in bowler_parts):
                return v
        return None

    # Check matchups between our top batters and their top bowlers
    for batter_id, batter_sr, batter_avg, batter_name in our_batters:
        for bowler_id, bowler_econ, bowler_name in opp_bowlers:
            matchup = find_matchup_loose(matchups, batter_id, bowler_id)
            if matchup:
                matchup_sr = matchup.get("strike_rate", 0)
                # Phase 2 Task 6: Lower threshold from 120 to 110 for more coverage
                if matchup_sr > 110:
                    # Moderately strong to elite batter advantage (>110 SR in h2h)
                    bonus += 1.5  # +1.5 runs per favorable matchup

    # Cap bonus and return (max +5 runs from this factor)
    return min(5.0, bonus)


def _calculate_variable_chase_penalty(
    pitch_difficulty: str,
    opponent_squad: List[Dict],
    matchups: Dict[str, Any],
) -> float:
    """
    Phase 2 Task 5: Calculate dynamic chase penalty based on opponent bowling strength.

    Replaces fixed penalty (-15 to -30) with economy-based calibration.

    Base penalties by pitch:
    - spin_friendly: -15
    - seam_friendly: -20
    - flat: -10
    - balanced: -15

    Adjustments:
    - Weak opponent bowling (economy > 8.0): +3 (less penalty)
    - Strong opponent bowling (economy < 7.0): -3 (more penalty)
    - Elite batter-bowler matchups: -1 per matchup (reduces penalty)

    Returns: Adjusted chase penalty (e.g., -12 to -23)
    """
    # Base penalty by pitch type
    base_penalties = {
        "spin_friendly": -15,
        "seam_friendly": -20,
        "flat": -10,
        "balanced": -15,
    }
    base_penalty = base_penalties.get(pitch_difficulty, -15)

    # Calculate opponent bowling economy (top 3 bowlers)
    opponent_economies = []
    for bowler in opponent_squad[:5]:  # Check top bowlers
        economy = bowler.get("economy", 8.0)
        if isinstance(economy, (int, float)):
            opponent_economies.append(economy)

    if opponent_economies:
        # Use average of available economies (or top 3)
        top_economies = sorted(opponent_economies)[:3]
        avg_economy = sum(top_economies) / len(top_economies) if top_economies else 8.0
    else:
        avg_economy = 8.0

    # Adjust based on bowling economy
    if avg_economy > 8.0:  # Weak bowling
        economy_adjustment = 3  # Less penalty needed
    elif avg_economy < 7.0:  # Strong bowling
        economy_adjustment = -3  # More penalty appropriate
    else:
        economy_adjustment = 0

    # Count elite batter-bowler matchups (further reduce penalty if we have advantages)
    # This is a simplified check; more sophisticated matching in actual implementation
    elite_matchups = 0  # Could be enhanced to count actual elite matchups
    matchup_adjustment = -elite_matchups * 1.0

    # Combine adjustments
    final_penalty = base_penalty + economy_adjustment + matchup_adjustment

    # Cap the penalty to reasonable bounds
    return max(-25.0, min(-5.0, final_penalty))


def _calculate_recent_form_bonus(analyst_insights: Dict[str, Any], scenario: str, our_squad: List[Dict]) -> Dict[str, Any]:
    """
    Phase 2 Task 4: Calculate runs and WP bonus for recent star performances.

    Identifies breakout performers from analyst_insights:
    - Exceptional form rating: +3 runs, +2% WP
    - Multiple strong scores in notes: +2 runs, +1% WP (batting_first only)

    Returns: {"runs_bonus": float, "wp_bonus": float}
    """
    runs_bonus = 0.0
    wp_bonus = 0.0

    if not analyst_insights or not our_squad:
        return {"runs_bonus": runs_bonus, "wp_bonus": wp_bonus}

    # Check each player in our squad for recent form
    for player in our_squad:
        player_id = player.get("id", "")
        if not player_id:
            continue

        # Look up player in analyst_insights
        player_insights = analyst_insights.get(player_id, {})
        if not player_insights:
            continue

        # Check overall form rating
        overall_form = player_insights.get("overall_form", {})
        rating = overall_form.get("rating", "").lower()
        notes = overall_form.get("notes", "").lower()

        # Exceptional form: +3 runs, +2% WP
        if rating == "exceptional":
            runs_bonus += 3.0
            wp_bonus += 0.02

        # Strong form with evidence of recent success: +2 runs, +1% WP (batting_first only)
        elif rating == "strong" and scenario == "batting_first":
            # Look for signs of recent success in notes
            has_consecutive_scores = any(phrase in notes for phrase in ["consecutive", "runs in last", "last t20i series", "recent"])
            if has_consecutive_scores:
                runs_bonus += 2.0
                wp_bonus += 0.01

    # Cap the bonuses to avoid over-application
    return {
        "runs_bonus": min(runs_bonus, 10.0),  # Cap at +10 runs
        "wp_bonus": min(wp_bonus, 0.08),  # Cap at +8% WP
    }


def _calculate_pitch_calibration_adjustment(
    pitch_difficulty: str,
    venue_data: Dict[str, Any],
    scenario: str,
    base_runs: float,
    series_score: int = 0,
) -> float:
    """
    Apply second-order pitch effects based on scenario and venue combination.

    Instead of flat pitch adjustments, consider:
    - Flat pitch + home advantage → higher runs
    - Spin pitch + aggressive batting → less suppression (especially when dominant)
    - Pace pitch + chase scenario → more runs penalty

    Returns: Adjustment runs (negative or positive)
    """
    pitch_type = venue_data.get("pitch", {}).get("type", "balanced")

    # Base pitch adjustments (from venue_pace_score)
    base_adjustments = {
        "flat": 8.0,          # Current: flat pitches → +8 runs
        "balanced": 0.0,      # Current: no adjustment
        "spin_friendly": -15.0,  # Current: spin → -15 runs
        "seam_friendly": -5.0,   # Current: seam → -5 runs
    }

    base_adjustment = base_adjustments.get(pitch_type, 0.0)
    additional = 0.0

    # Second-order effect 1: Flat pitch + home/series momentum
    # (Model currently gives +8, but flat pitches at home with momentum get +15-20)
    if pitch_type == "flat" and scenario == "batting_first":
        additional = 8.0  # Increase from base +8 to effective +16

    # Second-order effect 2: Spin pitch + aggressive batting in dominant series
    # (Model currently suppresses -15, but dominant home teams (3-0+) score much better)
    # Validation showed India vs SL Match 4: spin -15 penalty was too aggressive
    # Phase 2 refinement: elite teams at home with dominant series position → no suppression
    elif pitch_type == "spin_friendly" and scenario == "batting_first":
        if series_score >= 3:
            # Dominant home team on spin pitch: elite scenario, minimal/no suppression
            # Changed from -5 to 0 (no penalty) when dominant
            additional = 15.0  # Reduce penalty from -15 to 0 effectively
        else:
            # Normal case: home team batting on spin pitch with momentum is less suppressed
            additional = 5.0  # Reduce penalty from -15 to -10 effectively

    # Second-order effect 3: Pace pitch + chase scenario
    # (Chasing on pace is harder; currently -15 base. No additional for chasing)
    elif pitch_type == "seam_friendly" and scenario == "chasing":
        additional = -3.0  # Increase penalty slightly for pace + chase difficulty

    # Cap the total adjustment
    total_adjustment = base_adjustment + additional
    return max(-20.0, min(20.0, total_adjustment))


def prediction_node(state: PreMatchState) -> Dict[str, Any]:
    """
    Compute runs estimate and win probability, applying scenario adjustments.

    Flow:
      1. Monte Carlo → raw base_runs and raw win_probability
      2. ScenarioHandler.adjust_runs_prediction() → applies chase penalty
      3. ScenarioHandler.adjust_win_probability() → reduces prob for chasing
      4. Batter-vs-Bowler specificity → apply matchup boost for elite matchups
      5. Series Momentum → apply aggression boost for dominant series position
      6. (Phase 2 Task 3) Series Context Awareness → adjust momentum based on sweep likelihood
    """
    our_squad = state.get("our_squad", [])
    opponent_squad = state.get("opponent_squad", [])
    analyst_insights = state.get("analyst_insights", {})
    team_id = state.get("team_id", "")
    opponent_id = state.get("opponent_id", "")
    venue_data = state.get("venue_data", {})
    scenario = state.get("scenario", "unknown")
    pitch_difficulty = state.get("pitch_difficulty", "moderate")
    chase_penalty = state.get("chase_penalty", 0)
    matchups = state.get("matchups", {})
    series_score = state.get("series_score", 0)  # For context-aware pitch adjustment

    # Derive strength scores
    our_bat = squad_batting_strength(our_squad, analyst_insights, team_id)
    their_bat = squad_batting_strength(opponent_squad, analyst_insights, opponent_id)
    our_bowl = squad_bowling_strength(our_squad)
    their_bowl = squad_bowling_strength(opponent_squad)

    pace_score = venue_pace_score(venue_data)
    venue_factor = min(1.0, pace_score / 10.0)

    # Monte Carlo simulation
    mc_result = estimate_win_probability(
        our_batting_strength=our_bat,
        opponent_batting_strength=their_bat,
        our_bowling_strength=our_bowl,
        opponent_bowling_strength=their_bowl,
        venue_factor=venue_factor,
        n_simulations=10_000,
    )

    base_runs = mc_result["our_avg_score"]

    # Apply scenario adjustments via ScenarioHandler
    handler = ScenarioHandler()
    toss_winner = state.get("toss_winner")
    toss_decision = state.get("toss_decision")
    if toss_winner and toss_decision:
        handler.set_toss(winner=toss_winner, decision=toss_decision)
        handler.identify_scenario(team_id, state.get("opponent_id", ""))

    confidence = 0.75 if scenario != "unknown" else 0.50
    runs_result = handler.adjust_runs_prediction(base_runs, pitch_difficulty, confidence)
    win_result = handler.adjust_win_probability(
        base_win_prob=mc_result["win_probability"],
        pitch_difficulty=pitch_difficulty,
        is_chasing=(scenario == "chasing"),
    )

    # Phase 2 Task 5: Override fixed chase penalty with variable calculation
    # When chasing, replace the standard penalty with economy-based calibration
    if scenario == "chasing":
        variable_penalty = _calculate_variable_chase_penalty(pitch_difficulty, opponent_squad, matchups)
        fixed_penalty = chase_penalty
        if variable_penalty != fixed_penalty:
            # Apply the difference to runs_result
            penalty_difference = variable_penalty - fixed_penalty
            runs_result["adjusted_runs"] += penalty_difference
            runs_result["adjusted_runs"] = round(runs_result["adjusted_runs"], 1)
            if "upper_bound" in runs_result:
                runs_result["upper_bound"] += penalty_difference
            if "lower_bound" in runs_result:
                runs_result["lower_bound"] += penalty_difference
            # Update chase_penalty in state for reporting
            chase_penalty = variable_penalty

    # ── Pitch Calibration Refinement ───────────────────────────────────────────
    # Apply second-order pitch effects (e.g., flat + home → more runs, not just +8)
    # Now context-aware: reduce spin suppression when team is dominant (3-0+)
    pitch_adjustment = _calculate_pitch_calibration_adjustment(
        pitch_difficulty, venue_data, scenario, base_runs, series_score
    )
    if pitch_adjustment != 0:
        runs_result["adjusted_runs"] += pitch_adjustment
        runs_result["adjusted_runs"] = round(runs_result["adjusted_runs"], 1)
        pitch_reasoning = f" (pitch 2nd-order: {pitch_adjustment:+.0f} runs)"
    else:
        pitch_reasoning = ""

    # ── Batter-vs-Bowler Specificity Enhancement ───────────────────────────────
    # In chase scenarios, weight elite batter-vs-bowler matchups (e.g., Mandhana vs Ismail)
    batter_bowler_boost = _calculate_batter_bowler_boost(our_squad, opponent_squad, matchups, scenario)
    if batter_bowler_boost > 0:
        runs_result["adjusted_runs"] += batter_bowler_boost
        runs_result["adjusted_runs"] = round(runs_result["adjusted_runs"], 1)
        win_result["adjusted_win_probability"] = min(0.95, win_result["adjusted_win_probability"] + batter_bowler_boost * 0.01)
        batter_bowler_reasoning = f" (+{batter_bowler_boost:.0f} runs from elite matchup advantage)"
    else:
        batter_bowler_reasoning = ""

    # ── Recent Form Bonus (Phase 2 Task 4) ────────────────────────────────────
    # Boost predictions for players in exceptional form or with recent breakout performances
    form_bonus_result = _calculate_recent_form_bonus(analyst_insights, scenario, our_squad)
    form_runs_bonus = form_bonus_result.get("runs_bonus", 0.0)
    form_wp_bonus = form_bonus_result.get("wp_bonus", 0.0)

    if form_runs_bonus > 0:
        runs_result["adjusted_runs"] += form_runs_bonus
        runs_result["adjusted_runs"] = round(runs_result["adjusted_runs"], 1)
        if "upper_bound" in runs_result:
            runs_result["upper_bound"] += form_runs_bonus
        if "lower_bound" in runs_result:
            runs_result["lower_bound"] += form_runs_bonus
        win_result["adjusted_win_probability"] = min(0.95, win_result["adjusted_win_probability"] + form_wp_bonus)
        form_reasoning = f" (+{form_runs_bonus:.0f} runs from recent form bonus)"
    else:
        form_reasoning = ""

    # ── Series Momentum Factor ─────────────────────────────────────────────────
    # If team is up 3-0 or better in series and batting first, apply aggression boost
    series_score = state.get("series_score", 0)
    series_number = state.get("series_number", 0)
    batting_first_scenario = (toss_winner == team_id and toss_decision == "bat_first")

    series_momentum_reasoning = ""
    if series_score >= 3 and batting_first_scenario:
        # Determine multiplier based on series stage and lead
        # After Match 3: if 3-0, potential for 5-0 sweep → stronger aggression
        # This addresses cases like India vs SL Match 4 (3-0 up, still room for whitewash)
        if series_score == 3 and series_number >= 4:
            # Potential 5-0 scenario: boost aggression based on team aggressiveness
            # Aggressive teams (India, West Indies, Pakistan) get +30%
            # Conservative teams (NZ, SA, Australia, etc.) get +25%
            # Phase 2 Task 3: Adjust based on series context / sweep likelihood
            team_for_momentum = team_id.lower() if team_id else ""
            sweep_likelihood = state.get("sweep_likelihood", 1.0)  # Default: assume sweep is likely

            if team_for_momentum in ("india", "west_indies", "pakistan"):
                # Aggressive teams in sweep scenarios: base +30%, adjusted by likelihood
                # 1.30 + (likelihood - 1.0) * 0.10 = range from 1.20 to 1.30
                base_multiplier = 1.30
                likelihood_adjustment = (sweep_likelihood - 1.0) * 0.10
                aggression_multiplier = max(1.15, base_multiplier + likelihood_adjustment)
                wp_bonus = 0.07 + (0.02 * sweep_likelihood)  # 0.07 to 0.09
            else:
                # Conservative teams: base +25%, adjusted by likelihood
                # 1.25 + (likelihood - 1.0) * 0.10 = range from 1.15 to 1.25
                base_multiplier = 1.25
                likelihood_adjustment = (sweep_likelihood - 1.0) * 0.10
                aggression_multiplier = max(1.10, base_multiplier + likelihood_adjustment)
                wp_bonus = 0.06 + (0.02 * sweep_likelihood)  # 0.06 to 0.08

            momentum_type = "sweep"
        else:
            # Standard 3-0 or 4-0 lead (series effectively decided)
            aggression_multiplier = 1.15
            momentum_type = "dominant"
            wp_bonus = 0.05

        runs_result["adjusted_runs"] *= aggression_multiplier
        runs_result["adjusted_runs"] = round(runs_result["adjusted_runs"], 1)
        if "upper_bound" in runs_result:
            runs_result["upper_bound"] *= aggression_multiplier
            runs_result["upper_bound"] = round(runs_result["upper_bound"], 1)
        if "lower_bound" in runs_result:
            runs_result["lower_bound"] *= aggression_multiplier
            runs_result["lower_bound"] = round(runs_result["lower_bound"], 1)

        # WP boost
        original_wp = win_result["adjusted_win_probability"]
        win_result["adjusted_win_probability"] = min(0.95, original_wp + wp_bonus)

        multiplier_pct = int((aggression_multiplier - 1) * 100)
        series_momentum_reasoning = f" ({momentum_type} series {series_score}-0, match {series_number}: +{multiplier_pct}% runs, +{int(wp_bonus*100)}% WP)"

    win_reasoning = win_result["reasoning"] + pitch_reasoning + batter_bowler_reasoning + form_reasoning + series_momentum_reasoning
    if scenario == "unknown":
        win_reasoning += " (toss not yet known — confidence reduced)"

    return {
        "base_runs_estimate": round(base_runs, 1),
        "adjusted_runs_estimate": round(runs_result["adjusted_runs"], 1),
        "runs_lower": round(runs_result.get("lower_bound", base_runs - 10), 1),
        "runs_upper": round(runs_result.get("upper_bound", base_runs + 10), 1),
        "win_probability": round(win_result["adjusted_win_probability"], 3),
        "win_probability_reasoning": win_reasoning,
    }


# ---------------------------------------------------------------------------
# Main pipeline runner
# ---------------------------------------------------------------------------

def _run_pipeline_single(
    team_id: str,
    opponent_id: str,
    venue_id: str,
    match_date: str,
    toss_winner: Optional[str],
    toss_decision: Optional[str],
    series_number: int = 0,
    series_score: int = 0,
    sweep_likelihood: float = 1.0,
) -> PreMatchState:
    """Internal: run the pipeline for one specific toss outcome."""
    state: PreMatchState = {
        "team_id": team_id,
        "opponent_id": opponent_id,
        "venue_id": venue_id,
        "match_date": match_date,
        "toss_winner": toss_winner,
        "toss_decision": toss_decision,
        "series_number": series_number,
        "series_score": series_score,
        "sweep_likelihood": sweep_likelihood,
        "errors": [],
        "warnings": [],
    }

    pipeline = [
        ("data", data_node),
        ("scenario", scenario_node),
        ("opponent_analysis", opponent_analysis_node),
        ("squad_selector", squad_selector_node),
        ("batting_order", batting_order_node),
        ("bowling_plan", bowling_plan_node),
        ("prediction", prediction_node),
        ("strategy", strategy_node),
    ]

    for node_name, node_fn in pipeline:
        try:
            updates = node_fn(state)
            state.update(updates)
        except Exception as e:
            state["errors"] = state.get("errors", []) + [f"{node_name}: {e}"]

    return state


def run_pre_match_pipeline(
    team_id: str,
    opponent_id: str,
    venue_id: str,
    match_date: str = "",
    toss_winner: Optional[str] = None,
    toss_decision: Optional[str] = None,
    series_number: int = 0,
    series_score: int = 0,
    sweep_likelihood: float = 1.0,
) -> PreMatchState:
    """
    Run the full pre-match pipeline and return completed state.

    When toss_winner is known, runs one scenario path.
    When toss_winner is None (pre-toss), runs BOTH scenarios (batting_first
    and chasing) and blends the results 50/50 — because either outcome is
    equally likely before the coin is flipped.

    The returned state includes:
      - `batting_first_scenario`: full state snapshot for batting-first path
      - `chasing_scenario`: full state snapshot for chasing path
      - Blended headline figures in the top-level fields (runs, win_probability)
      - `scenario` = "pre_toss_blended" to distinguish from toss-known runs

    Args:
        team_id: Our team (e.g. "india")
        opponent_id: Opponent (e.g. "south_africa")
        venue_id: Venue slug (e.g. "lords")
        match_date: ISO date string (e.g. "2026-06-17")
        toss_winner: team_id of toss winner, or None if toss not yet known
        toss_decision: "bat_first" or "bowl_first", or None
        series_number: Which match in series (e.g. 4 for 4th match)
        series_score: Number of matches won in series so far by our team

    Returns:
        Completed PreMatchState with all fields populated
    """
    # ──────────────────────────────────────────────────────────────────────────
    # VALIDATION GATE: Hard fail on invalid inputs
    # ──────────────────────────────────────────────────────────────────────────
    from wt20_oracle.validation import validate_match_inputs
    from wt20_oracle.io.loader import _read

    venues_data = _read(Path(__file__).parent / "data" / "venues.json")
    validation = validate_match_inputs(
        team_id,
        opponent_id,
        venue_id,
        match_date,
        toss_winner,
        toss_decision,
        venues_data,
    )

    if not validation.valid:
        # Hard fail: return early with error state
        return {
            "team_id": team_id,
            "opponent_id": opponent_id,
            "venue_id": venue_id,
            "match_date": match_date,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "scenario": None,
            "win_probability": None,
            "adjusted_runs_estimate": None,
            "runs_lower": None,
            "runs_upper": None,
            "selected_xi": [],
            "batting_order": [],
            "bowling_plan": [],
            "strategy_brief": None,
            "key_matchups": [],
            "tactical_flags": [],
        }

    if toss_winner is not None:
        # Toss known — single deterministic path
        return _run_pipeline_single(
            team_id, opponent_id, venue_id, match_date, toss_winner, toss_decision,
            series_number, series_score, sweep_likelihood
        )

    # ── Pre-toss: run both scenarios and blend ────────────────────────────────
    #
    # Scenario A: we win toss and bat first
    state_bat = _run_pipeline_single(
        team_id, opponent_id, venue_id, match_date,
        toss_winner=team_id,
        toss_decision="bat_first",
        series_number=series_number,
        series_score=series_score,
        sweep_likelihood=sweep_likelihood,
    )

    # Scenario B: opponent wins toss and bats first → we chase
    state_chase = _run_pipeline_single(
        team_id, opponent_id, venue_id, match_date,
        toss_winner=opponent_id,
        toss_decision="bat_first",
        series_number=series_number,
        series_score=series_score,
        sweep_likelihood=sweep_likelihood,
    )

    # ── Blend headline numbers (equal 50/50 weight) ───────────────────────────
    bat_runs = state_bat.get("adjusted_runs_estimate") or 0.0
    chase_runs = state_chase.get("adjusted_runs_estimate") or 0.0
    bat_lower = state_bat.get("runs_lower") or 0.0
    chase_lower = state_chase.get("runs_lower") or 0.0
    bat_upper = state_bat.get("runs_upper") or 0.0
    chase_upper = state_chase.get("runs_upper") or 0.0
    bat_wp = state_bat.get("win_probability") or 0.5
    chase_wp = state_chase.get("win_probability") or 0.5

    blended_runs = round((bat_runs + chase_runs) / 2, 1)
    blended_lower = round((bat_lower + chase_lower) / 2, 1)
    blended_upper = round((bat_upper + chase_upper) / 2, 1)
    blended_wp = round((bat_wp + chase_wp) / 2, 3)

    # Combine errors / warnings from both paths
    all_errors = (state_bat.get("errors") or []) + (state_chase.get("errors") or [])
    all_warnings = (state_bat.get("warnings") or []) + (state_chase.get("warnings") or [])

    # Base the merged state on the batting-first path (XI, bowling plan are
    # scenario-independent at this stage), then overlay blended numbers
    merged: PreMatchState = {
        **state_bat,
        # Blended headline fields
        "scenario": "pre_toss_blended",
        "adjusted_runs_estimate": blended_runs,
        "base_runs_estimate": round((
            (state_bat.get("base_runs_estimate") or 0.0) +
            (state_chase.get("base_runs_estimate") or 0.0)
        ) / 2, 1),
        "runs_lower": blended_lower,
        "runs_upper": blended_upper,
        "win_probability": blended_wp,
        "win_probability_reasoning": (
            f"Pre-toss blend: batting-first WP={bat_wp:.1%}, "
            f"chasing WP={chase_wp:.1%} → blended {blended_wp:.1%}"
        ),
        "chase_penalty": state_chase.get("chase_penalty", 0),
        # Per-scenario snapshots for downstream analysis
        "batting_first_scenario": {
            "scenario": state_bat.get("scenario"),
            "adjusted_runs_estimate": bat_runs,
            "runs_lower": bat_lower,
            "runs_upper": bat_upper,
            "win_probability": bat_wp,
            "pitch_difficulty": state_bat.get("pitch_difficulty"),
            "chase_penalty": 0,
            "tactical_flags": state_bat.get("tactical_flags"),
            "strategy_brief": state_bat.get("strategy_brief"),
        },
        "chasing_scenario": {
            "scenario": state_chase.get("scenario"),
            "adjusted_runs_estimate": chase_runs,
            "runs_lower": chase_lower,
            "runs_upper": chase_upper,
            "win_probability": chase_wp,
            "pitch_difficulty": state_chase.get("pitch_difficulty"),
            "chase_penalty": state_chase.get("chase_penalty", 0),
            "tactical_flags": state_chase.get("tactical_flags"),
            "strategy_brief": state_chase.get("strategy_brief"),
        },
        "errors": all_errors,
        "warnings": all_warnings,
        # Clear toss fields — not yet known
        "toss_winner": None,
        "toss_decision": None,
    }

    return merged
