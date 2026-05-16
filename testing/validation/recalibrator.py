"""
Model Recalibrator Module
=========================

Handles post-match recalibration of model parameters based on validation results.
Implements guard rails to prevent overfitting while enabling continuous improvement.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class RecalibrationAction:
    """Record of a model recalibration action."""
    parameter_name: str
    old_value: any
    new_value: any
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RecalibrationResult:
    """Result of recalibration validation."""
    metric_name: str
    old_accuracy: float
    new_accuracy: float
    improvement: float
    passed_validation: bool
    reason: str


class ModelRecalibrator:
    """Handles model recalibration with guard rails."""

    # Guard rail: Don't change modifiers >15% from baseline
    MODIFIER_DRIFT_GUARD = 0.15

    # Guard rail: Require 3% improvement to deploy
    MIN_IMPROVEMENT_THRESHOLD = 0.03

    # Guard rail: Max parameters to change per cycle
    MAX_PARAMS_PER_CYCLE = 5

    def __init__(self, model_baseline: Dict = None):
        """Initialize recalibrator.

        Args:
            model_baseline: Baseline model parameters for drift checking
        """
        self.model_baseline = model_baseline or {}
        self.recalibration_history: List[RecalibrationAction] = []
        self.validation_results: List[RecalibrationResult] = []

    def validate_parameter_change(
        self,
        parameter_name: str,
        old_value: float,
        new_value: float
    ) -> Dict[str, any]:
        """Validate if parameter change is safe.

        Args:
            parameter_name: Name of parameter
            old_value: Current/old value
            new_value: Proposed new value

        Returns:
            Dict with validation result and reasoning
        """
        if isinstance(new_value, (int, float)) and isinstance(old_value, (int, float)):
            # Check drift from baseline
            if parameter_name in self.model_baseline:
                baseline = self.model_baseline[parameter_name]
                drift_pct = abs(new_value - baseline) / abs(baseline) if baseline != 0 else 0

                if drift_pct > self.MODIFIER_DRIFT_GUARD:
                    return {
                        "valid": False,
                        "reason": f"Drift {drift_pct:.1%} exceeds guard rail {self.MODIFIER_DRIFT_GUARD:.0%}",
                        "recommendation": "Reduce change magnitude or increase data window"
                    }

        return {
            "valid": True,
            "reason": "Parameter change within guard rails"
        }

    def check_recalibration_cycle(
        self,
        proposed_actions: List[Dict]
    ) -> Dict[str, any]:
        """Check if proposed recalibration cycle is valid.

        Args:
            proposed_actions: List of proposed parameter changes

        Returns:
            Dict with validation result
        """
        if len(proposed_actions) > self.MAX_PARAMS_PER_CYCLE:
            return {
                "valid": False,
                "reason": f"Too many parameters ({len(proposed_actions)}) in one cycle (max {self.MAX_PARAMS_PER_CYCLE})",
                "recommendation": "Split recalibration across multiple cycles or investigate structural issues"
            }

        return {
            "valid": True,
            "reason": f"Recalibration cycle valid ({len(proposed_actions)} parameters)"
        }

    def record_recalibration(
        self,
        parameter_name: str,
        old_value: any,
        new_value: any,
        reason: str
    ) -> None:
        """Record a recalibration action in history.

        Args:
            parameter_name: Parameter name
            old_value: Old value
            new_value: New value
            reason: Reason for change
        """
        action = RecalibrationAction(
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason
        )
        self.recalibration_history.append(action)

    def validate_improvement(
        self,
        metric_name: str,
        old_accuracy: float,
        new_accuracy: float,
        allow_small_regression: bool = False
    ) -> RecalibrationResult:
        """Validate if recalibration improved metrics.

        Args:
            metric_name: Name of metric (e.g., "winner_accuracy")
            old_accuracy: Old accuracy score
            new_accuracy: New accuracy score
            allow_small_regression: Allow <1% regression if offset by other improvements

        Returns:
            RecalibrationResult with validation
        """
        improvement = new_accuracy - old_accuracy

        # Check if improvement meets threshold
        passed = improvement >= self.MIN_IMPROVEMENT_THRESHOLD
        if not passed and allow_small_regression:
            passed = improvement >= -0.01  # Allow 1% regression

        reason = ""
        if improvement > self.MIN_IMPROVEMENT_THRESHOLD:
            reason = f"✓ Improvement {improvement:.1%} exceeds threshold"
        elif improvement > 0:
            reason = f"⚠ Improvement {improvement:.1%} below threshold (need {self.MIN_IMPROVEMENT_THRESHOLD:.1%})"
        elif improvement < -0.01:
            reason = f"✗ Regression {improvement:.1%} detected"
        else:
            reason = f"→ No significant change ({improvement:.1%})"

        result = RecalibrationResult(
            metric_name=metric_name,
            old_accuracy=old_accuracy,
            new_accuracy=new_accuracy,
            improvement=improvement,
            passed_validation=passed,
            reason=reason
        )

        self.validation_results.append(result)
        return result

    def should_deploy(self) -> bool:
        """Determine if recalibration should be deployed.

        Returns:
            True if improvements validated and no degradation
        """
        if not self.validation_results:
            return False

        # Check primary metrics (winner, runs)
        primary_metrics = ["winner_accuracy", "runs_prediction_mae"]
        passed_primary = 0

        for result in self.validation_results:
            if result.metric_name in primary_metrics:
                if result.passed_validation:
                    passed_primary += 1

        # All primary metrics must pass
        if passed_primary < len(primary_metrics):
            return False

        # Check for major regressions
        for result in self.validation_results:
            if result.improvement < -0.05:  # >5% regression not acceptable
                return False

        return True

    def generate_audit_trail(self, match_id: str) -> Dict:
        """Generate audit trail of recalibration.

        Args:
            match_id: Match identifier

        Returns:
            Audit trail dict
        """
        return {
            "recalibration_id": f"REC_{match_id}_{len(self.recalibration_history):03d}",
            "match_id": match_id,
            "timestamp": datetime.now().isoformat(),
            "parameters_changed": [
                {
                    "parameter": action.parameter_name,
                    "old_value": action.old_value,
                    "new_value": action.new_value,
                    "reason": action.reason,
                    "changed_at": action.timestamp
                }
                for action in self.recalibration_history
            ],
            "validation_results": [
                {
                    "metric": result.metric_name,
                    "old_accuracy": result.old_accuracy,
                    "new_accuracy": result.new_accuracy,
                    "improvement": result.improvement,
                    "passed": result.passed_validation,
                    "reason": result.reason
                }
                for result in self.validation_results
            ],
            "deployment_decision": {
                "should_deploy": self.should_deploy(),
                "reason": self._generate_deployment_reason()
            }
        }

    def _generate_deployment_reason(self) -> str:
        """Generate reason for deployment decision."""
        if not self.validation_results:
            return "No validation results available"

        if self.should_deploy():
            improvements = [r.improvement for r in self.validation_results if r.improvement > 0]
            avg_improvement = sum(improvements) / len(improvements) if improvements else 0
            return f"✓ All metrics passed validation with {avg_improvement:.1%} average improvement"

        failures = [r.metric_name for r in self.validation_results if not r.passed_validation]
        return f"✗ Deployment blocked: {', '.join(failures)} did not meet validation criteria"

    def save_audit_trail(self, audit_trail: Dict, output_path: Path) -> None:
        """Save audit trail to file.

        Args:
            audit_trail: Audit trail dict
            output_path: Path to save JSON
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(audit_trail, f, indent=2)

    def generate_recalibration_report(self) -> str:
        """Generate human-readable recalibration report.

        Returns:
            Formatted report string
        """
        report = "═" * 80 + "\n"
        report += "MODEL RECALIBRATION REPORT\n"
        report += "═" * 80 + "\n\n"

        # Parameters changed
        if self.recalibration_history:
            report += "PARAMETERS CHANGED:\n"
            for i, action in enumerate(self.recalibration_history, 1):
                report += f"  {i}. {action.parameter_name}\n"
                report += f"     Old: {action.old_value}\n"
                report += f"     New: {action.new_value}\n"
                report += f"     Reason: {action.reason}\n\n"

        # Validation results
        if self.validation_results:
            report += "VALIDATION RESULTS:\n"
            report += f"{'Metric':<30} {'Old':<10} {'New':<10} {'Improvement':<15} {'Status'}\n"
            report += "─" * 80 + "\n"

            for result in self.validation_results:
                status = "✓ PASS" if result.passed_validation else "✗ FAIL"
                report += f"{result.metric_name:<30} {result.old_accuracy:<10.1%} "
                report += f"{result.new_accuracy:<10.1%} {result.improvement:<15.1%} {status}\n"

        # Deployment decision
        report += "\n" + "─" * 80 + "\n"
        report += "DEPLOYMENT DECISION:\n"
        if self.should_deploy():
            report += "  ✓ APPROVED FOR DEPLOYMENT\n"
        else:
            report += "  ✗ BLOCKED - VALIDATION FAILED\n"

        report += "═" * 80 + "\n"
        return report


# Example usage
if __name__ == "__main__":
    # Initialize with baseline
    baseline = {
        "chase_penalty": -20,
        "form_modifier_deepti": 1.08,
        "pace_friendly_willowmoore": 8.0
    }

    recalibrator = ModelRecalibrator(model_baseline=baseline)

    # Simulate recalibration actions
    recalibrator.record_recalibration(
        parameter_name="chase_penalty",
        old_value=-20,
        new_value=-25,
        reason="Increased penalty for difficult pitches"
    )

    recalibrator.record_recalibration(
        parameter_name="pace_friendly_willowmoore",
        old_value=8.0,
        new_value=6.5,
        reason="Actual match showed pitch was more difficult than expected"
    )

    # Validate improvements
    recalibrator.validate_improvement(
        metric_name="winner_accuracy",
        old_accuracy=0.0,
        new_accuracy=0.85,
        allow_small_regression=False
    )

    recalibrator.validate_improvement(
        metric_name="runs_prediction_mae",
        old_accuracy=0.82,
        new_accuracy=0.90,
        allow_small_regression=False
    )

    # Generate report
    print(recalibrator.generate_recalibration_report())
    print(f"\nDeploy decision: {recalibrator.should_deploy()}")
