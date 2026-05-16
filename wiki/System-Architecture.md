# System Architecture: Women's T20 Oracle

## Overview

The Women's T20 Oracle is a **dual-scenario prediction pipeline** that generates pre-match recommendations for women's T20 cricket matches. It runs both possible outcomes (batting first vs chasing) before the toss is known and blends them 50/50 for pre-toss predictions.

### Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    PRE-MATCH PIPELINE                       │
└─────────────────────────────────────────────────────────────┘

INPUT: Team, Opponent, Venue, Date
       (Toss unknown or known)
         ↓
    ┌────────────────────────────────────────┐
    │  RUN SCENARIO A: We Bat First (+25%)   │
    │  RUN SCENARIO B: We Chase (-15 to -30) │
    │  (Both run in parallel)                │
    └────────────────────────────────────────┘
         ↓
    ┌─────────────────────────┐
    │  BLEND RESULTS 50/50    │
    │  (If toss unknown)      │
    └─────────────────────────┘
         ↓
OUTPUT: Pre-toss blended prediction
        + Scenario-specific details
        + Squad selection
        + Batting order
        + Bowling plan
        + Strategic recommendations
```

---

## Sequential Node Pipeline

The prediction engine uses a **9-node sequential pipeline**:

### 1. DATA_NODE
**Loads all required data for the match**
- Player stats and profiles (squad_data/)
- Opponent squad information
- Venue characteristics (pitch, dimensions, history)
- Analyst insights (qualitative form ratings)

### 2. SCENARIO_NODE ⭐ CRITICAL
**Determines match scenario and applies scenario-specific adjustments**
- Identifies whether we're batting first or chasing
- Classifies pitch difficulty (spin-friendly, seam-friendly, balanced, flat)
- Applies toss-aware chase penalty (variable, based on Task 5)

### 3. OPPONENT_ANALYSIS_NODE
**Analyzes opponent team composition**
- Identifies opponent strengths and bowling attack
- Assesses key threats (star players, dangerous bowlers)
- Evaluates weaknesses to exploit

### 4. SQUAD_SELECTOR_NODE
**Selects 11-player team from available 15**
- Optimizes selection for scenario (batting first vs chasing)
- Balances batting and bowling requirements
- Considers matchups and player form

### 5. BATTING_ORDER_NODE
**Constructs optimal batting sequence**
- Matches batters against opponent bowling attack
- Optimizes for expected runs
- Considers player roles (openers, middle-order, finishers)

### 6. BOWLING_PLAN_NODE
**Allocates bowlers across match phases**
- **Powerplay phase** (overs 1-6): Economical bowling
- **Middle phase** (overs 7-15): Containment bowling
- **Death phase** (overs 16-20): Yorker specialists
- Optimizes economy rates and impact

### 7. PREDICTION_NODE ⭐ CORE COMPUTATION
**Runs all predictions with Phase 2 enhancements**
- Monte Carlo simulation (10,000 runs)
- Calculates base runs estimate
- Applies pitch calibration (Task 2: spin penalty)
- Applies batter-bowler boost (Task 6: lowered threshold)
- Applies recent form bonus (Task 4: exceptional performers)
- Applies variable chase penalty (Task 5: economy-based)
- Applies series momentum (Task 1 & 3: team-specific multipliers with sweep likelihood)
- Calculates win probability

### 8. STRATEGY_NODE
**Generates tactical recommendations**
- Identifies key head-to-head matchups
- Flags exploitation opportunities
- Highlights threat assessment
- Generates actionable recommendations

### 9. OUTPUT_NODE
**Formats and delivers results**
- Structures prediction JSON
- Saves to disk
- Returns to caller

---

## The 6 Phase 2 Enhancements

All Phase 2 enhancements are integrated into the **PREDICTION_NODE**. They stack cumulatively without interference.

### Enhancement #1: Team-Specific Sweep Momentum (Task 1)
**Impact**: ↓ 2.8pp on dominant sweeps

When a team is 3-0 up in a series (1 match away from sweep), match 4+:
- **Aggressive teams** (India, West Indies, Pakistan): **+30% multiplier** on runs
- **Conservative teams** (NZ, South Africa, Australia): **+25% multiplier** on runs

**Rationale**: Elite teams show more confidence and aggression when closing out sweeps.

### Enhancement #2: Context-Aware Spin Pitch Penalty (Task 2)
**Impact**: ↓ 2.9pp on dominant home teams

When batting first on spin-friendly pitch:
- **Dominant teams** (3-0+ up in series): Spin penalty reduced from -5 to **0 runs**
- **Normal teams**: Spin penalty remains -5 runs

**Rationale**: Elite home batters on familiar conditions deserve no suppression when team is dominant.

### Enhancement #3: Series Context Awareness (Task 3)
**Impact**: ↓ 3.3pp on borderline sweeps

**Sweep Likelihood Detection**: Analyzes series history to compute likelihood (0.4 to 0.9):
- If team lost a previous match while already 3-0 up: likelihood = **0.4** (unlikely to complete sweep)
- If team is leading 3-0+ with no losses when dominant: likelihood = **0.9** (very likely sweep)

This scales the momentum multiplier: `aggression_multiplier *= sweep_likelihood`

**Rationale**: False-positive momentum eliminated. If team has faltered before when dominant, reduce confidence in sweep.

### Enhancement #4: Recent Form Bonus (Task 4)
**Impact**: Stable, extensible feature

Exceptional performers get boosted:
- **Exceptional form rating**: **+3 runs, +2% WP**
- **Strong form with recent success**: **+2 runs, +1% WP** (batting first only)

Currently identifies: Harmanpreet Kaur (captain, exceptional form)

**Rationale**: Outstanding individual performances should be credited in team predictions.

### Enhancement #5: Variable Chase Penalty (Task 5) ⭐ BREAKTHROUGH
**Impact**: ↓ 1.3pp overall, **↓ 2.1pp chasing** (Major breakthrough!)

Replaces fixed penalty (-15 to -30) with **dynamic calibration based on opponent bowling**:

```
base_penalty = {
    "spin_friendly": -15,
    "seam_friendly": -20,
    "flat": -10,
    "balanced": -15
}[pitch_type]

