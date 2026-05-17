"""
Canonical schema definitions for wt20-oracle data files.

These are used by gap_detector.py to identify missing or null fields.
Each entry is (field_path, severity) where severity is "critical" or "warning".
"""

# Required fields per player record
PLAYER_REQUIRED = [
    ("id", "critical"),
    ("name", "critical"),
    ("team", "critical"),
    ("role", "critical"),
    ("batting_hand", "warning"),
    ("bowling_hand", "warning"),
    ("caps", "warning"),
    ("t20i_stats.batting.matches", "warning"),
    ("t20i_stats.batting.runs", "warning"),
    ("t20i_stats.batting.average", "warning"),
    ("t20i_stats.batting.strike_rate", "critical"),
    ("t20i_stats.batting.boundary_pct", "warning"),
    ("t20i_stats.batting.dot_ball_pct", "warning"),
    ("t20i_stats.batting.phase_splits.powerplay", "warning"),
    ("t20i_stats.batting.phase_splits.middle", "warning"),
    ("t20i_stats.batting.phase_splits.death", "warning"),
    ("t20i_stats.bowling.economy", "critical"),
    ("t20i_stats.bowling.wickets", "warning"),
    ("t20i_stats.bowling.phase_splits.powerplay", "warning"),
    ("t20i_stats.bowling.phase_splits.death", "warning"),
    ("fitness_status", "warning"),
]

# Required fields per team record
TEAM_REQUIRED = [
    ("id", "critical"),
    ("name", "critical"),
    ("icc_ranking", "warning"),
    ("captain", "warning"),
    ("batting_phase_performance.powerplay", "warning"),
    ("batting_phase_performance.middle", "warning"),
    ("batting_phase_performance.death", "warning"),
    ("bowling_phase_performance.powerplay", "warning"),
    ("bowling_phase_performance.death", "warning"),
]

# Required fields per venue record
VENUE_REQUIRED = [
    ("id", "critical"),
    ("name", "critical"),
    ("city", "warning"),
    ("country", "warning"),
    ("pitch.type", "critical"),
    ("pitch.pace_advantage", "warning"),
    ("pitch.spin_advantage", "warning"),
    ("conditions.dew_factor", "warning"),
    ("women_t20_stats.avg_first_innings_score", "critical"),
    ("women_t20_stats.avg_winning_chase_score", "critical"),
    ("women_t20_stats.matches_played", "warning"),
]

# Analyst insights: per-team player entries expected
ANALYST_INSIGHTS_REQUIRED = [
    ("last_updated", "critical"),
    ("version", "warning"),
]

# How many days before a data file is considered "stale"
STALENESS_THRESHOLDS = {
    "analyst_insights.json": 7,    # critical source — stale after 7 days
    "players": 14,                  # player stats — stale after 2 weeks
    "teams.json": 30,               # team aggregates — stale after a month
    "venues.json": 90,              # venues rarely change
    "schedule.json": 3,             # schedule can change quickly
}


def get_nested(obj: dict, path: str):
    """Traverse a dot-separated path in a dict. Returns None if any key is missing."""
    parts = path.split(".")
    current = obj
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current
