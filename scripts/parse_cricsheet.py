"""
CricSheet data pipeline.

Reads ball-by-ball JSON match files from data/raw/cricsheet/ and populates:
  data/players/{team}.json   — per-player stats, phase splits, form windows
  data/matchups.json         — batter vs bowler head-to-head matrix

Usage:
    python scripts/parse_cricsheet.py
    python scripts/parse_cricsheet.py --source t20i     # T20Is only
    python scripts/parse_cricsheet.py --since 2024-01-01
    python scripts/parse_cricsheet.py --validate        # dry run, print gaps
"""

import argparse
import json
import zipfile
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, DefaultDict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "wt20_oracle" / "data" / "raw" / "cricsheet"
PLAYERS_DIR = ROOT / "wt20_oracle" / "data" / "players"
DATA_DIR = ROOT / "wt20_oracle" / "data"

ZIPS = {
    "t20i":    RAW_DIR / "t20s_female.zip",
    "wpl":     RAW_DIR / "wpl_female.zip",
    "wbbl":    RAW_DIR / "wbbl_female.zip",
    "hundred": RAW_DIR / "hundred_female.zip",
}

# Teams whose players we want full stats for (all 12 WC squads)
WC_TEAMS = {
    "India", "Australia", "England", "New Zealand", "South Africa",
    "Pakistan", "West Indies", "Sri Lanka", "Bangladesh",
    "Ireland", "Scotland", "Netherlands",
}

# Map CricSheet team names → our TeamID slugs
TEAM_SLUG = {
    "India":        "india",
    "Australia":    "australia",
    "England":      "england",
    "New Zealand":  "new_zealand",
    "South Africa": "south_africa",
    "Pakistan":     "pakistan",
    "West Indies":  "west_indies",
    "Sri Lanka":    "sri_lanka",
    "Bangladesh":   "bangladesh",
    "Ireland":      "ireland",
    "Scotland":     "scotland",
    "Netherlands":  "netherlands",
}

# Domestic league weight when blending with T20I stats (downweight factor)
LEAGUE_WEIGHT = {
    "t20i":    1.0,
    "wpl":     0.75,
    "wbbl":    0.70,
    "hundred": 0.65,
}


# ---------------------------------------------------------------------------
# Phase helpers
# ---------------------------------------------------------------------------

def over_to_phase(over: int) -> str:
    """0-indexed over number → phase label."""
    if over < 6:
        return "powerplay"
    elif over < 15:
        return "middle"
    else:
        return "death"


# ---------------------------------------------------------------------------
# Accumulators
# ---------------------------------------------------------------------------

def _batting_acc() -> dict:
    return {
        "matches": set(),          # match IDs — deduped at end
        "innings": 0,
        "runs": 0,
        "balls": 0,
        "dismissals": 0,
        "fours": 0,
        "sixes": 0,
        "dot_balls": 0,
        "fifties": 0,
        "hundreds": 0,
        "phases": {
            "powerplay": _phase_acc(),
            "middle":    _phase_acc(),
            "death":     _phase_acc(),
        },
        "vs_pace":      _split_acc(),
        "vs_spin":      _split_acc(),
        "vs_left_arm":  _split_acc(),
        "vs_right_arm": _split_acc(),
        # form windows keyed by ISO date strings, rolled up after
        "by_match": [],            # list of {date, runs, balls, source}
        "icc_tournament": _phase_acc(),
    }


def _bowling_acc() -> dict:
    return {
        "matches": set(),
        "innings": 0,
        "balls": 0,
        "runs": 0,
        "wickets": 0,
        "dot_balls": 0,
        "fours_conceded": 0,
        "sixes_conceded": 0,
        "phases": {
            "powerplay": _bowl_phase_acc(),
            "middle":    _bowl_phase_acc(),
            "death":     _bowl_phase_acc(),
        },
        "vs_left_hand":  _bowl_split_acc(),
        "vs_right_hand": _bowl_split_acc(),
        "by_match": [],
        "icc_tournament": _bowl_phase_acc(),
    }


def _phase_acc() -> dict:
    return {"balls": 0, "runs": 0, "dismissals": 0, "dot_balls": 0, "fours": 0, "sixes": 0}


