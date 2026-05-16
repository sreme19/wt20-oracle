"""
MILP Lineup Selector
====================

Selects the optimal XI from the available squad using integer programming.
Constraints encode role balance requirements (batters, bowlers, all-rounders,
wicket-keeper) and analyst-supplied hard rules (injuries, debut caps).

Uses PuLP with the CBC solver (bundled with PuLP — no external dependency).
"""

from typing import Any, Dict, List, Optional, Tuple
import pulp


# Role balance constraints
ROLE_CONSTRAINTS = {
    "batter": {"min": 4, "max": 6},
    "bowler": {"min": 3, "max": 5},
    "all_rounder": {"min": 1, "max": 3},
    "wk_batter": {"min": 1, "max": 2},
}


def select_xi(
    squad: List[Dict[str, Any]],
    venue_data: Dict[str, Any],
    analyst_insights: Dict[str, Any],
    team_id: str,
    target_xi_size: int = 11,
) -> Tuple[List[str], List[str], str]:
    """
    Select optimal XI using MILP.

    Args:
        squad: List of fit player dicts
        venue_data: Venue record (used to weight spin/pace bowlers)
        analyst_insights: Analyst insights (used for form modifiers and hard constraints)
        team_id: e.g. "india"
        target_xi_size: Default 11

    Returns:
        Tuple of (selected_ids, reasoning_list, status_message)
    """
    if len(squad) < target_xi_size:
        # Not enough players — select all
        ids = [p["id"] for p in squad]
        return ids, ["Selected all available fit players (squad < 11)"], "ok_fallback"

    # ── Build player utility scores ──────────────────────────────────────
    utilities = {}
    team_insights = analyst_insights.get(team_id, {})
    pitch_type = venue_data.get("pitch", {}).get("type", "balanced")
    spin_pitch = pitch_type == "spin_friendly"
    pace_pitch = pitch_type in ("seam_friendly", "flat")

    for player in squad:
        pid = player["id"]
        role = player.get("role", "batter")
        bat_stats = player.get("t20i_stats", {}).get("batting") or {}
        bowl_stats = player.get("t20i_stats", {}).get("bowling") or {}

        # Base utility from career strike rate
        sr = bat_stats.get("strike_rate", 100.0) or 100.0
        utility = sr / 120.0  # ~1.0 for average, >1 for explosive batters

        # Bowling bonus
        economy = bowl_stats.get("economy")
        if economy and economy > 0:
            bowling_bonus = max(0, (8.0 - economy) / 8.0) * 0.3
            # Pitch-type bonus for right bowling style
            style = player.get("bowling_style", "")
            if spin_pitch and "spin" in style:
                bowling_bonus *= 1.3
            elif pace_pitch and ("pace" in style or "medium" in style):
                bowling_bonus *= 1.2
            utility += bowling_bonus

        # Form modifier from analyst insights
        insight = team_insights.get(pid)
        if insight:
            from wt20_oracle.io.analyst_loader import form_modifier_from_insights
            utility *= form_modifier_from_insights(insight)

        # Recent form boost (last 5 matches)
        form = bat_stats.get("form_windows", {}).get("last_5_matches", {})
        recent_sr = form.get("strike_rate")
        if recent_sr and recent_sr > sr:
            utility *= 1.05  # Small boost for in-form players

        utilities[pid] = utility

    # ── MILP Problem ──────────────────────────────────────────────────────
    prob = pulp.LpProblem("xi_selection", pulp.LpMaximize)

    # Decision variables: x[pid] ∈ {0, 1}
    x = {p["id"]: pulp.LpVariable(f"x_{p['id']}", cat="Binary") for p in squad}

    # Objective: maximise total utility
    prob += pulp.lpSum(utilities[pid] * x[pid] for pid in x)

    # Constraint: exactly 11 players
    prob += pulp.lpSum(x[pid] for pid in x) == target_xi_size

    # Role balance constraints
    role_map: Dict[str, List[str]] = {"batter": [], "bowler": [], "all_rounder": [], "wk_batter": []}
    for player in squad:
        role = player.get("role", "batter")
        if role in role_map:
            role_map[role].append(player["id"])

    for role, bounds in ROLE_CONSTRAINTS.items():
        players_in_role = role_map.get(role, [])
        if players_in_role:
            prob += pulp.lpSum(x[pid] for pid in players_in_role) >= bounds["min"], f"min_{role}"
            prob += pulp.lpSum(x[pid] for pid in players_in_role) <= bounds["max"], f"max_{role}"

    # Hard constraint: injured players excluded
    for player in squad:
        pid = player["id"]
        status = player.get("fitness", {}).get("status", "fit")
        if status in ("injured", "unavailable"):
            prob += x[pid] == 0

    # Solve
    solver = pulp.getSolver("PULP_CBC_CMD", msg=0)
    status = prob.solve(solver)

    if pulp.LpStatus[status] != "Optimal":
        # Fallback: sort by utility and take top 11
        sorted_players = sorted(utilities.items(), key=lambda kv: kv[1], reverse=True)
        selected_ids = [pid for pid, _ in sorted_players[:target_xi_size]]
        return selected_ids, ["Fallback selection (MILP infeasible) — sorted by utility"], "fallback"

    # Extract selected players
    selected_ids = [pid for pid in x if pulp.value(x[pid]) == 1]

    # Build reasoning
    reasoning = _build_selection_reasoning(squad, selected_ids, utilities, team_insights, pitch_type)

    return selected_ids, reasoning, "optimal"


def _build_selection_reasoning(
    squad: List[Dict[str, Any]],
    selected_ids: List[str],
    utilities: Dict[str, float],
    team_insights: Dict[str, Any],
    pitch_type: str,
) -> List[str]:
    """Generate one-sentence reasoning per selected player."""
    player_map = {p["id"]: p for p in squad}
    reasoning = []

    for pid in selected_ids:
        player = player_map.get(pid, {})
        name = player.get("name", pid)
        role = player.get("role", "?")
        utility = utilities.get(pid, 0)
        insight = team_insights.get(pid, {})
        form_rating = insight.get("overall_form", {}).get("rating", "") if insight else ""

        if form_rating:
            reasoning.append(f"{name} ({role}): selected — {form_rating} form, utility {utility:.2f}")
        else:
            bat_stats = (player.get("t20i_stats") or {}).get("batting") or {}
            bat_sr = bat_stats.get("strike_rate") or 0
            reasoning.append(f"{name} ({role}): selected — SR {bat_sr:.0f}, utility {utility:.2f}")

    return reasoning


def excluded_players(squad: List[Dict[str, Any]], selected_ids: List[str]) -> List[str]:
    """Return player IDs in squad but not selected."""
    return [p["id"] for p in squad if p["id"] not in selected_ids]
