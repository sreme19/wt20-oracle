"""
Unit Tests: ScenarioHandler
===========================

Tests toss dependency, scenario identification, pitch classification,
run adjustments, and win probability adjustments.

Key scenario validated: India vs SA April 27 — India won toss, chose to
bowl first → India ends up CHASING, not batting first as original model assumed.
"""

import pytest
import sys
from pathlib import Path

# Ensure testing package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from testing.prediction_pipeline.scenario_handler import ScenarioHandler, TossInfo


# ---------------------------------------------------------------------------
# TossInfo Tests
# ---------------------------------------------------------------------------

class TestTossInfo:

    def test_bat_first_winner_is_batting_first(self):
        toss = TossInfo(winner="india", decision="bat_first")
        assert toss.is_team_batting_first("india") is True

    def test_bat_first_loser_is_chasing(self):
        toss = TossInfo(winner="india", decision="bat_first")
        assert toss.is_team_batting_first("sa") is False

    def test_bowl_first_winner_is_chasing(self):
        """India wins toss, chooses to bowl → India is chasing."""
        toss = TossInfo(winner="india", decision="bowl_first")
        assert toss.is_team_batting_first("india") is False

    def test_bowl_first_loser_bats_first(self):
        """India wins toss, chooses to bowl → SA bats first."""
        toss = TossInfo(winner="india", decision="bowl_first")
        assert toss.is_team_batting_first("sa") is True

    def test_india_vs_sa_actual_scenario(self):
        """The exact India vs SA April 27 toss: India won, chose bowl first."""
        toss = TossInfo(winner="india", decision="bowl_first")
        # India ends up chasing (NOT batting first as old model assumed)
        assert toss.is_team_batting_first("india") is False
        # SA bats first
        assert toss.is_team_batting_first("sa") is True


# ---------------------------------------------------------------------------
# ScenarioHandler: set_toss / identify_scenario
# ---------------------------------------------------------------------------

class TestScenarioIdentification:

    def setup_method(self):
        self.handler = ScenarioHandler()

    def test_no_toss_returns_unknown(self):
        result = self.handler.identify_scenario("india", "sa")
        assert result == "unknown"

    def test_batting_first_scenario(self):
        self.handler.set_toss(winner="india", decision="bat_first")
        scenario = self.handler.identify_scenario("india", "sa")
        assert scenario == "batting_first"

    def test_chasing_scenario(self):
        self.handler.set_toss(winner="india", decision="bowl_first")
        scenario = self.handler.identify_scenario("india", "sa")
        assert scenario == "chasing"

    def test_india_vs_sa_real_scenario(self):
        """India won toss, bowled first → India chases. Critical missed root cause."""
        self.handler.set_toss(winner="india", decision="bowl_first")
        assert self.handler.identify_scenario("india", "sa") == "chasing"

    def test_scenario_stored_on_handler(self):
        self.handler.set_toss(winner="india", decision="bat_first")
        self.handler.identify_scenario("india", "sa")
        assert self.handler.scenario_type == "batting_first"

    def test_toss_info_stored_correctly(self):
        self.handler.set_toss(winner="team1", decision="bowl_first")
        assert self.handler.toss_info.winner == "team1"
        assert self.handler.toss_info.decision == "bowl_first"


# ---------------------------------------------------------------------------
# ScenarioHandler: classify_pitch_difficulty
# ---------------------------------------------------------------------------

