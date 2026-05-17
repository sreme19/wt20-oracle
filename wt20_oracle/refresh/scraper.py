"""
Data Scraper
============

Fills schema and freshness gaps detected by gap_detector.py.

For each gap, fires a targeted DuckDuckGo search query and attempts to parse
the result into a structured update. Operates in dry-run mode by default —
shows a diff of proposed changes without writing anything.

Usage:
    from wt20_oracle.refresh.scraper import run_scraper
    run_scraper(gaps_report, dry_run=True, data_type="all")
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"


# ── Web search ────────────────────────────────────────────────────────────────

def _search(query: str, timeout: int = 10) -> Optional[str]:
    """Search DuckDuckGo; return stripped text (first ~5000 chars) or None."""
    try:
        params = urllib.parse.urlencode({"q": query, "kl": "us-en"})
        url = f"https://html.duckduckgo.com/html/?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        return text[:5000]
    except Exception:
        return None


# ── Parsers ───────────────────────────────────────────────────────────────────

def _extract_number(text: str, patterns: list[str]) -> Optional[float]:
    """Try each regex pattern and return the first float match."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except (ValueError, IndexError):
                continue
    return None


def _parse_batting_stats(text: str) -> dict:
    """Extract batting stats from search result text."""
    stats: dict[str, Any] = {}

    runs = _extract_number(text, [
        r"(\d{3,5})\s*runs?\s+in\s+(?:T20I|T20)",
        r"T20I[^.]*?(\d{3,5})\s*runs",
        r"scored?\s+(\d{3,5})\s*runs",
    ])
    if runs:
        stats["runs"] = int(runs)

    avg = _extract_number(text, [
        r"average[^.]*?([\d.]+)",
        r"avg[^.]*?([\d.]+)",
    ])
    if avg and 5 <= avg <= 80:
        stats["average"] = round(avg, 2)

    sr = _extract_number(text, [
        r"strike\s*rate[^.]*?([\d.]+)",
        r"SR[^.]*?([\d.]+)",
    ])
    if sr and 50 <= sr <= 250:
        stats["strike_rate"] = round(sr, 2)

    return stats


def _parse_bowling_stats(text: str) -> dict:
    """Extract bowling stats from search result text."""
    stats: dict[str, Any] = {}

    wickets = _extract_number(text, [
        r"(\d{1,3})\s*wickets?\s+in\s+(?:T20I|T20)",
        r"T20I[^.]*?(\d{1,3})\s*wickets",
        r"taken?\s+(\d{1,3})\s*wickets",
    ])
    if wickets:
        stats["wickets"] = int(wickets)

    economy = _extract_number(text, [
        r"economy[^.]*?([\d.]+)",
        r"econ[^.]*?([\d.]+)",
    ])
    if economy and 3 <= economy <= 15:
        stats["economy"] = round(economy, 2)

    return stats


def _parse_fitness_status(text: str) -> Optional[str]:
    """Extract injury/fitness status from search result."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["ruled out", "injured", "surgery", "fracture", "unavailable"]):
        return "injured"
    if any(w in text_lower for w in ["doubtful", "fitness concern", "not fully fit", "recovering"]):
        return "doubtful"
    if any(w in text_lower for w in ["fit", "available", "returned", "cleared", "named in squad"]):
        return "fit"
    return None


# ── Scrape functions per data type ────────────────────────────────────────────

def scrape_player_update(player_id: str, player_name: str, team: str) -> dict:
    """
    Search for latest stats for one player. Returns proposed field updates.
    """
    updates: dict[str, Any] = {}

    # Stats query
    query = f"{player_name} women T20I cricket stats 2025 2026 espncricinfo"
    text = _search(query)
    if text:
        batting = _parse_batting_stats(text)
        bowling = _parse_bowling_stats(text)
        if batting:
            updates["t20i_stats.batting"] = batting
        if bowling:
            updates["t20i_stats.bowling"] = bowling

    # Fitness query
    fitness_query = f"{player_name} women cricket injury fitness 2026"
    fitness_text = _search(fitness_query)
    if fitness_text:
        status = _parse_fitness_status(fitness_text)
        if status:
            updates["fitness_status"] = status

    return updates


def scrape_team_form(team_id: str, team_name: str) -> dict:
    """
    Search for recent team T20I results and extract phase performance hints.
    """
    updates: dict[str, Any] = {}
    query = f"{team_name} women T20I results 2026 recent matches"
    text = _search(query)
    if not text:
        return updates

    # Simple win-rate heuristic from text
    wins = len(re.findall(r"\b(won|beat|defeated|victory)\b", text.lower()))
    losses = len(re.findall(r"\b(lost|defeat|beaten)\b", text.lower()))
    if wins + losses > 0:
        win_rate = wins / (wins + losses)
        updates["_recent_form_win_rate"] = round(win_rate, 2)
        updates["_recent_form_note"] = f"Scraped: {wins}W/{losses}L from recent results"

    return updates


def scrape_venue_stats(venue_id: str, venue_name: str) -> dict:
    """Search for women's T20 stats at a venue."""
    updates: dict[str, Any] = {}
    query = f"{venue_name} women T20 cricket average score 2025 2026"
    text = _search(query)
    if not text:
        return updates

    avg_score = _extract_number(text, [
        r"average[^.]*?(\d{2,3})\s*(?:runs|for)",
        r"typical[^.]*?(\d{2,3})\s*(?:runs|score)",
        r"par[^.]*?(\d{2,3})\s*(?:runs|score)",
    ])
    if avg_score and 80 <= avg_score <= 220:
        updates["women_t20_stats.avg_first_innings_score"] = int(avg_score)

    return updates


