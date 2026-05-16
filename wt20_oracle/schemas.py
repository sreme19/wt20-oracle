from enum import Enum
from typing import Optional
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class TeamID(str, Enum):
    INDIA = "india"
    AUSTRALIA = "australia"
    ENGLAND = "england"
    NEW_ZEALAND = "new_zealand"
    SOUTH_AFRICA = "south_africa"
    PAKISTAN = "pakistan"
    WEST_INDIES = "west_indies"
    SRI_LANKA = "sri_lanka"
    BANGLADESH = "bangladesh"
    IRELAND = "ireland"
    SCOTLAND = "scotland"
    NETHERLANDS = "netherlands"


class Group(str, Enum):
    A = "A"  # India, Australia, South Africa, Pakistan, Bangladesh, Netherlands
    B = "B"  # England, New Zealand, West Indies, Sri Lanka, Ireland, Scotland


class TournamentStage(str, Enum):
    GROUP = "group"
    SEMI_FINAL = "semi_final"
    FINAL = "final"


class Phase(str, Enum):
    POWERPLAY = "powerplay"   # overs 1-6
    MIDDLE = "middle"         # overs 7-15
    DEATH = "death"           # overs 16-20


class PlayerRole(str, Enum):
    BATTER = "batter"
    BOWLER = "bowler"
    ALL_ROUNDER = "all_rounder"
    WK_BATTER = "wk_batter"


class BattingHand(str, Enum):
    RIGHT = "right"
    LEFT = "left"


class BowlingStyle(str, Enum):
    RIGHT_ARM_PACE = "right_arm_pace"
    RIGHT_ARM_MEDIUM = "right_arm_medium"
    LEFT_ARM_PACE = "left_arm_pace"
    LEFT_ARM_MEDIUM = "left_arm_medium"
    RIGHT_ARM_OFF_SPIN = "right_arm_off_spin"
    RIGHT_ARM_LEG_SPIN = "right_arm_leg_spin"
    LEFT_ARM_ORTHODOX = "left_arm_orthodox"
    LEFT_ARM_WRIST_SPIN = "left_arm_wrist_spin"


class PitchType(str, Enum):
    FLAT = "flat"
    SEAM_FRIENDLY = "seam_friendly"
    SPIN_FRIENDLY = "spin_friendly"
    BALANCED = "balanced"


