"""
Monte Carlo Win Probability
============================

Estimates win probability via vectorised NumPy simulation.
Called BEFORE the ScenarioHandler applies scenario adjustments —
the pipeline then calls ScenarioHandler.adjust_win_probability()
on the raw Monte Carlo output.

Key inputs:
  - our_batting_strength: composite score 0-1 (SR-based)
  - opponent_bowling_strength: composite score 0-1 (economy-based)
  - venue_factor: 0-1 (batting-friendly = high)
  - n_simulations: default 10,000
"""

import numpy as np
from typing import Dict, Any, Optional


def estimate_first_innings_score(
    batting_strength: float,
    bowling_strength: float,
    venue_factor: float,
    base_score: float = 152.0,
    n_simulations: int = 10_000,
    rng_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Simulate first-innings score distribution.

    Args:
        batting_strength: 0-1, higher = stronger batting lineup
        bowling_strength: 0-1, higher = stronger opponent bowling (suppresses runs)
        venue_factor: 0-1, higher = more batting-friendly
        base_score: Historical average first innings score for venue
        n_simulations: Number of Monte Carlo iterations
        rng_seed: Optional seed for reproducibility

    Returns:
        Dict with mean, std, p10, p25, p50, p75, p90, confidence
    """
    rng = np.random.default_rng(rng_seed)

    # Net run multiplier: batting benefit minus bowling suppression
    net_factor = 1.0 + (batting_strength - 0.5) * 0.3 - (bowling_strength - 0.5) * 0.2 + (venue_factor - 0.5) * 0.15
    expected_score = base_score * net_factor

    # Variance reflects uncertainty — wider at lower data quality
    std_dev = expected_score * 0.10  # ±10% of expected as 1-sigma

    scores = rng.normal(loc=expected_score, scale=std_dev, size=n_simulations)
    scores = np.clip(scores, 80, 220)  # T20 realistic bounds

    return {
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "p10": float(np.percentile(scores, 10)),
        "p25": float(np.percentile(scores, 25)),
        "p50": float(np.percentile(scores, 50)),
        "p75": float(np.percentile(scores, 75)),
        "p90": float(np.percentile(scores, 90)),
        "n_simulations": n_simulations,
        "confidence": _confidence_label(batting_strength, bowling_strength),
    }


def estimate_win_probability(
    our_batting_strength: float,
    opponent_batting_strength: float,
    our_bowling_strength: float,
    opponent_bowling_strength: float,
    venue_factor: float,
    n_simulations: int = 10_000,
    rng_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Simulate head-to-head win probability (pre-scenario adjustment).

    Returns raw probability before ScenarioHandler applies chase penalty.

    Args:
        our_batting_strength: 0-1
        opponent_batting_strength: 0-1
        our_bowling_strength: 0-1 (higher = we restrict them better)
        opponent_bowling_strength: 0-1 (higher = they restrict us)
        venue_factor: 0-1 (batting-friendly = high)
        n_simulations: Monte Carlo iterations
        rng_seed: Optional reproducibility seed

    Returns:
        Dict with win_probability, our_avg_score, their_avg_score, margin_distribution
    """
    rng = np.random.default_rng(rng_seed)
    base = 152.0

    # Our innings
    our_factor = 1.0 + (our_batting_strength - 0.5) * 0.3 - (opponent_bowling_strength - 0.5) * 0.2 + (venue_factor - 0.5) * 0.1
    our_scores = rng.normal(loc=base * our_factor, scale=base * 0.10, size=n_simulations)
    our_scores = np.clip(our_scores, 70, 230)

    # Opponent innings
    their_factor = 1.0 + (opponent_batting_strength - 0.5) * 0.3 - (our_bowling_strength - 0.5) * 0.2 + (venue_factor - 0.5) * 0.1
    their_scores = rng.normal(loc=base * their_factor, scale=base * 0.10, size=n_simulations)
    their_scores = np.clip(their_scores, 70, 230)

    wins = np.sum(our_scores > their_scores)
    win_prob = float(wins / n_simulations)

    margins = our_scores - their_scores

    return {
        "win_probability": win_prob,
        "our_avg_score": float(np.mean(our_scores)),
        "their_avg_score": float(np.mean(their_scores)),
        "avg_margin": float(np.mean(margins)),
        "p10_margin": float(np.percentile(margins, 10)),
        "p90_margin": float(np.percentile(margins, 90)),
        "n_simulations": n_simulations,
        "confidence": _confidence_label(our_batting_strength, opponent_bowling_strength),
    }


def squad_batting_strength(squad: list, analyst_insights: dict = None, team_id: str = "") -> float:
    """
    Derive a 0-1 batting strength score from squad data.

    Uses average strike rate relative to baseline (120 SR = 0.5).
    """
    if not squad:
        return 0.5

    strike_rates = []
    for player in squad:
        stats = player.get("t20i_stats", {}).get("batting") or {}
        sr = stats.get("strike_rate")
        if sr and sr > 0:
            strike_rates.append(sr)

    if not strike_rates:
        return 0.5

    avg_sr = sum(strike_rates) / len(strike_rates)
    # Normalise: SR 120 → 0.5, SR 140 → ~0.67, SR 100 → ~0.33
    strength = min(1.0, max(0.0, (avg_sr - 80) / 100))

    # Apply form modifier from analyst insights
    if analyst_insights and team_id:
        from wt20_oracle.io.analyst_loader import form_modifier_from_insights, load_analyst_insights
        team_insights = analyst_insights.get(team_id, {})
        modifiers = []
        for player in squad[:6]:  # Top-order matters most
            pid = player.get("id", "")
            insight = team_insights.get(pid)
            if insight:
                modifiers.append(form_modifier_from_insights(insight))
        if modifiers:
            avg_mod = sum(modifiers) / len(modifiers)
            strength = min(1.0, strength * avg_mod)

    return round(strength, 3)


def squad_bowling_strength(squad: list) -> float:
    """
    Derive a 0-1 bowling strength (run-suppression) score.

    Uses average economy relative to baseline (7.5 econ = 0.5).
    Lower economy = stronger bowling.
    """
    if not squad:
        return 0.5

    economies = []
    for player in squad:
        stats = player.get("t20i_stats", {}).get("bowling") or {}
        economy = stats.get("economy")
        innings = stats.get("innings", 0) or 0
        if economy and economy > 0 and innings >= 5:
            economies.append(economy)

    if not economies:
        return 0.5

    avg_econ = sum(economies) / len(economies)
    # Normalise: econ 7.5 → 0.5, econ 6.0 → 0.75, econ 9.0 → 0.25
    strength = min(1.0, max(0.0, (9.5 - avg_econ) / 5.0))
    return round(strength, 3)


def _confidence_label(batting: float, bowling: float) -> str:
    avg = (batting + bowling) / 2
    if avg >= 0.6:
        return "high"
    elif avg >= 0.4:
        return "medium"
    else:
        return "low"