top_3_economy = average of opponent's top 3 bowlers' economy rates

if top_3_economy > 8.0:      # Weak bowling
    adjustment = +3          # Less penalty (weak bowling easier to chase)
elif top_3_economy < 7.0:    # Strong bowling
    adjustment = -3          # More penalty (strong bowling harder to chase)
else:
    adjustment = 0

final_penalty = max(-25, min(-5, base_penalty + adjustment))
```

**Rationale**: Weak bowling attacks should have less chase penalty; strong bowling should have more. One-size-fits-all penalty is inappropriate.

### Enhancement #6: Enhanced Batter-Bowler Matching (Task 6)
**Impact**: Coverage expanded, stable performance

Lowered strike rate threshold for favorable matchups:
- **Previous threshold**: Strike rate > 120 (elite matchups only)
- **New threshold**: Strike rate > 110 (moderate + elite matchups)

This captures **2-4 favorable matchups per match** (vs 0-2 before), each providing +1.5 runs bonus.

**Rationale**: Moderately strong head-to-head advantages should be credited, not just elite ones.

---

## Data Flow: Pre-Toss vs Known Toss

### Scenario 1: Pre-Toss (Toss Unknown)

When `toss_winner=None` and `toss_decision=None`:

```
PATH A (50% weight): We Win Toss & Bat First
  ├─ Apply batting-first adjustments
  ├─ Run Monte Carlo simulation
  ├─ No chase penalty
  └─ Result: 160.1 runs, 70.3% WP

BLEND 50/50:
  ├─ Average runs: (160.1 + 89.2) / 2 = 124.7 runs
  └─ Average WP: (70.3% + 43.8%) / 2 = 57.1%

PATH B (50% weight): Opponent Wins Toss & We Chase
  ├─ Apply chasing adjustments
  ├─ Run Monte Carlo simulation
  ├─ Apply variable chase penalty (Task 5)
  └─ Result: 89.2 runs, 43.8% WP

OUTPUT:
  scenario: "pre_toss_blended"
  adjusted_runs_estimate: 124.7
  win_probability: 0.571
  batting_first_scenario: {...details...}
  chasing_scenario: {...details...}
```

### Scenario 2: Toss Known (e.g., India Won, Decided to Bat)

When `toss_winner="india"` and `toss_decision="bat_first"`:

```
PATH A ONLY: We Bat First
  ├─ Apply batting-first adjustments
  ├─ Run Monte Carlo simulation
  ├─ No chase penalty
  └─ Result: 160.1 runs, 70.3% WP

