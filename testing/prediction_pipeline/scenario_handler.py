"""
Scenario Handler Module
=======================

Implements toss dependency and scenario-aware predictions.
Critical for distinguishing batting first vs chasing scenarios.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TossInfo:
    """Toss outcome information."""
    winner: str  # "team1" or "team2"
    decision: str  # "bat_first" or "bowl_first"

    def is_team_batting_first(self, team_id: str) -> bool:
        """Check if team is batting first."""
        if self.decision == "bat_first":
            return self.winner == team_id
        else:  # bowl_first
            return self.winner != team_id


class ScenarioHandler:
    """Handles scenario-aware prediction adjustments."""

    # Chase penalty by pitch difficulty
    CHASE_PENALTY_BY_PITCH = {
        "easy": -15,        # Easy to bat: -15 runs when chasing
        "moderate": -20,    # Neutral pitch: -20 runs when chasing
        "difficult": -25,   # Hard to bat: -25 runs when chasing
        "very_difficult": -30  # Extremely hard: -30 runs when chasing
    }

    # Pitch difficulty classification
    PITCH_DIFFICULTY_SCALE = {
        "pace_friendly": ("easy", "moderate"),      # 7-8+ pace score
        "balanced": ("moderate", "moderate"),        # 5-7 pace score
        "spin_friendly": ("moderate", "difficult"),  # 3-5 pace score
        "very_difficult": ("difficult", "very_difficult")  # <3 pace score
    }

    def __init__(self):
        """Initialize scenario handler."""
        self.toss_info: Optional[TossInfo] = None
        self.scenario_type: Optional[str] = None

    def set_toss(self, winner: str, decision: str) -> None:
        """Set toss outcome.

        Args:
            winner: "team1" or "team2"
            decision: "bat_first" or "bowl_first"
        """
        self.toss_info = TossInfo(winner=winner, decision=decision)

    def identify_scenario(self, team_id: str, opponent_id: str) -> str:
        """Identify if team is batting first or chasing.

        Args:
            team_id: Team we're predicting for
            opponent_id: Opponent team

        Returns:
            "batting_first" or "chasing"
        """
        if self.toss_info is None:
            return "unknown"

        is_batting_first = self.toss_info.is_team_batting_first(team_id)
        self.scenario_type = "batting_first" if is_batting_first else "chasing"
        return self.scenario_type

    def get_chase_penalty(self, pitch_difficulty: str) -> int:
        """Get runs penalty for chasing scenario.

        Args:
            pitch_difficulty: "easy", "moderate", "difficult", or "very_difficult"

        Returns:
            Penalty in runs (negative number)
        """
        return self.CHASE_PENALTY_BY_PITCH.get(pitch_difficulty, -20)

    def classify_pitch_difficulty(self, pace_friendly_score: float) -> str:
        """Classify pitch difficulty based on pace-friendly score.

        Args:
            pace_friendly_score: 0-10 scale

        Returns:
            "easy", "moderate", "difficult", or "very_difficult"
        """
        if pace_friendly_score >= 7.5:
            return "easy"
        elif pace_friendly_score >= 6.0:
            return "moderate"
        elif pace_friendly_score >= 4.0:
            return "difficult"
        else:
            return "very_difficult"

    def adjust_runs_prediction(
        self,
        base_runs: float,
        pitch_difficulty: str,
        confidence: float = 1.0
    ) -> Dict[str, float]:
        """Adjust runs prediction based on scenario.

        Args:
            base_runs: Base expected runs (batting first scenario)
            pitch_difficulty: Pitch difficulty classification
            confidence: Prediction confidence (0-1)

        Returns:
            Dict with adjusted runs, lower_bound, upper_bound
        """
        result = {
            "base_runs": base_runs,
            "scenario": self.scenario_type,
            "confidence": confidence
        }

        if self.scenario_type == "chasing":
            penalty = self.get_chase_penalty(pitch_difficulty)
            adjusted_runs = base_runs + penalty
            margin = 8 * (1 - confidence)  # Wider margin if less confident

            result.update({
                "adjusted_runs": adjusted_runs,
                "penalty": penalty,
                "lower_bound": adjusted_runs - margin,
                "upper_bound": adjusted_runs + margin,
                "adjustment_reason": f"Chase penalty {penalty} runs for {pitch_difficulty} pitch"
            })
        else:  # batting_first
            margin = 8 * (1 - confidence)

            result.update({
                "adjusted_runs": base_runs,
                "penalty": 0,
                "lower_bound": base_runs - margin,
                "upper_bound": base_runs + margin,
                "adjustment_reason": "Batting first: no penalty"
            })

        return result

    def adjust_win_probability(
        self,
        base_win_prob: float,
        pitch_difficulty: str,
        is_chasing: bool
    ) -> Dict[str, float]:
        """Adjust win probability based on scenario.

        Args:
            base_win_prob: Base win probability (0-1)
            pitch_difficulty: Pitch difficulty
            is_chasing: Whether team is chasing

        Returns:
            Dict with adjusted probability and reasoning
        """
        adjusted_prob = base_win_prob
        adjustment = 0

        if is_chasing:
            # Chasing reduces win probability
            difficulty_penalties = {
                "easy": -0.05,
                "moderate": -0.10,
                "difficult": -0.15,
                "very_difficult": -0.20
            }
            adjustment = difficulty_penalties.get(pitch_difficulty, -0.10)
            adjusted_prob = max(0.0, min(1.0, base_win_prob + adjustment))

        return {
            "base_win_probability": base_win_prob,
            "adjusted_win_probability": adjusted_prob,
            "adjustment": adjustment,
            "scenario": self.scenario_type,
            "reasoning": self._generate_win_prob_reasoning(
                base_win_prob, adjusted_prob, is_chasing, pitch_difficulty
            )
        }

    @staticmethod
    def _generate_win_prob_reasoning(
        base_prob: float,
        adjusted_prob: float,
        is_chasing: bool,
        pitch_difficulty: str
    ) -> str:
        """Generate explanation for win probability adjustment."""
        if not is_chasing:
            return "Batting first: standard conditions"

        difficulty_names = {
            "easy": "easy to bat on",
            "moderate": "neutral conditions",
            "difficult": "challenging to bat on",
            "very_difficult": "extremely difficult pitch"
        }

        pitch_desc = difficulty_names.get(pitch_difficulty, "unknown pitch")
        prob_pct = int(adjusted_prob * 100)

        return f"Chasing on {pitch_desc} reduces win probability to {prob_pct}%"

    def generate_scenario_report(self) -> Dict:
        """Generate report of scenario information."""
        if self.toss_info is None:
            return {
                "status": "pending",
                "message": "Toss information not yet available",
                "prediction_confidence": "low"
            }

        return {
            "status": "complete",
            "toss_winner": self.toss_info.winner,
            "toss_decision": self.toss_info.decision,
            "scenario": self.scenario_type,
            "prediction_confidence": "high",
            "message": f"Toss known: {self.toss_info.winner} chose to {self.toss_info.decision}"
        }


# Example usage
if __name__ == "__main__":
    # Example: India vs South Africa, India wins toss and bowls first
    handler = ScenarioHandler()
    handler.set_toss(winner="team1", decision="bowl_first")

    scenario = handler.identify_scenario(team_id="team1", opponent_id="team2")
    print(f"Scenario: {scenario}")  # Should be "chasing"

    # Willowmoore is difficult (pace score 6.5)
    pitch_diff = handler.classify_pitch_difficulty(6.5)
    print(f"Pitch difficulty: {pitch_diff}")  # Should be "difficult"

    # Adjust runs prediction
    base_runs = 162
    adjusted = handler.adjust_runs_prediction(base_runs, pitch_diff, confidence=0.55)
    print(f"\nRuns prediction adjustment:")
    print(f"  Base: {adjusted['base_runs']} runs")
    print(f"  Adjusted: {adjusted['adjusted_runs']} runs")
    print(f"  Range: {adjusted['lower_bound']:.0f}-{adjusted['upper_bound']:.0f}")
    print(f"  Reason: {adjusted['adjustment_reason']}")

    # Adjust win probability
    base_win_prob = 0.55
    win_adj = handler.adjust_win_probability(base_win_prob, pitch_diff, is_chasing=True)
    print(f"\nWin probability adjustment:")
    print(f"  Base: {base_win_prob:.0%}")
    print(f"  Adjusted: {win_adj['adjusted_win_probability']:.0%}")
    print(f"  Reason: {win_adj['reasoning']}")
