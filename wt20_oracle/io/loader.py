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
    """
    Load venue data by ID with validation.

    Validates:
    - Venue exists in database
    - Has required fields (name, city, pitch)
    - Pitch type is valid (seam_friendly, balanced, spin_friendly, flat)
    - Warns if women_t20_stats are sparse
    """
    venues = _read(DATA_DIR / "venues.json")
    venue = None
    for v in venues:
        if v.get("id") == venue_id:
            venue = v
            break

    if not venue:
        raise ValueError(f"Venue '{venue_id}' not found in venues.json")

    # Validate required structure
    required_fields = ["name", "city", "pitch"]
    missing = [f for f in required_fields if f not in venue or not venue.get(f)]
    if missing:
        raise ValueError(
            f"Venue '{venue_id}' missing required fields: {', '.join(missing)}"
        )

    # Validate pitch.type
    valid_pitch_types = ["seam_friendly", "balanced", "spin_friendly", "flat"]
    pitch_type = venue.get("pitch", {}).get("type")
    if pitch_type not in valid_pitch_types:
        raise ValueError(
            f"Invalid pitch type '{pitch_type}' for venue '{venue_id}'. "
            f"Must be one of: {', '.join(valid_pitch_types)}"
        )

    # Warn if women_t20_stats are sparse
    stats = venue.get("women_t20_stats", {})
    sparse_stats = all(
        v is None
        for v in [
            stats.get("matches_played"),
            stats.get("avg_first_innings_score"),
            stats.get("toss_impact"),
        ]
    )
    if sparse_stats:
        import warnings
        warnings.warn(
            f"Venue '{venue_id}': Limited women's T20 statistics available. "
            f"Predictions may be less accurate.",
            UserWarning,
        )

    return venue


def load_team(team_id: str) -> Dict[str, Any]:
    """Load team-level statistics."""
    teams = _read(DATA_DIR / "teams.json")
    team_list = teams if isinstance(teams, list) else teams.get("teams", [])
    for t in team_list:
        if t.get("id") == team_id:
            return t
    return {}


def _build_name_id_map() -> Dict[str, str]:
    """
    Build a display-name → snake_case_id map from all squad JSONs.

    Handles three name formats found in matchups.json:
      - Full name:       "Harmanpreet Kaur"  → harmanpreet_kaur
      - All initials:    "H Kaur"            → harmanpreet_kaur  (1 word before surname)
      - Multi-initial:   "JI Rodrigues"      → jemimah_rodrigues (initials of all but last word)
    """
    name_map: Dict[str, str] = {}
    players_dir = DATA_DIR / "players"
    if not players_dir.exists():
        return name_map

    for squad_file in players_dir.glob("*.json"):
        raw = _read(squad_file)
        squad = raw if isinstance(raw, list) else raw.get("squad", [])
        for p in squad:
            pid: str = p.get("id", "")
            full_name: str = p.get("name", "")
            if not pid or not full_name:
                continue

            # Full name → id
            name_map[full_name] = pid

            parts = full_name.split()
            if len(parts) < 2:
                continue

            # "H Kaur" style — first initial + surname
            simple = parts[0][0].upper() + " " + parts[-1]
            name_map.setdefault(simple, pid)

            # "JI Rodrigues" style — initials of all but last word + surname
            if len(parts) > 2:
                multi_init = "".join(w[0].upper() for w in parts[:-1]) + " " + parts[-1]
                name_map.setdefault(multi_init, pid)

    return name_map


def load_matchups() -> Dict[str, Any]:
    """
    Load batter-vs-bowler matchup matrix keyed 'batter_id::bowler_id'.

    matchups.json stores player names as display abbreviations ("S Mandhana",
    "H Kaur", "JI Rodrigues"). This function normalises those to snake_case IDs
    so downstream code can look up matchups using player IDs.
    """
    path = DATA_DIR / "matchups.json"
    if not path.exists():
        return {}
    raw = _read(path)

    # Support both list and pre-keyed dict formats
    matchup_list = raw.get("matchups", raw) if isinstance(raw, dict) else raw
    if not isinstance(matchup_list, list):
        # Already keyed dict — return as-is (legacy format)
        return matchup_list

    name_map = _build_name_id_map()
    result: Dict[str, Any] = {}

    for m in matchup_list:
        batter_display = m.get("batter_id", "")
        bowler_display = m.get("bowler_id", "")

        batter_id = name_map.get(batter_display, batter_display)
        bowler_id = name_map.get(bowler_display, bowler_display)

        key = f"{batter_id}::{bowler_id}"
        result[key] = {**m, "batter_id": batter_id, "bowler_id": bowler_id}

    return result


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
