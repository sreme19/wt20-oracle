"""
Batch Predictions Runner
========================

Runs pre-match predictions for 30 historical WT20 team matches
(Nov 2025 – May 2026) and stores results in matches/ for regression
and validation testing.

Each match is run with toss_winner=None (scenario: unknown) because
historical toss data is not embedded here — scenario probabilities use
the balanced unknown path.

Usage:
    python scripts/batch_predictions.py
    python scripts/batch_predictions.py --match-id ind_sl_vis_20251106
    python scripts/batch_predictions.py --dry-run
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Ensure project root is on the path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from wt20_oracle.pre_match_graph import run_pre_match_pipeline

# ---------------------------------------------------------------------------
# Match fixtures (30 historical matches, Nov 2025 – May 2026)
# All involve WT20 2026 qualifying nations only
# ---------------------------------------------------------------------------

FIXTURES = [
    # ── India vs Sri Lanka in India (Dec 2025, 5-match series) ──────────────
    # Result: India won 5-0
    # Actual dates: Dec 21, 23, 26, 28, 30 (ESPNcricinfo confirmed)
    {
        "id": "ind_sl_vis1_20251221",
        "date": "2025-12-21",
        "team_id": "india",
        "opponent_id": "sri_lanka",
        "venue_id": "aca_vdca_visakhapatnam",
        "series": "India vs Sri Lanka T20I Series 2025",
        "match_no": 1,
        "series_result": "win",  # India won
        "series_wins_before": 0,
    },
    {
        "id": "ind_sl_vis2_20251223",
        "date": "2025-12-23",
        "team_id": "india",
        "opponent_id": "sri_lanka",
        "venue_id": "aca_vdca_visakhapatnam",
        "series": "India vs Sri Lanka T20I Series 2025",
        "match_no": 2,
        "series_result": "win",
        "series_wins_before": 1,
    },
    {
        "id": "ind_sl_tvm1_20251226",
        "date": "2025-12-26",
        "team_id": "india",
        "opponent_id": "sri_lanka",
        "venue_id": "greenfield_thiruvananthapuram",
        "series": "India vs Sri Lanka T20I Series 2025",
        "match_no": 3,
        "series_result": "win",
        "series_wins_before": 2,
    },
    {
        "id": "ind_sl_tvm2_20251228",
        "date": "2025-12-28",
        "team_id": "india",
        "opponent_id": "sri_lanka",
        "venue_id": "greenfield_thiruvananthapuram",
        "series": "India vs Sri Lanka T20I Series 2025",
        "match_no": 4,
        "series_result": "win",
        "series_wins_before": 3,  # ← 3-0 up going into this match: MOMENTUM FACTOR APPLIES
    },
    {
        "id": "ind_sl_tvm3_20251230",
        "date": "2025-12-30",
        "team_id": "india",
        "opponent_id": "sri_lanka",
        "venue_id": "greenfield_thiruvananthapuram",
        "series": "India vs Sri Lanka T20I Series 2025",
        "match_no": 5,
        "series_result": "win",
        "series_wins_before": 4,
    },
    # ── Australia vs India in Australia (Feb 2026, 3-match series) ───────────
    # Result: India won 2-1 (AUS perspective: LOSS, then NR, then LOSS)
    # Actual dates: Feb 15, 19, 21 (ESPNcricinfo confirmed)
    {
        "id": "aus_ind_scg_20260215",
        "date": "2026-02-15",
        "team_id": "australia",
        "opponent_id": "india",
        "venue_id": "scg_sydney",
        "series": "Australia vs India T20I Series 2026",
        "match_no": 1,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    {
        "id": "aus_ind_can_20260219",
        "date": "2026-02-19",
        "team_id": "australia",
        "opponent_id": "india",
        "venue_id": "manuka_oval_canberra",
        "series": "Australia vs India T20I Series 2026",
        "match_no": 2,
        "series_result": "no_result",
        "series_wins_before": 0,
    },
    {
        "id": "aus_ind_adl_20260221",
        "date": "2026-02-21",
        "team_id": "australia",
        "opponent_id": "india",
        "venue_id": "adelaide_oval",
        "series": "Australia vs India T20I Series 2026",
        "match_no": 3,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    # ── West Indies vs Sri Lanka in Caribbean (Feb–Mar 2026, 3-match series) ──
    # Result: SL won 2-0 (WI perspective: NR, LOSS, LOSS)
    # Actual dates: Feb 28, Mar 1, Mar 3 (ESPNcricinfo confirmed)
    {
        "id": "wi_sl_gren1_20260228",
        "date": "2026-02-28",
        "team_id": "west_indies",
        "opponent_id": "sri_lanka",
        "venue_id": "national_cricket_stadium_grenada",
        "series": "West Indies vs Sri Lanka T20I Series 2026",
        "match_no": 1,
        "series_result": "no_result",
        "series_wins_before": 0,
    },
    {
        "id": "wi_sl_gren2_20260301",
        "date": "2026-03-01",
        "team_id": "west_indies",
        "opponent_id": "sri_lanka",
        "venue_id": "national_cricket_stadium_grenada",
        "series": "West Indies vs Sri Lanka T20I Series 2026",
        "match_no": 2,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    {
        "id": "wi_sl_gren3_20260303",
        "date": "2026-03-03",
        "team_id": "west_indies",
        "opponent_id": "sri_lanka",
        "venue_id": "national_cricket_stadium_grenada",
        "series": "West Indies vs Sri Lanka T20I Series 2026",
        "match_no": 3,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    # ── New Zealand vs South Africa in New Zealand (Mar 2026, 5-match) ────────
    # Result: NZ won 4-1
    # Actual dates: Mar 15, 17, 20, 22, 25 (ESPNcricinfo confirmed)
    # Match 4 venue: Basin Reserve, Wellington (not Sky Stadium)
    {
        "id": "nz_sa_bay_20260315",
        "date": "2026-03-15",
        "team_id": "new_zealand",
        "opponent_id": "south_africa",
        "venue_id": "bay_oval_mount_maunganui",
        "series": "New Zealand vs South Africa T20I Series 2026",
        "match_no": 1,
        "series_result": "win",
        "series_wins_before": 0,
    },
    {
        "id": "nz_sa_sed_20260317",
        "date": "2026-03-17",
        "team_id": "new_zealand",
        "opponent_id": "south_africa",
        "venue_id": "seddon_park_hamilton",
        "series": "New Zealand vs South Africa T20I Series 2026",
        "match_no": 2,
        "series_result": "loss",
        "series_wins_before": 1,
    },
    {
        "id": "nz_sa_eden_20260320",
        "date": "2026-03-20",
        "team_id": "new_zealand",
        "opponent_id": "south_africa",
        "venue_id": "eden_park_auckland",
        "series": "New Zealand vs South Africa T20I Series 2026",
        "match_no": 3,
        "series_result": "win",
        "series_wins_before": 1,
    },
    {
        "id": "nz_sa_bas_20260322",
        "date": "2026-03-22",
        "team_id": "new_zealand",
        "opponent_id": "south_africa",
        "venue_id": "basin_reserve_wellington",
        "series": "New Zealand vs South Africa T20I Series 2026",
        "match_no": 4,
        "series_result": "win",
        "series_wins_before": 2,
    },
    {
        "id": "nz_sa_hag_20260325",
        "date": "2026-03-25",
        "team_id": "new_zealand",
        "opponent_id": "south_africa",
        "venue_id": "hagley_oval_christchurch",
        "series": "New Zealand vs South Africa T20I Series 2026",
        "match_no": 5,
        "series_result": "win",
        "series_wins_before": 3,
    },
    # ── South Africa vs India in South Africa (Apr 2026, 5-match) ─────────────
    # Result: SA won 4-1
    # Actual dates: Apr 17, 19, 22, 25, 27 (ESPNcricinfo confirmed)
    # Match 5 venue: Willowmoore Park, Benoni (not Supersport Park, Centurion)
    {
        "id": "sa_ind_dur1_20260417",
        "date": "2026-04-17",
        "team_id": "south_africa",
        "opponent_id": "india",
        "venue_id": "kingsmead_durban",
        "series": "South Africa vs India T20I Series 2026",
        "match_no": 1,
        "series_result": "win",
        "series_wins_before": 0,
    },
    {
        "id": "sa_ind_dur2_20260419",
        "date": "2026-04-19",
        "team_id": "south_africa",
        "opponent_id": "india",
        "venue_id": "kingsmead_durban",
        "series": "South Africa vs India T20I Series 2026",
        "match_no": 2,
        "series_result": "win",
        "series_wins_before": 1,
    },
    {
        "id": "sa_ind_wan1_20260422",
        "date": "2026-04-22",
        "team_id": "south_africa",
        "opponent_id": "india",
        "venue_id": "wanderers_johannesburg",
        "series": "South Africa vs India T20I Series 2026",
        "match_no": 3,
        "series_result": "win",
        "series_wins_before": 2,  # ← 2-0 up going into this; momentum starts at 3
    },
    {
        "id": "sa_ind_wan2_20260425",
        "date": "2026-04-25",
        "team_id": "south_africa",
        "opponent_id": "india",
        "venue_id": "wanderers_johannesburg",
        "series": "South Africa vs India T20I Series 2026",
        "match_no": 4,
        "series_result": "loss",
        "series_wins_before": 3,  # ← 3-0 up but lost this one
    },
    {
        "id": "sa_ind_ben_20260427",
        "date": "2026-04-27",
        "team_id": "south_africa",
        "opponent_id": "india",
        "venue_id": "willowmoore_park",
        "series": "South Africa vs India T20I Series 2026",
        "match_no": 5,
        "series_result": "win",
        "series_wins_before": 3,  # ← 3-0 up: MOMENTUM FACTOR APPLIES
        "notes": "Willowmoore Park, Benoni",
    },
    # ── Bangladesh vs Sri Lanka in Bangladesh (Apr–May 2026, 3-match series) ──
    # Result: SL won 2-1
    # Actual dates: Apr 28, 30, May 2 (ESPNcricinfo confirmed)
    {
        "id": "ban_sl_syl1_20260428",
        "date": "2026-04-28",
        "team_id": "bangladesh",
        "opponent_id": "sri_lanka",
        "venue_id": "sylhet_international",
        "series": "Bangladesh vs Sri Lanka T20I Series 2026",
        "match_no": 1,
        "series_result": "win",
        "series_wins_before": 0,
    },
    {
        "id": "ban_sl_syl2_20260430",
        "date": "2026-04-30",
        "team_id": "bangladesh",
        "opponent_id": "sri_lanka",
        "venue_id": "sylhet_international",
        "series": "Bangladesh vs Sri Lanka T20I Series 2026",
        "match_no": 2,
        "series_result": "loss",
        "series_wins_before": 1,
    },
    {
        "id": "ban_sl_syl3_20260502",
        "date": "2026-05-02",
        "team_id": "bangladesh",
        "opponent_id": "sri_lanka",
        "venue_id": "sylhet_international",
        "series": "Bangladesh vs Sri Lanka T20I Series 2026",
        "match_no": 3,
        "series_result": "loss",
        "series_wins_before": 1,
    },
    # ── WT20 Qualifier Asia (Nepal, Jan–Feb 2026) — associate WC teams ────────
    # NOTE: Bangladesh, Pakistan, Sri Lanka were direct qualifiers and did not
    # play in the official Asia Qualifier. These are synthetic calibration
    # fixtures using Nepal qualifier venues for model testing only.
    {
        "id": "ban_pak_kir_20260122",
        "date": "2026-01-22",
        "team_id": "bangladesh",
        "opponent_id": "pakistan",
        "venue_id": "tribhuvan_university_kirtipur",
        "series": "ICC Women's T20 WC Asia Qualifier 2026 (synthetic)",
        "match_no": 1,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    {
        "id": "sl_pak_kir_20260125",
        "date": "2026-01-25",
        "team_id": "sri_lanka",
        "opponent_id": "pakistan",
        "venue_id": "tribhuvan_university_kirtipur",
        "series": "ICC Women's T20 WC Asia Qualifier 2026 (synthetic)",
        "match_no": 2,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    {
        "id": "ban_sl_mul_20260128",
        "date": "2026-01-28",
        "team_id": "bangladesh",
        "opponent_id": "sri_lanka",
        "venue_id": "upper_mulpani_kathmandu",
        "series": "ICC Women's T20 WC Asia Qualifier 2026 (synthetic)",
        "match_no": 3,
        "series_result": "win",
        "series_wins_before": 0,
    },
    # ── England home series warm-ups (May 2026) ───────────────────────────────
    # Result: England won 2-1
    {
        "id": "eng_nz_oval_20260501",
        "date": "2026-05-01",
        "team_id": "england",
        "opponent_id": "new_zealand",
        "venue_id": "the_oval",
        "series": "England vs New Zealand T20I Series 2026",
        "match_no": 1,
        "series_result": "win",
        "series_wins_before": 0,
    },
    {
        "id": "eng_nz_rose_20260504",
        "date": "2026-05-04",
        "team_id": "england",
        "opponent_id": "new_zealand",
        "venue_id": "rose_bowl",
        "series": "England vs New Zealand T20I Series 2026",
        "match_no": 2,
        "series_result": "loss",
        "series_wins_before": 1,
    },
    {
        "id": "eng_nz_hd_20260507",
        "date": "2026-05-07",
        "team_id": "england",
        "opponent_id": "new_zealand",
        "venue_id": "headingley",
        "series": "England vs New Zealand T20I Series 2026",
        "match_no": 3,
        "series_result": "win",
        "series_wins_before": 1,
    },
]

assert len(FIXTURES) == 30, f"Expected 30 fixtures, got {len(FIXTURES)}"

MATCHES_DIR = ROOT / "matches"


# ─────────────────────────────────────────────────────────────────────────
# Phase 2 Task 3: Series Context Awareness
# ─────────────────────────────────────────────────────────────────────────

def detect_sweep_likelihood(
    fixtures: list,
    current_match_no: int,
    team_id: str,
    opponent_id: str,
    series_name: str,
) -> float:
    """
    Estimate likelihood of completing a sweep when team is 3-0 up.

    Returns: sweep_likelihood (0.0 to 1.0)
    - 1.0 = very likely to complete sweep
    - 0.5 = neutral, unknown
    - 0.0 = unlikely to complete sweep (team has loss while dominant)
    """
    # Get all matches in this series up to current match
    series_matches = [
        f for f in fixtures
        if f.get("series") == series_name
        and f.get("team_id") == team_id
        and f.get("match_no") < current_match_no
    ]

    # Sort by match number to get chronological order
    series_matches = sorted(series_matches, key=lambda x: x.get("match_no", 0))

    # Count wins and losses while accumulating
    wins = 0
    had_loss_when_dominant = False

    for match in series_matches:
        if match.get("series_result") == "win":
            wins += 1
        elif match.get("series_result") == "loss":
            # Check if team was already in dominant position (3-0+)
            if wins >= 3:
                had_loss_when_dominant = True

    # Sweep likelihood logic:
    # - If team had a loss while already 3-0 up, reduce likelihood (0.4)
    # - If team is on winning streak without losses, high likelihood (0.9)
    # - Otherwise neutral (0.5)

    if had_loss_when_dominant:
        # Team has already shown inability to complete sweep
        return 0.40  # Less likely to sweep
    elif wins >= 3 and not series_matches[-1].get("series_result") == "loss":
        # Team is 3-0 up with no losses at dominant level
        return 0.90  # Very likely to complete sweep
    else:
        # Default neutral likelihood
        return 0.50


def apply_series_context_adjustment(
    team_id: str,
    series_score: int,
    series_number: int,
    fixtures: list,
    series_name: str,
) -> float:
    """
    Apply series context adjustment to sweep momentum multiplier.

    Returns: sweep_likelihood_multiplier (0.0 to 1.0)
    - If team is 3-0 up and sweep is likely, return 1.0 (apply full momentum)
    - If team is 3-0 up but sweep is unlikely, return 0.5 (reduce momentum)
    """
    if series_score != 3 or series_number < 4:
        # Not a sweep scenario
        return 1.0

    # Calculate sweep likelihood
    likelihood = detect_sweep_likelihood(
        fixtures, series_number, team_id, "dummy_opponent", series_name
    )

    # Scale the momentum: full (1.0) if likely, reduced (0.5) if unlikely
    # Formula: 0.5 + (0.5 * likelihood)
    # likelihood=1.0 → multiplier=1.0 (full momentum)
    # likelihood=0.5 → multiplier=0.75 (75% momentum)
    # likelihood=0.4 → multiplier=0.7 (70% momentum)
    return 0.5 + (0.5 * likelihood)


def run_and_save(fixture: dict, dry_run: bool = False) -> dict:
    """Run pipeline for one fixture and save results to disk."""
    match_id = fixture["id"]
    match_dir = MATCHES_DIR / match_id
    prediction_path = match_dir / "prediction" / "prediction.json"

    if prediction_path.exists():
        print(f"  [skip] {match_id} — already exists")
        return {"status": "skipped", "id": match_id}

    if dry_run:
        print(f"  [dry-run] would run: {match_id}")
        return {"status": "dry_run", "id": match_id}

    print(f"  Running {match_id} ({fixture['team_id']} vs {fixture['opponent_id']} at {fixture['venue_id']})...")

    try:
        # Phase 2 Task 3: Calculate sweep likelihood based on series context
        series_number = fixture.get("match_no", 0)
        series_score = fixture.get("series_wins_before", 0)
        series_name = fixture.get("series", "")
        team_id = fixture["team_id"]
        opponent_id = fixture["opponent_id"]

        sweep_likelihood = apply_series_context_adjustment(
            team_id=team_id,
            series_score=series_score,
            series_number=series_number,
            fixtures=FIXTURES,
            series_name=series_name,
        )

        state = run_pre_match_pipeline(
            team_id=team_id,
            opponent_id=opponent_id,
            venue_id=fixture["venue_id"],
            match_date=fixture["date"],
            toss_winner=None,
            toss_decision=None,
            series_number=series_number,
            series_score=series_score,
            sweep_likelihood=sweep_likelihood,
        )

        # Build output payload
        result = {
            "match_id": match_id,
            "fixture": fixture,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "scenario": state.get("scenario"),
            "pitch_difficulty": state.get("pitch_difficulty"),
            "chase_penalty": state.get("chase_penalty"),
            "base_runs_estimate": state.get("base_runs_estimate"),
            "adjusted_runs_estimate": state.get("adjusted_runs_estimate"),
            "runs_lower": state.get("runs_lower"),
            "runs_upper": state.get("runs_upper"),
            "win_probability": state.get("win_probability"),
            "win_probability_reasoning": state.get("win_probability_reasoning"),
            "selected_xi": state.get("selected_xi"),
            "batting_order": state.get("batting_order"),
            "bowling_plan": state.get("bowling_plan"),
            "key_matchups": state.get("key_matchups"),
            "tactical_flags": state.get("tactical_flags"),
            "errors": state.get("errors", []),
            "warnings": state.get("warnings", []),
        }

        # Include per-scenario details if present (dual-scenario predictions)
        if state.get("batting_first_scenario"):
            result["batting_first_scenario"] = state["batting_first_scenario"]
        if state.get("chasing_scenario"):
            result["chasing_scenario"] = state["chasing_scenario"]

        # Save metadata and prediction
        match_dir.mkdir(parents=True, exist_ok=True)
        (match_dir / "prediction").mkdir(exist_ok=True)
        (match_dir / "actual").mkdir(exist_ok=True)

        metadata = {
            "match_id": match_id,
            "series": fixture.get("series", ""),
            "match_no": fixture.get("match_no", 1),
            "date": fixture["date"],
            "team_id": fixture["team_id"],
            "opponent_id": fixture["opponent_id"],
            "venue_id": fixture["venue_id"],
            "notes": fixture.get("notes", ""),
            "prediction_generated": result["generated_at"],
        }

        with open(match_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        with open(prediction_path, "w") as f:
            json.dump(result, f, indent=2)

        errors = state.get("errors", [])
        status = "ok" if not errors else "ok_with_errors"
        print(f"    → {status}: runs={result['adjusted_runs_estimate']}, wp={result['win_probability']}")
        if errors:
            for e in errors:
                print(f"    ⚠  {e}")

        return {"status": status, "id": match_id, "errors": errors}

    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        return {"status": "error", "id": match_id, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Batch prediction runner for 30 historical matches")
    parser.add_argument("--match-id", help="Run only a specific match ID")
    parser.add_argument("--dry-run", action="store_true", help="List what would run without executing")
    parser.add_argument("--force", action="store_true", help="Re-run even if prediction already exists")
    args = parser.parse_args()

    fixtures = FIXTURES
    if args.match_id:
        fixtures = [f for f in FIXTURES if f["id"] == args.match_id]
        if not fixtures:
            print(f"ERROR: match ID '{args.match_id}' not found")
            sys.exit(1)

    if args.force:
        # Remove existing predictions so they get re-run
        for fixture in fixtures:
            p = MATCHES_DIR / fixture["id"] / "prediction" / "prediction.json"
            if p.exists():
                p.unlink()

    print(f"\nBatch predictions: {len(fixtures)} match(es) to process")
    print("=" * 60)

    results = []
    for fixture in fixtures:
        r = run_and_save(fixture, dry_run=args.dry_run)
        results.append(r)

    # Summary
    ok = sum(1 for r in results if r["status"] in ("ok", "ok_with_errors"))
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")

    print("\n" + "=" * 60)
    print(f"Done: {ok} ran, {skipped} skipped, {errors} errors")

    # Save run summary
    if not args.dry_run:
        summary_path = MATCHES_DIR / "batch_run_summary.json"
        summary = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total": len(fixtures),
            "ok": ok,
            "skipped": skipped,
            "errors": errors,
            "results": results,
        }
        MATCHES_DIR.mkdir(parents=True, exist_ok=True)
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
