# Retraining & Recalibration Policy
## Feedback Loop for Continuous Model Improvement

---

## 1. Core Philosophy

This is a **prediction & prescriptive engine**, not an exact forecasting system.

**Key Principles**:
- Accuracy is measured on **KEY DECISION NODES**, not overall metrics
- Retraining is **continuous & incremental**, not batch/periodic
- Each actual result feeds back into model recalibration
- Focus on **directional correctness** over point accuracy
- Validate on **holdout matches** to prevent overfitting

---

## 2. Key Decision Nodes (Priority Hierarchy)

### **TIER 1: Match Outcome** (Critical)
- **Node**: Winner prediction (binary: team1 wins or team2 wins)
- **Metric**: Win prediction accuracy (0-100%)
- **Target**: 65%+ accuracy on winner prediction
- **Impact**: Highest business value (determines strategy)
- **Retraining Trigger**: Miss on winner prediction

### **TIER 2: Score Range** (High)
- **Node**: Expected runs ± margin
- **Metric**: Prediction within ±10% of actual
- **Target**: 80%+ predictions within ±10 runs
- **Impact**: Determines chasing strategy, required run rate
- **Retraining Trigger**: Consecutive misses >15 run error

### **TIER 3: Key Decision Factors** (High)
- **Nodes**: 
  - Toss impact (bat first vs chase)
  - Pitch difficulty (favorable vs challenging)
  - Squad composition (11-player XI selection)
- **Metrics**: Factor-specific accuracy
- **Target**: 70%+ accuracy per factor
- **Impact**: Enables prescriptive recommendations
- **Retraining Trigger**: Systematic bias detected

### **TIER 4: Player Performance** (Medium)
- **Node**: Key player runs/wickets
- **Metric**: Within ±15% of actual performance
- **Target**: 75%+ accuracy on key players
- **Impact**: Supports squad strategy
- **Retraining Trigger**: 2 consecutive major misses

### **TIER 5: Match Structure** (Low)
- **Nodes**: Phase-wise breakdown (powerplay, middle, death)
- **Metric**: Phase accuracy within ±15% per phase
- **Target**: 70%+ per phase
- **Impact**: Narrative/educational value
- **Retraining Trigger**: Directional errors (e.g., death overs much higher)

---

## 3. Retraining Data Windows

### **Rolling Window Approach**

```
MATCH DATA POOL FOR RETRAINING:

├─ Immediate: Last 5 matches (Days 0-30)
│  └─ Weight: 100% (highest)
│  └─ Use: Detect recent form changes, seasonal patterns
│
├─ Recent: Last 10-20 matches (Days 30-90)
│  └─ Weight: 80% (high)
│  └─ Use: Confirm patterns, validate emergent trends
│
├─ Historical: Last 50-100 matches (Days 90-365)
│  └─ Weight: 50% (moderate)
│  └─ Use: Base patterns, stable characteristics
│
└─ Archive: >365 days old
   └─ Weight: 0% (exclude)
   └─ Reason: Player forms change, conditions differ
```

### **Why Rolling Window?**
- **Recent matches** capture form, injuries, recent learnings
- **Historical matches** provide statistical stability
- **Old data** introduces noise (players retire, teams change style)
- **Weights** prevent recent flukes from overriding patterns

---

## 4. Retraining Triggers & Procedures

### **Trigger A: Outcome Prediction Miss on Winner** (Critical)

**When**: Prediction says Team A wins, but Team B actually wins

**Immediate Action** (within 24 hours):
```
Step 1: Root Cause Analysis
├─ Was it a scenario dependency (toss, batting first)?
├─ Was it a form modifier misalignment?
├─ Was it a pitch characteristic error?
└─ Was it external factor (weather, injury)?

Step 2: Identify Affected Parameter
├─ Confidence scoring (too high?)
├─ Win probability calculation (systematic bias?)
├─ Key decision node weighting (wrong emphasis?)
└─ Form modifiers (not reflecting actual form?)

Step 3: Quantify Impact
├─ Error magnitude (5% vs 50% confidence error?)
├─ Frequency (first occurrence or repeated?)
├─ Root cause category (model gap vs data gap?)
└─ Preventability (could we have known pre-match?)
```

