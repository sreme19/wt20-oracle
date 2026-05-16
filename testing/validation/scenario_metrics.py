"""
Scenario-Aware Metrics Module
=============================

Implements TIER 1 decision node metrics:
- Scenario Correctness (Batting First vs Chasing)
- Winner Prediction Accuracy
- Runs Prediction Accuracy

Supersedes overall accuracy in importance.
"""

from typing import Dict, Tuple


class ScenarioMetrics:
    """Calculate scenario-aware accuracy metrics."""

    @staticmethod
    def calculate_scenario_accuracy(
        predicted_scenario: str,
        actual_scenario: str
    ) -> bool:
        """Calculate if scenario was correctly predicted.

        Args:
            predicted_scenario: "batting_first" or "chasing" or "unknown"
            actual_scenario: "batting_first" or "chasing"

        Returns:
            True if predicted scenario matches actual
        """
        if predicted_scenario == "unknown":
            return False  # Unknown counts as wrong

        return predicted_scenario == actual_scenario

    @staticmethod
    def calculate_winner_accuracy(
        predicted_winner: str,
        actual_winner: str
    ) -> Tuple[bool, float]:
        """Calculate winner prediction accuracy.

        Args:
            predicted_winner: Predicted winner ("team1", "team2", "unknown")
            actual_winner: Actual winner ("team1", "team2")

        Returns:
            Tuple of (correct: bool, confidence_score: float)
        """
        correct = predicted_winner == actual_winner
        confidence_score = 1.0 if correct else 0.0

        return correct, confidence_score

    @staticmethod
    def calculate_runs_accuracy(
        predicted_runs: float,
        actual_runs: float,
        target_margin: float = 10.0
    ) -> Dict[str, any]:
        """Calculate runs prediction accuracy.

        Args:
            predicted_runs: Predicted runs
            actual_runs: Actual runs
            target_margin: Target margin for "within range" (default ±10 runs)

        Returns:
            Dict with accuracy metrics
        """
        error = actual_runs - predicted_runs
        abs_error = abs(error)
        pct_error = (abs_error / actual_runs * 100) if actual_runs > 0 else 0

        within_margin = abs_error <= target_margin
        margin_pct = (abs_error / actual_runs * 100) if actual_runs > 0 else 0

        return {
            "predicted_runs": predicted_runs,
            "actual_runs": actual_runs,
            "error": error,
            "abs_error": abs_error,
            "pct_error": pct_error,
            "within_target_margin": within_margin,
            "target_margin": target_margin,
            "accuracy_score": max(0, 100 - pct_error),  # 0-100 scale
            "magnitude": "high" if abs_error > 20 else "medium" if abs_error > 10 else "low"
        }

    @staticmethod
    def calculate_weighted_decision_score(
        scenario_correct: bool,
        winner_correct: bool,
        runs_accuracy_pct: float,
        scenario_weight: float = 0.50,
        winner_weight: float = 0.30,
        runs_weight: float = 0.20
    ) -> Dict[str, any]:
        """Calculate weighted score for key decision nodes.

        Args:
            scenario_correct: Whether scenario was predicted correctly
            winner_correct: Whether winner was predicted correctly
            runs_accuracy_pct: Runs prediction accuracy (0-100)
            scenario_weight: Weight for scenario (default 50%)
            winner_weight: Weight for winner (default 30%)
            runs_weight: Weight for runs (default 20%)

        Returns:
            Dict with weighted score
        """
        # Convert booleans to scores
        scenario_score = 100 if scenario_correct else 0
        winner_score = 100 if winner_correct else 0

        # Weighted average
        total_weight = scenario_weight + winner_weight + runs_weight
        weighted_score = (
            scenario_score * scenario_weight +
            winner_score * winner_weight +
            runs_accuracy_pct * runs_weight
        ) / total_weight

        return {
            "scenario_score": scenario_score,
            "scenario_weight": scenario_weight,
            "winner_score": winner_score,
            "winner_weight": winner_weight,
            "runs_score": runs_accuracy_pct,
            "runs_weight": runs_weight,
            "weighted_decision_score": weighted_score,
            "overall_assessment": get_assessment(weighted_score)
        }

    @staticmethod
    def compare_old_vs_new_accuracy(
        old_scenario_aware_score: float,
        new_scenario_aware_score: float
    ) -> Dict[str, any]:
        """Compare old vs new scoring methodology.

        Args:
            old_scenario_aware_score: Old methodology score
            new_scenario_aware_score: New methodology score

        Returns:
            Comparison dict
        """
        improvement = new_scenario_aware_score - old_scenario_aware_score

        return {
            "old_score": old_scenario_aware_score,
            "new_score": new_scenario_aware_score,
            "improvement": improvement,
            "improvement_pct": (improvement / old_scenario_aware_score * 100) if old_scenario_aware_score > 0 else 0,
            "methodology_change": "Now weights scenario (50%) + winner (30%) + runs (20%)",
            "why_changed": "Component accuracy (squad, order) irrelevant if scenario is wrong"
        }