class TestPitchClassification:

    def setup_method(self):
        self.handler = ScenarioHandler()

    def test_high_pace_score_is_easy(self):
        assert self.handler.classify_pitch_difficulty(8.5) == "easy"

    def test_boundary_75_is_easy(self):
        assert self.handler.classify_pitch_difficulty(7.5) == "easy"

    def test_pace_score_7_is_moderate(self):
        assert self.handler.classify_pitch_difficulty(7.0) == "moderate"

    def test_pace_score_6_is_moderate(self):
        assert self.handler.classify_pitch_difficulty(6.0) == "moderate"

    def test_pace_score_55_is_difficult(self):
        assert self.handler.classify_pitch_difficulty(5.5) == "difficult"

    def test_pace_score_4_is_difficult(self):
        assert self.handler.classify_pitch_difficulty(4.0) == "difficult"

    def test_pace_score_below_4_is_very_difficult(self):
        assert self.handler.classify_pitch_difficulty(3.9) == "very_difficult"

    def test_zero_score_is_very_difficult(self):
        assert self.handler.classify_pitch_difficulty(0.0) == "very_difficult"

    def test_willowmoore_pace_65_is_moderate(self):
        """
        Willowmoore Park pace score 6.5 → moderate difficulty.
        Old model had it as 8.0 (easy) — this was a root cause of the failure.
        """
        result = self.handler.classify_pitch_difficulty(6.5)
        assert result == "moderate"

    def test_old_willowmoore_score_80_was_easy(self):
        """Original (incorrect) Willowmoore rating of 8.0 → classified as easy."""
        result = self.handler.classify_pitch_difficulty(8.0)
        assert result == "easy"


# ---------------------------------------------------------------------------
# ScenarioHandler: get_chase_penalty
# ---------------------------------------------------------------------------

class TestChasePenalty:

    def setup_method(self):
        self.handler = ScenarioHandler()

    def test_easy_pitch_penalty(self):
        assert self.handler.get_chase_penalty("easy") == -15

    def test_moderate_pitch_penalty(self):
        assert self.handler.get_chase_penalty("moderate") == -20

    def test_difficult_pitch_penalty(self):
        assert self.handler.get_chase_penalty("difficult") == -25

    def test_very_difficult_pitch_penalty(self):
        assert self.handler.get_chase_penalty("very_difficult") == -30

    def test_unknown_pitch_defaults_to_moderate(self):
        assert self.handler.get_chase_penalty("unknown") == -20

    def test_all_penalties_are_negative(self):
        for difficulty in ["easy", "moderate", "difficult", "very_difficult"]:
            assert self.handler.get_chase_penalty(difficulty) < 0

    def test_harder_pitch_larger_penalty(self):
        easy = self.handler.get_chase_penalty("easy")
        moderate = self.handler.get_chase_penalty("moderate")
        difficult = self.handler.get_chase_penalty("difficult")
        very_difficult = self.handler.get_chase_penalty("very_difficult")
        assert easy > moderate > difficult > very_difficult


# ---------------------------------------------------------------------------
# ScenarioHandler: adjust_runs_prediction
# ---------------------------------------------------------------------------

class TestRunsAdjustment:

    def setup_method(self):
        self.handler = ScenarioHandler()

    def test_batting_first_no_penalty(self):
        self.handler.set_toss(winner="india", decision="bat_first")
        self.handler.identify_scenario("india", "sa")
        result = self.handler.adjust_runs_prediction(162, "moderate")
        assert result["penalty"] == 0
        assert result["adjusted_runs"] == 162

    def test_chasing_applies_penalty(self):
        self.handler.set_toss(winner="india", decision="bowl_first")
        self.handler.identify_scenario("india", "sa")
        result = self.handler.adjust_runs_prediction(162, "moderate")
        assert result["penalty"] == -20
        assert result["adjusted_runs"] == 142

    def test_india_vs_sa_scenario_correction(self):
        """
        Original prediction: India bats first, 162 runs.
        Corrected: India chases on moderate pitch → 162 - 20 = 142 runs.
        Actual: India scored 132 (within ±10 of 142 — PASS).
        """
        self.handler.set_toss(winner="india", decision="bowl_first")
        self.handler.identify_scenario("india", "sa")
        result = self.handler.adjust_runs_prediction(162, "moderate", confidence=0.75)
        assert result["adjusted_runs"] == 142
        assert abs(result["adjusted_runs"] - 132) <= 15  # Within reasonable range

    def test_difficult_pitch_chase_penalty(self):
        self.handler.set_toss(winner="india", decision="bowl_first")
        self.handler.identify_scenario("india", "sa")
        result = self.handler.adjust_runs_prediction(162, "difficult")
        assert result["penalty"] == -25
        assert result["adjusted_runs"] == 137

    def test_result_contains_bounds(self):
        self.handler.set_toss(winner="india", decision="bat_first")
        self.handler.identify_scenario("india", "sa")
        result = self.handler.adjust_runs_prediction(162, "moderate", confidence=1.0)
        assert "lower_bound" in result
        assert "upper_bound" in result

    def test_lower_confidence_widens_bounds(self):
        self.handler.set_toss(winner="india", decision="bat_first")
        self.handler.identify_scenario("india", "sa")
        r_high = self.handler.adjust_runs_prediction(162, "moderate", confidence=1.0)
        r_low = self.handler.adjust_runs_prediction(162, "moderate", confidence=0.5)
        high_width = r_high["upper_bound"] - r_high["lower_bound"]
        low_width = r_low["upper_bound"] - r_low["lower_bound"]
        assert low_width > high_width

    def test_result_contains_scenario(self):
        self.handler.set_toss(winner="india", decision="bat_first")
        self.handler.identify_scenario("india", "sa")
        result = self.handler.adjust_runs_prediction(162, "moderate")
        assert result["scenario"] == "batting_first"

    def test_result_contains_base_runs(self):
        self.handler.set_toss(winner="india", decision="bat_first")
        self.handler.identify_scenario("india", "sa")
        result = self.handler.adjust_runs_prediction(162, "moderate")
        assert result["base_runs"] == 162


