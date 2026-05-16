"""
Data Fetcher & Cache
====================

Automatically fetches match details from internet search and caches results.
Uses smart triggers: auto-fetch for upcoming matches, explicit --fetch otherwise.

Features:
  - WebSearch MCP tool integration for real match info
  - File-based caching to avoid repeated searches
  - User confirmation before updating venues.json
  - Fuzzy matching to extract venue from search results
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Cache location
CACHE_DIR = Path(__file__).parent.parent / ".claude"
CACHE_FILE = CACHE_DIR / "wt20_cache.json"


def is_future_match(match_date: str) -> bool:
    """Check if match is in future (within next 7 days)."""
    if not match_date:
        return False
    try:
        match = datetime.strptime(match_date, "%Y-%m-%d").date()
        today = datetime.now().date()
        return today <= match <= today + timedelta(days=7)
    except (ValueError, TypeError):
        return False


def should_auto_fetch(match_date: str, venue_id: str) -> bool:
    """
    Determine if auto-fetch should trigger.

    Auto-fetch if:
      - match_date is in future (within 7 days)
      - venue_id is provided (already valid, user can skip)

    Returns False if:
      - match_date is past or missing
      - venue_id is already provided (user intent explicit)
    """
    if venue_id:
        return False  # User provided venue, no need to fetch
    return is_future_match(match_date)  # Future matches auto-fetch


def get_cache(key: str) -> Optional[Dict]:
    """Retrieve cached result for a match."""
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        return cache.get(key)
    except (json.JSONDecodeError, IOError):
        return None


def set_cache(key: str, value: Dict) -> None:
    """Store result in cache file."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = {}
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                cache = json.load(f)
        except json.JSONDecodeError:
            cache = {}

    cache[key] = {**value, "cached_at": datetime.utcnow().isoformat()}

    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not write cache: {e}", file=sys.stderr)


def list_existing_venues() -> List[str]:
    """Get all existing venue IDs from database."""
    venues_file = Path(__file__).parent / "data" / "venues.json"
    if not venues_file.exists():
        return []
    try:
        with open(venues_file) as f:
            venues = json.load(f)
        return [v.get("id", "") for v in venues]
    except (json.JSONDecodeError, IOError):
        return []


def fetch_match_details(
    team_a: str,
    team_b: str,
    match_date: str = "",
    force_fetch: bool = False,
) -> Dict[str, Any]:
    """
    Fetch match details from internet search.

    Returns:
    {
        "status": "success|partial|failed",
        "venue_id": "county_ground_derby",
        "venue_name": "County Ground, Derby",
        "series": "England vs New Zealand T20I Series 2026",
        "message": "...",
        "requires_confirmation": bool,
        "venue_to_add": {...} or None,
        "cached": bool
    }
    """
    cache_key = f"{team_a}_{team_b}_{match_date}"

    # Check cache first
    cached_result = get_cache(cache_key)
    if cached_result and not force_fetch:
        return {**cached_result, "cached": True}

    # Build search query
    search_query = f"{team_a.upper()} vs {team_b.upper()} Women T20 Cricket"
    if match_date:
        search_query += f" {match_date}"

    # Call WebSearch (will be mocked in implementation)
    search_result = search_cricket_match_info(search_query)
    if not search_result:
        result = {
            "status": "failed",
            "message": "Could not find match details online",
            "requires_confirmation": False,
            "venue_to_add": None,
            "cached": False,
        }
        set_cache(cache_key, result)
        return result

    # Parse search results
    extracted = parse_search_results(search_result, team_a, team_b, match_date)

    if not extracted:
        result = {
            "status": "partial",
            "message": "Found match but could not extract venue details",
            "venue_id": None,
            "venue_name": None,
            "series": None,
            "requires_confirmation": False,
            "venue_to_add": None,
            "cached": False,
        }
        set_cache(cache_key, result)
        return result

    # Check if venue already exists
    existing_venues = list_existing_venues()
    venue_exists = extracted.get("venue_id") in existing_venues
    venue_to_add = None if venue_exists else extracted

    result = {
        "status": "success",
        "venue_id": extracted.get("venue_id"),
        "venue_name": extracted.get("venue_name"),
        "series": extracted.get("series"),
        "message": "Match details retrieved successfully",
        "requires_confirmation": not venue_exists,
        "venue_to_add": venue_to_add,
        "cached": False,
    }

    set_cache(cache_key, result)
    return result


def search_cricket_match_info(query: str) -> Optional[str]:
    """Search DuckDuckGo for cricket match info; returns raw result text."""
    import urllib.request
    import urllib.parse
    import re

    try:
        params = urllib.parse.urlencode({"q": query, "kl": "us-en"})
        url = f"https://html.duckduckgo.com/html/?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        return text[:6000]
    except Exception:
        return None