def get_assessment(score: float) -> str:
    """Get assessment label for score.

    Args:
        score: Score 0-100

    Returns:
        Assessment string
    """
    if score >= 80:
        return "EXCELLENT"
    elif score >= 65:
        return "GOOD"
    elif score >= 50:
        return "FAIR"
    elif score >= 30:
        return "POOR"
    else:
        return "FAILING"


# Example usage
if __name__ == "__main__":
    metrics = ScenarioMetrics()

    # Example: India vs SA April 27
    print("SCENARIO-AWARE METRICS EXAMPLE")
    print("=" * 70)

    # Scenario
    print("\n1. SCENARIO PREDICTION:")
    scenario_correct = metrics.calculate_scenario_accuracy(
        predicted_scenario="batting_first",  # Wrong!
        actual_scenario="chasing"
    )
    print(f"   Predicted: Batting first")
    print(f"   Actual: Chasing")
    print(f"   Correct: {scenario_correct}")

    # Winner
    print("\n2. WINNER PREDICTION:")
    winner_correct, confidence = metrics.calculate_winner_accuracy(
        predicted_winner="team1",  # India
        actual_winner="team2"  # SA
    )
    print(f"   Predicted: India")
    print(f"   Actual: South Africa")
    print(f"   Correct: {winner_correct} (Confidence: {confidence:.0%})")

    # Runs
    print("\n3. RUNS PREDICTION:")
    runs_result = metrics.calculate_runs_accuracy(
        predicted_runs=162,
        actual_runs=132,
        target_margin=10
    )
    print(f"   Predicted: {runs_result['predicted_runs']:.0f} runs")
    print(f"   Actual: {runs_result['actual_runs']:.0f} runs")
    print(f"   Error: {runs_result['error']:.0f} runs ({runs_result['pct_error']:.1f}%)")
    print(f"   Within ±10: {runs_result['within_target_margin']}")
    print(f"   Accuracy: {runs_result['accuracy_score']:.1f}%")

    # Weighted decision score
    print("\n4. WEIGHTED DECISION SCORE:")
    decision_score = metrics.calculate_weighted_decision_score(
        scenario_correct=False,
        winner_correct=False,
        runs_accuracy_pct=runs_result['accuracy_score'],
        scenario_weight=0.50,
        winner_weight=0.30,
        runs_weight=0.20
    )
    print(f"   Scenario: {decision_score['scenario_score']:.0f}% (weight {decision_score['scenario_weight']:.0%})")
    print(f"   Winner: {decision_score['winner_score']:.0f}% (weight {decision_score['winner_weight']:.0%})")
    print(f"   Runs: {decision_score['runs_score']:.0f}% (weight {decision_score['runs_weight']:.0%})")
    print(f"   Weighted Score: {decision_score['weighted_decision_score']:.1f}%")
    print(f"   Assessment: {decision_score['overall_assessment']}")

    print("\n" + "=" * 70)
    print("CONCLUSION: Prediction failed on TIER 1 decision nodes")
    print("           Component accuracy (squad, order) irrelevant when scenario is wrong")
