"""
Data loaders for the wt20-oracle Streamlit dashboard.

All functions return pandas DataFrames. Results are cached via
st.cache_data so repeated page renders don't re-read disk.
"""

import json
from pathlib import Path
from typing import Optional

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
PROJECT_ROOT = Path(__file__).parent.parent.parent
MATCHES_DIR = PROJECT_ROOT / "matches"


# ── Predictions ───────────────────────────────────────────────────────────────

def load_predictions() -> pd.DataFrame:
    """
    Load all prediction.json files from matches/ into a flat DataFrame.
    Dual-scenario predictions get one row per scenario (batting_first / chasing).
    """
    rows = []
    if not MATCHES_DIR.exists():
        return pd.DataFrame()

    for match_dir in sorted(MATCHES_DIR.iterdir()):
        if not match_dir.is_dir():
            continue
        pred_file = match_dir / "prediction" / "prediction.json"
        meta_file = match_dir / "metadata.json"
        if not pred_file.exists():
            continue

        try:
            with open(pred_file) as f:
                pred = json.load(f)
            meta: dict = {}
            if meta_file.exists():
                with open(meta_file) as f:
                    meta = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        base = {
            "match_id": match_dir.name,
            "team": pred.get("team") or meta.get("team_id", "india"),
            "opponent": pred.get("opponent") or meta.get("opponent_id", "?"),
            "venue": pred.get("venue") or meta.get("venue_id", "?"),
            "date": meta.get("date", ""),
            "scenario": pred.get("scenario", "unknown"),
            "pitch_difficulty": pred.get("pitch_difficulty"),
            "chase_penalty": pred.get("chase_penalty"),
            "runs_base": (pred.get("runs_estimate") or {}).get("base"),
            "runs_adjusted": (pred.get("runs_estimate") or {}).get("adjusted"),
            "runs_lower": (pred.get("runs_estimate") or {}).get("lower"),
            "runs_upper": (pred.get("runs_estimate") or {}).get("upper"),
            "generated_at": pred.get("generated_at", ""),
            "errors": len(pred.get("errors", [])),
            "warnings": len(pred.get("warnings", [])),
        }

        bf = pred.get("batting_first_scenario")
        ch = pred.get("chasing_scenario")

        if bf and ch:
            rows.append({**base,
                "situation": "Batting First",
                "win_probability": bf.get("win_probability"),
                "strategy_brief": (bf.get("strategy_brief") or "")[:120],
            })
            rows.append({**base,
                "situation": "Chasing",
                "win_probability": ch.get("win_probability"),
                "strategy_brief": (ch.get("strategy_brief") or "")[:120],
            })
        else:
            rows.append({**base,
                "situation": "Single",
                "win_probability": pred.get("win_probability"),
                "strategy_brief": (pred.get("strategy_brief") or "")[:120],
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["opponent"] = df["opponent"].str.replace("_", " ").str.title()
    df["venue"] = df["venue"].str.replace("_", " ").str.title()
    df["win_pct"] = (df["win_probability"] * 100).round(1)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


# ── Players ───────────────────────────────────────────────────────────────────

def load_players(team_filter: Optional[str] = None) -> pd.DataFrame:
    """
    Load all player JSON files into a flat DataFrame.
    One row per player. Phase splits are flattened to powerplay/middle/death columns.
    """
    rows = []
    players_dir = DATA_DIR / "players"
    if not players_dir.exists():
        return pd.DataFrame()

    for pf in sorted(players_dir.glob("*.json")):
        team_id = pf.stem
        if team_filter and team_id != team_filter.lower():
            continue
        try:
            with open(pf) as f:
                players = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        for p in (players if isinstance(players, list) else [p]):
            t20i = p.get("t20i_stats") or {}
            bat = t20i.get("batting") or {}
            bowl = t20i.get("bowling") or {}
            bat_pp = (bat.get("phase_splits") or {}).get("powerplay") or {}
            bat_md = (bat.get("phase_splits") or {}).get("middle") or {}
            bat_dt = (bat.get("phase_splits") or {}).get("death") or {}
            bowl_pp = (bowl.get("phase_splits") or {}).get("powerplay") or {}
            bowl_md = (bowl.get("phase_splits") or {}).get("middle") or {}
            bowl_dt = (bowl.get("phase_splits") or {}).get("death") or {}

            rows.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "team": team_id,
                "role": p.get("role"),
                "batting_hand": p.get("batting_hand"),
                "bowling_style": p.get("bowling_style"),
                "caps": p.get("caps"),
                "fitness_status": p.get("fitness_status", "unknown"),
                # Batting
                "bat_matches": bat.get("matches"),
                "bat_runs": bat.get("runs"),
                "bat_average": bat.get("average"),
                "bat_sr": bat.get("strike_rate"),
                "bat_boundary_pct": bat.get("boundary_pct"),
                "bat_dot_pct": bat.get("dot_ball_pct"),
                "bat_fifties": bat.get("fifties", 0),
                # Batting phases
                "bat_pp_sr": bat_pp.get("strike_rate"),
                "bat_md_sr": bat_md.get("strike_rate"),
                "bat_dt_sr": bat_dt.get("strike_rate"),
                # Bowling
                "bowl_matches": bowl.get("matches"),
                "bowl_wickets": bowl.get("wickets"),
                "bowl_economy": bowl.get("economy"),
                "bowl_average": bowl.get("average"),
                "bowl_sr": bowl.get("strike_rate"),
                # Bowling phases
                "bowl_pp_econ": bowl_pp.get("economy"),
                "bowl_md_econ": bowl_md.get("economy"),
                "bowl_dt_econ": bowl_dt.get("economy"),
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["team_display"] = df["team"].str.replace("_", " ").str.title()
        df["role_display"] = df["role"].str.replace("_", " ").str.title()
    return df


# ── Teams ─────────────────────────────────────────────────────────────────────

def load_teams() -> pd.DataFrame:
    """Load teams.json into a flat DataFrame with phase performance columns."""
    teams_path = DATA_DIR / "teams.json"
    if not teams_path.exists():
        return pd.DataFrame()

    with open(teams_path) as f:
        teams = json.load(f)

    rows = []
    for t in (teams if isinstance(teams, list) else []):
        bat = t.get("batting_phase_performance", {})
        bowl = t.get("bowling_phase_performance", {})

        rows.append({
            "id": t.get("id"),
            "name": t.get("name"),
            "group": t.get("group"),
            "icc_ranking": t.get("icc_ranking"),
            "captain": t.get("captain"),
            # Batting phases
            "bat_pp_avg": (bat.get("powerplay") or {}).get("avg_score"),
            "bat_pp_rr": (bat.get("powerplay") or {}).get("run_rate"),
            "bat_md_avg": (bat.get("middle") or {}).get("avg_score"),
            "bat_md_rr": (bat.get("middle") or {}).get("run_rate"),
            "bat_dt_avg": (bat.get("death") or {}).get("avg_score"),
            "bat_dt_rr": (bat.get("death") or {}).get("run_rate"),
            # Bowling phases
            "bowl_pp_econ": (bowl.get("powerplay") or {}).get("economy"),
            "bowl_pp_wkts": (bowl.get("powerplay") or {}).get("wickets_taken_per_match"),
            "bowl_md_econ": (bowl.get("middle") or {}).get("economy"),
            "bowl_dt_econ": (bowl.get("death") or {}).get("economy"),
            "bowl_dt_wkts": (bowl.get("death") or {}).get("wickets_taken_per_match"),
        })

    return pd.DataFrame(rows)


# ── Matchups ──────────────────────────────────────────────────────────────────

def load_matchups(batter_filter: Optional[str] = None, bowler_filter: Optional[str] = None,
                  min_balls: int = 6) -> pd.DataFrame:
    """
    Load matchups.json. Filters to records with >= min_balls faced.
    Optionally filter by batter_id or bowler_id substring.
    """
    matchups_path = DATA_DIR / "matchups.json"
    if not matchups_path.exists():
        return pd.DataFrame()

    with open(matchups_path) as f:
        data = json.load(f)

    records = data.get("matchups", [])
    rows = []
    for m in records:
        if m.get("balls_faced", 0) < min_balls:
            continue
        if batter_filter and batter_filter.lower() not in m.get("batter_id", "").lower():
            continue
        if bowler_filter and bowler_filter.lower() not in m.get("bowler_id", "").lower():
            continue
        rows.append({
            "batter": m.get("batter_id"),
            "bowler": m.get("bowler_id"),
            "balls": m.get("balls_faced"),
            "runs": m.get("runs"),
            "dismissals": m.get("dismissals"),
            "strike_rate": m.get("strike_rate"),
            "dot_pct": m.get("dot_ball_pct"),
            "boundary_pct": m.get("boundary_pct"),
            "pp_balls": (m.get("by_phase") or {}).get("powerplay", {}).get("balls"),
            "md_balls": (m.get("by_phase") or {}).get("middle", {}).get("balls"),
            "dt_balls": (m.get("by_phase") or {}).get("death", {}).get("balls"),
        })

    return pd.DataFrame(rows)


# ── Prediction XI frequency ───────────────────────────────────────────────────

def load_xi_frequency() -> pd.DataFrame:
    """Count how often each player appears in predicted XIs."""
    counts: dict[str, int] = {}
    if not MATCHES_DIR.exists():
        return pd.DataFrame()

    for match_dir in MATCHES_DIR.iterdir():
        pred_file = match_dir / "prediction" / "prediction.json"
        if not pred_file.exists():
            continue
        try:
            with open(pred_file) as f:
                pred = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        for pid in pred.get("selected_xi", []):
            counts[pid] = counts.get(pid, 0) + 1

    if not counts:
        return pd.DataFrame()

    df = pd.DataFrame(list(counts.items()), columns=["player_id", "xi_count"])
    df = df.sort_values("xi_count", ascending=False).reset_index(drop=True)
    return df
