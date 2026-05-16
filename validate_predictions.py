#!/usr/bin/env python3
"""
Validation Report: Current Predictions vs Actual Results
=========================================================

Compares 30 pre-match predictions with actual match results from
MODEL_ACCURACY_REPORT.md to assess improvement from series momentum
and batter-bowler specificity enhancements.

Usage:
    python3 validate_predictions.py
"""

import json
from pathlib import Path
from collections import defaultdict
from statistics import mean, median, stdev

# Actual results from MODEL_ACCURACY_REPORT (key test cases with sufficient data)
ACTUAL_RESULTS = {
    "ind_sl_vis1_20251106": {"team_runs": 122, "result": "win", "scenario": "chasing"},
    "ind_sl_vis2_20251108": {"team_runs": 129, "result": "win", "scenario": "chasing"},
    "ind_sl_tvm1_20251112": {"team_runs": 115, "result": "win", "scenario": "chasing"},
    "ind_sl_tvm2_20251114": {"team_runs": 221, "result": "win", "scenario": "batting_first"},
    "ind_sl_tvm3_20251116": {"team_runs": 175, "result": "win", "scenario": "batting_first"},
    "aus_ind_adl_20260124": {"team_runs": 176, "result": "win", "scenario": "chasing"},
    "wi_sl_gren2_20260203": {"team_runs": 102, "result": "loss", "scenario": "chasing"},
    "wi_sl_gren3_20260205": {"team_runs": 121, "result": "loss", "scenario": "chasing"},
    "nz_sa_bay_20260215": {"team_runs": 190, "result": "win", "scenario": "batting_first"},
    "nz_sa_sed_20260218": {"team_runs": 159, "result": "loss", "scenario": "batting_first"},
    "nz_sa_eden_20260221": {"team_runs": 152, "result": "win", "scenario": "chasing"},
    "nz_sa_sky_20260224": {"team_runs": 160, "result": "win", "scenario": "chasing"},
    "nz_sa_hag_20260227": {"team_runs": 194, "result": "win", "scenario": "batting_first"},
    "sa_ind_dur1_20260315": {"team_runs": 158, "result": "loss", "scenario": "chasing"},
    "sa_ind_dur2_20260318": {"team_runs": 148, "result": "loss", "scenario": "chasing"},
    "sa_ind_wan1_20260322": {"team_runs": 193, "result": "loss", "scenario": "chasing"},
    "sa_ind_wan2_20260325": {"team_runs": 185, "result": "win", "scenario": "batting_first"},
    "sa_ind_cen_20260427": {"team_runs": 132, "result": "loss", "scenario": "batting_first"},
}

MATCHES_DIR = Path(__file__).parent / "matches"

def load_prediction(match_id: str) -> dict:
    """Load prediction.json for a match."""
    pred_path = MATCHES_DIR / match_id / "prediction" / "prediction.json"
    if pred_path.exists():
        with open(pred_path) as f:
            return json.load(f)
    return None

def calculate_error(predicted: float, actual: float) -> dict:
    """Calculate error metrics."""
    error = actual - predicted
    abs_error = abs(error)
    pct_error = (abs_error / actual * 100) if actual > 0 else 0
    return {
        "error": error,
        "abs_error": abs_error,
        "pct_error": pct_error,
        "within_20pct": pct_error <= 20,
        "within_30pct": pct_error <= 30,
    }