def _bowl_phase_acc() -> dict:
    return {"balls": 0, "runs": 0, "wickets": 0, "dot_balls": 0}


def _split_acc() -> dict:
    return {"balls": 0, "runs": 0, "dismissals": 0, "dot_balls": 0}


def _bowl_split_acc() -> dict:
    return {"balls": 0, "runs": 0, "wickets": 0, "dot_balls": 0}


# ---------------------------------------------------------------------------
# Match file parsing
# ---------------------------------------------------------------------------

SPIN_STYLES = {
    "off break", "leg break", "left-arm orthodox", "left-arm wrist spin",
    "slow left-arm orthodox", "leg break googly", "off spin",
}


def _is_spin(bowling_style: Optional[str]) -> bool:
    if not bowling_style:
        return False
    return any(s in bowling_style.lower() for s in ["spin", "break", "orthodox", "googly"])


def _is_left_arm(bowling_style: Optional[str]) -> bool:
    if not bowling_style:
        return False
    return "left" in bowling_style.lower()


ICC_EVENT_KEYWORDS = ("world cup", "t20 world cup", "asia cup", "icc women's")


def parse_match(
    match: dict,
    source: str,
    batting_stats: dict,
    bowling_stats: dict,
    matchups: dict,
    bowler_meta: dict,
    batter_meta: dict,
    is_icc_tournament: bool = False,
) -> None:
    """Extract ball-by-ball data from one CricSheet match dict."""
    info = match.get("info", {})
    match_date_str = info.get("dates", [None])[0]
    match_id = match.get("meta", {}).get("data_version", "") + "_" + str(match_date_str)

    # Per-match innings accumulators for form_windows
    match_batting: Dict[str, dict] = defaultdict(
        lambda: {"runs": 0, "balls": 0, "dismissed": False}
    )
    match_bowling: Dict[str, dict] = defaultdict(
        lambda: {"balls": 0, "runs": 0, "wickets": 0}
    )

    # Collect bowling style metadata from registry if present
    registry = info.get("registry", {}).get("people", {})

    innings_list = match.get("innings", [])
    for inning in innings_list:
        batting_team = inning.get("team", "")
        overs_data = inning.get("overs", [])

        for over_obj in overs_data:
            over_num = over_obj.get("over", 0)
            phase = over_to_phase(over_num)

            for delivery in over_obj.get("deliveries", []):
                batter = delivery.get("batter", "")
                bowler = delivery.get("bowler", "")
                non_striker = delivery.get("non_striker", "")

                runs_obj = delivery.get("runs", {})
                batter_runs = runs_obj.get("batter", 0)
                extras = runs_obj.get("extras", 0)
                total_runs = runs_obj.get("total", 0)

                is_dot = batter_runs == 0
                is_four = batter_runs == 4
                is_six = batter_runs == 6

                wickets = delivery.get("wickets", [])
                batter_out = any(
                    w.get("player_out") == batter for w in wickets
                )

                # Bowler metadata for split categorisation
                bowl_style = bowler_meta.get(bowler)
                is_spin_bowl = _is_spin(bowl_style)
                is_left_arm_bowl = _is_left_arm(bowl_style)

                # Batter hand
                bat_hand = batter_meta.get(batter, {}).get("batting_hand")
                is_left_hand_bat = bat_hand == "left"

                # ---- BATTING ----
                if batter not in batting_stats:
                    batting_stats[batter] = _batting_acc()
                b = batting_stats[batter]
                b["matches"].add(match_id)
                b["runs"] += batter_runs
                b["balls"] += 1
                if is_dot:
                    b["dot_balls"] += 1
                if is_four:
                    b["fours"] += 1
                if is_six:
                    b["sixes"] += 1
                if batter_out:
                    b["dismissals"] += 1

                ph = b["phases"][phase]
                ph["balls"] += 1
                ph["runs"] += batter_runs
                if batter_out:
                    ph["dismissals"] += 1
                if is_dot:
                    ph["dot_balls"] += 1
                if is_four:
                    ph["fours"] += 1
                if is_six:
                    ph["sixes"] += 1

                split_key = "vs_spin" if is_spin_bowl else "vs_pace"
                b[split_key]["balls"] += 1
                b[split_key]["runs"] += batter_runs
                if batter_out:
                    b[split_key]["dismissals"] += 1
                if is_dot:
                    b[split_key]["dot_balls"] += 1

                arm_key = "vs_left_arm" if is_left_arm_bowl else "vs_right_arm"
                b[arm_key]["balls"] += 1
                b[arm_key]["runs"] += batter_runs
                if batter_out:
                    b[arm_key]["dismissals"] += 1
                if is_dot:
                    b[arm_key]["dot_balls"] += 1

                # Per-match batting for form windows
                match_batting[batter]["runs"] += batter_runs
                match_batting[batter]["balls"] += 1
                if batter_out:
                    match_batting[batter]["dismissed"] = True

                if is_icc_tournament:
                    b["icc_tournament"]["balls"] += 1
                    b["icc_tournament"]["runs"] += batter_runs
                    if batter_out:
                        b["icc_tournament"]["dismissals"] += 1

                # ---- BOWLING ----
                if bowler not in bowling_stats:
                    bowling_stats[bowler] = _bowling_acc()
                bw = bowling_stats[bowler]
                bw["matches"].add(match_id)
                bw["balls"] += 1
                bw["runs"] += total_runs - extras  # runs off the bat only for economy
                if is_dot and batter_runs == 0 and extras == 0:
                    bw["dot_balls"] += 1
                for w in wickets:
                    if w.get("kind") not in ("run out", "obstructing the field", "retired hurt"):
                        bw["wickets"] += 1

                bph = bw["phases"][phase]
                bph["balls"] += 1
                bph["runs"] += total_runs - extras
                for w in wickets:
                    if w.get("kind") not in ("run out", "obstructing the field", "retired hurt"):
                        bph["wickets"] += 1
                if is_dot and extras == 0:
                    bph["dot_balls"] += 1

                hand_key = "vs_left_hand" if is_left_hand_bat else "vs_right_hand"
                bw[hand_key]["balls"] += 1
                bw[hand_key]["runs"] += total_runs - extras
                for w in wickets:
                    if w.get("kind") not in ("run out", "obstructing the field", "retired hurt"):
                        bw[hand_key]["wickets"] += 1
                if is_dot and extras == 0:
                    bw[hand_key]["dot_balls"] += 1

                # Per-match bowling for form windows
                match_bowling[bowler]["balls"] += 1
                match_bowling[bowler]["runs"] += total_runs - extras
                for w in wickets:
                    if w.get("kind") not in ("run out", "obstructing the field", "retired hurt"):
                        match_bowling[bowler]["wickets"] += 1

                if is_icc_tournament:
                    bw["icc_tournament"]["balls"] += 1
                    bw["icc_tournament"]["runs"] += total_runs - extras
                    for w in wickets:
                        if w.get("kind") not in ("run out", "obstructing the field", "retired hurt"):
                            bw["icc_tournament"]["wickets"] += 1

                # ---- MATCHUP ----
                key = (batter, bowler)
                if key not in matchups:
                    matchups[key] = {
                        "balls": 0, "runs": 0, "dismissals": 0,
                        "fours": 0, "sixes": 0, "dot_balls": 0,
                        "phases": {
                            "powerplay": {"balls": 0, "runs": 0, "dismissals": 0},
                            "middle":    {"balls": 0, "runs": 0, "dismissals": 0},
                            "death":     {"balls": 0, "runs": 0, "dismissals": 0},
                        },
                        "last_match_date": match_date_str,
                    }
                mu = matchups[key]
                mu["balls"] += 1
                mu["runs"] += batter_runs
                if batter_out:
                    mu["dismissals"] += 1
                if is_four:
                    mu["fours"] += 1
                if is_six:
                    mu["sixes"] += 1
                if is_dot:
                    mu["dot_balls"] += 1
                mu["phases"][phase]["balls"] += 1
                mu["phases"][phase]["runs"] += batter_runs
                if batter_out:
                    mu["phases"][phase]["dismissals"] += 1
                if match_date_str and (mu["last_match_date"] is None or match_date_str > mu["last_match_date"]):
                    mu["last_match_date"] = match_date_str

    # Append per-match summaries to by_match for form window computation
    for batter, mb in match_batting.items():
        if mb["balls"] > 0 and batter in batting_stats:
            batting_stats[batter]["by_match"].append({
                "date":      match_date_str,
                "runs":      mb["runs"],
                "balls":     mb["balls"],
                "dismissed": mb["dismissed"],
                "source":    source,
            })
    for bowler, mb in match_bowling.items():
        if mb["balls"] > 0 and bowler in bowling_stats:
            bowling_stats[bowler]["by_match"].append({
                "date":    match_date_str,
                "balls":   mb["balls"],
                "runs":    mb["runs"],
                "wickets": mb["wickets"],
                "source":  source,
            })