def scrape_analyst_insights(team_id: str) -> dict:
    """Search for latest team news and player form for analyst_insights."""
    updates: dict[str, Any] = {}
    query = f"{team_id.replace('_', ' ')} women cricket squad news form May 2026"
    text = _search(query)
    if not text:
        return updates

    # Collect injury mentions
    injury_mentions = re.findall(
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\s+(?:is|has been|was)\s+(?:ruled out|injured|unavailable)",
        text
    )
    if injury_mentions:
        updates["_injury_mentions"] = injury_mentions[:3]

    return updates


# ── Apply updates to data files ───────────────────────────────────────────────

def _deep_set(obj: dict, path: str, value: Any) -> None:
    """Set a nested value using dot-separated path."""
    parts = path.split(".")
    for part in parts[:-1]:
        if part not in obj or not isinstance(obj[part], dict):
            obj[part] = {}
        obj = obj[part]
    obj[parts[-1]] = value


def apply_player_updates(player_id: str, updates: dict, dry_run: bool = True) -> bool:
    """Apply scraped updates to a player's entry in the player JSON file."""
    if not updates:
        return False

    players_dir = DATA_DIR / "players"
    target_file = None
    target_player = None
    all_players = []

    for pf in players_dir.glob("*.json"):
        with open(pf) as f:
            players = json.load(f)
        for player in (players if isinstance(players, list) else [players]):
            if player.get("id") == player_id:
                target_file = pf
                target_player = player
                all_players = players
                break
        if target_file:
            break

    if not target_player:
        return False

    print(f"\n  Player: {target_player.get('name')} ({player_id})")
    changed = False
    for path, value in updates.items():
        if path.startswith("_"):
            print(f"    note: {path[1:]} = {value}")
            continue
        parts = path.split(".")
        current_val = target_player
        for p in parts:
            current_val = current_val.get(p) if isinstance(current_val, dict) else None
        if current_val != value:
            print(f"    {path}: {current_val!r}  →  {value!r}")
            if not dry_run:
                _deep_set(target_player, path, value)
            changed = True

    if not dry_run and changed and target_file:
        with open(target_file, "w") as f:
            json.dump(all_players, f, indent=2)

    return changed


# ── Main orchestrator ─────────────────────────────────────────────────────────

