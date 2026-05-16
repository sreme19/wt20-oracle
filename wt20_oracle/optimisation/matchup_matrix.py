"""
Matchup Matrix
==============

Looks up batter-vs-bowler head-to-head records and computes matchup scores.
Used by SquadSelector, BowlingPlan, and StrategyNode.
"""

from typing import Any, Dict, List, Optional


def get_matchup_score(
    matchups: Dict[str, Any],
    batter_id: str,
    bowler_id: str,
    from_batter_perspective: bool = True,
) -> Optional[float]:
    """
    Return a 0-100 matchup score.

    from_batter_perspective=True  → higher = better for batter
    from_batter_perspective=False → higher = better for bowler
    """
    key = f"{batter_id}::{bowler_id}"
    record = matchups.get(key)

    if not record:
        return None

    balls = record.get("balls_faced", 0)
    if balls < 6:
        return None  # Too few balls — unreliable

    sr = record.get("strike_rate", 100.0)
    dot_pct = record.get("dot_ball_pct", 40.0)
    dismissals = record.get("dismissals", 0)
    dismissal_rate = dismissals / balls

    if from_batter_perspective:
        score = (sr / 150) * 50 + (1 - dot_pct / 100) * 30 + (1 - dismissal_rate * 30) * 20
    else:
        score = (1 - sr / 150) * 50 + (dot_pct / 100) * 30 + (dismissal_rate * 30) * 20

    return max(0.0, min(100.0, score))


def find_favourable_matchups(
    matchups: Dict[str, Any],
    our_batters: List[str],
    opponent_bowlers: List[str],
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """Find top-N most favourable batter-vs-bowler matchups for our team."""
    scored = []
    for batter in our_batters:
        for bowler in opponent_bowlers:
            score = get_matchup_score(matchups, batter, bowler, from_batter_perspective=True)
            if score is not None:
                record = matchups[f"{batter}::{bowler}"]
                scored.append({
                    "batter": batter,
                    "bowler": bowler,
                    "score": score,
                    "strike_rate": record.get("strike_rate"),
                    "balls_faced": record.get("balls_faced"),
                    "insight": _matchup_insight(score, record),
                })
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_n]


def find_dangerous_matchups(
    matchups: Dict[str, Any],
    opponent_batters: List[str],
    our_bowlers: List[str],
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """Find matchups where opponent batter has edge over our bowlers."""
    scored = []
    for batter in opponent_batters:
        for bowler in our_bowlers:
            score = get_matchup_score(matchups, batter, bowler, from_batter_perspective=True)
            if score is not None:
                record = matchups[f"{batter}::{bowler}"]
                scored.append({
                    "opponent_batter": batter,
                    "our_bowler": bowler,
                    "score": score,
                    "strike_rate": record.get("strike_rate"),
                    "insight": f"Threat: batter SR {record.get('strike_rate', '?'):.0f} against this bowler",
                })
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_n]


def _matchup_insight(score: float, record: Dict[str, Any]) -> str:
    sr = record.get("strike_rate", 0)
    balls = record.get("balls_faced", 0)
    dismissals = record.get("dismissals", 0)
    if score >= 70:
        return f"Strong: SR {sr:.0f} over {balls} balls, {dismissals} dismissal(s)"
    elif score >= 50:
        return f"Favourable: SR {sr:.0f} over {balls} balls"
    elif score >= 30:
        return f"Even: SR {sr:.0f} over {balls} balls, {dismissals} dismissal(s)"
    else:
        return f"Caution: bowler has edge, SR only {sr:.0f} over {balls} balls"
