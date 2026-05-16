#!/usr/bin/env python3
"""
Match Structure Initialization Script
======================================

Creates standardized directory structure and metadata for each match.
Ensures consistency across all match analyses.
"""

from pathlib import Path
from datetime import datetime
import json
import argparse
import sys


def slugify(text):
    """Convert text to lowercase slug format."""
    return text.lower().replace(" ", "_").replace("-", "_")


def create_match_structure(team1, team2, date, venue, venue_id=None, country=None):
    """
    Create match directory structure.

    Args:
        team1: First team name
        team2: Second team name
        date: Match date (YYYY-MM-DD format)
        venue: Venue name
        venue_id: Venue ID (generated if not provided)
        country: Country (extracted from venue if not provided)

    Returns:
        dict: Match info and directory paths created
    """

    # Root matches directory
    base_path = Path(__file__).parent.parent.parent / "matches"
    base_path.mkdir(parents=True, exist_ok=True)

    # Generate match ID from teams and date
    t1_slug = slugify(team1)
    t2_slug = slugify(team2)
    date_slug = date.replace("-", "")
    match_id = f"{t1_slug}_vs_{t2_slug}_{date_slug}"

    # Create match directory
    match_dir = base_path / match_id
    match_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    subdirs = {
        "prediction": match_dir / "prediction",
        "actual": match_dir / "actual",
        "validation": match_dir / "validation",
        "analysis": match_dir / "analysis",
        "logs": match_dir / "logs"
    }

    for subdir in subdirs.values():
        subdir.mkdir(parents=True, exist_ok=True)

    # Generate venue ID if not provided
    if not venue_id:
        venue_id = slugify(venue)

    # Create metadata
    metadata = {
        "match_id": match_id,
        "match_date": date,
        "teams": {
            "team1": team1,
            "team2": team2
        },
        "venue": {
            "name": venue,
            "city": "TBD",
            "country": country or "TBD",
            "venue_id": venue_id
        },
        "format": "T20I",
        "toss": {
            "winner": None,
            "decision": None
        },
        "status": "pending",
        "result": {
            "winner": None,
            "margin": {
                "value": None,
                "unit": None
            }
        },
        "pipeline": {
            "created_at": datetime.now().isoformat() + "Z",
            "prediction_time": None,
            "match_start": None,
            "match_end": None,
            "completed_at": None
        },
        "execution": {
            "prediction_duration_ms": None,
            "validation_duration_ms": None,
            "model_version": "0.1-MVP",
            "analyst_insights_enabled": True
        },
        "accuracy": {
            "overall": None,
            "squad_selection": None,
            "batting_order": None,
            "match_outcome": None,
            "key_player": None
        },
        "directories": {
            "prediction": "./prediction/",
            "actual": "./actual/",
            "validation": "./validation/",
            "analysis": "./analysis/",
            "logs": "./logs/"
        }
    }

    # Save metadata
    metadata_file = match_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    return {
        "match_id": match_id,
        "match_dir": str(match_dir),
        "metadata_file": str(metadata_file),
        "subdirectories": {k: str(v) for k, v in subdirs.items()}
    }


def print_structure(result):
    """Print created structure in tree format."""
    print("\n" + "=" * 80)
    print("✓ MATCH STRUCTURE CREATED")
    print("=" * 80)
    print(f"\nMatch ID: {result['match_id']}")
    print(f"Location: {result['match_dir']}")
    print(f"\nDirectory Structure:")
    print(f"  {result['match_id']}/")
    for subdir, path in result['subdirectories'].items():
        print(f"    ├── {subdir}/")
    print(f"    └── metadata.json")
    print(f"\nFiles Created:")
    print(f"  ✓ metadata.json - Match metadata and pipeline tracking")
    print(f"\nNext Steps:")
    print(f"  1. Run prediction: python testing/orchestration/main.py --match-id {result['match_id']} --predict")
    print(f"  2. Add actual result: Place actual_result.json in actual/ directory")
    print(f"  3. Run validation: python testing/orchestration/main.py --match-id {result['match_id']} --validate")
    print(f"  4. View results: cat {result['match_dir']}/metadata.json")
    print("=" * 80 + "\n")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Create standardized match directory structure for wt20-oracle"
    )
    parser.add_argument("--team1", required=True, help="First team name")
    parser.add_argument("--team2", required=True, help="Second team name")
    parser.add_argument("--date", required=True, help="Match date (YYYY-MM-DD)")
    parser.add_argument("--venue", required=True, help="Venue name")
    parser.add_argument("--venue-id", help="Venue ID (auto-generated if not provided)")
    parser.add_argument("--country", help="Country (TBD if not provided)")

    args = parser.parse_args()

    try:
        result = create_match_structure(
            team1=args.team1,
            team2=args.team2,
            date=args.date,
            venue=args.venue,
            venue_id=args.venue_id,
            country=args.country
        )
        print_structure(result)
        return 0
    except Exception as e:
        print(f"✗ Error creating match structure: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
