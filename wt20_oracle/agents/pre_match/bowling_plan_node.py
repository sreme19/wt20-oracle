"""
Bowling Plan Node
=================

Assigns bowlers to phases (powerplay, middle, death) for the selected XI.
Respects the 4-over maximum per bowler in T20I cricket.
Uses matchup data and pitch type to prioritise bowler selection.
"""

from typing import Any, Dict, List

from wt20_oracle.state import PreMatchState
from wt20_oracle.io.loader import get_player


# Phase over allocations (T20 = 20 overs total)
PHASE_OVERS = {
    "powerplay": 6,   # overs 1-6
    "middle": 9,      # overs 7-15
    "death": 5,       # overs 16-20
}

MAX_OVERS_PER_BOWLER = 4


def bowling_plan_node(state: PreMatchState) -> Dict[str, Any]:
    """LangGraph node: build bowling plan."""
    selected_xi = state.get("selected_xi", [])
    our_squad = state.get("our_squad", [])
    venue_data = state.get("venue_data", {})
    matchups = state.get("matchups", {})
    opponent_squad = state.get("opponent_squad", [])
    analyst_insights = state.get("analyst_insights", {})
    team_id = state.get("team_id", "")
    scenario = state.get("scenario", "unknown")

    pitch_type = venue_data.get("pitch", {}).get("type", "balanced")
    spin_pitch = pitch_type == "spin_friendly"
    pace_pitch = pitch_type in ("seam_friendly", "flat")

    # Identify bowlers from the XI
    bowlers = _identify_bowlers(selected_xi, our_squad)
    if not bowlers:
        return {
            "bowling_plan": [],
            "bowling_reasoning": "No bowlers identified in selected XI",
        }

    # Score each bowler per phase
    phase_assignments = _assign_phases(bowlers, our_squad, pitch_type, analyst_insights, team_id)

    # Build plan output
    plan = []
    for pid, phases in phase_assignments.items():
        player = get_player(our_squad, pid)
        name = player.get("name", pid) if player else pid
        bowl_stats = (player or {}).get("t20i_stats", {}).get("bowling") or {}
        economy = bowl_stats.get("economy", 7.5)

        for phase in phases:
            plan.append({
                "player_id": pid,
                "player_name": name,
                "phase": phase,
                "max_overs": MAX_OVERS_PER_BOWLER,
                "economy": economy,
                "rationale": _phase_rationale(pid, player, phase, pitch_type, spin_pitch, pace_pitch),
            })

    reasoning = _build_bowling_reasoning(bowlers, our_squad, pitch_type, scenario)

    return {
        "bowling_plan": plan,
        "bowling_reasoning": reasoning,
    }


def _identify_bowlers(selected_xi: List[str], squad: List[Dict]) -> List[str]:
    """Return player IDs from XI who can bowl."""
    bowlers = []
    for pid in selected_xi:
        player = get_player(squad, pid)
        if not player:
            continue
        role = player.get("role", "")
        bowl_stats = player.get("t20i_stats", {}).get("bowling") or {}
        innings = bowl_stats.get("innings", 0) or 0
        # Include all-rounders, bowlers, and anyone with 5+ bowling innings
        if role in ("bowler", "all_rounder") or innings >= 5:
            bowlers.append(pid)
    return bowlers


def _assign_phases(
    bowlers: List[str],
    squad: List[Dict],
    pitch_type: str,
    analyst_insights: Dict,
    team_id: str,
) -> Dict[str, List[str]]:
    """
    Assign bowlers to phases based on their specialist stats.

    Returns {player_id: [list of phases they should bowl in]}
    """
    assignments: Dict[str, List[str]] = {pid: [] for pid in bowlers}
    spin_pitch = pitch_type == "spin_friendly"
    pace_pitch = pitch_type in ("seam_friendly", "flat")

    for pid in bowlers:
        player = get_player(squad, pid)
        if not player:
            continue

        bowl_stats = player.get("t20i_stats", {}).get("bowling") or {}
        style = player.get("bowling_style", "")
        is_spinner = "spin" in style or "orthodox" in style or "wrist" in style

        pp_specialist = bowl_stats.get("powerplay_specialist", False)
        death_specialist = bowl_stats.get("death_specialist", False)

        phase_splits = bowl_stats.get("phase_splits", {})
        pp_econ = phase_splits.get("powerplay", {}).get("economy", 99)
        mid_econ = phase_splits.get("middle", {}).get("economy", 99)
        death_econ = phase_splits.get("death", {}).get("economy", 99)

        # Powerplay
        if pp_specialist or (pp_econ is not None and pp_econ < 7.0):
            if not (spin_pitch and not is_spinner):  # Don't use pace-only in spin conditions
                assignments[pid].append("powerplay")

        # Middle overs — spinners preferred on spin pitches
        if (spin_pitch and is_spinner) or (not spin_pitch):
            if mid_econ is None or mid_econ < 8.0:
                assignments[pid].append("middle")

        # Death overs
        if death_specialist or (death_econ is not None and death_econ < 8.5):
            assignments[pid].append("death")

        # Ensure every bowler gets at least one phase
        if not assignments[pid]:
            assignments[pid].append("middle")  # Default: middle overs

    return assignments


def _phase_rationale(
    pid: str,
    player: Dict,
    phase: str,
    pitch_type: str,
    spin_pitch: bool,
    pace_pitch: bool,
) -> str:
    if not player:
        return f"Assigned to {phase} overs"

    name = player.get("name", pid)
    style = player.get("bowling_style", "")
    bowl_stats = player.get("t20i_stats", {}).get("bowling") or {}
    splits = bowl_stats.get("phase_splits", {})
    phase_econ = splits.get(phase, {}).get("economy")

    pitch_note = ""
    if spin_pitch and ("spin" in style):
        pitch_note = " (spin pitch advantage)"
    elif pace_pitch and ("pace" in style or "medium" in style):
        pitch_note = " (pace pitch advantage)"

    if phase_econ:
        return f"{name}: {phase} specialist, economy {phase_econ:.1f}{pitch_note}"
    return f"{name}: assigned {phase} overs{pitch_note}"


def _build_bowling_reasoning(
    bowler_ids: List[str],
    squad: List[Dict],
    pitch_type: str,
    scenario: str,
) -> str:
    count = len(bowler_ids)
    names = []
    for pid in bowler_ids[:4]:
        p = get_player(squad, pid)
        if p:
            names.append(p.get("name", pid))

    pitch_note = {
        "spin_friendly": "spin-friendly pitch — spinners prioritised in middle overs",
        "seam_friendly": "seam-friendly conditions — pace bowlers to exploit movement",
        "flat": "flat pitch — containment strategy, mix of pace and spin",
        "balanced": "balanced conditions — standard rotation",
    }.get(pitch_type, "balanced conditions")

    scenario_note = ""
    if scenario == "chasing":
        scenario_note = " Defending a target — aggressive line and length to restrict."

    return (
        f"{count} bowlers available: {', '.join(names)}{'...' if count > 4 else ''}. "
        f"{pitch_note}.{scenario_note}"
    )
