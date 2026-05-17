"""
Prediction Accuracy Auditor
============================

Fetches recent Women's T20 International results from the internet,
matches them against existing predictions in matches/, and reports
prediction accuracy.

No model retraining — read-only comparison only.

Usage (CLI):
    wt20-oracle accuracy
    wt20-oracle accuracy --last-n 5
    wt20-oracle accuracy --opponent australia

Usage (Python):
    from wt20_oracle.accuracy.auditor import run_accuracy_audit
    report = run_accuracy_audit()
"""

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
MATCHES_DIR = PROJECT_ROOT / "matches"


# ── Web search ────────────────────────────────────────────────────────────────

def _search(query: str, timeout: int = 12) -> Optional[str]:
    """DuckDuckGo HTML search; return stripped plain text or None."""
    try:
        params = urllib.parse.urlencode({"q": query, "kl": "us-en"})
        url = f"https://html.duckduckgo.com/html/?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        return text[:8000]
    except Exception:
        return None


# ── Result parsing ────────────────────────────────────────────────────────────

# Team name aliases for fuzzy matching
TEAM_ALIASES: dict[str, list[str]] = {
    "india": ["india", "ind", "indian"],
    "australia": ["australia", "aus", "australian"],
    "england": ["england", "eng", "english"],
    "south_africa": ["south africa", "sa", "proteas"],
    "new_zealand": ["new zealand", "nz", "new zealanders"],
    "west_indies": ["west indies", "wi", "windies"],
    "pakistan": ["pakistan", "pak"],
    "sri_lanka": ["sri lanka", "sl"],
    "bangladesh": ["bangladesh", "ban"],
    "ireland": ["ireland", "ire"],
    "scotland": ["scotland", "sco"],
    "zimbabwe": ["zimbabwe", "zim"],
}


def _normalise_team(name: str) -> Optional[str]:
    """Map a raw team name mention to a canonical team_id."""
    name_lower = name.lower().strip()
    for team_id, aliases in TEAM_ALIASES.items():
        if any(alias in name_lower for alias in aliases):
            return team_id
    return None


def _parse_match_result(snippet: str) -> Optional[dict]:
    """
    Try to extract a match result from a text snippet.
    Returns dict with keys: team_a, team_b, winner, score_a, score_b, date_str
    or None if parsing fails.
    """
    snippet_lower = snippet.lower()

    # Look for "X beat Y" / "X defeated Y" / "X won against Y"
    won_patterns = [
        r"([A-Za-z ]+?)\s+(?:beat|defeated|beat\s+back|won\s+against)\s+([A-Za-z ]+?)\s+(?:by|in)",
        r"([A-Za-z ]+?)\s+(?:beat|defeated)\s+([A-Za-z ]+?)\s+(?:to|by|\d)",
    ]

    winner = None
    loser = None
    for pat in won_patterns:
        m = re.search(pat, snippet, re.IGNORECASE)
        if m:
            w = _normalise_team(m.group(1))
            l = _normalise_team(m.group(2))
            if w and l and w != l:
                winner = w
                loser = l
                break

    if not winner:
        return None

    # Try to extract score (e.g. 145/6, 132 for 8)
    score_pat = r"(\d{2,3})(?:/(\d{1,2})|\s+for\s+(\d{1,2}))"
    scores = re.findall(score_pat, snippet)
    score_a = int(scores[0][0]) if scores else None
    score_b = int(scores[1][0]) if len(scores) > 1 else None

    # Try to extract date
    date_pat = r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s*(202\d)"
    dm = re.search(date_pat, snippet, re.IGNORECASE)
    date_str = None
    if dm:
        try:
            d = datetime.strptime(f"{dm.group(1)} {dm.group(2)} {dm.group(3)}", "%d %b %Y")
            date_str = d.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return {
        "winner": winner,
        "loser": loser,
        "score_winner": score_a,
        "score_loser": score_b,
        "date_str": date_str,
        "raw_snippet": snippet[:200],
    }


def fetch_recent_results(last_n: int = 10, opponent: Optional[str] = None) -> list[dict]:
    """
    Search for recent Women's T20 International results.
    Returns list of parsed result dicts.
    """
    results = []

    queries = [
        "India women T20 International result 2026 won lost",
        "Women T20I cricket result May 2026 India",
        "ICC women T20 international match result 2026",
    ]
    if opponent:
        queries.insert(0, f"India women vs {opponent} T20I result 2026")

    seen_snippets: set[str] = set()

    for query in queries:
        text = _search(query)
        if not text:
            continue

        # Split into sentence-like chunks and try to parse each
        chunks = re.split(r"[.!?]|\s{3,}", text)
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) < 30:
                continue
            if chunk in seen_snippets:
                continue
            seen_snippets.add(chunk)

            parsed = _parse_match_result(chunk)
            if parsed and parsed.get("winner"):
                # Filter for India-related matches
                if "india" in (parsed.get("winner", "") + parsed.get("loser", "")):
                    results.append(parsed)

        if len(results) >= last_n:
            break

    # Deduplicate by winner+loser+date
    seen: set[str] = set()
    deduped = []
    for r in results:
        key = f"{r['winner']}_{r['loser']}_{r.get('date_str', '')}"
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return deduped[:last_n]


