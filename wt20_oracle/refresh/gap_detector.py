"""
Gap Detector
============

Scans all wt20-oracle data files and reports:
  1. Freshness gaps  — files with stale or missing last_updated timestamps
  2. Schema gaps     — records with missing or null required fields

Usage:
    from wt20_oracle.refresh.gap_detector import detect_all_gaps
    report = detect_all_gaps()
    print_gap_report(report)
"""

import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional

from wt20_oracle.refresh.schema import (
    PLAYER_REQUIRED,
    TEAM_REQUIRED,
    VENUE_REQUIRED,
    ANALYST_INSIGHTS_REQUIRED,
    STALENESS_THRESHOLDS,
    get_nested,
)

DATA_DIR = Path(__file__).parent.parent / "data"


# ── Freshness ─────────────────────────────────────────────────────────────────

def _days_since(date_str: str) -> Optional[int]:
    """Return days elapsed since an ISO date string. None if unparseable."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            d = datetime.strptime(date_str[:19], fmt).date()
            return (date.today() - d).days
        except ValueError:
            continue
    return None


def _file_mtime_days(path: Path) -> Optional[int]:
    """Days since file was last modified on disk."""
    try:
        mtime = path.stat().st_mtime
        d = date.fromtimestamp(mtime)
        return (date.today() - d).days
    except OSError:
        return None


def check_freshness() -> list[dict]:
    """Return a list of freshness gap entries across all data files."""
    gaps = []

    # analyst_insights.json — has explicit last_updated
    ai_path = DATA_DIR / "analyst_insights.json"
    if ai_path.exists():
        with open(ai_path) as f:
            ai = json.load(f)
        last_updated = ai.get("last_updated") or ai.get("metadata", {}).get("last_updated")
        days = _days_since(last_updated) if last_updated else None
        threshold = STALENESS_THRESHOLDS["analyst_insights.json"]
        gaps.append({
            "file": "analyst_insights.json",
            "last_updated": last_updated or "UNKNOWN",
            "days_stale": days,
            "threshold_days": threshold,
            "stale": days is None or days > threshold,
            "severity": "critical" if (days is None or days > threshold) else "ok",
        })

    # Player JSONs — use file mtime (no embedded timestamp)
    players_dir = DATA_DIR / "players"
    if players_dir.exists():
        for pf in sorted(players_dir.glob("*.json")):
            days = _file_mtime_days(pf)
            threshold = STALENESS_THRESHOLDS["players"]
            gaps.append({
                "file": f"players/{pf.name}",
                "last_updated": f"mtime ({pf.stat().st_mtime:.0f})",
                "days_stale": days,
                "threshold_days": threshold,
                "stale": days is None or days > threshold,
                "severity": "warning" if (days is None or days > threshold) else "ok",
            })

    # teams.json
    teams_path = DATA_DIR / "teams.json"
    if teams_path.exists():
        days = _file_mtime_days(teams_path)
        threshold = STALENESS_THRESHOLDS["teams.json"]
        gaps.append({
            "file": "teams.json",
            "last_updated": f"mtime",
            "days_stale": days,
            "threshold_days": threshold,
            "stale": days is None or days > threshold,
            "severity": "warning" if (days is None or days > threshold) else "ok",
        })

    # schedule.json
    sched_path = DATA_DIR / "schedule.json"
    if sched_path.exists():
        days = _file_mtime_days(sched_path)
        threshold = STALENESS_THRESHOLDS["schedule.json"]
        gaps.append({
            "file": "schedule.json",
            "last_updated": f"mtime",
            "days_stale": days,
            "threshold_days": threshold,
            "stale": days is None or days > threshold,
            "severity": "warning" if (days is None or days > threshold) else "ok",
        })

    return gaps


# ── Schema gaps ───────────────────────────────────────────────────────────────

def _check_record(record: dict, required_fields: list[tuple[str, str]], source: str) -> list[dict]:
    """Check a single record against required fields. Returns list of gap dicts."""
    gaps = []
    record_id = record.get("id") or record.get("name") or "?"
    for field_path, severity in required_fields:
        val = get_nested(record, field_path)
        if val is None:
            gaps.append({
                "source": source,
                "record_id": record_id,
                "field": field_path,
                "issue": "missing",
                "severity": severity,
            })
        elif val == "" or val == [] or val == {}:
            gaps.append({
                "source": source,
                "record_id": record_id,
                "field": field_path,
                "issue": "empty",
                "severity": "warning",
            })
    return gaps


def check_player_schema() -> list[dict]:
    gaps = []
    players_dir = DATA_DIR / "players"
    if not players_dir.exists():
        return gaps
    for pf in sorted(players_dir.glob("*.json")):
        with open(pf) as f:
            players = json.load(f)
        if not isinstance(players, list):
            players = [players]
        for player in players:
            gaps.extend(_check_record(player, PLAYER_REQUIRED, f"players/{pf.name}"))
    return gaps


def check_team_schema() -> list[dict]:
    teams_path = DATA_DIR / "teams.json"
    if not teams_path.exists():
        return []
    with open(teams_path) as f:
        teams = json.load(f)
    if not isinstance(teams, list):
        teams = list(teams.values()) if isinstance(teams, dict) else [teams]
    gaps = []
    for team in teams:
        gaps.extend(_check_record(team, TEAM_REQUIRED, "teams.json"))
    return gaps


def check_venue_schema() -> list[dict]:
    venues_path = DATA_DIR / "venues.json"
    if not venues_path.exists():
        return []
    with open(venues_path) as f:
        venues = json.load(f)
    gaps = []
    for venue in venues:
        gaps.extend(_check_record(venue, VENUE_REQUIRED, "venues.json"))
    return gaps


def check_analyst_insights_schema() -> list[dict]:
    ai_path = DATA_DIR / "analyst_insights.json"
    if not ai_path.exists():
        return []
    with open(ai_path) as f:
        ai = json.load(f)
    gaps = []
    for field_path, severity in ANALYST_INSIGHTS_REQUIRED:
        val = get_nested(ai, field_path)
        if val is None:
            gaps.append({
                "source": "analyst_insights.json",
                "record_id": "root",
                "field": field_path,
                "issue": "missing",
                "severity": severity,
            })
    return gaps


# ── Cross-reference: schedule vs player roster ────────────────────────────────

def check_squad_coverage() -> list[dict]:
    """Check that every player named in teams.json squads has a player JSON file."""
    teams_path = DATA_DIR / "teams.json"
    players_dir = DATA_DIR / "players"
    if not teams_path.exists() or not players_dir.exists():
        return []

    with open(teams_path) as f:
        teams = json.load(f)

    # Collect all player IDs from all player JSON files
    known_ids: set[str] = set()
    for pf in players_dir.glob("*.json"):
        with open(pf) as f:
            players = json.load(f)
        if isinstance(players, list):
            for p in players:
                known_ids.add(p.get("id", ""))

    gaps = []
    for team in (teams if isinstance(teams, list) else []):
        team_id = team.get("id", "?")
        player_file = players_dir / f"{team_id}.json"
        if not player_file.exists():
            gaps.append({
                "source": "players/",
                "record_id": team_id,
                "field": "player_file",
                "issue": f"no player JSON for team '{team_id}'",
                "severity": "critical",
            })
    return gaps


# ── Main entry ────────────────────────────────────────────────────────────────

def detect_all_gaps(data_type: str = "all", team: Optional[str] = None) -> dict:
    """
    Run full gap detection. Returns a structured report dict.

    Args:
        data_type: "all" | "players" | "teams" | "venues" | "analyst"
        team:      if set, filter player gaps to this team only
    """
    report: dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "freshness_gaps": [],
        "schema_gaps": [],
        "summary": {},
    }

    if data_type in ("all", "players", "teams", "venues", "analyst"):
        report["freshness_gaps"] = check_freshness()

    schema_gaps: list[dict] = []
    if data_type in ("all", "analyst"):
        schema_gaps.extend(check_analyst_insights_schema())
    if data_type in ("all", "players"):
        player_gaps = check_player_schema()
        if team:
            player_gaps = [g for g in player_gaps if team.lower() in g["source"].lower()]
        schema_gaps.extend(player_gaps)
    if data_type in ("all", "teams"):
        schema_gaps.extend(check_team_schema())
    if data_type in ("all", "venues"):
        schema_gaps.extend(check_venue_schema())
    if data_type == "all":
        schema_gaps.extend(check_squad_coverage())

    report["schema_gaps"] = schema_gaps

    stale_count = sum(1 for g in report["freshness_gaps"] if g.get("stale"))
    critical_count = sum(1 for g in schema_gaps if g.get("severity") == "critical")
    warning_count = sum(1 for g in schema_gaps if g.get("severity") == "warning")

    report["summary"] = {
        "stale_files": stale_count,
        "total_files_checked": len(report["freshness_gaps"]),
        "schema_critical": critical_count,
        "schema_warnings": warning_count,
        "total_gaps": stale_count + critical_count + warning_count,
    }

    return report


def print_gap_report(report: dict, verbose: bool = False) -> None:
    """Print a human-readable gap report to stdout."""
    s = report["summary"]
    print(f"\n{'─' * 65}")
    print(f"DATA GAP REPORT  (generated {report['generated_at'][:10]})")
    print(f"{'─' * 65}")
    print(f"Files checked:    {s['total_files_checked']}")
    print(f"Stale files:      {s['stale_files']}")
    print(f"Schema critical:  {s['schema_critical']}")
    print(f"Schema warnings:  {s['schema_warnings']}")
    print(f"Total gaps:       {s['total_gaps']}")

    # Freshness table
    stale = [g for g in report["freshness_gaps"] if g.get("stale")]
    if stale:
        print(f"\n{'─' * 65}")
        print("STALE FILES")
        print(f"  {'File':<35} {'Last Updated':<15} {'Days'}")
        print(f"  {'─'*33} {'─'*13} {'─'*5}")
        for g in stale:
            days = g.get("days_stale")
            days_str = str(days) if days is not None else "?"
            lu = str(g.get("last_updated", "?"))[:13]
            print(f"  {g['file']:<35} {lu:<15} {days_str}")
    else:
        print("\n  All files are fresh.")

    # Schema gaps
    critical = [g for g in report["schema_gaps"] if g.get("severity") == "critical"]
    warnings = [g for g in report["schema_gaps"] if g.get("severity") == "warning"]

    if critical:
        print(f"\n{'─' * 65}")
        print("CRITICAL SCHEMA GAPS")
        for g in critical:
            print(f"  [{g['source']}] {g['record_id']} → {g['field']} ({g['issue']})")

    if warnings and verbose:
        print(f"\n{'─' * 65}")
        print("SCHEMA WARNINGS")
        for g in warnings[:30]:
            print(f"  [{g['source']}] {g['record_id']} → {g['field']} ({g['issue']})")
        if len(warnings) > 30:
            print(f"  ... and {len(warnings) - 30} more (run with --verbose to see all)")

    print(f"\n{'─' * 65}")
    if s["total_gaps"] == 0:
        print("  No gaps detected. Data is fresh and schema-complete.")
    elif s["schema_critical"] > 0 or s["stale_files"] > 0:
        print("  Run: wt20-oracle refresh --data-type all  (to scrape and fill gaps)")
    else:
        print("  Minor warnings only. Run: wt20-oracle refresh --dry-run  to preview fixes.")
    print()
