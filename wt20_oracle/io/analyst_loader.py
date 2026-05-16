"""
Load and apply curated analyst insights for decision support.

Analyst insights are qualitative assessments of players that inform:
  - Form window adjustments (soft modifiers on strike rates)
  - Matchup score reweighting (context-aware adjustments)
  - MILP constraints (hard rules: injuries, debuts, etc)
  - Narrative explanations (why recommendations are made)

Curated in: wt20_oracle/data/analyst_insights.json
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_analyst_insights() -> Dict[str, Any]:
    """Load analyst_insights.json; return full data structure."""
    insights_path = Path(__file__).parent.parent / "data" / "analyst_insights.json"
    if not insights_path.exists():
        return {"_meta": {}, "insights": {}}

    with open(insights_path) as f:
        return json.load(f)


def get_player_insights(player_id: str, team: str, insights_db: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Retrieve insights for a specific player."""
    team_insights = insights_db.get(team, {})
    # Note: player_id might be "harmanpreet_kaur" but insights uses "Harmanpreet Kaur"
    # This is a lookup; we'll need to build reverse map in name_map context
    return team_insights.get(player_id)


def form_modifier_from_insights(player_insights: Optional[Dict[str, Any]]) -> float:
    """
    Convert analyst form assessment to a strike rate modifier.

    Returns:
      1.0 = no adjustment
      1.05 = +5% boost for "strong" form
      0.95 = -5% penalty for "poor" form
    """
    if not player_insights:
        return 1.0

    form = player_insights.get("overall_form", {})
    rating = form.get("rating", "").lower()

    if "strong" in rating or "exceptional" in rating or "elite" in rating:
        return 1.05
    elif "poor" in rating or "struggle" in rating or "weak" in rating:
        return 0.95
    elif "improving" in rating:
        return 1.02
    elif "emerging" in rating or "developing" in rating:
        return 0.98  # Slight caution for debuts
    else:
        return 1.0


def matchup_modifier_from_insights(
    batter_insights: Optional[Dict[str, Any]],
    opponent_team: str,
    bowler_name: Optional[str] = None
) -> float:
    """
    Reweight matchup score based on analyst's vs-opponent assessment.

    Args:
      batter_insights: Player insights dict
      opponent_team: e.g. "australia"
      bowler_name: Optional; if provided, check specific bowler notes

    Returns:
      Multiplier to apply to historical matchup SR.
      1.0 = no adjustment
      0.90 = -10% for noted weakness
      1.10 = +10% for noted strength
    """
    if not batter_insights:
        return 1.0

    vs_opponent = batter_insights.get("vs_opponent", {})
    opp_data = vs_opponent.get(opponent_team)

    if not opp_data:
        return 1.0

    assessment = opp_data.get("assessment", "").lower()

    if "struggle" in assessment or "caution" in assessment:
        return 0.90
    elif "strong" in assessment or "excellent" in assessment:
        return 1.10
    elif "adequate" in assessment:
        return 1.0
    else:
        return 1.0


def constraint_from_injury(player_insights: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Generate MILP constraint if player has injury concern.

    Returns:
      String describing constraint, or None if no constraints needed.
      Example: "avoid_death_overs" for shoulder injury
    """
    if not player_insights:
        return None

    injury = player_insights.get("injury_status", "").lower()
    concerns = player_insights.get("concerns", "").lower() if player_insights.get("concerns") else ""

    if "shoulder" in injury or "shoulder" in concerns:
        return "avoid_death_overs"  # Power shots risky
    elif "ankle" in injury or "ankle" in concerns:
        return "cautious_powerplay"  # Movement limited
    elif "knee" in injury or "knee" in concerns:
        return "avoid_running"  # Quick singles risky

    return None


def psychological_notes_for_narrative(player_insights: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract psychological assessment for narrative generation."""
    if not player_insights:
        return None
    return player_insights.get("psychological_state")


def recent_concerns_for_narrative(player_insights: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract concerns for narrative warnings."""
    if not player_insights:
        return None
    return player_insights.get("concerns")


def vs_opponent_recommendation(
    player_insights: Optional[Dict[str, Any]],
    opponent_team: str
) -> Optional[str]:
    """Get analyst's specific recommendation for this matchup."""
    if not player_insights:
        return None

    vs_opponent = player_insights.get("vs_opponent", {})
    opp_data = vs_opponent.get(opponent_team)

    if not opp_data:
        return None

    return opp_data.get("recommendation")


def player_role_from_insights(player_insights: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Infer role from insights.
    Returns: "batter", "bowler", "allrounder", or None
    """
    if not player_insights:
        return None

    roles = player_insights.get("roles", [])
    if roles:
        return "/".join(roles)

    # Infer from presence of batting/bowling sections
    if player_insights.get("phase_performance"):
        if player_insights.get("bowling_role"):
            return "bowler"
        else:
            return "batter"

    return None


class AnalystInsightEnricher:
    """Context manager to load and apply analyst insights to player data."""

    def __init__(self):
        self.insights_db = load_analyst_insights()

    def enrich_player_json(self, player: Dict[str, Any], team: str) -> Dict[str, Any]:
        """
        Add analyst_insights to player dict for output.

        Args:
          player: Player dict from squad JSON
          team: Team slug (e.g. "india")

        Returns:
          Player dict with added "analyst_insights" field
        """
        player_id = player.get("id", "")
        team_insights = self.insights_db.get(team, {})

        # Try to find by player_id
        player_insight = team_insights.get(player_id)

        if player_insight and "_note" not in player_insight:
            player["analyst_insights"] = {
                "form_rating": player_insight.get("overall_form", {}).get("rating"),
                "form_confidence": player_insight.get("overall_form", {}).get("confidence"),
                "concerns": player_insight.get("concerns"),
                "injury_status": player_insight.get("injury_status"),
                "last_updated": player_insight.get("last_updated"),
                "analyst": player_insight.get("analyst"),
            }
        else:
            player["analyst_insights"] = None

        return player


if __name__ == "__main__":
    # Test: load and inspect
    insights = load_analyst_insights()
    print(f"Loaded analyst insights for {len([k for k in insights.keys() if k != '_meta'])} teams")

    india_insights = insights.get("india", {})
    print(f"\nIndia players with insights: {len([k for k in india_insights.keys() if k != '_note'])}")

    harman = india_insights.get("harmanpreet_kaur")
    if harman:
        print(f"\nHarmanpreet Kaur form: {harman.get('overall_form')}")
        print(f"Modifier: {form_modifier_from_insights(harman)}")
        vs_aus = harman.get("vs_opponent", {}).get("australia")
        if vs_aus:
            print(f"vs Australia: {vs_aus.get('assessment')}, recommendation: {vs_aus.get('recommendation')}")