# ---------------------------------------------------------------------------
# ScenarioHandler: adjust_win_probability
# ---------------------------------------------------------------------------

class TestWinProbabilityAdjustment:

    def setup_method(self):
        self.handler = ScenarioHandler()

    def test_batting_first_no_adjustment(self):
        result = self.handler.adjust_win_probability(0.60, "moderate", is_chasing=False)
        assert result["adjusted_win_probability"] == 0.60
        assert result["adjustment"] == 0

    def test_chasing_moderate_reduces_prob(self):
        result = self.handler.adjust_win_probability(0.60, "moderate", is_chasing=True)
        assert result["adjusted_win_probability"] == pytest.approx(0.50)
        assert result["adjustment"] == -0.10

    def test_chasing_easy_pitch_small_reduction(self):
        result = self.handler.adjust_win_probability(0.60, "easy", is_chasing=True)
        assert result["adjusted_win_probability"] == pytest.approx(0.55)

    def test_chasing_very_difficult_large_reduction(self):
        result = self.handler.adjust_win_probability(0.60, "very_difficult", is_chasing=True)
        assert result["adjusted_win_probability"] == pytest.approx(0.40)

    def test_probability_never_below_zero(self):
        result = self.handler.adjust_win_probability(0.10, "very_difficult", is_chasing=True)
        assert result["adjusted_win_probability"] >= 0.0

    def test_probability_never_above_one(self):
        result = self.handler.adjust_win_probability(1.0, "easy", is_chasing=False)
        assert result["adjusted_win_probability"] <= 1.0

    def test_harder_pitch_larger_prob_reduction(self):
        r_easy = self.handler.adjust_win_probability(0.60, "easy", is_chasing=True)
        r_hard = self.handler.adjust_win_probability(0.60, "very_difficult", is_chasing=True)
        assert r_hard["adjusted_win_probability"] < r_easy["adjusted_win_probability"]

    def test_result_contains_reasoning(self):
        result = self.handler.adjust_win_probability(0.55, "difficult", is_chasing=True)
        assert "reasoning" in result
        assert len(result["reasoning"]) > 0


# ---------------------------------------------------------------------------
# ScenarioHandler: generate_scenario_report
# ---------------------------------------------------------------------------

class TestScenarioReport:

    def setup_method(self):
        self.handler = ScenarioHandler()

    def test_no_toss_returns_pending_status(self):
        report = self.handler.generate_scenario_report()
        assert report["status"] == "pending"
        assert report["prediction_confidence"] == "low"

    def test_with_toss_returns_complete_status(self):
        self.handler.set_toss(winner="india", decision="bat_first")
        self.handler.identify_scenario("india", "sa")
        report = self.handler.generate_scenario_report()
        assert report["status"] == "complete"
        assert report["prediction_confidence"] == "high"

    def test_report_includes_toss_details(self):
        self.handler.set_toss(winner="india", decision="bowl_first")
        report = self.handler.generate_scenario_report()
        assert report["toss_winner"] == "india"
        assert report["toss_decision"] == "bowl_first"
