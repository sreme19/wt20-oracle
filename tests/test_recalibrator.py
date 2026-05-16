"""
Unit Tests: ModelRecalibrator
==============================

Tests guard rails, parameter validation, improvement thresholds,
deployment decisions, and audit trail generation.

Guard Rails under test:
  - Drift guard: ±15% from baseline max
  - Improvement threshold: min 3% required to deploy
  - Cycle limit: max 5 parameters per cycle
  - Rollback trigger: >5% regression blocks deployment
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from testing.validation.recalibrator import ModelRecalibrator, RecalibrationAction, RecalibrationResult


# ---------------------------------------------------------------------------
# Guard Rail: validate_parameter_change
# ---------------------------------------------------------------------------

class TestParameterValidation:

    def setup_method(self):
        self.baseline = {
            "chase_penalty": -20,
            "form_modifier": 1.08,
            "pace_friendly_willowmoore": 8.0
        }
        self.recalibrator = ModelRecalibrator(model_baseline=self.baseline)

    def test_within_drift_is_valid(self):
        result = self.recalibrator.validate_parameter_change(
            "chase_penalty", old_value=-20, new_value=-22
        )
        assert result["valid"] is True

    def test_exceeds_drift_is_invalid(self):
        """Changing chase_penalty from -20 to -24 = 20% drift → blocked."""
        result = self.recalibrator.validate_parameter_change(
            "chase_penalty", old_value=-20, new_value=-24
        )
        assert result["valid"] is False
        assert "Drift" in result["reason"]

    def test_exact_boundary_15pct_is_valid(self):
        """Exactly 15% drift → should pass (guard is strictly >)."""
        result = self.recalibrator.validate_parameter_change(
            "chase_penalty", old_value=-20, new_value=-23
        )
        assert result["valid"] is True

    def test_parameter_not_in_baseline_always_valid(self):
        """New parameter with no baseline → cannot check drift → valid."""
        result = self.recalibrator.validate_parameter_change(
            "new_param", old_value=1.0, new_value=2.0
        )
        assert result["valid"] is True

    def test_willowmoore_recalibration_from_80_to_65(self):
        """
        Willowmoore: 8.0 (original, wrong) → 6.5 (corrected).
        Change: 18.75% drift from baseline 8.0 → BLOCKED by guard rail.
        Should trigger alert to split across cycles.
        """
        result = self.recalibrator.validate_parameter_change(
            "pace_friendly_willowmoore", old_value=8.0, new_value=6.5
        )
        assert result["valid"] is False
        assert "recommendation" in result

    def test_valid_change_returns_reason(self):
        result = self.recalibrator.validate_parameter_change(
            "form_modifier", old_value=1.08, new_value=1.10
        )
        assert "reason" in result
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Guard Rail: check_recalibration_cycle (max 5 params)
# ---------------------------------------------------------------------------

class TestRecalibrationCycle:

    def setup_method(self):
        self.recalibrator = ModelRecalibrator()

    def _make_actions(self, n):
        return [{"param": f"param_{i}", "old": 1.0, "new": 1.1} for i in range(n)]

    def test_one_param_is_valid(self):
        result = self.recalibrator.check_recalibration_cycle(self._make_actions(1))
        assert result["valid"] is True

    def test_five_params_is_valid(self):
        result = self.recalibrator.check_recalibration_cycle(self._make_actions(5))
        assert result["valid"] is True

    def test_six_params_is_invalid(self):
        result = self.recalibrator.check_recalibration_cycle(self._make_actions(6))
        assert result["valid"] is False
        assert "Too many parameters" in result["reason"]

    def test_ten_params_is_invalid(self):
        result = self.recalibrator.check_recalibration_cycle(self._make_actions(10))
        assert result["valid"] is False

    def test_invalid_cycle_has_recommendation(self):
        result = self.recalibrator.check_recalibration_cycle(self._make_actions(6))
        assert "recommendation" in result

    def test_count_shown_in_reason(self):
        result = self.recalibrator.check_recalibration_cycle(self._make_actions(3))
        assert "3" in result["reason"]


# ---------------------------------------------------------------------------
# record_recalibration
# ---------------------------------------------------------------------------

class TestRecordRecalibration:

    def setup_method(self):
        self.recalibrator = ModelRecalibrator()

    def test_action_is_recorded(self):
        self.recalibrator.record_recalibration("chase_penalty", -20, -25, "Increased for difficult pitch")
        assert len(self.recalibrator.recalibration_history) == 1

    def test_action_stores_correct_values(self):
        self.recalibrator.record_recalibration("chase_penalty", -20, -25, "Test reason")
        action = self.recalibrator.recalibration_history[0]
        assert action.parameter_name == "chase_penalty"
        assert action.old_value == -20
        assert action.new_value == -25
        assert action.reason == "Test reason"

    def test_multiple_actions_all_stored(self):
        self.recalibrator.record_recalibration("param_a", 1, 2, "reason a")
        self.recalibrator.record_recalibration("param_b", 3, 4, "reason b")
        assert len(self.recalibrator.recalibration_history) == 2

    def test_action_has_timestamp(self):
        self.recalibrator.record_recalibration("chase_penalty", -20, -25, "Test")
        action = self.recalibrator.recalibration_history[0]
        assert action.timestamp is not None
        assert len(action.timestamp) > 10


# ---------------------------------------------------------------------------
# validate_improvement (improvement threshold guard)
# ---------------------------------------------------------------------------

class TestValidateImprovement:

    def setup_method(self):
        self.recalibrator = ModelRecalibrator()

    def test_large_improvement_passes(self):
        result = self.recalibrator.validate_improvement("winner_accuracy", 0.0, 0.85)
        assert result.passed_validation is True

    def test_improvement_below_threshold_fails(self):
        """Improvement of 2% < 3% threshold → fails."""
        result = self.recalibrator.validate_improvement("winner_accuracy", 0.80, 0.82)
        assert result.passed_validation is False

    def test_exact_threshold_passes(self):
        """Improvement of 3.1% (clear of float precision) → passes."""
        result = self.recalibrator.validate_improvement("winner_accuracy", 0.80, 0.831)
        assert result.passed_validation is True

    def test_no_improvement_fails(self):
        result = self.recalibrator.validate_improvement("winner_accuracy", 0.70, 0.70)
        assert result.passed_validation is False

    def test_regression_fails(self):
        result = self.recalibrator.validate_improvement("winner_accuracy", 0.80, 0.75)
        assert result.passed_validation is False

    def test_small_regression_allowed_when_flag_set(self):
        """allow_small_regression=True allows up to 1% degradation."""
        result = self.recalibrator.validate_improvement(
            "winner_accuracy", 0.80, 0.795, allow_small_regression=True
        )
        assert result.passed_validation is True

    def test_large_regression_blocked_even_with_flag(self):
        result = self.recalibrator.validate_improvement(
            "winner_accuracy", 0.80, 0.70, allow_small_regression=True
        )
        assert result.passed_validation is False

    def test_improvement_calculated_correctly(self):
        result = self.recalibrator.validate_improvement("winner_accuracy", 0.60, 0.80)
        assert result.improvement == pytest.approx(0.20)

    def test_result_stored_in_history(self):
        self.recalibrator.validate_improvement("winner_accuracy", 0.60, 0.80)
        assert len(self.recalibrator.validation_results) == 1

    def test_india_vs_sa_recalibration_improvement(self):
        """
        Post India vs SA recalibration:
        winner_accuracy 0.0 → 0.85 (scenario-aware framework).
        """
        result = self.recalibrator.validate_improvement("winner_accuracy", 0.0, 0.85)
        assert result.passed_validation is True
        assert result.improvement == pytest.approx(0.85)


# ---------------------------------------------------------------------------
# should_deploy
# ---------------------------------------------------------------------------

class TestShouldDeploy:

    def setup_method(self):
        self.recalibrator = ModelRecalibrator()

    def _add_passing_primary_metrics(self):
        self.recalibrator.validate_improvement("winner_accuracy", 0.50, 0.85)
        self.recalibrator.validate_improvement("runs_prediction_mae", 0.70, 0.90)

    def test_no_results_blocks_deploy(self):
        assert self.recalibrator.should_deploy() is False

    def test_all_primary_pass_allows_deploy(self):
        self._add_passing_primary_metrics()
        assert self.recalibrator.should_deploy() is True

    def test_winner_accuracy_fail_blocks_deploy(self):
        self.recalibrator.validate_improvement("winner_accuracy", 0.80, 0.81)  # <3% → fail
        self.recalibrator.validate_improvement("runs_prediction_mae", 0.70, 0.90)
        assert self.recalibrator.should_deploy() is False

    def test_runs_mae_fail_blocks_deploy(self):
        self.recalibrator.validate_improvement("winner_accuracy", 0.50, 0.85)
        self.recalibrator.validate_improvement("runs_prediction_mae", 0.80, 0.81)  # <3% → fail
        assert self.recalibrator.should_deploy() is False

    def test_large_regression_blocks_deploy(self):
        """Any metric regressing >5% blocks deployment."""
        self._add_passing_primary_metrics()
        self.recalibrator.validate_improvement("secondary_metric", 0.90, 0.80)  # 10% regression
        assert self.recalibrator.should_deploy() is False

    def test_small_regression_acceptable(self):
        """Secondary metric with <5% regression still allows deploy if primaries pass."""
        self._add_passing_primary_metrics()
        self.recalibrator.validate_improvement("secondary_metric", 0.90, 0.87)  # 3.3% regression < 5%
        assert self.recalibrator.should_deploy() is True


# ---------------------------------------------------------------------------
# generate_audit_trail
# ---------------------------------------------------------------------------

class TestAuditTrail:

    def setup_method(self):
        self.recalibrator = ModelRecalibrator()
        self.recalibrator.record_recalibration("chase_penalty", -20, -25, "Difficult pitch correction")
        self.recalibrator.validate_improvement("winner_accuracy", 0.0, 0.85)
        self.recalibrator.validate_improvement("runs_prediction_mae", 0.70, 0.90)

    def test_audit_trail_has_match_id(self):
        trail = self.recalibrator.generate_audit_trail("india_vs_sa_20260427")
        assert trail["match_id"] == "india_vs_sa_20260427"

    def test_audit_trail_has_timestamp(self):
        trail = self.recalibrator.generate_audit_trail("india_vs_sa_20260427")
        assert "timestamp" in trail

    def test_audit_trail_includes_parameters(self):
        trail = self.recalibrator.generate_audit_trail("india_vs_sa_20260427")
        assert len(trail["parameters_changed"]) == 1
        assert trail["parameters_changed"][0]["parameter"] == "chase_penalty"

    def test_audit_trail_includes_validation_results(self):
        trail = self.recalibrator.generate_audit_trail("india_vs_sa_20260427")
        assert len(trail["validation_results"]) == 2

    def test_audit_trail_includes_deployment_decision(self):
        trail = self.recalibrator.generate_audit_trail("india_vs_sa_20260427")
        assert "deployment_decision" in trail
        assert "should_deploy" in trail["deployment_decision"]

    def test_audit_trail_is_json_serializable(self):
        trail = self.recalibrator.generate_audit_trail("india_vs_sa_20260427")
        json_str = json.dumps(trail)
        assert len(json_str) > 0

    def test_audit_trail_recalibration_id_format(self):
        trail = self.recalibrator.generate_audit_trail("india_vs_sa_20260427")
        assert trail["recalibration_id"].startswith("REC_india_vs_sa_20260427_")


# ---------------------------------------------------------------------------
# save_audit_trail
# ---------------------------------------------------------------------------

class TestSaveAuditTrail:

    def test_saves_to_file(self):
        recalibrator = ModelRecalibrator()
        recalibrator.record_recalibration("param_a", 1.0, 1.1, "Test")
        recalibrator.validate_improvement("winner_accuracy", 0.50, 0.85)
        recalibrator.validate_improvement("runs_prediction_mae", 0.70, 0.90)
        trail = recalibrator.generate_audit_trail("test_match")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit" / "trail.json"
            recalibrator.save_audit_trail(trail, output_path)
            assert output_path.exists()
            with open(output_path) as f:
                loaded = json.load(f)
            assert loaded["match_id"] == "test_match"

    def test_creates_parent_directories(self):
        recalibrator = ModelRecalibrator()
        recalibrator.validate_improvement("winner_accuracy", 0.50, 0.85)
        recalibrator.validate_improvement("runs_prediction_mae", 0.70, 0.90)
        trail = recalibrator.generate_audit_trail("test_match")

        with tempfile.TemporaryDirectory() as tmpdir:
            deep_path = Path(tmpdir) / "a" / "b" / "c" / "audit.json"
            recalibrator.save_audit_trail(trail, deep_path)
            assert deep_path.exists()


# ---------------------------------------------------------------------------
# generate_recalibration_report (human-readable)
# ---------------------------------------------------------------------------

class TestRecalibrationReport:

    def test_report_is_string(self):
        r = ModelRecalibrator()
        r.record_recalibration("chase_penalty", -20, -25, "Correction")
        r.validate_improvement("winner_accuracy", 0.0, 0.85)
        r.validate_improvement("runs_prediction_mae", 0.70, 0.90)
        report = r.generate_recalibration_report()
        assert isinstance(report, str)

    def test_report_contains_parameter_name(self):
        r = ModelRecalibrator()
        r.record_recalibration("chase_penalty", -20, -25, "Correction")
        r.validate_improvement("winner_accuracy", 0.50, 0.85)
        r.validate_improvement("runs_prediction_mae", 0.70, 0.90)
        report = r.generate_recalibration_report()
        assert "chase_penalty" in report

    def test_approved_report_shows_approved(self):
        r = ModelRecalibrator()
        r.validate_improvement("winner_accuracy", 0.50, 0.85)
        r.validate_improvement("runs_prediction_mae", 0.70, 0.90)
        report = r.generate_recalibration_report()
        assert "APPROVED" in report

    def test_blocked_report_shows_blocked(self):
        r = ModelRecalibrator()
        r.validate_improvement("winner_accuracy", 0.80, 0.81)  # Won't pass threshold
        r.validate_improvement("runs_prediction_mae", 0.80, 0.81)
        report = r.generate_recalibration_report()
        assert "BLOCKED" in report
