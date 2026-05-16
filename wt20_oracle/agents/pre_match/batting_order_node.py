"""
Batting Order Node
==================

Determines the optimal batting order for the selected XI.

Key factors:
  - Scenario (batting_first vs chasing) — different orders for each
  - Player strike rate and phase performance
  - Matchup data vs opponent's likely powerplay/death bowlers
  - Analyst insights (form, psychological state)
"""

from typing import Any, Dict, List

from wt20_oracle.state import PreMatchState
from wt20_oracle.io.loader import get_player


def batting_order_node(state: PreMatchState) -> Dict[str, Any]:
    """LangGraph node: determine batting order."""
    selected_xi = state.get("selected_xi", [])
    our_squad = state.get("our_squad", [])
    scenario = state.get("scenario", "unknown")
    analyst_insights = state.get("analyst_insights", {})
    team_id = state.get("team_id", "")
    matchups = state.get("matchups", {})
    opponent_squad = state.get("opponent_squad", [])

    if not selected_xi:
        return {"batting_order": [], "batting_reasoning": {}}

    # Score each player for each position
    player_scores = _score_players_for_batting(
        selected_xi, our_squad, scenario, analyst_insights, team_id
    )

    # Sort: openers need explosive SR + good powerplay record
    # Middle order: anchors + flexible hitters
    # Lower order: all-rounders and bowlers
    ordered = _assign_batting_positions(player_scores, our_squad, selected_xi, scenario)

    reasoning = {}
    for pos, pid in enumerate(ordered, 1):
        player = get_player(our_squad, pid)
        name = player.get("name", pid) if player else pid
        reasoning[pid] = _position_reasoning(pos, pid, player, scenario)

    return {
        "batting_order": ordered,
        "batting_reasoning": reasoning,
    }


def _score_players_for_batting(
    selected_xi: List[str],
    squad: List[Dict],
    scenario: str,
    analyst_insights: Dict,
    team_id: str,
) -> Dict[str, float]:
    """Score each player for their batting utility."""
    team_ins = analyst_insights.get(team_id, {})
    scores = {}

    for pid in selected_xi:
        player = get_player(squad, pid)
        if not player:
            scores[pid] = 0.5
            continue

        bat = player.get("t20i_stats", {}).get("batting") or {}
        sr = bat.get("strike_rate", 100.0) or 100.0
        avg = bat.get("average", 20.0) or 20.0
        innings = bat.get("innings", 0) or 0
        role = player.get("role", "batter")

        # Base score: combination of SR and average
        score = (sr / 130) * 0.5 + (avg / 30) * 0.3

        # Boost pure batters and wk-batters over bowlers
        if role in ("batter", "wk_batter"):
            score += 0.2
        elif role == "all_rounder":
            score += 0.1

        # Chasing: value aggressive batters higher (SR matters more)
        if scenario == "chasing":
            score += (sr / 130) * 0.1

        # Analyst insight modifier
        insight = team_ins.get(pid)
        if insight:
            from wt20_oracle.io.analyst_loader import form_modifier_from_insights
            score *= form_modifier_from_insights(insight)

        scores[pid] = score

    return scores


def _assign_batting_positions(
    scores: Dict[str, float],
    squad: List[Dict],
    selected_xi: List[str],
    scenario: str,
) -> List[str]:
    """Assign players to batting positions."""
    # Categorise players
    wk_batters = []
    top_order = []   # High scorers → open or #3
    middle_order = []
    lower_order = []  # Bowlers

    for pid in selected_xi:
        player = get_player(squad, pid)
        role = player.get("role", "batter") if player else "batter"
        score = scores.get(pid, 0.5)

        if role == "wk_batter":
            wk_batters.append((pid, score))
        elif role == "batter" and score >= 0.7:
            top_order.append((pid, score))
        elif role in ("batter", "all_rounder") and score >= 0.5:
            middle_order.append((pid, score))
        else:
            lower_order.append((pid, score))

    # Sort each group by score desc
    for lst in (wk_batters, top_order, middle_order, lower_order):
        lst.sort(key=lambda x: x[1], reverse=True)

    # Compose order: 2 openers + WK + top order + middle + lower
    ordered_ids = []
    # Positions 1-2: Top 2 by score (prefer explosive openers)
    all_batters = top_order + wk_batters + middle_order
    all_batters.sort(key=lambda x: x[1], reverse=True)
    openers = [pid for pid, _ in all_batters[:2]]
    ordered_ids.extend(openers)

    # Fill remaining positions
    for pid, _ in all_batters[2:]:
        if pid not in ordered_ids:
            ordered_ids.append(pid)
    for pid, _ in lower_order:
        if pid not in ordered_ids:
            ordered_ids.append(pid)

    # Catch any stragglers
    for pid in selected_xi:
        if pid not in ordered_ids:
            ordered_ids.append(pid)

    return ordered_ids[:11]


def _position_reasoning(pos: int, pid: str, player: Dict, scenario: str) -> str:
    if not player:
        return f"Position {pos}: data unavailable"
    name = player.get("name", pid)
    role = player.get("role", "batter")
    sr = ((player.get("t20i_stats") or {}).get("batting") or {}).get("strike_rate") or 0
    if pos <= 2:
        return f"Opens — SR {sr:.0f}, aggressive start needed {'chasing' if scenario == 'chasing' else 'setting total'}"
    elif pos <= 5:
        return f"#{pos} — anchor/accelerator, SR {sr:.0f}"
    else:
        return f"#{pos} ({role}) — depth batting, lower-order contribution"