**Recalibration Decision**:
- **If root cause identified**: Adjust specific parameter immediately
- **If pattern confirmed**: Add constraint/rule (e.g., "apply chase penalty")
- **If first occurrence**: Log & monitor, retrain after 2nd similar miss
- **If systematic bias**: Urgent recalibration across affected component

### **Trigger B: Score Prediction Error >15 Runs** (High)

**When**: Predicted 162, actual was 132 or 190 (deviation >15)

**Action**:
```
Step 1: Error Decomposition
├─ Scenario error (batting first vs chase)
├─ Pitch assessment error
├─ Batter performance error
├─ External factor (weather, dew)
└─ Multiple errors combined

Step 2: Recalibration
├─ Adjust pitch modifiers for this venue
├─ Update form modifiers for affected batters
├─ Recalibrate phase-wise scoring model
└─ Add scenario-specific adjustments

Step 3: Validation
├─ Test on holdout matches (next 2-3 predictions)
├─ Verify error range improves to <10 runs
└─ Confirm no other metrics degraded
```

### **Trigger C: Systematic Pattern Detected** (High)

**When**: 3+ consecutive errors show same pattern

**Example Patterns**:
- "Chasing predictions always 15 runs too high"
- "Pitch-friendly assessments off by 1-2 hardness points"
- "Form modifiers underestimate star players by 10%"

**Action**:
```
Step 1: Confirm Pattern
├─ Verify across 3+ matches
├─ Check if pattern affects specific venues/teams
├─ Quantify direction & magnitude

Step 2: Root Cause
├─ Is it a model bias?
├─ Is it a data collection issue?
├─ Is it a structural gap?

Step 3: Systematic Fix
├─ Update formula/coefficient
├─ Add correction factor
├─ Introduce new variable if needed

Step 4: Validate
├─ Apply to all historical matches
├─ Verify improvement on test set
├─ Check no new biases introduced
```

---

## 5. Recalibration Parameters (By Component)

### **A. Winner Prediction**

**Parameters to Recalibrate**:
```
win_probability = f(
  venue_factor,           ← Adjust if pitch assessment off
  form_modifiers,         ← Update for each player
  head_to_head,          ← Add recent H2H data
  confidence_scoring,    ← Reduce if too optimistic
  scenario_penalty       ← NEW: Add first/chase penalty
)
```

**Recalibration Window**: After each win prediction miss
**Data Source**: Gap analysis from match validation
**Validation**: Test on next 3 upcoming matches before deploy

### **B. Runs Prediction**

**Parameters to Recalibrate**:
```
expected_runs = phase_breakdown × form_modifiers × pitch_modifiers × scenario_multiplier

Components to recalibrate:
├─ phase_breakdown      (powerplay/middle/death scoring)
├─ form_modifiers       (per-player recent form)
├─ pitch_modifiers      (venue hardness, pace, spin)
└─ scenario_multiplier  (first inning +5%, chase -20%)
```

**Recalibration Window**: After each 15+ run error
**Validation Method**: MAE (Mean Absolute Error) must improve
**Prevent Overfitting**: Keep historical average as baseline, don't drift >10% from base

### **C. Squad Selection**

**Parameters to Recalibrate**:
```
squad_confidence = historical_selection_pattern × recent_form × injury_status × pitch_match

Recalibrate when:
├─ Prediction miss >2 players
├─ Same player repeatedly mispredicted
├─ Tactical pattern emerges (e.g., captain always swaps spinner for pacer on pace pitches)
```

**Data Window**: Last 20 matches for this team + venue combination
**Update Frequency**: After every 2 squad selection misses

### **D. Form Modifiers**

**Parameters to Recalibrate**:
```
form_modifier = base_average × recent_form_window × current_game_type

Recent form window:
├─ Last 5 matches: Weight 100%
├─ Last 5-10 matches: Weight 60%
├─ Last 10-20 matches: Weight 30%
└─ Season average: Weight 10% (anchor)
```

**Recalibration Trigger**: After 3+ consecutive predictions with >±15 run error for same player
**Update Data**: Last 5 completed matches with actual performance data

### **E. Pitch Characteristics**

**Parameters to Recalibrate**:
```
pitch_score = (hardness + grass_coverage + bounce + pace_friendly) / 4

Update when:
├─ First match at venue: Use base values
├─ Subsequent matches: Refine based on actual behavior
├─ 5+ matches: Recalibrate full profile
```

