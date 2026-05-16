"""
Strategy Node
=============

Synthesises all upstream outputs into a cohesive tactical brief.

This node is the final assembly point before the CLI narrator formats
the recommendation. It calls ScenarioHandler to produce the scenario
report, ScenarioMetrics for a pre-match confidence score, and
structures the key matchups for the narrative.
"""

from typing import Any, Dict, List

from wt20_oracle.state import PreMatchState
from wt20_oracle.io.loader import get_player
from wt20_oracle.optimisation.matchup_matrix import find_favourable_matchups, find_dangerous_matchups

# New retraining framework modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from testing.prediction_pipeline.scenario_handler import ScenarioHandler
from testing.validation.scenario_metrics import ScenarioMetrics, get_assessment


def strategy_node(state: PreMatchState) -> Dict[str, Any]:
    """LangGraph node: synthesise strategy brief."""
    team_id = state.get("team_id", "")
    opponent_id = state.get("opponent_id", "")
    venue_data = state.get("venue_data", {})
    scenario = state.get("scenario", "unknown")
    adjusted_runs = state.get("adjusted_runs_estimate", 0)
    win_probability = state.get("win_probability", 0.5)
    selected_xi = state.get("selected_xi", [])
    batting_order = state.get("batting_order", [])
    bowling_plan = state.get("bowling_plan", [])
    our_squad = state.get("our_squad", [])
    opponent_squad = state.get("opponent_squad", [])
    matchups = state.get("matchups", {})
    toss_winner = state.get("toss_winner")
    toss_decision = state.get("toss_decision")
    chase_penalty = state.get("chase_penalty", 0)

    # ── Key matchups ───────────────────────────────────────────────────────
    our_top_batters = [pid for pid in (batting_order or selected_xi)[:6]]
    opponent_bowler_ids = [
        p["id"] for p in opponent_squad
        if p.get("role") in ("bowler", "all_rounder")
    ][:6]
    our_bowler_ids = [
        entry["player_id"] for entry in bowling_plan
        if entry.get("player_id")
    ]
    opponent_batter_ids = [p["id"] for p in opponent_squad[:6]]

    favourable = find_favourable_matchups(matchups, our_top_batters, opponent_bowler_ids)
    dangerous = find_dangerous_matchups(matchups, opponent_batter_ids, our_bowler_ids)

    key_matchups = [
        {
            "type": "exploit",
            "batter": m["batter"],
            "bowler": m["bowler"],
            "insight": m["insight"],
        }
        for m in favourable
    ] + [
        {
            "type": "threat",
            "opponent_batter": m["opponent_batter"],
            "our_bowler": m["our_bowler"],
            "insight": m["insight"],
        }
        for m in dangerous
    ]

    # ── Tactical flags ─────────────────────────────────────────────────────
    flags = _build_tactical_flags(state, venue_data, scenario)

    # ── Strategy brief ─────────────────────────────────────────────────────
    brief = _build_strategy_brief(
        team_id=team_id,
        opponent_id=opponent_id,
        scenario=scenario,
        adjusted_runs=adjusted_runs,
        win_probability=win_probability,
        chase_penalty=chase_penalty,
        toss_winner=toss_winner,
        toss_decision=toss_decision,
        venue_data=venue_data,
        batting_order=batting_order,
        our_squad=our_squad,
        bowling_plan=bowling_plan,
        flags=flags,
    )

    return {
        "strategy_brief": brief,
        "key_matchups": key_matchups,
        "tactical_flags": flags,
    }


def _build_tactical_flags(state: PreMatchState, venue_data: Dict, scenario: str) -> List[str]:
    """Generate tactical flag list based on match context."""
    flags = []
    pitch_type = venue_data.get("pitch", {}).get("type", "balanced")

    if pitch_type == "spin_friendly":
        flags.append("prioritise_spinners_middle_overs")
    elif pitch_type in ("seam_friendly", "flat"):
        flags.append("use_pace_in_powerplay")

    dew = venue_data.get("conditions", {}).get("dew_factor", "low")
    if dew in ("medium", "high"):
        flags.append("dew_factor_affects_grip_and_swing")

    if scenario == "chasing":
        flags.append("chase_scenario_requires_calculated_aggression")
        flags.append("monitor_required_run_rate_per_phase")
    elif scenario == "batting_first":
        flags.append("set_par_total_conservative_approach_first_6_overs")

    win_prob = state.get("win_probability", 0.5)
    if win_prob < 0.40:
        flags.append("underdog_scenario_high_risk_strategy_required")
    elif win_prob > 0.65:
        flags.append("favourite_execute_standard_game_plan")

    return flags