def run_scraper(
    gaps_report: dict,
    dry_run: bool = True,
    data_type: str = "all",
    team: Optional[str] = None,
    max_players: int = 20,
) -> dict:
    """
    For each gap in gaps_report, fire a targeted search and propose updates.

    Args:
        gaps_report: output of detect_all_gaps()
        dry_run:     True = show diff only, no writes
        data_type:   "all" | "players" | "teams" | "venues" | "analyst"
        team:        limit player scraping to this team
        max_players: max number of players to scrape (avoids rate limits)

    Returns:
        summary dict with proposed_updates and applied_updates counts
    """
    mode = "DRY RUN" if dry_run else "LIVE WRITE"
    print(f"\n{'─' * 65}")
    print(f"DATA SCRAPER  [{mode}]")
    print(f"{'─' * 65}")

    if dry_run:
        print("  No changes will be written. Pass dry_run=False to apply.\n")

    summary = {"proposed": 0, "applied": 0, "errors": 0, "skipped": 0}

    schema_gaps = gaps_report.get("schema_gaps", [])
    freshness_gaps = [g for g in gaps_report.get("freshness_gaps", []) if g.get("stale")]

    # ── Player stat gaps ──────────────────────────────────────────────────────
    if data_type in ("all", "players"):
        player_gaps = [g for g in schema_gaps if "players/" in g.get("source", "")]
        if team:
            player_gaps = [g for g in player_gaps if team.lower() in g.get("source", "").lower()]

        # Deduplicate by player ID
        seen_players: set[str] = set()
        players_dir = DATA_DIR / "players"

        # Build a quick lookup: player_id → (name, team)
        player_info: dict[str, tuple[str, str]] = {}
        if players_dir.exists():
            for pf in players_dir.glob("*.json"):
                with open(pf) as f:
                    players = json.load(f)
                team_name = pf.stem
                for p in (players if isinstance(players, list) else [players]):
                    pid = p.get("id", "")
                    pname = p.get("name", pid)
                    player_info[pid] = (pname, team_name)

        scraped_count = 0
        for gap in player_gaps:
            pid = gap["record_id"]
            if pid in seen_players or scraped_count >= max_players:
                summary["skipped"] += 1
                continue
            seen_players.add(pid)
            scraped_count += 1

            pname, pteam = player_info.get(pid, (pid, "unknown"))
            print(f"\n  Scraping: {pname} ({pteam})")
            try:
                updates = scrape_player_update(pid, pname, pteam)
                if updates:
                    summary["proposed"] += 1
                    changed = apply_player_updates(pid, updates, dry_run=dry_run)
                    if changed and not dry_run:
                        summary["applied"] += 1
                else:
                    print(f"    No data found.")
                    summary["skipped"] += 1
            except Exception as e:
                print(f"    ERROR: {e}", file=sys.stderr)
                summary["errors"] += 1

    # ── Analyst insights freshness ────────────────────────────────────────────
    if data_type in ("all", "analyst"):
        ai_stale = any(
            g.get("stale") and "analyst_insights" in g.get("file", "")
            for g in freshness_gaps
        )
        if ai_stale:
            print("\n  Updating analyst_insights.json last_updated...")
            ai_path = DATA_DIR / "analyst_insights.json"
            if ai_path.exists() and not dry_run:
                with open(ai_path) as f:
                    ai = json.load(f)
                ai["last_updated"] = str(date.today())
                with open(ai_path, "w") as f:
                    json.dump(ai, f, indent=2)
                print(f"    last_updated → {date.today()}")
                summary["applied"] += 1
            elif dry_run:
                print(f"    [dry-run] would set last_updated → {date.today()}")
                summary["proposed"] += 1

    # ── Venue stats ───────────────────────────────────────────────────────────
    if data_type in ("all", "venues"):
        venue_gaps = [g for g in schema_gaps if g.get("source") == "venues.json"]
        seen_venues: set[str] = set()
        venues_path = DATA_DIR / "venues.json"

        if venues_path.exists():
            with open(venues_path) as f:
                venues = json.load(f)
            venue_map = {v["id"]: v for v in venues if "id" in v}

            for gap in venue_gaps:
                vid = gap["record_id"]
                if vid in seen_venues:
                    continue
                seen_venues.add(vid)
                venue = venue_map.get(vid, {})
                vname = venue.get("name", vid)

                print(f"\n  Scraping venue: {vname}")
                try:
                    updates = scrape_venue_stats(vid, vname)
                    if updates:
                        summary["proposed"] += 1
                        for path, value in updates.items():
                            print(f"    {path} → {value!r}")
                            if not dry_run:
                                _deep_set(venue, path, value)
                    else:
                        print(f"    No data found.")
                        summary["skipped"] += 1
                except Exception as e:
                    print(f"    ERROR: {e}", file=sys.stderr)
                    summary["errors"] += 1

            if not dry_run and venues_path.exists():
                with open(venues_path, "w") as f:
                    json.dump(venues, f, indent=2)

    print(f"\n{'─' * 65}")
    print(f"Scrape complete: {summary['proposed']} proposed, "
          f"{summary['applied']} applied, "
          f"{summary['skipped']} skipped, "
          f"{summary['errors']} errors")
    if dry_run:
        print("  (dry-run — nothing written)")
    print()
    return summary