# ---------------------------------------------------------------------------
# Stat finalisation helpers
# ---------------------------------------------------------------------------

def _reliability(balls: int) -> str:
    if balls < 36:   # < ~6 overs equivalent
        return "low"
    elif balls < 120:
        return "medium"
    return "high"


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return round(a / b, 2) if b > 0 else default


_TODAY = date(2026, 5, 15)


def _batting_form_windows(by_match: List[dict]) -> dict:
    """Compute last-12m, last-6m, last-5 form windows from per-match innings list."""
    sorted_matches = sorted(
        [m for m in by_match if m.get("date")],
        key=lambda m: m["date"],
        reverse=True,
    )
    cutoff_12m = date(_TODAY.year - 1, _TODAY.month, _TODAY.day).isoformat()
    cutoff_6m_month = _TODAY.month - 6
    cutoff_6m_year  = _TODAY.year
    if cutoff_6m_month <= 0:
        cutoff_6m_month += 12
        cutoff_6m_year  -= 1
    cutoff_6m = date(cutoff_6m_year, cutoff_6m_month, _TODAY.day).isoformat()

    def window_stats(matches: List[dict]) -> dict:
        if not matches:
            return {"matches": 0, "runs": 0, "balls": 0, "strike_rate": 0.0, "average": 0.0}
        r = sum(m["runs"] for m in matches)
        b = sum(m["balls"] for m in matches)
        d = sum(1 for m in matches if m.get("dismissed"))
        return {
            "matches":     len(matches),
            "runs":        r,
            "balls":       b,
            "strike_rate": _safe_div(r * 100, b),
            "average":     _safe_div(r, d if d > 0 else 1),
        }

    last_5   = sorted_matches[:5]
    last_6m  = [m for m in sorted_matches if m["date"] >= cutoff_6m]
    last_12m = [m for m in sorted_matches if m["date"] >= cutoff_12m]

    return {
        "last_5_matches": window_stats(last_5),
        "last_6_months":  window_stats(last_6m),
        "last_12_months": window_stats(last_12m),
    }