def parse_search_results(
    search_result: str, team_a: str, team_b: str, match_date: str
) -> Optional[Dict[str, str]]:
    """
    Extract venue, series, date from search result text.

    Simple heuristic parsing - looks for keywords like:
    - Venue patterns: "at X", "County Ground", "Lords", etc.
    - Date patterns: month names, numeric dates
    - Series patterns: "T20I Series", "International", etc.

    Returns:
    {
        "venue_id": "county_ground_derby",
        "venue_name": "County Ground, Derby",
        "series": "England vs New Zealand T20I Series 2026",
        "city": "Derby",
        "country": "England"
    }
    or None if parsing fails
    """
    if not search_result:
        return None

    # Normalize search result
    text = search_result.lower()

    # Extract venue name (heuristic: look for "at X" patterns)
    venue_name = None
    series = None
    city = None
    country = None

    # Common venue keywords to look for
    venue_keywords = [
        "lords",
        "old trafford",
        "headingley",
        "edgbaston",
        "the oval",
        "rose bowl",
        "county ground",
        "sydney",
        "melbourne",
        "perth",
        "brisbane",
        "adelaid",
        "canberra",
        "auckland",
        "wellington",
        "christchurch",
        "dubai",
        "dambulla",
        "colombo",
        "lahore",
        "karachi",
        "dhaka",
        "sylhet",
        "johannesburg",
        "durban",
        "capetown",
        "cape town",
    ]

    # Try to find venue in search results
    for keyword in venue_keywords:
        if keyword in text:
            # Build venue_name (capitalize properly)
            parts = keyword.split()
            venue_name = " ".join(p.capitalize() for p in parts)
            break

    if not venue_name:
        # No venue found
        return None

    # Create venue_id from venue_name (slugified)
    venue_id = (
        venue_name.lower().replace(" ", "_").replace("'", "").replace(",", "")
    )

    # Try to extract series info
    if "t20i" in text or "test" in text or "odi" in text:
        if "series" in text:
            series = f"{team_a.title()} vs {team_b.title()} T20I Series"
            if match_date:
                year = match_date.split("-")[0]
                series += f" {year}"

    return {
        "venue_id": venue_id,
        "venue_name": venue_name,
        "series": series,
        "city": city,
        "country": country,
        "pitch_type": "balanced",  # Default
    }


def show_fetch_confirmation(fetch_result: Dict) -> bool:
    """
    Interactive: show user what was found, get confirmation.
    Returns: True if user confirms, False otherwise.
    """
    if not fetch_result.get("requires_confirmation"):
        return True

    print(f"\n📍 Found match details:")
    print(f"   Venue: {fetch_result.get('venue_name', '?')}")
    if fetch_result.get("series"):
        print(f"   Series: {fetch_result['series']}")

    print(f"\n⚠️  This is a NEW venue. Add to database?")
    print("   Options: [y]es, [n]o, [s]kip")

    try:
        response = input("   Your choice: ").strip().lower()
        return response in ["y", "yes"]
    except (EOFError, KeyboardInterrupt):
        return False


def update_venues_json_with_confirmation(venue_data: Dict) -> bool:
    """
    Show user what will be added, then write to venues.json.
    Returns: True if updated, False if user declined.
    """
    if not show_fetch_confirmation(
        {
            "venue_name": venue_data.get("venue_name", "Unknown"),
            "series": venue_data.get("series", ""),
            "requires_confirmation": True,
        }
    ):
        return False

    venues_file = Path(__file__).parent / "data" / "venues.json"
    if not venues_file.exists():
        print("Error: venues.json not found", file=sys.stderr)
        return False

    # Build complete venue entry
    new_venue = {
        "id": venue_data.get("venue_id"),
        "name": venue_data.get("venue_name"),
        "city": venue_data.get("city", "Unknown"),
        "country": venue_data.get("country", "Unknown"),
        "capacity": None,
        "dimensions": {
            "straight_boundary_m": None,
            "square_boundary_m": None,
            "oval": True,
        },
        "pitch": {
            "type": venue_data.get("pitch_type", "balanced"),
            "pace_advantage": False,
            "spin_advantage": False,
            "notes": "Auto-fetched from internet",
        },
        "conditions": {
            "dew_factor": "medium",
            "typically_day_night": False,
            "avg_humidity_pct": None,
        },
        "women_t20_stats": {
            "matches_played": None,
            "avg_first_innings_score": None,
            "avg_winning_chase_score": None,
            "toss_impact": {"bat_first_win_pct": None, "field_first_win_pct": None},
            "pace_economy": None,
            "spin_economy": None,
            "highest_score": None,
            "lowest_defended": None,
        },
        "notes": f"Auto-fetched {datetime.now().date()}. Stats to be populated.",
    }

    try:
        with open(venues_file, "r") as f:
            venues = json.load(f)

        # Check if venue already exists
        if any(v.get("id") == new_venue["id"] for v in venues):
            print(f"✓ Venue {new_venue['id']} already exists")
            return True

        venues.append(new_venue)

        with open(venues_file, "w") as f:
            json.dump(venues, f, indent=2)

        print(f"✓ Added venue: {new_venue['id']} ({new_venue['name']})")
        return True
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error updating venues.json: {e}", file=sys.stderr)
        return False
