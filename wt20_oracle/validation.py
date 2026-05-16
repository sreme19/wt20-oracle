"""
Match Input Validation
======================

Validates all match inputs before pipeline execution.
Hard fails on invalid/incomplete data; never proceeds with degraded predictions.

Validation Rules:
  ✓ team_id and opponent_id must be in list of 12 valid teams
  ✓ venue_id must exist in venues.json
  ✓ venue must have pitch.type in valid types
  ✓ match_date (if provided) must be ISO format YYYY-MM-DD
  ✓ toss_winner (if provided) must match team_id or opponent_id
  ✓ toss_decision (if provided) must be in ["bat_first", "bowl_first"]
  ✓ Warn if venue has null women_t20_stats (incomplete data)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from difflib import get_close_matches


@dataclass
class ValidationResult:
    """Result of validation check."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: Dict[str, Any] = field(default_factory=dict)


def get_valid_teams() -> List[str]:
    """Return list of 12 valid tournament teams."""
    return [
        "india",
        "australia",
        "south_africa",
        "pakistan",
        "bangladesh",
        "netherlands",
        "england",
        "new_zealand",
        "west_indies",
        "sri_lanka",
        "ireland",
        "scotland",
    ]


def is_valid_iso_date(date_str: str) -> bool:
    """Check if date is valid ISO format YYYY-MM-DD."""
    if not date_str:
        return True  # Optional field
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def suggest_nearest_venue(requested: str, venues_data: List[Dict]) -> List[str]:
    """Fuzzy match venue names, return top 3 similar venues."""
    if not venues_data:
        return []

    venue_ids = [v.get("id", "") for v in venues_data]
    venue_names = [v.get("name", "") for v in venues_data]

    # Try matching both ID and name
    matches_by_id = get_close_matches(requested, venue_ids, n=3, cutoff=0.6)
    matches_by_name = get_close_matches(requested, venue_names, n=3, cutoff=0.6)

    # Return IDs (or IDs of matched names)
    result = list(dict.fromkeys(matches_by_id))  # Remove duplicates while preserving order

    if not result and matches_by_name:
        # If no ID matches, return IDs of matched name venues
        for name in matches_by_name:
            for v in venues_data:
                if v.get("name") == name:
                    result.append(v.get("id", ""))
                    break

    return result[:3]


def validate_match_inputs(
    team_id: str,
    opponent_id: str,
    venue_id: str,
    match_date: str = "",
    toss_winner: Optional[str] = None,
    toss_decision: Optional[str] = None,
    venues_data: Optional[List[Dict]] = None,
) -> ValidationResult:
    """
    Validate all match inputs. Hard fails on invalid data.

    Args:
        team_id: Our team (e.g. "india")
        opponent_id: Opponent (e.g. "south_africa")
        venue_id: Venue slug (e.g. "lords")
        match_date: ISO date string (e.g. "2026-06-17")
        toss_winner: Team ID of toss winner
        toss_decision: "bat_first" or "bowl_first"
        venues_data: List of venue dicts from venues.json

    Returns:
        ValidationResult with errors (hard fails) and warnings
    """
    errors = []
    warnings = []
    suggestions = {}

    # ──────────────────────────────────────────────────────────────────────────
    # Validate teams
    # ──────────────────────────────────────────────────────────────────────────
    valid_teams = get_valid_teams()

    if team_id not in valid_teams:
        errors.append(f"Team '{team_id}' not valid. Choose from: {', '.join(valid_teams)}")

    if opponent_id not in valid_teams:
        errors.append(
            f"Opponent '{opponent_id}' not valid. Choose from: {', '.join(valid_teams)}"
        )

    if team_id == opponent_id:
        errors.append("Team and opponent cannot be the same")

    # ──────────────────────────────────────────────────────────────────────────
    # Validate venue exists
    # ──────────────────────────────────────────────────────────────────────────
    if venue_id:
        if not venues_data:
            warnings.append("Could not validate venue: venues data not loaded")
        else:
            venue_exists = any(v.get("id") == venue_id for v in venues_data)
            if not venue_exists:
                similar = suggest_nearest_venue(venue_id, venues_data)
                errors.append(f"Venue '{venue_id}' not found in database")
                if similar:
                    suggestions["similar_venues"] = similar
                    errors.append(f"Did you mean: {similar[0]}?")

    # ──────────────────────────────────────────────────────────────────────────
    # Validate date format
    # ──────────────────────────────────────────────────────────────────────────
    if match_date and not is_valid_iso_date(match_date):
        errors.append(f"Invalid date format '{match_date}'. Use YYYY-MM-DD")

    # ──────────────────────────────────────────────────────────────────────────
    # Validate toss inputs
    # ──────────────────────────────────────────────────────────────────────────
    if toss_winner:
        if toss_winner not in [team_id, opponent_id]:
            errors.append(f"Toss winner '{toss_winner}' must be {team_id} or {opponent_id}")

    if toss_decision and toss_decision not in ["bat_first", "bowl_first"]:
        errors.append("Toss decision must be 'bat_first' or 'bowl_first'")

    # Both or neither
    if (toss_winner and not toss_decision) or (toss_decision and not toss_winner):
        errors.append("Both toss_winner and toss_decision must be provided together")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
    )


def validate_venue_details(venue_id: str, venues_data: List[Dict]) -> Dict[str, Any]:
    """
    Detailed venue validation. Checks structure and data completeness.

    Args:
        venue_id: Venue ID to validate
        venues_data: List of venue dicts

    Returns:
        {
            "valid": bool,
            "missing_fields": List[str],
            "warnings": List[str],
            "pitch_valid": bool
        }
    """
    venue = next((v for v in venues_data if v.get("id") == venue_id), None)

    if not venue:
        return {
            "valid": False,
            "missing_fields": ["venue_not_found"],
            "warnings": [],
            "pitch_valid": False,
        }

    missing_fields = []
    warnings = []

    # Check required fields
    required = ["name", "city", "pitch"]
    for field in required:
        if field not in venue or not venue[field]:
            missing_fields.append(field)

    # Validate pitch type
    valid_pitch_types = ["seam_friendly", "balanced", "spin_friendly", "flat"]
    pitch_type = venue.get("pitch", {}).get("type")

    if pitch_type not in valid_pitch_types:
        missing_fields.append("pitch.type")

    # Warn if stats are sparse
    stats = venue.get("women_t20_stats", {})
    if all(
        v is None
        for v in [
            stats.get("matches_played"),
            stats.get("avg_first_innings_score"),
            stats.get("toss_impact"),
        ]
    ):
        warnings.append(
            f"Limited women's T20 statistics for {venue_id}. "
            "Predictions may be less accurate. Consider using --fetch."
        )

    return {
        "valid": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "warnings": warnings,
        "pitch_valid": pitch_type in valid_pitch_types,
    }