def finalise_batting(acc: dict) -> dict:
    balls = acc["balls"]
    runs = acc["runs"]
    dismissals = acc["dismissals"]

    def phase_out(ph: dict) -> dict:
        return {
            "balls":        ph["balls"],
            "runs":         ph["runs"],
            "strike_rate":  _safe_div(ph["runs"] * 100, ph["balls"]),
            "dot_ball_pct": _safe_div(ph["dot_balls"] * 100, ph["balls"]),
            "boundary_pct": _safe_div((ph["fours"] + ph["sixes"]) * 100, ph["balls"]),
            "dismissals":   ph["dismissals"],
        }

    def split_out(sp: dict) -> dict:
        return {
            "strike_rate":    _safe_div(sp["runs"] * 100, sp["balls"]),
            "dot_ball_pct":   _safe_div(sp["dot_balls"] * 100, sp["balls"]),
            "dismissal_rate": _safe_div(sp["dismissals"], sp["balls"]),
        }

    icc = acc["icc_tournament"]
    n_matches = len(acc["matches"])
    return {
        "matches":       n_matches,
        "caps":          n_matches,
        "innings":       acc["innings"] or n_matches,
        "runs":          runs,
        "average":       _safe_div(runs, dismissals if dismissals > 0 else 1),
        "strike_rate":   _safe_div(runs * 100, balls),
        "boundary_pct":  _safe_div((acc["fours"] + acc["sixes"]) * 100, balls),
        "dot_ball_pct":  _safe_div(acc["dot_balls"] * 100, balls),
        "fifties":       acc["fifties"],
        "hundreds":      acc["hundreds"],
        "phase_splits": {
            "powerplay": phase_out(acc["phases"]["powerplay"]),
            "middle":    phase_out(acc["phases"]["middle"]),
            "death":     phase_out(acc["phases"]["death"]),
        },
        "vs_pace":      split_out(acc["vs_pace"]),
        "vs_spin":      split_out(acc["vs_spin"]),
        "vs_left_arm":  split_out(acc["vs_left_arm"]),
        "vs_right_arm": split_out(acc["vs_right_arm"]),
        "form_windows": _batting_form_windows(acc["by_match"]),
        "icc_tournament_record": {
            "matches":      len({m["date"] for m in acc["by_match"] if m.get("source") == "icc"}),
            "runs":         icc["runs"],
            "average":      _safe_div(icc["runs"], icc["dismissals"] if icc["dismissals"] > 0 else 1),
            "strike_rate":  _safe_div(icc["runs"] * 100, icc["balls"]),
        },
        "pressure_index": {
            "high_rr_sr": None,
            "low_rr_sr":  None,
            "defending_sr": None,
        },
        "statistical_reliability": _reliability(balls),
    }


