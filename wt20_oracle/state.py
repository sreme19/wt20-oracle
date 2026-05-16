"""
Pipeline State Contract
========================

Single TypedDict passed between every node in the pre-match graph.
Nodes read from it and return updated copies — never mutate in place.

Key design: toss fields (toss_winner, toss_decision, scenario) are set
by the ScenarioNode early in the pipeline so every downstream node
(runs prediction, win probability) can apply the correct adjustments.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class PreMatchState(TypedDict, total=False):
    # ── Inputs ─────────────────────────────────────────────────────────────
    team_id: str                        # e.g. "india"
    opponent_id: str                    # e.g. "south_africa"
    venue_id: str                       # e.g. "lords"
    match_date: str                     # ISO date "2026-06-17"

    # ── Toss & Scenario (set by ScenarioNode) ──────────────────────────────
    toss_winner: Optional[str]          # team_id or None if not yet known
    toss_decision: Optional[str]        # "bat_first" or "bowl_first" or None
    scenario: str                       # "batting_first" | "chasing" | "unknown"
    pitch_difficulty: str               # "easy" | "moderate" | "difficult" | "very_difficult"
    chase_penalty: int                  # runs penalty for chasing (0 if batting first)
    scenario_report: Dict[str, Any]     # ScenarioHandler.generate_scenario_report()

    # ── Raw Data (loaded by DataNode) ──────────────────────────────────────
    our_squad: List[Dict[str, Any]]     # list of player dicts (india.json)
    opponent_squad: List[Dict[str, Any]]
    venue_data: Dict[str, Any]          # venue record from venues.json
    team_data: Dict[str, Any]           # our team record from teams.json
    opponent_data: Dict[str, Any]
    matchups: Dict[str, Any]            # keyed "batter_id::bowler_id"
    analyst_insights: Dict[str, Any]    # from analyst_insights.json

    # ── Opponent Analysis (set by OpponentAnalysisNode) ────────────────────
    opponent_strengths: List[str]
    opponent_weaknesses: List[str]
    opponent_key_bowlers: List[str]
    opponent_key_batters: List[str]

    # ── Squad Selection (set by SquadSelectorNode) ─────────────────────────
    selected_xi: List[str]              # list of player IDs
    selection_reasoning: List[str]      # one sentence per selection decision
    excluded_players: List[str]         # squad members not selected

    # ── Batting Order (set by BattingOrderNode) ────────────────────────────
    batting_order: List[str]            # player IDs in batting position order
    batting_reasoning: Dict[str, str]   # player_id → reason for position

    # ── Bowling Plan (set by BowlingPlanNode) ──────────────────────────────
    bowling_plan: List[Dict[str, Any]]  # [{player_id, phase, max_overs, rationale}]
    bowling_reasoning: str

    # ── Runs & Win Probability (set by PredictionNode) ─────────────────────
    base_runs_estimate: float           # before scenario adjustment
    adjusted_runs_estimate: float       # after chase penalty
    runs_lower: float
    runs_upper: float
    win_probability: float              # 0.0–1.0, scenario-adjusted
    win_probability_reasoning: str

    # ── Strategy (set by StrategyNode) ─────────────────────────────────────
    strategy_brief: str                 # plain-English summary
    key_matchups: List[Dict[str, Any]]  # [{batter, bowler, insight}]
    tactical_flags: List[str]           # e.g. ["target_powerplay_spinner"]

    # ── Validation (set post-match by ValidationNode) ──────────────────────
    actual_result: Optional[Dict[str, Any]]
    decision_score: Optional[float]     # weighted TIER 1 score (0-100)
    validation_report: Optional[Dict[str, Any]]

    # ── Errors / Warnings ──────────────────────────────────────────────────
    errors: List[str]
    warnings: List[str]