# ── Prediction matching ───────────────────────────────────────────────────────

def _load_all_predictions() -> list[dict]:
    """Load all prediction.json files from matches/ directory."""
    predictions = []
    if not MATCHES_DIR.exists():
        return predictions

    for match_dir in MATCHES_DIR.iterdir():
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
            predictions.append({
                "match_id": match_dir.name,
                "team": pred.get("team") or meta.get("team_id"),
                "opponent": pred.get("opponent") or meta.get("opponent_id"),
                "date": pred.get("date") or meta.get("date", ""),
                "win_probability": pred.get("win_probability"),
                "batting_first_scenario": pred.get("batting_first_scenario"),
                "chasing_scenario": pred.get("chasing_scenario"),
                "runs_estimate": pred.get("runs_estimate", {}),
                "generated_at": pred.get("generated_at", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue

    return predictions


def _match_prediction_to_result(result: dict, predictions: list[dict]) -> Optional[dict]:
    """
    Find the best matching prediction for a scraped result.
    Matches on opponent + optionally date proximity.
    """
    winner = result.get("winner", "")
    loser = result.get("loser", "")
    result_date = result.get("date_str")

    # The result should involve india as winner or loser
    our_opponent = loser if winner == "india" else winner if loser == "india" else None
    if not our_opponent:
        return None

    candidates = [
        p for p in predictions
        if (p.get("opponent", "") == our_opponent or p.get("team", "") == our_opponent)
    ]

    if not candidates:
        return None

    # If we have a date, prefer predictions closest to the result date
    if result_date:
        def date_distance(p: dict) -> int:
            pd = p.get("date", "")
            if not pd or pd == "unknown":
                return 9999
            try:
                d1 = datetime.strptime(result_date, "%Y-%m-%d").date()
                d2 = datetime.strptime(pd, "%Y-%m-%d").date()
                return abs((d1 - d2).days)
            except ValueError:
                return 9999

        candidates.sort(key=date_distance)
        # Only match if within 5 days
        if date_distance(candidates[0]) > 5:
            return None

    return candidates[0]


# ── Accuracy computation ──────────────────────────────────────────────────────

def _compute_accuracy(result: dict, prediction: dict) -> dict:
    """
    Compute accuracy metrics for one matched result+prediction pair.

    Returns:
        winner_correct: bool
        win_prob_calibrated: bool (predicted prob was on correct side of 50%)
        win_prob_predicted: Optional[float]
        runs_delta: Optional[int]  (|predicted - actual| if scores available)
        actual_winner: str
        predicted_winner: str
    """
    actual_winner = result.get("winner", "")
    india_won = actual_winner == "india"

    # Determine predicted winner from win_probability
    win_prob = prediction.get("win_probability")
    # Also check dual scenario — use whichever scenario was blended
    if win_prob is None:
        bf = prediction.get("batting_first_scenario") or {}
        ch = prediction.get("chasing_scenario") or {}
        wp_bf = bf.get("win_probability")
        wp_ch = ch.get("win_probability")
        if wp_bf is not None and wp_ch is not None:
            win_prob = (wp_bf + wp_ch) / 2
        elif wp_bf is not None:
            win_prob = wp_bf
        elif wp_ch is not None:
            win_prob = wp_ch

    predicted_india_win = win_prob is not None and win_prob > 0.5
    winner_correct = (india_won == predicted_india_win)
    win_prob_calibrated = winner_correct  # simplified: correct side of 50%

    # Runs delta
    runs_delta = None
    score_winner = result.get("score_winner")
    runs_est = prediction.get("runs_estimate", {})
    pred_runs = runs_est.get("adjusted") or runs_est.get("base")
    if score_winner and pred_runs:
        runs_delta = abs(int(score_winner) - int(pred_runs))

    return {
        "winner_correct": winner_correct,
        "win_prob_calibrated": win_prob_calibrated,
        "win_prob_predicted": round(win_prob, 3) if win_prob is not None else None,
        "win_prob_label": f"{win_prob:.0%}" if win_prob is not None else "N/A",
        "runs_delta": runs_delta,
        "actual_winner": actual_winner,
        "predicted_winner": "india" if predicted_india_win else result.get("loser", "opponent"),
        "india_won_actual": india_won,
    }


# ── Main entry ────────────────────────────────────────────────────────────────

def run_accuracy_audit(
    last_n: int = 10,
    opponent: Optional[str] = None,
) -> dict:
    """
    Fetch recent WT20 Women's results, match against predictions, compute accuracy.

    Returns:
        audit_report dict with matched_results and summary stats
    """
    print("\nFetching recent Women's T20 International results...")
    results = fetch_recent_results(last_n=last_n, opponent=opponent)
    print(f"  Found {len(results)} result(s) from internet search.")

    print("Loading existing predictions from matches/...")
    predictions = _load_all_predictions()
    print(f"  Loaded {len(predictions)} prediction(s).")

    matched: list[dict] = []
    unmatched: list[dict] = []

    for result in results:
        pred = _match_prediction_to_result(result, predictions)
        if pred:
            accuracy = _compute_accuracy(result, pred)
            matched.append({
                "match_id": pred["match_id"],
                "opponent": result.get("loser") if result["winner"] == "india" else result.get("winner"),
                "date": result.get("date_str") or pred.get("date", "unknown"),
                "actual_winner": result["winner"],
                "predicted_winner": accuracy["predicted_winner"],
                "winner_correct": accuracy["winner_correct"],
                "win_probability_predicted": accuracy["win_prob_label"],
                "win_prob_calibrated": accuracy["win_prob_calibrated"],
                "runs_delta": accuracy["runs_delta"],
                "raw_result": result.get("raw_snippet", "")[:100],
            })
        else:
            unmatched.append(result)

    total_matched = len(matched)
    correct_winners = sum(1 for m in matched if m["winner_correct"])
    calibrated = sum(1 for m in matched if m["win_prob_calibrated"])
    avg_runs_delta = (
        sum(m["runs_delta"] for m in matched if m["runs_delta"] is not None)
        / max(1, sum(1 for m in matched if m["runs_delta"] is not None))
    ) if matched else None

    summary = {
        "total_results_found": len(results),
        "matched_to_predictions": total_matched,
        "unmatched": len(unmatched),
        "winner_accuracy": f"{correct_winners}/{total_matched}" if total_matched else "N/A",
        "winner_accuracy_pct": round(correct_winners / total_matched * 100, 1) if total_matched else None,
        "win_prob_calibration": f"{calibrated}/{total_matched}" if total_matched else "N/A",
        "avg_runs_delta": round(avg_runs_delta, 1) if avg_runs_delta is not None else None,
    }

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "matched_results": matched,
        "unmatched_results": unmatched,
        "summary": summary,
    }


def print_accuracy_report(report: dict) -> None:
    """Print a formatted accuracy audit report."""
    s = report["summary"]
    matched = report["matched_results"]

    print(f"\n{'═' * 70}")
    print("PREDICTION ACCURACY AUDIT  —  Women's T20 International Results")
    print(f"{'═' * 70}")
    print(f"Results found online:      {s['total_results_found']}")
    print(f"Matched to predictions:    {s['matched_to_predictions']}")
    print(f"Unmatched (no prediction): {s['unmatched']}")

    if not matched:
        print("\n  No matched predictions found.")
        print("  Either no prior predictions exist for recent matches,")
        print("  or the internet search did not return parseable results.")
        print(f"\n{'═' * 70}\n")
        return

    print(f"\n{'─' * 70}")
    print(f"  {'Match':<30} {'Actual':<15} {'Predicted':<15} {'Win%':<8} {'Correct'}")
    print(f"  {'─'*28} {'─'*13} {'─'*13} {'─'*6} {'─'*7}")
    for m in matched:
        opp = m.get("opponent", "?").replace("_", " ").title()
        actual = m["actual_winner"].replace("_", " ").title()
        predicted = m["predicted_winner"].replace("_", " ").title()
        wp = m["win_probability_predicted"]
        correct = "✓" if m["winner_correct"] else "✗"
        print(f"  {'India vs ' + opp:<30} {actual:<15} {predicted:<15} {wp:<8} {correct}")
        if m.get("runs_delta") is not None:
            print(f"    Runs delta: ±{m['runs_delta']} runs from prediction")

    print(f"\n{'─' * 70}")
    print(f"Winner prediction accuracy:   {s['winner_accuracy']}", end="")
    if s.get("winner_accuracy_pct") is not None:
        print(f"  ({s['winner_accuracy_pct']}%)", end="")
    print()
    print(f"Win prob. calibration:        {s['win_prob_calibration']}")
    if s.get("avg_runs_delta") is not None:
        print(f"Avg runs delta:               ±{s['avg_runs_delta']} runs")

    print(f"\n{'═' * 70}\n")