def _bowling_form_windows(by_match: List[dict]) -> dict:
    sorted_matches = sorted(
        [m for m in by_match if m.get("date")],
        key=lambda m: m["date"],
        reverse=True,
    )
    cutoff_12m = date(_TODAY.year - 1, _TODAY.month, _TODAY.day).isoformat()
    cutoff_6m_month = _TODAY.month - 6
    cutoff_6m_year  = _TODAY.year
    if cutoff_6m_month <= 0:
        cutoff_6m_month += 12
        cutoff_6m_year  -= 1
    cutoff_6m = date(cutoff_6m_year, cutoff_6m_month, _TODAY.day).isoformat()

    def window_stats(matches: List[dict]) -> dict:
        if not matches:
            return {"matches": 0, "overs": 0.0, "wickets": 0, "economy": 0.0}
        b = sum(m["balls"] for m in matches)
        r = sum(m["runs"] for m in matches)
        w = sum(m["wickets"] for m in matches)
        overs = b / 6
        return {
            "matches": len(matches),
            "overs":   round(overs, 1),
            "wickets": w,
            "economy": _safe_div(r, overs),
        }

    last_5   = sorted_matches[:5]
    last_6m  = [m for m in sorted_matches if m["date"] >= cutoff_6m]
    last_12m = [m for m in sorted_matches if m["date"] >= cutoff_12m]

    return {
        "last_5_matches": window_stats(last_5),
        "last_6_months":  window_stats(last_6m),
        "last_12_months": window_stats(last_12m),
    }


def finalise_bowling(acc: dict) -> dict:
    balls = acc["balls"]
    runs = acc["runs"]
    wickets = acc["wickets"]

    def bph_out(ph: dict) -> dict:
        overs = ph["balls"] / 6
        return {
            "overs":        round(overs, 1),
            "runs":         ph["runs"],
            "wickets":      ph["wickets"],
            "economy":      _safe_div(ph["runs"], overs),
            "dot_ball_pct": _safe_div(ph["dot_balls"] * 100, ph["balls"]),
        }

    def bsp_out(sp: dict) -> dict:
        overs = sp["balls"] / 6
        return {
            "economy":          _safe_div(sp["runs"], overs),
            "dot_ball_pct":     _safe_div(sp["dot_balls"] * 100, sp["balls"]),
            "wickets_per_over": _safe_div(sp["wickets"], overs),
        }

    icc = acc["icc_tournament"]
    icc_overs = icc["balls"] / 6
    n_matches = len(acc["matches"])
    return {
        "matches":       n_matches,
        "caps":          n_matches,
        "innings":       acc["innings"] or n_matches,
        "overs":         round(balls / 6, 1),
        "wickets":       wickets,
        "average":       _safe_div(runs, wickets if wickets > 0 else 1),
        "economy":       _safe_div(runs, balls / 6),
        "strike_rate":   _safe_div(balls, wickets if wickets > 0 else 1),
        "dot_ball_pct":  _safe_div(acc["dot_balls"] * 100, balls),
        "phase_splits": {
            "powerplay": bph_out(acc["phases"]["powerplay"]),
            "middle":    bph_out(acc["phases"]["middle"]),
            "death":     bph_out(acc["phases"]["death"]),
        },
        "vs_left_hand":  bsp_out(acc["vs_left_hand"]),
        "vs_right_hand": bsp_out(acc["vs_right_hand"]),
        "death_specialist":     acc["phases"]["death"]["balls"] > 60,
        "powerplay_specialist": acc["phases"]["powerplay"]["balls"] > 60,
        "form_windows": _bowling_form_windows(acc["by_match"]),
        "icc_tournament_record": {
            "matches":  len({m["date"] for m in acc["by_match"] if m.get("source") == "icc"}),
            "wickets":  icc["wickets"],
            "economy":  _safe_div(icc["runs"], icc_overs),
        },
        "statistical_reliability": _reliability(balls),
    }