**Data Source**: Actual match results + surface observations
**Confidence**: Increase after 3+ data points

---

## 6. Validation & Holdout Strategy

### **Holdout Set: Never Retrain On**

```
Matches to EXCLUDE from retraining:
├─ Current match (being validated)
├─ Next 2 scheduled matches (test set)
└─ Random 10% of historical matches (validation set)
```

**Why**: Prevent overfitting by testing on unseen data

### **Testing Procedure After Recalibration**

```
Step 1: Apply recalibration to historical matches (not used in retraining)
Step 2: Calculate accuracy on this holdout set
Step 3: Compare:
       Original model: X% accuracy
       Recalibrated model: Y% accuracy
Step 4: If Y > X + 3%: Deploy
        If Y < X: Revert recalibration
        If Y ≈ X: Use original (no improvement)
```

**Minimum Improvement Threshold**: 3% accuracy gain
**Rollback Condition**: Any drop in accuracy

---

## 7. Retraining Frequency & Cadence

### **Continuous Stream**

```
Per Match Completed:
├─ T+0h: Actual result obtained
├─ T+2h: Gap analysis completed
├─ T+4h: Root cause identified
├─ T+6h: Decision to recalibrate or not
├─ T+8h: If recalibrating, apply changes
├─ T+10h: Validate on next 3 matches
├─ T+24h: Deploy if validated, else revert

Per 5 Matches:
├─ Aggregate error patterns
├─ Confirm systematic biases
├─ Make high-confidence recalibrations

Per 20 Matches:
├─ Full model audit
├─ Identify underperforming components
├─ Plan structural improvements
├─ Update data windows
```

### **No Batch Retraining**
- ❌ Don't wait for 50 matches to retrain
- ✓ Retrain incrementally after each match
- ✓ Small adjustments compound over time
- ✓ Detect patterns early before they become biases

---

## 8. Decision Rules for Retraining

### **Decision Matrix**

| Error Type | Magnitude | Frequency | Action | Urgency |
|-----------|-----------|-----------|--------|---------|
| Winner prediction miss | Any | 1st occurrence | Log & monitor | Low |
| Winner prediction miss | Any | 2nd occurrence | Urgent RCA | Critical |
| Runs error | 10-15 runs | 1st | Analyze | Medium |
| Runs error | 10-15 runs | 2nd-3rd | Recalibrate | High |
| Runs error | >15 runs | Any | Immediate RCA | Critical |
| Systematic pattern | <10% drift | Confirmed | Batch update | Medium |
| Systematic pattern | >10% drift | Confirmed | Urgent recalibration | High |
| Form modifier | 20+ run error | 2+ times | Update per-player | Medium |
| Pitch assessment | 2+ venue misses | Same venue | Recalibrate venue | High |
| Squad selection | 3+ player misses | Any | Review pattern | Medium |

---

## 9. Prevent Overfitting: Guard Rails

### **Rule 1: Never Overfit to Single Match**
```
❌ Bad: "India collapsed once, so apply -25 run penalty forever"
✓ Good: "India collapsed once, monitor for pattern, confirm on 2nd similar case"
```

### **Rule 2: Maintain Historical Baseline**
```
Form modifier drift guard:
├─ Don't let modifier change >±0.15 from base
├─ If drift detected, increase data window
├─ Use weighted average (recent 60%, historical 40%)
```

### **Rule 3: Require Confirmation Before Deployment**
```
After recalibration:
├─ Must pass validation on holdout set
├─ Must show 3%+ accuracy improvement
├─ Must not degrade other metrics
└─ Require 2 consecutive improvements before full deploy
```

### **Rule 4: Limit Parameter Changes Per Cycle**
```
Per recalibration cycle:
├─ Change max 3-5 parameters
├─ Don't over-adjust (max ±5% per parameter)
├─ If >2 parameters need changes, flag for audit
├─ Multiple issues suggest structural gap, not parameter drift
```

---

## 10. Metrics to Track During Retraining

### **Per-Component Accuracy Tracking**

