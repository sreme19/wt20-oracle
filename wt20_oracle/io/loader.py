"""
Data Loader
===========

Loads all static reference data (players, venues, teams, matchups, schedule)
from wt20_oracle/data/ and returns typed dicts ready for the pipeline state.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"


def _read(path: Path) -> Any:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Individual loaders
# ---------------------------------------------------------------------------

def load_squad(team_id: str) -> List[Dict[str, Any]]:
    """Load squad player list for a team."""
    path = DATA_DIR / "players" / f"{team_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"No squad data for team: {team_id}")
    data = _read(path)
    return data if isinstance(data, list) else data.get("squad", [])


def load_venue(venue_id: str) -> Dict[str, Any]:
    """Load venue data by ID."""
    venues = _read(DATA_DIR / "venues.json")
    for v in venues:
        if v.get("id") == venue_id:
            return v
    raise ValueError(f"Venue '{venue_id}' not found in venues.json")


def load_team(team_id: str) -> Dict[str, Any]:
    """Load team-level statistics."""
    teams = _read(DATA_DIR / "teams.json")
    team_list = teams if isinstance(teams, list) else teams.get("teams", [])
    for t in team_list:
        if t.get("id") == team_id:
            return t
    return {}


def load_matchups() -> Dict[str, Any]:
    """Load batter-vs-bowler matchup matrix keyed 'batter_id::bowler_id'."""
    path = DATA_DIR / "matchups.json"
    if not path.exists():
        return {}
    data = _read(path)
    if isinstance(data, dict):
        return data
    return {f"{m['batter_id']}::{m['bowler_id']}": m for m in data}


def load_analyst_insights() -> Dict[str, Any]:
    """Load curated analyst insights."""
    path = DATA_DIR / "analyst_insights.json"
    if not path.exists():
        return {}
    return _read(path)


def load_schedule() -> Dict[str, Any]:
    """Load tournament schedule."""
    path = DATA_DIR / "schedule.json"
    if not path.exists():
        return {}
    return _read(path)


# ---------------------------------------------------------------------------
# Composite loader
# ---------------------------------------------------------------------------

def load_match_context(
    team_id: str,
    opponent_id: str,
    venue_id: str,
) -> Dict[str, Any]:
    """Load all data needed for a single pre-match pipeline run."""
    errors: List[str] = []

    our_squad = []
    try:
        our_squad = load_squad(team_id)
    except FileNotFoundError as e:
        errors.append(str(e))

    opponent_squad = []
    try:
        opponent_squad = load_squad(opponent_id)
    except FileNotFoundError as e:
        errors.append(str(e))

    venue_data = {}
    try:
        venue_data = load_venue(venue_id)
    except ValueError as e:
        errors.append(str(e))

    return {
        "our_squad": our_squad,
        "opponent_squad": opponent_squad,
        "venue_data": venue_data,
        "team_data": load_team(team_id),
        "opponent_data": load_team(opponent_id),
        "matchups": load_matchups(),
        "analyst_insights": load_analyst_insights(),
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_player(squad: List[Dict[str, Any]], player_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a player dict by ID from a squad list."""
    for p in squad:
        if p.get("id") == player_id:
            return p
    return None


def get_fit_players(squad: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return only players with fitness status 'fit' or unset."""
    return [
        p for p in squad
        if p.get("fitness", {}).get("status", "fit") in ("fit", None, "")
    ]


def get_matchup(
    matchups: Dict[str, Any],
    batter_id: str,
    bowler_id: str,
) -> Optional[Dict[str, Any]]:
    """Look up a specific batter-vs-bowler matchup."""
    return matchups.get(f"{batter_id}::{bowler_id}")


def venue_pace_score(venue_data: Dict[str, Any]) -> float:
    """
    Derive a 0-10 pace-friendliness score from venue pitch data.

    seam_friendly → 7.5-8.0  (fast bowlers benefit, batters need adjustment)
    flat          → 8.5-9.0  (easy to bat)
    balanced      → 5.5-6.5
    spin_friendly → 3.5-4.5  (difficult for batters)
    """
    pitch_type = venue_data.get("pitch", {}).get("type", "balanced")
    pace_advantage = venue_data.get("pitch", {}).get("pace_advantage", False)
    spin_advantage = venue_data.get("pitch", {}).get("spin_advantage", False)

    base_scores = {
        "seam_friendly": 7.5,
        "flat": 8.5,
        "balanced": 6.0,
        "spin_friendly": 4.0,
    }
    score = base_scores.get(pitch_type, 6.0)

    if pace_advantage:
        score = min(10.0, score + 0.5)
    if spin_advantage:
        score = max(0.0, score - 1.0)

    return score


def avg_first_innings_score(venue_data: Dict[str, Any], fallback: float = 152.0) -> float:
    """Get average first innings score for the venue, or a sensible default."""
    val = venue_data.get("women_t20_stats", {}).get("avg_first_innings_score")
    return float(val) if val is not None else fallback