def finalise_matchup(batter: str, bowler: str, acc: dict) -> dict:
    balls = acc["balls"]

    def reliability(b: int) -> str:
        if b < 6:
            return "low"
        elif b <= 20:
            return "medium"
        return "high"

    return {
        "batter_id":    batter,
        "bowler_id":    bowler,
        "balls_faced":  balls,
        "runs":         acc["runs"],
        "dismissals":   acc["dismissals"],
        "strike_rate":  _safe_div(acc["runs"] * 100, balls),
        "dot_ball_pct": _safe_div(acc["dot_balls"] * 100, balls),
        "boundary_pct": _safe_div((acc["fours"] + acc["sixes"]) * 100, balls),
        "by_phase": {
            phase: {
                "balls":      acc["phases"][phase]["balls"],
                "runs":       acc["phases"][phase]["runs"],
                "dismissals": acc["phases"][phase]["dismissals"],
            }
            for phase in ("powerplay", "middle", "death")
        },
        "statistical_reliability": reliability(balls),
        "last_updated": acc["last_match_date"],
    }


# ---------------------------------------------------------------------------
# Load matches from a ZIP
# ---------------------------------------------------------------------------

def load_matches_from_zip(zip_path: Path, since: Optional[date] = None) -> List[dict]:
    matches = []
    if not zip_path.exists():
        print(f"  [SKIP] {zip_path.name} not found")
        return matches
    with zipfile.ZipFile(zip_path) as zf:
        json_files = [n for n in zf.namelist() if n.endswith(".json") and "info" not in n]
        for name in json_files:
            with zf.open(name) as f:
                try:
                    match = json.load(f)
                except json.JSONDecodeError:
                    continue
                if since:
                    match_dates = match.get("info", {}).get("dates", [])
                    if not match_dates:
                        continue
                    try:
                        match_date = date.fromisoformat(str(match_dates[0]))
                    except ValueError:
                        continue
                    if match_date < since:
                        continue
                matches.append(match)
    return matches


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def _load_lookups() -> tuple:
    """Load name_map.json and bowler_styles.json; return (cricsheet_to_id, bowler_styles, batting_hands)."""
    scripts_dir = Path(__file__).parent
    name_map_path = scripts_dir / "name_map.json"
    styles_path   = scripts_dir / "bowler_styles.json"

    # cricsheet_name → player_id
    cricsheet_to_id: Dict[str, str] = {}
    if name_map_path.exists():
        raw = json.loads(name_map_path.read_text())
        for team_data in raw.values():
            if isinstance(team_data, dict) and "_note" not in team_data:
                for entry in team_data.values():
                    if isinstance(entry, dict):
                        pid = entry.get("player_id", "")
                        for cs_name in entry.get("cricsheet_names", []):
                            cricsheet_to_id[cs_name] = pid

    bowler_styles: Dict[str, str] = {}
    batting_hands: Dict[str, str] = {}
    if styles_path.exists():
        raw = json.loads(styles_path.read_text())
        bowler_styles = raw.get("bowler_styles", {})
        batting_hands = raw.get("batting_hands", {})

    return cricsheet_to_id, bowler_styles, batting_hands