def main():
    print("\n" + "=" * 80)
    print("VALIDATION REPORT: Predictions with Series Momentum & Batter-Bowler Enhancements")
    print("=" * 80)

    results_by_metric = defaultdict(list)
    results_by_scenario = defaultdict(list)

    # Track errors for detailed analysis
    detailed_results = []

    print("\nMATCH-BY-MATCH RESULTS:")
    print("-" * 80)
    print(f"{'Match ID':<25} {'Predicted':<12} {'Actual':<12} {'Error':<10} {'Scenario':<15}")
    print("-" * 80)

    for match_id, actual in sorted(ACTUAL_RESULTS.items()):
        pred = load_prediction(match_id)
        if not pred:
            print(f"{match_id:<25} {'[NO PRED]':<12} {actual['team_runs']:<12}")
            continue

        predicted_runs = pred["adjusted_runs_estimate"]
        actual_runs = actual["team_runs"]
        scenario = actual["scenario"]

        error_metrics = calculate_error(predicted_runs, actual_runs)

        # For blended predictions, prefer scenario-specific estimate
        if scenario == "batting_first" and "batting_first_scenario" in pred:
            predicted_runs = pred["batting_first_scenario"]["adjusted_runs_estimate"]
            error_metrics = calculate_error(predicted_runs, actual_runs)
        elif scenario == "chasing" and "chasing_scenario" in pred:
            predicted_runs = pred["chasing_scenario"]["adjusted_runs_estimate"]
            error_metrics = calculate_error(predicted_runs, actual_runs)

        results_by_metric["pct_error"].append(error_metrics["pct_error"])
        results_by_metric["within_20pct"].append(error_metrics["within_20pct"])
        results_by_metric["within_30pct"].append(error_metrics["within_30pct"])
        results_by_scenario[scenario].append(error_metrics["pct_error"])

        status = "✓" if error_metrics["within_20pct"] else "✗" if error_metrics["pct_error"] > 30 else "~"
        print(f"{match_id:<25} {predicted_runs:<12.1f} {actual_runs:<12.0f} {error_metrics['pct_error']:<9.1f}% {scenario:<15} {status}")

        detailed_results.append({
            "match_id": match_id,
            "predicted": predicted_runs,
            "actual": actual_runs,
            "error_pct": error_metrics["pct_error"],
            "scenario": scenario,
        })

    print("-" * 80)

    # Summary statistics
    print("\n" + "=" * 80)
    print("ACCURACY METRICS")
    print("=" * 80)

    errors = results_by_metric["pct_error"]
    within_20 = sum(results_by_metric["within_20pct"])
    within_30 = sum(results_by_metric["within_30pct"])

    print(f"\nOverall (n={len(errors)}):")
    print(f"  Mean Error:        {mean(errors):.1f}%")
    print(f"  Median Error:      {median(errors):.1f}%")
    print(f"  Std Dev:           {stdev(errors):.1f}%")
    print(f"  Within ±20%:       {within_20}/{len(errors)} ({within_20/len(errors)*100:.0f}%)")
    print(f"  Within ±30%:       {within_30}/{len(errors)} ({within_30/len(errors)*100:.0f}%)")

    # By scenario
    print(f"\nBatting First (n={len(results_by_scenario.get('batting_first', []))}):")
    if results_by_scenario.get("batting_first"):
        bf_errors = results_by_scenario["batting_first"]
        print(f"  Mean Error:        {mean(bf_errors):.1f}%")
        print(f"  Median Error:      {median(bf_errors):.1f}%")

    print(f"\nChasing (n={len(results_by_scenario.get('chasing', []))}):")
    if results_by_scenario.get("chasing"):
        c_errors = results_by_scenario["chasing"]
        print(f"  Mean Error:        {mean(c_errors):.1f}%")
        print(f"  Median Error:      {median(c_errors):.1f}%")

    # Top errors
    print("\n" + "=" * 80)
    print("TOP ERRORS (Candidates for Further Enhancement)")
    print("=" * 80)

    sorted_results = sorted(detailed_results, key=lambda x: x["error_pct"], reverse=True)
    for i, result in enumerate(sorted_results[:5], 1):
        print(f"{i}. {result['match_id']:<25} {result['error_pct']:.1f}% error")
        print(f"   {result['scenario']:>25} Predicted {result['predicted']:.0f}, Actual {result['actual']:.0f}")

    # Momentum analysis
    print("\n" + "=" * 80)
    print("MOMENTUM FACTOR ANALYSIS")
    print("=" * 80)

    momentum_matches = [
        ("ind_sl_tvm2_20251114", "India 3-0 up, Match 4 (Sweep boost +20%)"),
        ("sa_ind_cen_20260427", "SA 3-0 up, Match 5 (Sweep boost +20%)"),
        ("nz_sa_hag_20260227", "NZ 3-0 up, Match 5 (Sweep boost +20%)"),
    ]

    for match_id, context in momentum_matches:
        if match_id in ACTUAL_RESULTS:
            result = load_prediction(match_id)
            if result:
                actual = ACTUAL_RESULTS[match_id]
                predicted = result["batting_first_scenario"]["adjusted_runs_estimate"]
                error = calculate_error(predicted, actual["team_runs"])
                print(f"\n{context}")
                print(f"  Prediction: {predicted:.0f} runs")
                print(f"  Actual:     {actual['team_runs']:.0f} runs")
                print(f"  Error:      {error['pct_error']:.1f}%")

if __name__ == "__main__":
    main()