def _build_strategy_brief(
    team_id: str,
    opponent_id: str,
    scenario: str,
    adjusted_runs: float,
    win_probability: float,
    chase_penalty: int,
    toss_winner: Any,
    toss_decision: Any,
    venue_data: Dict,
    batting_order: List[str],
    our_squad: List[Dict],
    bowling_plan: List[Dict],
    flags: List[str],
) -> str:
    """Compose plain-English strategy brief."""
    venue_name = venue_data.get("name", "the venue")
    pitch_type = venue_data.get("pitch", {}).get("type", "balanced")
    pitch_notes = venue_data.get("pitch", {}).get("notes", "")

    lines = []
    lines.append(f"STRATEGY BRIEF: {team_id.upper()} vs {opponent_id.upper()} at {venue_name}")
    lines.append("=" * 70)

    # Toss and scenario
    if toss_winner and toss_decision:
        lines.append(f"\nTOSS: {toss_winner} chose to {toss_decision.replace('_', ' ')}.")
    lines.append(f"SCENARIO: {scenario.replace('_', ' ').title()}")

    # Runs target / projection
    if scenario == "batting_first":
        lines.append(f"\nTARGET: Set a score of ~{adjusted_runs:.0f} runs.")
        lines.append("  → Aggressive powerplay (target 50+ in 6 overs).")
        lines.append("  → Consolidate in middle (build platform overs 7-15).")
        lines.append("  → Accelerate death (last 5 overs, target 50+ runs).")
    elif scenario == "chasing":
        lines.append(f"\nCHASE PLAN: Need ~{adjusted_runs:.0f} runs to win.")
        if chase_penalty != 0:
            lines.append(f"  (Chase penalty applied: {chase_penalty} runs vs batting-first estimate)")
        lines.append("  → Patient powerplay — don't lose more than 2 wickets.")
        lines.append("  → Accelerate from over 12 if on track.")
        lines.append("  → Keep wickets in hand for last 5 overs push.")
    else:
        lines.append(f"\nESTIMATED SCORE: ~{adjusted_runs:.0f} runs (toss outcome unknown)")

    # Win probability
    prob_pct = int(win_probability * 100)
    assessment = get_assessment(prob_pct)
    lines.append(f"\nWIN PROBABILITY: {prob_pct}% ({assessment})")

    # Pitch conditions
    lines.append(f"\nPITCH: {pitch_type.replace('_', ' ').title()}")
    if pitch_notes:
        lines.append(f"  {pitch_notes}")

    # Top batting order (first 4)
    if batting_order and our_squad:
        lines.append("\nBATTING ORDER (Top 4):")
        for pos, pid in enumerate(batting_order[:4], 1):
            player = get_player(our_squad, pid)
            name = player.get("name", pid) if player else pid
            sr = ((player or {}).get("t20i_stats") or {}).get("batting") or {}
            sr = sr.get("strike_rate") or 0
            lines.append(f"  {pos}. {name} (SR {sr:.0f})")

    # Key bowlers
    phase_bowlers = {}
    for entry in bowling_plan:
        phase = entry.get("phase", "middle")
        if phase not in phase_bowlers:
            phase_bowlers[phase] = []
        phase_bowlers[phase].append(entry.get("player_name", entry.get("player_id", "?")))

    if phase_bowlers:
        lines.append("\nBOWLING PLAN:")
        for phase in ("powerplay", "middle", "death"):
            bowlers = phase_bowlers.get(phase, [])
            if bowlers:
                lines.append(f"  {phase.title()}: {', '.join(set(bowlers))}")

    # Tactical flags
    if flags:
        lines.append("\nTACTICAL NOTES:")
        for flag in flags:
            lines.append(f"  • {flag.replace('_', ' ').capitalize()}")

    lines.append("\n" + "=" * 70)
    return "\n".join(lines)
