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
    # ── India vs Sri Lanka in India (Nov 2025, 5-match series) ──────────────
    # Result: India won 5-0
    {
        "id": "ind_sl_vis1_20251106",
        "date": "2025-11-06",
        "team_id": "india",
        "opponent_id": "sri_lanka",
        "venue_id": "aca_vdca_visakhapatnam",
        "series": "India vs Sri Lanka T20I Series 2025",
        "match_no": 1,
        "series_result": "win",  # India won
        "series_wins_before": 0,
    },
    {
        "id": "ind_sl_vis2_20251108",
        "date": "2025-11-08",
        "team_id": "india",
        "opponent_id": "sri_lanka",
        "venue_id": "aca_vdca_visakhapatnam",
        "series": "India vs Sri Lanka T20I Series 2025",
        "match_no": 2,
        "series_result": "win",
        "series_wins_before": 1,
    },
    {
        "id": "ind_sl_tvm1_20251112",
        "date": "2025-11-12",
        "team_id": "india",
        "opponent_id": "sri_lanka",
        "venue_id": "greenfield_thiruvananthapuram",
        "series": "India vs Sri Lanka T20I Series 2025",
        "match_no": 3,
        "series_result": "win",
        "series_wins_before": 2,
    },
    {
        "id": "ind_sl_tvm2_20251114",
        "date": "2025-11-14",
        "team_id": "india",
        "opponent_id": "sri_lanka",
        "venue_id": "greenfield_thiruvananthapuram",
        "series": "India vs Sri Lanka T20I Series 2025",
        "match_no": 4,
        "series_result": "win",
        "series_wins_before": 3,  # ← 3-0 up going into this match: MOMENTUM FACTOR APPLIES
    },
    {
        "id": "ind_sl_tvm3_20251116",
        "date": "2025-11-16",
        "team_id": "india",
        "opponent_id": "sri_lanka",
        "venue_id": "greenfield_thiruvananthapuram",
        "series": "India vs Sri Lanka T20I Series 2025",
        "match_no": 5,
        "series_result": "win",
        "series_wins_before": 4,
    },
    # ── Australia vs India in Australia (Jan–Feb 2026, 3-match series) ───────
    # Result: India won 2-1 (AUS perspective: LOSS, then NR, then LOSS)
    {
        "id": "aus_ind_scg_20260118",
        "date": "2026-01-18",
        "team_id": "australia",
        "opponent_id": "india",
        "venue_id": "scg_sydney",
        "series": "Australia vs India T20I Series 2026",
        "match_no": 1,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    {
        "id": "aus_ind_can_20260121",
        "date": "2026-01-21",
        "team_id": "australia",
        "opponent_id": "india",
        "venue_id": "manuka_oval_canberra",
        "series": "Australia vs India T20I Series 2026",
        "match_no": 2,
        "series_result": "no_result",
        "series_wins_before": 0,
    },
    {
        "id": "aus_ind_adl_20260124",
        "date": "2026-01-24",
        "team_id": "australia",
        "opponent_id": "india",
        "venue_id": "adelaide_oval",
        "series": "Australia vs India T20I Series 2026",
        "match_no": 3,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    # ── West Indies vs Sri Lanka in Caribbean (Feb 2026, 3-match series) ─────
    # Result: SL won 2-0 (WI perspective: NR, LOSS, LOSS)
    {
        "id": "wi_sl_gren1_20260201",
        "date": "2026-02-01",
        "team_id": "west_indies",
        "opponent_id": "sri_lanka",
        "venue_id": "national_cricket_stadium_grenada",
        "series": "West Indies vs Sri Lanka T20I Series 2026",
        "match_no": 1,
        "series_result": "no_result",
        "series_wins_before": 0,
    },
    {
        "id": "wi_sl_gren2_20260203",
        "date": "2026-02-03",
        "team_id": "west_indies",
        "opponent_id": "sri_lanka",
        "venue_id": "national_cricket_stadium_grenada",
        "series": "West Indies vs Sri Lanka T20I Series 2026",
        "match_no": 2,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    {
        "id": "wi_sl_gren3_20260205",
        "date": "2026-02-05",
        "team_id": "west_indies",
        "opponent_id": "sri_lanka",
        "venue_id": "national_cricket_stadium_grenada",
        "series": "West Indies vs Sri Lanka T20I Series 2026",
        "match_no": 3,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    # ── New Zealand vs South Africa in New Zealand (Feb–Mar 2026, 5-match) ──
    # Result: NZ won 4-1
    {
        "id": "nz_sa_bay_20260215",
        "date": "2026-02-15",
        "team_id": "new_zealand",
        "opponent_id": "south_africa",
        "venue_id": "bay_oval_mount_maunganui",
        "series": "New Zealand vs South Africa T20I Series 2026",
        "match_no": 1,
        "series_result": "win",
        "series_wins_before": 0,
    },
    {
        "id": "nz_sa_sed_20260218",
        "date": "2026-02-18",
        "team_id": "new_zealand",
        "opponent_id": "south_africa",
        "venue_id": "seddon_park_hamilton",
        "series": "New Zealand vs South Africa T20I Series 2026",
        "match_no": 2,
        "series_result": "loss",
        "series_wins_before": 1,
    },
    {
        "id": "nz_sa_eden_20260221",
        "date": "2026-02-21",
        "team_id": "new_zealand",
        "opponent_id": "south_africa",
        "venue_id": "eden_park_auckland",
        "series": "New Zealand vs South Africa T20I Series 2026",
        "match_no": 3,
        "series_result": "win",
        "series_wins_before": 1,
    },
    {
        "id": "nz_sa_sky_20260224",
        "date": "2026-02-24",
        "team_id": "new_zealand",
        "opponent_id": "south_africa",
        "venue_id": "sky_stadium_wellington",
        "series": "New Zealand vs South Africa T20I Series 2026",
        "match_no": 4,
        "series_result": "win",
        "series_wins_before": 2,
    },
    {
        "id": "nz_sa_hag_20260227",
        "date": "2026-02-27",
        "team_id": "new_zealand",
        "opponent_id": "south_africa",
        "venue_id": "hagley_oval_christchurch",
        "series": "New Zealand vs South Africa T20I Series 2026",
        "match_no": 5,
        "series_result": "win",
        "series_wins_before": 3,
    },
    # ── South Africa vs India in South Africa (Mar–Apr 2026, 5-match) ────────
    # Result: SA won 4-1
    {
        "id": "sa_ind_dur1_20260315",
        "date": "2026-03-15",
        "team_id": "south_africa",
        "opponent_id": "india",
        "venue_id": "kingsmead_durban",
        "series": "South Africa vs India T20I Series 2026",
        "match_no": 1,
        "series_result": "win",
        "series_wins_before": 0,
    },
    {
        "id": "sa_ind_dur2_20260318",
        "date": "2026-03-18",
        "team_id": "south_africa",
        "opponent_id": "india",
        "venue_id": "kingsmead_durban",
        "series": "South Africa vs India T20I Series 2026",
        "match_no": 2,
        "series_result": "win",
        "series_wins_before": 1,
    },
    {
        "id": "sa_ind_wan1_20260322",
        "date": "2026-03-22",
        "team_id": "south_africa",
        "opponent_id": "india",
        "venue_id": "wanderers_johannesburg",
        "series": "South Africa vs India T20I Series 2026",
        "match_no": 3,
        "series_result": "win",
        "series_wins_before": 2,  # ← 2-0 up going into this; momentum starts at 3
    },
    {
        "id": "sa_ind_wan2_20260325",
        "date": "2026-03-25",
        "team_id": "south_africa",
        "opponent_id": "india",
        "venue_id": "wanderers_johannesburg",
        "series": "South Africa vs India T20I Series 2026",
        "match_no": 4,
        "series_result": "loss",
        "series_wins_before": 3,  # ← 3-0 up but lost this one
    },
    {
        "id": "sa_ind_cen_20260427",
        "date": "2026-04-27",
        "team_id": "south_africa",
        "opponent_id": "india",
        "venue_id": "supersport_park_centurion",
        "series": "South Africa vs India T20I Series 2026",
        "match_no": 5,
        "series_result": "win",
        "series_wins_before": 3,  # ← 3-0 up: MOMENTUM FACTOR APPLIES
        "notes": "The match that exposed the scenario-detection bug",
    },
    # ── Bangladesh vs Sri Lanka in Bangladesh (Mar 2026, 3-match series) ─────
    # Result: SL won 2-1
    {
        "id": "ban_sl_syl1_20260301",
        "date": "2026-03-01",
        "team_id": "bangladesh",
        "opponent_id": "sri_lanka",
        "venue_id": "sylhet_international",
        "series": "Bangladesh vs Sri Lanka T20I Series 2026",
        "match_no": 1,
        "series_result": "win",
        "series_wins_before": 0,
    },
    {
        "id": "ban_sl_syl2_20260303",
        "date": "2026-03-03",
        "team_id": "bangladesh",
        "opponent_id": "sri_lanka",
        "venue_id": "sylhet_international",
        "series": "Bangladesh vs Sri Lanka T20I Series 2026",
        "match_no": 2,
        "series_result": "loss",
        "series_wins_before": 1,
    },
    {
        "id": "ban_sl_syl3_20260305",
        "date": "2026-03-05",
        "team_id": "bangladesh",
        "opponent_id": "sri_lanka",
        "venue_id": "sylhet_international",
        "series": "Bangladesh vs Sri Lanka T20I Series 2026",
        "match_no": 3,
        "series_result": "loss",
        "series_wins_before": 1,
    },
    # ── WT20 Qualifier Asia (Nepal, Apr 2026) — associate WC teams ───────────
    # Group matches (not series): Pakistan dominates
    {
        "id": "ban_pak_kir_20260405",
        "date": "2026-04-05",
        "team_id": "bangladesh",
        "opponent_id": "pakistan",
        "venue_id": "tribhuvan_university_kirtipur",
        "series": "ICC Women's T20 WC Asia Qualifier 2026",
        "match_no": 1,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    {
        "id": "sl_pak_kir_20260407",
        "date": "2026-04-07",
        "team_id": "sri_lanka",
        "opponent_id": "pakistan",
        "venue_id": "tribhuvan_university_kirtipur",
        "series": "ICC Women's T20 WC Asia Qualifier 2026",
        "match_no": 2,
        "series_result": "loss",
        "series_wins_before": 0,
    },
    {
        "id": "ban_sl_mul_20260410",
        "date": "2026-04-10",
        "team_id": "bangladesh",
        "opponent_id": "sri_lanka",
        "venue_id": "upper_mulpani_kathmandu",
        "series": "ICC Women's T20 WC Asia Qualifier 2026",
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
        state = run_pre_match_pipeline(
            team_id=fixture["team_id"],
            opponent_id=fixture["opponent_id"],
            venue_id=fixture["venue_id"],
            match_date=fixture["date"],
            toss_winner=None,
            toss_decision=None,
            series_number=fixture.get("match_no", 0),
            series_score=fixture.get("series_wins_before", 0),
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