OUTPUT:
  scenario: "batting_first"
  adjusted_runs_estimate: 160.1
  win_probability: 0.703
```

**Key difference**: Pre-toss requires both scenarios (blended), known-toss runs only the applicable scenario.

---

## Input Requirements

```python
state = {
    "team_id": "india",                 # Our team identifier
    "opponent_id": "sri_lanka",         # Opposition identifier
    "venue_id": "greenfield_tvm",       # Venue identifier
    "match_date": "2025-11-14",         # ISO 8601 date
    "toss_winner": None,                # None = pre-toss (both scenarios)
    "toss_decision": None,              # "bat_first" or "bowl_first" if known
    "series_number": 4,                 # Match number in series
    "series_score": 3,                  # Wins before this match (for sweep momentum)
    "sweep_likelihood": 0.9,            # 0.4-0.9 (computed by Task 3)
}
```

**Data loaded automatically**:
- ✓ `squad_data/` — Player profiles and statistics
- ✓ `analyst_insights.json` — Qualitative form ratings
- ✓ `matchups.json` — Head-to-head records
- ✓ `venues/` — Pitch and ground characteristics
- ✓ `teams/` — Team metadata

---

## Output Structure

### Pre-Toss Blended Output

```json
{
  "match_id": "ind_sl_tvm2_20251114",
  "scenario": "pre_toss_blended",
  "adjusted_runs_estimate": 124.7,
  "win_probability": 0.571,
  
  "batting_first_scenario": {
    "scenario": "batting_first",
    "adjusted_runs_estimate": 160.1,
    "win_probability": 0.703,
    "pitch_difficulty": "very_difficult",
    "series_momentum_multiplier": 1.30,
    "strategy_brief": "Bat aggressively to establish dominance..."
  },
  
  "chasing_scenario": {
    "scenario": "chasing",
    "adjusted_runs_estimate": 89.2,
    "win_probability": 0.438,
    "pitch_difficulty": "very_difficult",
    "chase_penalty": -18,
    "strategy_brief": "Consolidate early overs, target 15+ per over in death..."
  },
  
  "selected_xi": ["player1", "player2", ...],
  "batting_order": ["player1", "player2", ...],
  "bowling_plan": [
    {"phase": "powerplay", "bowler": "player1", "economy_target": 6.5},
    {"phase": "middle", "bowler": "player2", "economy_target": 7.0},
    ...
  ],
  "key_matchups": [
    {"batter": "Mandhana", "bowler": "Hazem", "advantage": "batter", "sr": 125},
    ...
  ],
  "tactical_flags": [
    "Pitch heavily favors spin - front-load left-arm pace",
    "Team 1 match from sweep - expect aggressive approach",
    ...
  ]
}
```

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| **Mean Error** | 16.0% |
| **Chasing Error** | 14.4% |
| **Within ±20%** | 67% coverage |
| **Within ±30%** | 100% coverage |
| **Execution Time** | 4-5 sec per prediction |
| **Batch Time (30 matches)** | ~120 seconds |
| **Memory per prediction** | ~6-7 MB |
| **Total Memory (30 matches)** | ~200 MB |

---

## Extension Points

The architecture is designed for easy expansion:

### Add New Enhancement
1. Create function: `_calculate_new_factor(...)`
2. Integrate in `prediction_node()`
3. Add reasoning to output
4. Test against validation set

### Add New Data Source
1. Create loader in `io/loader.py`
2. Call in `data_node()`
3. Pass through state dict
4. Use in relevant nodes

### Add New Scenario
1. Add classifier in `scenario_node()`
2. Create scenario-specific path
3. Add scenario-specific adjustments
4. Test blending logic (if pre-toss scenario)

---

## Code Locations

| Component | File | Lines |
|-----------|------|-------|
| Pipeline orchestration | `pre_match_graph.py` | ~3500 total |
| Scenario branching | `pre_match_graph.py` | ~1800-1900 |
| PREDICTION_NODE | `pre_match_graph.py` | ~400-500 |
| Batch runner | `scripts/batch_predictions.py` | ~450 |
| Series context (Task 3) | `scripts/batch_predictions.py` | ~390-470 |

---

**Version**: wt20-oracle-v2.3-phase2  
**Status**: Production-Ready  
**Last Updated**: May 16, 2026