def run(
    sources: Optional[List[str]] = None,
    since: Optional[date] = None,
    validate_only: bool = False,
) -> None:
    sources = sources or list(ZIPS.keys())

    cricsheet_to_id, bowler_styles, batting_hands = _load_lookups()
    print(f"Lookups loaded: {len(cricsheet_to_id)} name mappings, {len(bowler_styles)} bowling styles")

    # Build set of all known WC squad player CricSheet names
    wc_squad_names: Set[str] = set(cricsheet_to_id.keys())

    batting_stats: Dict[str, dict] = defaultdict(_batting_acc)
    bowling_stats: Dict[str, dict] = defaultdict(_bowling_acc)
    matchups: Dict[tuple, dict] = {}
    # Pre-populate meta from lookup files so we get style/hand splits even
    # for bowlers whose match-level registry is absent
    bowler_meta: Dict[str, Optional[str]] = dict(bowler_styles)
    batter_meta: Dict[str, dict] = {
        name: {"batting_hand": hand} for name, hand in batting_hands.items()
    }

    ICC_TOURNAMENT_SOURCES = {"t20i"}

    for source in sources:
        zip_path = ZIPS[source]
        print(f"Loading {source} from {zip_path.name}...")
        matches = load_matches_from_zip(zip_path, since=since)
        print(f"  {len(matches)} matches loaded")

        for match in matches:
            info = match.get("info", {})
            teams = info.get("teams", [])

            # Include match if: (1) WC team is playing, OR (2) any WC squad player is playing
            has_wc_team = any(t in WC_TEAMS for t in teams)
            has_wc_squad_member = False
            if not has_wc_team:
                # Check if any WC squad player appears in this match
                for inning in match.get("innings", []):
                    for over in inning.get("overs", []):
                        for d in over.get("deliveries", []):
                            if d.get("batter") in wc_squad_names or d.get("bowler") in wc_squad_names:
                                has_wc_squad_member = True
                                break
                        if has_wc_squad_member:
                            break
                    if has_wc_squad_member:
                        break

            if not has_wc_team and not has_wc_squad_member:
                continue

            event_name = info.get("event", {}).get("name", "").lower()
            is_icc = source in ICC_TOURNAMENT_SOURCES and any(
                kw in event_name for kw in ICC_EVENT_KEYWORDS
            )
            # Use "icc" as source tag in by_match for actual ICC events
            effective_source = "icc" if is_icc else source

            parse_match(
                match,
                source=effective_source,
                batting_stats=batting_stats,
                bowling_stats=bowling_stats,
                matchups=matchups,
                bowler_meta=bowler_meta,
                batter_meta=batter_meta,
                is_icc_tournament=is_icc,
            )

    if validate_only:
        _validate(batting_stats, bowling_stats, matchups, cricsheet_to_id)
        return

    _write_player_files(batting_stats, bowling_stats, cricsheet_to_id)
    _write_matchups(matchups)
    print("\nDone.")


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def _write_player_files(
    batting_stats: Dict[str, dict],
    bowling_stats: Dict[str, dict],
    cricsheet_to_id: Dict[str, str],
) -> None:
    """Merge computed stats into existing player JSON files.

    Matches on CricSheet abbreviated names via cricsheet_to_id lookup,
    falling back to direct full-name match for teams using full names (Bangladesh, Pakistan, etc.).
    """
    # Build reverse: player_id → list of CricSheet name aliases
    id_to_cs_names: Dict[str, List[str]] = defaultdict(list)
    for cs_name, pid in cricsheet_to_id.items():
        id_to_cs_names[pid].append(cs_name)

    for team_slug in TEAM_SLUG.values():
        player_file = PLAYERS_DIR / f"{team_slug}.json"
        if not player_file.exists():
            continue

        with open(player_file) as f:
            players: List[dict] = json.load(f)

        updated = 0
        for player in players:
            pid  = player.get("id", "")
            name = player.get("name", "")

            # Try CricSheet aliases first, then direct full-name match
            cs_aliases = id_to_cs_names.get(pid, [])
            batting_acc = None
            bowling_acc = None
            for alias in cs_aliases:
                if alias in batting_stats:
                    batting_acc = batting_stats[alias]
                    break
                if alias in bowling_stats:
                    bowling_acc = bowling_stats[alias]

            # Direct full-name fallback (Bangladesh, Pakistan use full names in CricSheet)
            if batting_acc is None and name in batting_stats:
                batting_acc = batting_stats[name]
            if bowling_acc is None and name in bowling_stats:
                bowling_acc = bowling_stats[name]

            # Also try each alias for bowling independently
            if bowling_acc is None:
                for alias in cs_aliases:
                    if alias in bowling_stats:
                        bowling_acc = bowling_stats[alias]
                        break

            if batting_acc:
                fb = finalise_batting(batting_acc)
                player["t20i_stats"]["batting"] = fb
                player["caps"] = fb["matches"]
                updated += 1

            if bowling_acc and player.get("bowling_style"):
                fb_bowl = finalise_bowling(bowling_acc)
                player["t20i_stats"]["bowling"] = fb_bowl
                if not batting_acc:
                    # Bowler-only: set caps from bowling matches
                    player["caps"] = fb_bowl["matches"]
                    updated += 1

        with open(player_file, "w") as f:
            json.dump(players, f, indent=2)

        print(f"  {team_slug}: {updated}/{len(players)} players updated")