class DewFactor(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FitnessStatus(str, Enum):
    FIT = "fit"
    DOUBTFUL = "doubtful"
    INJURED = "injured"
    UNAVAILABLE = "unavailable"


class StatisticalReliability(str, Enum):
    LOW = "low"        # < 6 balls / < 5 matches
    MEDIUM = "medium"  # 6-20 balls / 5-15 matches
    HIGH = "high"      # > 20 balls / > 15 matches


class MatchMode(str, Enum):
    PRE_MATCH = "pre_match"
    LIVE = "live"


class TossDecision(str, Enum):
    BAT = "bat"
    FIELD = "field"


class VenueID(str, Enum):
    LORDS = "lords"
    OLD_TRAFFORD = "old_trafford"
    HEADINGLEY = "headingley"
    EDGBASTON = "edgbaston"
    ROSE_BOWL = "rose_bowl"
    THE_OVAL = "the_oval"
    BRISTOL = "bristol"


# ---------------------------------------------------------------------------
# Shared sub-schemas (used inside player / team / matchup schemas)
# ---------------------------------------------------------------------------

class PhaseSplitSchema(TypedDict):
    balls: int
    runs: int
    strike_rate: float
    dot_ball_pct: float
    boundary_pct: float
    dismissals: int


class OppositionSplitSchema(TypedDict):
    strike_rate: float
    dot_ball_pct: float
    dismissal_rate: float     # dismissals per ball faced


class FormWindowSchema(TypedDict):
    matches: int
    runs: int
    average: float
    strike_rate: float


class BowlingPhaseSplitSchema(TypedDict):
    overs: float
    runs: int
    wickets: int
    economy: float
    dot_ball_pct: float


class BowlingOppositionSplitSchema(TypedDict):
    economy: float
    dot_ball_pct: float
    wickets_per_over: float


# ---------------------------------------------------------------------------
# Player batting / bowling stat blocks
# ---------------------------------------------------------------------------

class BattingStatsSchema(TypedDict):
    matches: int
    innings: int
    runs: int
    average: float
    strike_rate: float
    boundary_pct: float
    dot_ball_pct: float
    fifties: int
    hundreds: int
    phase_splits: dict[str, PhaseSplitSchema]        # keys: powerplay / middle / death
    vs_pace: OppositionSplitSchema
    vs_spin: OppositionSplitSchema
    vs_left_arm: OppositionSplitSchema
    vs_right_arm: OppositionSplitSchema
    form_windows: dict[str, FormWindowSchema]         # keys: last_12m / last_6m / last_5
    icc_tournament_record: FormWindowSchema
    pressure_index: dict[str, float]                  # high_rr_sr, low_rr_sr, defend_sr
    statistical_reliability: str                      # StatisticalReliability value


class BowlingStatsSchema(TypedDict):
    matches: int
    innings: int
    overs: float
    wickets: int
    average: float
    economy: float
    strike_rate: float
    dot_ball_pct: float
    phase_splits: dict[str, BowlingPhaseSplitSchema]  # powerplay / middle / death
    vs_left_hand: BowlingOppositionSplitSchema
    vs_right_hand: BowlingOppositionSplitSchema
    death_specialist: bool
    powerplay_specialist: bool
    form_windows: dict[str, dict]
    icc_tournament_record: dict
    statistical_reliability: str


class DomesticT20StatsSchema(TypedDict):
    league: str           # wpl / wbbl / hundred / wt20_challenge
    matches: int
    batting: Optional[BattingStatsSchema]
    bowling: Optional[BowlingStatsSchema]


class FitnessSchema(TypedDict):
    status: str           # FitnessStatus value
    notes: Optional[str]
    last_updated: str     # ISO date


# ---------------------------------------------------------------------------
# Top-level schemas — these map directly to JSON files
# ---------------------------------------------------------------------------

class PlayerSchema(TypedDict):
    id: str                              # snake_case unique ID e.g. "smriti_mandhana"
    name: str
    team: str                            # TeamID value
    role: str                            # PlayerRole value
    batting_hand: str                    # BattingHand value
    bowling_hand: Optional[str]          # BattingHand value, null if non-bowler
    bowling_style: Optional[str]         # BowlingStyle value
    caps: int                            # T20I caps
    t20i_stats: dict                     # BattingStatsSchema + BowlingStatsSchema
    domestic_t20: list[DomesticT20StatsSchema]
    fitness: FitnessSchema
    notes: Optional[str]                 # analyst qualitative notes


class TeamPhasePerformanceSchema(TypedDict):
    avg_score: float
    avg_wickets_lost: float
    run_rate: float
    economy: float                       # bowling economy in this phase
    wickets_taken_per_match: float


class TeamSchema(TypedDict):
    id: str                              # TeamID value
    name: str
    group: str                           # Group value
    icc_ranking: int
    captain: str                         # player ID
    coach: str
    batting_phase_performance: dict[str, TeamPhasePerformanceSchema]
    bowling_phase_performance: dict[str, TeamPhasePerformanceSchema]
    batting_first: dict                  # matches, wins, avg_score, avg_winning_score
    chasing: dict                        # matches, wins, avg_target, avg_winning_score
    toss: dict                           # won, elected_bat, elected_field
    h2h: dict                            # keyed by opponent TeamID: matches, wins, losses
    last_12_months: dict                 # matches, wins, losses, nrr
    set_plays: list[str]                 # known tactical tendencies
    weak_links: list[str]                # batting positions that collapse


class VenueDimensionsSchema(TypedDict):
    straight_boundary_m: int
    square_boundary_m: int
    oval: bool


class VenuePitchSchema(TypedDict):
    type: str                            # PitchType value
    pace_advantage: bool
    spin_advantage: bool
    notes: str


class VenueConditionsSchema(TypedDict):
    dew_factor: str                      # DewFactor value
    typically_day_night: bool
    avg_humidity_pct: int


class VenueT20StatsSchema(TypedDict):
    matches_played: int
    avg_first_innings_score: int
    avg_winning_chase_score: int
    toss_impact: dict                    # bat_first_win_pct, field_first_win_pct
    pace_economy: float
    spin_economy: float
    highest_score: int
    lowest_defended: int


class VenueSchema(TypedDict):
    id: str                              # VenueID value
    name: str
    city: str
    country: str
    capacity: int
    dimensions: VenueDimensionsSchema
    pitch: VenuePitchSchema
    conditions: VenueConditionsSchema
    women_t20_stats: VenueT20StatsSchema
    notes: str


class MatchSchema(TypedDict):
    id: str                              # "m001", "m002", ...
    date: str                            # ISO date
    time_local: str                      # "14:30 BST"
    day_night: bool
    team_a: str                          # TeamID value
    team_b: str                          # TeamID value
    venue_id: str                        # VenueID value
    stage: str                           # TournamentStage value
    group: Optional[str]                 # Group value — null for knockouts
    nrr_implications: Optional[str]      # human-readable NRR context


class ScheduleSchema(TypedDict):
    tournament: str
    host: str
    start_date: str
    final_date: str
    format: str
    groups: dict[str, list[str]]         # group label → list of TeamID values
    venues: list[str]                    # list of VenueID values
    matches: list[MatchSchema]


class MatchupSchema(TypedDict):
    batter_id: str
    bowler_id: str
    balls_faced: int
    runs: int
    dismissals: int
    strike_rate: float
    dot_ball_pct: float
    boundary_pct: float
    by_phase: dict[str, dict]            # powerplay / middle / death sub-stats
    statistical_reliability: str         # StatisticalReliability value
    last_updated: str                    # ISO date of most recent match included


# ---------------------------------------------------------------------------
# Live match state input contract
# ---------------------------------------------------------------------------

class BatterAtCreaseSchema(TypedDict):
    player_id: str
    runs_scored: int
    balls_faced: int
    strike_rate: float
    on_strike: bool


class BowlerCurrentSpellSchema(TypedDict):
    player_id: str
    overs_this_spell: float
    runs_this_spell: int
    wickets_this_spell: int
    economy_this_spell: float
    overs_remaining_quota: float         # 4 - overs already bowled in match


class LiveMatchStateSchema(TypedDict):
    match_id: str
    batting_team: str                    # TeamID value
    bowling_team: str                    # TeamID value
    innings: int                         # 1 or 2
    over: int                            # current over number (0-indexed)
    ball: int                            # ball within over (0-5)
    score: int
    wickets: int
    target: Optional[int]                # null in 1st innings
    required_run_rate: Optional[float]
    current_run_rate: float
    batters_at_crease: list[BatterAtCreaseSchema]
    current_bowler: BowlerCurrentSpellSchema
    overs_bowled_by: dict[str, float]    # player_id → overs bowled this match
    phase: str                           # Phase value
    dew_active: bool
    momentum_last_3_overs: float         # runs per over in last 3 overs
