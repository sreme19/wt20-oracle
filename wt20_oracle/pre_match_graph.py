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

from typing import Any, Dict, Optional

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


def prediction_node(state: PreMatchState) -> Dict[str, Any]:
    """
    Compute runs estimate and win probability, applying scenario adjustments.

    Flow:
      1. Monte Carlo → raw base_runs and raw win_probability
      2. ScenarioHandler.adjust_runs_prediction() → applies chase penalty
      3. ScenarioHandler.adjust_win_probability() → reduces prob for chasing
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

    win_reasoning = win_result["reasoning"]
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
) -> PreMatchState:
    """Internal: run the pipeline for one specific toss outcome."""
    state: PreMatchState = {
        "team_id": team_id,
        "opponent_id": opponent_id,
        "venue_id": venue_id,
        "match_date": match_date,
        "toss_winner": toss_winner,
        "toss_decision": toss_decision,
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

    Returns:
        Completed PreMatchState with all fields populated
    """
    if toss_winner is not None:
        # Toss known — single deterministic path
        return _run_pipeline_single(
            team_id, opponent_id, venue_id, match_date, toss_winner, toss_decision
        )

    # ── Pre-toss: run both scenarios and blend ────────────────────────────────
    #
    # Scenario A: we win toss and bat first
    state_bat = _run_pipeline_single(
        team_id, opponent_id, venue_id, match_date,
        toss_winner=team_id,
        toss_decision="bat_first",
    )

    # Scenario B: opponent wins toss and bats first → we chase
    state_chase = _run_pipeline_single(
        team_id, opponent_id, venue_id, match_date,
        toss_winner=opponent_id,
        toss_decision="bat_first",
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