def _write_matchups(matchups: Dict[tuple, dict]) -> None:
    out = {
        "_meta": {
            "description": "Batter vs bowler head-to-head records derived from CricSheet ball-by-ball data",
            "source": "cricsheet.org women's T20I + WPL + WBBL + The Hundred datasets",
            "last_updated": date.today().isoformat(),
            "total_pairs": len(matchups),
            "reliability_thresholds": {
                "low":    "fewer than 6 balls faced",
                "medium": "6 to 20 balls faced",
                "high":   "more than 20 balls faced",
            },
        },
        "matchups": [
            finalise_matchup(batter, bowler, acc)
            for (batter, bowler), acc in sorted(matchups.items())
        ],
    }
    out_path = DATA_DIR / "matchups.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  matchups.json: {len(matchups)} pairs written")


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------

def _validate(
    batting_stats: dict,
    bowling_stats: dict,
    matchups: dict,
    cricsheet_to_id: Optional[Dict[str, str]] = None,
) -> None:
    print("\n=== DATA VALIDATION REPORT ===\n")

    cricsheet_to_id = cricsheet_to_id or {}
    id_to_cs_names: Dict[str, List[str]] = defaultdict(list)
    for cs_name, pid in cricsheet_to_id.items():
        id_to_cs_names[pid].append(cs_name)

    # Players with no data found
    for team_slug in TEAM_SLUG.values():
        player_file = PLAYERS_DIR / f"{team_slug}.json"
        if not player_file.exists():
            continue
        with open(player_file) as f:
            players = json.load(f)
        missing = []
        for p in players:
            pid  = p.get("id", "")
            name = p.get("name", "")
            aliases = id_to_cs_names.get(pid, [])
            found = (
                name in batting_stats or any(a in batting_stats for a in aliases) or
                name in bowling_stats or any(a in bowling_stats for a in aliases)
            )
            if not found:
                missing.append(name)
        if missing:
            print(f"[{team_slug}] No data found for: {', '.join(missing)}")

    # Low-reliability matchups
    low = sum(1 for acc in matchups.values() if acc["balls"] < 6)
    med = sum(1 for acc in matchups.values() if 6 <= acc["balls"] <= 20)
    high = sum(1 for acc in matchups.values() if acc["balls"] > 20)
    print(f"\nMatchup reliability: {high} high / {med} medium / {low} low (total {len(matchups)})")

    # Players with thin T20I records
    thin = [
        name for name, acc in batting_stats.items()
        if acc["balls"] < 120 and any(
            p.get("name") == name
            for pf in PLAYERS_DIR.glob("*.json")
            for p in json.loads(pf.read_text())
        )
    ]
    print(f"\nPlayers with < 20 T20I innings equivalent (thin records): {len(thin)}")
    for name in sorted(thin):
        print(f"  - {name}: {batting_stats[name]['balls']} balls")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse CricSheet data into wt20-oracle JSON files")
    parser.add_argument(
        "--source",
        choices=list(ZIPS.keys()),
        nargs="+",
        help="Which dataset(s) to process (default: all)",
    )
    parser.add_argument(
        "--since",
        type=lambda s: date.fromisoformat(s),
        default=None,
        help="Only include matches on or after this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Dry run — print data gap report without writing files",
    )
    args = parser.parse_args()

    run(sources=args.source, since=args.since, validate_only=args.validate)