```
Dashboard Metrics:

WINNER PREDICTION
├─ Current accuracy: ___% (last 20 matches)
├─ Target accuracy: 65%+
├─ Direction: ⬆/⬇/→
├─ Confidence interval: ±__%
└─ Last adjustment: _____ (date)

RUNS PREDICTION
├─ Current MAE: ±___ runs (absolute error)
├─ Current MAPE: ___% (percentage error)
├─ Target: <±10 runs
├─ Within ±10 runs: ___%
└─ Last adjustment: _____ (date)

SQUAD SELECTION
├─ Current accuracy: ___% (correct XI prediction)
├─ Target: 85%+
├─ Common misses: _____
└─ Last adjustment: _____ (date)

FORM MODIFIERS
├─ Outliers (>±20 run error): ___
├─ Average drift from base: ±___%
├─ Players needing updates: _____
└─ Last adjustment: _____ (date)
```

---

## 11. Documentation & Change Log

### **Every Recalibration Must Record**

```json
{
  "recalibration_id": "REC_20260427_001",
  "match_id": "india_vs_sa_20260427",
  "recalibration_date": "2026-04-27T22:30:00Z",
  "trigger": "Winner prediction miss (India predicted, SA actual)",
  "root_cause": "Toss dependency not modeled + chase penalty missing",
  "parameters_changed": [
    {
      "parameter": "win_probability_confidence",
      "old_value": "55%",
      "new_value": "50%",
      "reason": "Over-confident on India before toss"
    },
    {
      "parameter": "chase_penalty_multiplier",
      "old_value": "0%",
      "new_value": "-20 runs",
      "reason": "Chasing is systematically harder than batting first"
    }
  ],
  "validation_result": "Tested on next 3 matches, 85% accuracy improvement",
  "deployed": true,
  "deployed_date": "2026-04-28T08:00:00Z"
}
```

**Purpose**: 
- Audit trail of all changes
- Detect if recalibrations conflict
- Track what worked vs didn't work
- Machine learning input for future automation

---

## 12. Special Cases

### **Case A: New Team/Venue**
```
First prediction for team/venue combination:
├─ Use generic/regional baseline
├─ Mark confidence as "Low"
├─ After 1st match: Recalibrate team/venue factors
├─ After 3rd match: Establish reliable patterns
├─ After 5th match: Full model calibration
```

### **Case B: Injured/Returning Player**
```
Major player changes:
├─ Reduce confidence on squad selection (mark as "TBD")
├─ Use last available form modifier
├─ After 1st match with new player: Recalibrate
├─ Monitor for 3 matches before stabilizing
```

### **Case C: Seasonal/Format Changes**
```
Inter-season gaps or format change:
├─ Reduce data window (use recent 20 matches max)
├─ Recalibrate all form modifiers
├─ Treat old data as reference only (10% weight)
├─ Increase retraining frequency for first 10 matches
```

---

## 13. Success Metrics for Retraining Program

### **Quarterly Assessment**

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Winner accuracy (rolling 20 matches) | 65%+ | ___% | ⬆/⬇ |
| Runs prediction MAE | <±10 runs | ±___ | ⬆/⬇ |
| Squad selection accuracy | 85%+ | ___% | ⬆/⬇ |
| Systematic pattern detection | <3 per 20 matches | ___ | ⬆/⬇ |
| Recalibration success rate | 80%+ | ___% | ⬆/⬇ |
| Time to recalibrate | <24h | ___h | ⬆/⬇ |
| Overfitting incidents | 0 | ___ | ⬆/⬇ |

**Quarterly Review**:
- If trending up → System is learning, improving
- If plateaued → Structural changes needed, not parameter tuning
- If trending down → Retraining causing overfitting, revert to baseline

---

## Summary: The Retraining Loop

```
CONTINUOUS FEEDBACK LOOP:

Match Played
    ↓
Actual Result Obtained
    ↓
Gap Analysis (vs prediction)
    ↓
Root Cause Analysis
    ↓
Decision: Recalibrate? YES/NO
    ↓
IF YES:
├─ Identify parameters to adjust
├─ Make changes (max 3-5 per cycle)
├─ Validate on holdout set
├─ If +3% improvement: Deploy
├─ If no improvement: Revert
└─ Log change in audit trail
    ↓
IF NO: Log reasoning & monitor for pattern
    ↓
Next Match Uses Updated Model
    ↓
[LOOP REPEATS]
```

This ensures continuous improvement without overfitting or structural degradation.
