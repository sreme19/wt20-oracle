"""
Squad Selector Node
===================

Selects the optimal XI from the available squad.
Runs MILP via milp_lineup.py and enriches with analyst insights.
"""

from typing import Any, Dict

from wt20_oracle.state import PreMatchState
from wt20_oracle.optimisation.milp_lineup import select_xi, excluded_players
from wt20_oracle.io.loader import get_fit_players


def squad_selector_node(state: PreMatchState) -> Dict[str, Any]:
    """LangGraph node: select the playing XI."""
    our_squad = state.get("our_squad", [])
    venue_data = state.get("venue_data", {})
    analyst_insights = state.get("analyst_insights", {})
    team_id = state.get("team_id", "")
    warnings = list(state.get("warnings", []))

    fit_squad = get_fit_players(our_squad)

    if not fit_squad:
        return {
            "selected_xi": [],
            "selection_reasoning": ["No fit players found"],
            "excluded_players": [],
            "warnings": warnings + ["No fit players available for selection"],
        }

    selected_ids, reasoning, status = select_xi(
        squad=fit_squad,
        venue_data=venue_data,
        analyst_insights=analyst_insights,
        team_id=team_id,
    )

    if status == "fallback":
        warnings.append("MILP infeasible — used fallback utility sort for XI selection")

    excluded = excluded_players(fit_squad, selected_ids)

    return {
        "selected_xi": selected_ids,
        "selection_reasoning": reasoning,
        "excluded_players": excluded,
        "warnings": warnings,
    }
