"""
Unit Tests: ScenarioMetrics
============================

Tests TIER 1 decision node accuracy: scenario (50%), winner (30%), runs (20%).

The India vs SA April 27 match is used as the canonical failure case:
  - Predicted: India bats first, wins, 162 runs
  - Actual: India chases (SA bats first), SA wins, India 132 vs SA 155
  - Old component accuracy: 77.6% (misleading — squad/order correct but scenario wrong)
  - New weighted decision score: ~23% (honest failure signal)
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from testing.validation.scenario_metrics import ScenarioMetrics, get_assessment


# ---------------------------------------------------------------------------
# calculate_scenario_accuracy
# ---------------------------------------------------------------------------

class TestScenarioAccuracy:

    def test_correct_scenario_returns_true(self):
        assert ScenarioMetrics.calculate_scenario_accuracy("batting_first", "batting_first") is True

    def test_wrong_scenario_returns_false(self):
        assert ScenarioMetrics.calculate_scenario_accuracy("batting_first", "chasing") is False

    def test_unknown_scenario_returns_false(self):
        """Unknown counts as wrong — cannot get credit for not predicting."""
        assert ScenarioMetrics.calculate_scenario_accuracy("unknown", "chasing") is False

    def test_chasing_correct(self):
        assert ScenarioMetrics.calculate_scenario_accuracy("chasing", "chasing") is True

    def test_india_vs_sa_scenario_failure(self):
        """
        Critical failure: model predicted 'batting_first', actual was 'chasing'.
        This single error cascaded to wrong winner and wrong runs.
        """
        result = ScenarioMetrics.calculate_scenario_accuracy(
            predicted_scenario="batting_first",
            actual_scenario="chasing"
        )
        assert result is False


# ---------------------------------------------------------------------------
# calculate_winner_accuracy
# ---------------------------------------------------------------------------

class TestWinnerAccuracy:

    def test_correct_winner(self):
        correct, confidence = ScenarioMetrics.calculate_winner_accuracy("india", "india")
        assert correct is True
        assert confidence == 1.0

    def test_wrong_winner(self):
        correct, confidence = ScenarioMetrics.calculate_winner_accuracy("india", "sa")
        assert correct is False
        assert confidence == 0.0

    def test_india_vs_sa_winner_failure(self):
        """Predicted India wins, actual SA wins."""
        correct, confidence = ScenarioMetrics.calculate_winner_accuracy(
            predicted_winner="india",
            actual_winner="sa"
        )
        assert correct is False
        assert confidence == 0.0

    def test_returns_tuple(self):
        result = ScenarioMetrics.calculate_winner_accuracy("team1", "team1")
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# calculate_runs_accuracy
# ---------------------------------------------------------------------------

class TestRunsAccuracy:

    def test_perfect_prediction_zero_error(self):
        result = ScenarioMetrics.calculate_runs_accuracy(132, 132)
        assert result["error"] == 0
        assert result["abs_error"] == 0
        assert result["within_target_margin"] is True

    def test_within_margin_returns_true(self):
        result = ScenarioMetrics.calculate_runs_accuracy(135, 132, target_margin=10)
        assert result["within_target_margin"] is True

    def test_outside_margin_returns_false(self):
        result = ScenarioMetrics.calculate_runs_accuracy(145, 132, target_margin=10)
        assert result["within_target_margin"] is False

    def test_error_sign_correct(self):
        """Actual > predicted → positive error."""
        result = ScenarioMetrics.calculate_runs_accuracy(120, 132)
        assert result["error"] == 12

    def test_india_vs_sa_runs_error(self):
        """
        Old model predicted 162, actual 132 → 30-run error (23% off).
        New adjusted prediction (142) → 10-run error (7.6% off, within ±10).
        """
        old_result = ScenarioMetrics.calculate_runs_accuracy(162, 132, target_margin=10)
        new_result = ScenarioMetrics.calculate_runs_accuracy(142, 132, target_margin=10)

        assert old_result["abs_error"] == 30
        assert old_result["within_target_margin"] is False

        assert new_result["abs_error"] == 10
        assert new_result["within_target_margin"] is True

    def test_high_magnitude_for_large_error(self):
        result = ScenarioMetrics.calculate_runs_accuracy(100, 132)
        assert result["magnitude"] == "high"

    def test_medium_magnitude(self):
        # abs_error = 11 (> 10) → medium
        result = ScenarioMetrics.calculate_runs_accuracy(121, 132)
        assert result["magnitude"] == "medium"

    def test_low_magnitude_for_small_error(self):
        result = ScenarioMetrics.calculate_runs_accuracy(130, 132)
        assert result["magnitude"] == "low"

    def test_accuracy_score_is_0_to_100(self):
        result = ScenarioMetrics.calculate_runs_accuracy(100, 132)
        assert 0 <= result["accuracy_score"] <= 100

    def test_perfect_prediction_score_100(self):
        result = ScenarioMetrics.calculate_runs_accuracy(132, 132)
        assert result["accuracy_score"] == pytest.approx(100.0)

    def test_result_has_all_fields(self):
        result = ScenarioMetrics.calculate_runs_accuracy(162, 132)
        required_fields = [
            "predicted_runs", "actual_runs", "error", "abs_error",
            "pct_error", "within_target_margin", "target_margin",
            "accuracy_score", "magnitude"
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# calculate_weighted_decision_score
# ---------------------------------------------------------------------------

class TestWeightedDecisionScore:

    def test_all_correct_returns_100(self):
        result = ScenarioMetrics.calculate_weighted_decision_score(
            scenario_correct=True,
            winner_correct=True,
            runs_accuracy_pct=100.0
        )
        assert result["weighted_decision_score"] == pytest.approx(100.0)

    def test_all_wrong_returns_0(self):
        result = ScenarioMetrics.calculate_weighted_decision_score(
            scenario_correct=False,
            winner_correct=False,
            runs_accuracy_pct=0.0
        )
        assert result["weighted_decision_score"] == pytest.approx(0.0)

    def test_india_vs_sa_old_framework_score(self):
        """
        India vs SA with old model:
        - Scenario: wrong (0%)
        - Winner: wrong (0%)
        - Runs accuracy: ~77.3% (162 vs 132 = 23% off → score 77%)
        Expected weighted: 0*0.5 + 0*0.3 + 77.3*0.2 = ~15.5%
        """
        runs_result = ScenarioMetrics.calculate_runs_accuracy(162, 132)
        result = ScenarioMetrics.calculate_weighted_decision_score(
            scenario_correct=False,
            winner_correct=False,
            runs_accuracy_pct=runs_result["accuracy_score"]
        )
        # Should be approximately 15% — "FAILING" assessment
        assert result["weighted_decision_score"] < 20
        assert result["overall_assessment"] in ("FAILING", "POOR")

    def test_india_vs_sa_new_framework_score(self):
        """
        India vs SA with new scenario-aware model:
        - Scenario: correct (100%)
        - Winner: correct (100%)
        - Runs accuracy: ~92% (142 predicted vs 132 actual = 7.6% off)
        Expected weighted: 100*0.5 + 100*0.3 + 92*0.2 = 98.4%
        """
        runs_result = ScenarioMetrics.calculate_runs_accuracy(142, 132)
        result = ScenarioMetrics.calculate_weighted_decision_score(
            scenario_correct=True,
            winner_correct=True,
            runs_accuracy_pct=runs_result["accuracy_score"]
        )
        assert result["weighted_decision_score"] > 85
        assert result["overall_assessment"] in ("EXCELLENT", "GOOD")

    def test_default_weights_sum_to_one(self):
        result = ScenarioMetrics.calculate_weighted_decision_score(
            scenario_correct=True, winner_correct=True, runs_accuracy_pct=100.0
        )
        total = result["scenario_weight"] + result["winner_weight"] + result["runs_weight"]
        assert total == pytest.approx(1.0)

    def test_scenario_has_highest_weight(self):
        result = ScenarioMetrics.calculate_weighted_decision_score(
            scenario_correct=True, winner_correct=True, runs_accuracy_pct=100.0
        )
        assert result["scenario_weight"] > result["winner_weight"]
        assert result["scenario_weight"] > result["runs_weight"]

    def test_winner_has_second_highest_weight(self):
        result = ScenarioMetrics.calculate_weighted_decision_score(
            scenario_correct=True, winner_correct=True, runs_accuracy_pct=100.0
        )
        assert result["winner_weight"] > result["runs_weight"]

    def test_custom_weights_applied(self):
        result = ScenarioMetrics.calculate_weighted_decision_score(
            scenario_correct=True,
            winner_correct=False,
            runs_accuracy_pct=0.0,
            scenario_weight=1.0,
            winner_weight=0.0,
            runs_weight=0.0
        )
        assert result["weighted_decision_score"] == pytest.approx(100.0)

    def test_only_scenario_wrong_large_penalty(self):
        """Getting scenario wrong (50% weight) should heavily penalise score."""
        result = ScenarioMetrics.calculate_weighted_decision_score(
            scenario_correct=False,
            winner_correct=True,
            runs_accuracy_pct=100.0
        )
        # score = 0*0.5 + 100*0.3 + 100*0.2 = 50
        assert result["weighted_decision_score"] == pytest.approx(50.0)

    def test_result_has_all_fields(self):
        result = ScenarioMetrics.calculate_weighted_decision_score(
            scenario_correct=True, winner_correct=True, runs_accuracy_pct=90.0
        )
        required = [
            "scenario_score", "scenario_weight",
            "winner_score", "winner_weight",
            "runs_score", "runs_weight",
            "weighted_decision_score", "overall_assessment"
        ]
        for field in required:
            assert field in result, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# compare_old_vs_new_accuracy
# ---------------------------------------------------------------------------

class TestCompareOldVsNew:

    def test_improvement_calculated(self):
        result = ScenarioMetrics.compare_old_vs_new_accuracy(15.5, 85.0)
        assert result["improvement"] == pytest.approx(69.5)

    def test_improvement_pct_calculated(self):
        result = ScenarioMetrics.compare_old_vs_new_accuracy(20.0, 80.0)
        assert result["improvement_pct"] == pytest.approx(300.0)

    def test_methodology_description_present(self):
        result = ScenarioMetrics.compare_old_vs_new_accuracy(15.5, 85.0)
        assert "methodology_change" in result
        assert "50%" in result["methodology_change"]

    def test_why_changed_present(self):
        result = ScenarioMetrics.compare_old_vs_new_accuracy(15.5, 85.0)
        assert "why_changed" in result

    def test_india_vs_sa_full_comparison(self):
        """
        Before: 15.5% decision score (scenario wrong, winner wrong, runs off by 30)
        After:  ~98% decision score (scenario right, winner right, runs within ±10)
        """
        result = ScenarioMetrics.compare_old_vs_new_accuracy(15.5, 98.0)
        assert result["old_score"] == 15.5
        assert result["new_score"] == 98.0
        assert result["improvement"] > 80


# ---------------------------------------------------------------------------
# get_assessment (module-level function)
# ---------------------------------------------------------------------------

class TestGetAssessment:

    def test_above_80_is_excellent(self):
        assert get_assessment(85) == "EXCELLENT"

    def test_exactly_80_is_excellent(self):
        assert get_assessment(80) == "EXCELLENT"

    def test_65_to_79_is_good(self):
        assert get_assessment(70) == "GOOD"

    def test_exactly_65_is_good(self):
        assert get_assessment(65) == "GOOD"

    def test_50_to_64_is_fair(self):
        assert get_assessment(55) == "FAIR"

    def test_30_to_49_is_poor(self):
        assert get_assessment(40) == "POOR"

    def test_below_30_is_failing(self):
        assert get_assessment(20) == "FAILING"

    def test_zero_is_failing(self):
        assert get_assessment(0) == "FAILING"

    def test_100_is_excellent(self):
        assert get_assessment(100) == "EXCELLENT"

    def test_india_vs_sa_old_score_is_failing(self):
        """~15% score → FAILING assessment."""
        assert get_assessment(15.5) == "FAILING"

    def test_india_vs_sa_new_score_is_excellent(self):
        """~98% score → EXCELLENT assessment."""
        assert get_assessment(98.0) == "EXCELLENT"
