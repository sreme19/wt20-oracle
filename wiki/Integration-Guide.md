# Integration Guide: Using Women's T20 Oracle Predictions

This guide shows how to integrate predictions into your code and use them for decision-making.

---

## Quick Start: Load a Prediction

```python
import json

# Load prediction for a specific match
match_id = "ind_sl_tvm2_20251114"
with open(f"matches/{match_id}/prediction/prediction.json") as f:
    prediction = json.load(f)

# Basic prediction data
runs = prediction["adjusted_runs_estimate"]              # 124.7 runs
win_prob = prediction["win_probability"]                # 0.571 (57.1%)
scenario = prediction["scenario"]                       # "pre_toss_blended"
```

---

## Scenario-Specific Access

### Pre-Toss Prediction (Toss Unknown)

When toss hasn't been decided yet:

```python
# Pre-toss blended prediction (50/50 both scenarios)
blended_runs = prediction["adjusted_runs_estimate"]     # 124.7
blended_wp = prediction["win_probability"]              # 0.571

# Scenario-specific details
batting_first = prediction["batting_first_scenario"]
chasing = prediction["chasing_scenario"]

print(f"If we bat first: {batting_first['adjusted_runs_estimate']:.1f} runs")
print(f"If we chase: {chasing['adjusted_runs_estimate']:.1f} runs")

# Decision logic
if batting_first["win_probability"] > 0.65:
    print("Prefer to bat first if we win toss")
elif chasing["win_probability"] > 0.65:
    print("Prefer to bowl first if we win toss")
else:
    print("Either decision viable")
```

### Known-Toss Prediction (Toss Decided)

When toss is already known:

```python
# Load prediction where toss was known (e.g., India won, decided to bat)
# Prediction will have only one scenario (no blending)

scenario_type = prediction["scenario"]  # "batting_first" or "chasing"

if scenario_type == "batting_first":
    runs = prediction["adjusted_runs_estimate"]         # Deterministic
    wp = prediction["win_probability"]                  # Deterministic
    print(f"Expected: {runs:.1f} runs, {wp:.1%} win probability")
else:
    print("We're chasing...")
```

---

## Strategic Recommendations

### Squad Selection

```python
# Get recommended 11-player team
selected_xi = prediction["selected_xi"]
print(f"Recommended XI: {', '.join(selected_xi)}")

# Check composition
batters = sum(1 for p in selected_xi if player_type(p) == "batter")
bowlers = sum(1 for p in selected_xi if player_type(p) == "bowler")
print(f"Composition: {batters} batters, {bowlers} bowlers")
```

### Batting Order

```python
# Get recommended batting order
batting_order = prediction["batting_order"]

print("Recommended Batting Order:")
for i, player in enumerate(batting_order, 1):
    print(f"  {i}. {player}")

# Customize based on conditions
if prediction["scenario"].includes("chasing"):
    print("Adjust for chase: be aggressive if targets achievable")
else:
    print("Adjust for bat first: accelerate in middle overs")
```

### Bowling Plan

```python
# Get bowling assignments by phase
bowling_plan = prediction["bowling_plan"]

print("Bowling Plan by Phase:")
for phase_info in bowling_plan:
    phase = phase_info["phase"]              # "powerplay", "middle", "death"
    bowler = phase_info["bowler"]
    economy = phase_info.get("economy_target")
    print(f"  {phase.title()}: {bowler} (target {economy:.1f} economy)")
```

---

## Matchup Analysis

### Key Batter-Bowler Matchups

```python
# Get identified favorable matchups
key_matchups = prediction["key_matchups"]

favorable = [m for m in key_matchups if m["advantage"] == "batter"]
threats = [m for m in key_matchups if m["advantage"] == "bowler"]

print(f"Favorable Matchups ({len(favorable)}):")
for match in favorable:
    sr = match.get("strike_rate", "N/A")
    print(f"  {match['batter']} vs {match['bowler']} (SR: {sr})")

print(f"\nThreat Matchups ({len(threats)}):")
for match in threats:
    eco = match.get("economy", "N/A")
    print(f"  {match['bowler']} vs {match['batter']} (Economy: {eco})")
```

### Matchup-Based Strategy

```python
# Exploit favorable matchups
for matchup in favorable:
    batter = matchup["batter"]
    bowler = matchup["bowler"]
    sr = matchup["strike_rate"]
    
    if sr > 120:
        print(f"EXPLOIT: {batter} against {bowler} (SR {sr})")
        print(f"  → Play aggressive, build momentum")
    elif sr > 110:
        print(f"ADVANTAGE: {batter} against {bowler} (SR {sr})")
        print(f"  → Press advantage, score runs")

# Mitigate threat matchups
for threat in threats:
    bowler = threat["bowler"]
    batter = threat["batter"]
    
    print(f"THREAT: {bowler} vs {batter}")
    print(f"  → Bat second, let others face this bowler")
```

---

## Tactical Recommendations

### Contextual Flags

```python
# Get tactical recommendations
flags = prediction["tactical_flags"]

print("Tactical Considerations:")
for i, flag in enumerate(flags, 1):
    print(f"  {i}. {flag}")

# Example flags might include:
#   - "Pitch heavily favors spin - use left-arm pace"
#   - "Team 1 match from sweep - expect aggressive approach"
#   - "Opponent has weak middle overs - target 15+ RPO 7-15"
#   - "Weather forecast: dew expected - prioritize pace bowlers"
```

---

## Phase 2 Enhancement Details

### Understanding Enhancement Adjustments

Each prediction includes enhancement details:

```python
batting_first = prediction["batting_first_scenario"]

# Task 1 & 3: Series momentum with sweep likelihood
if "series_momentum_multiplier" in batting_first:
    momentum = batting_first["series_momentum_multiplier"]
    print(f"Series momentum: ×{momentum:.2f}")
    # If 3-0 up in series, this multiplier applies

# Task 2: Spin pitch adjustment
if "spin_adjustment" in batting_first:
    adj = batting_first["spin_adjustment"]
    print(f"Spin pitch adjustment: {adj:+.0f} runs")
    # If dominant team on home spin pitch, penalty removed

# Task 4: Recent form bonus
if "form_bonus" in batting_first:
    bonus = batting_first["form_bonus"]
    print(f"Form bonus: {bonus:+.0f} runs")
    # If exceptional performers in squad

# Chasing scenario
chasing = prediction["chasing_scenario"]

# Task 5: Variable chase penalty
if "chase_penalty" in chasing:
    penalty = chasing["chase_penalty"]
    print(f"Chase penalty: {penalty:+.0f} runs (economy-based)")
    # Dynamic calibration based on opponent bowling

# Task 6: Batter-bowler matching
if "matchup_bonus" in chasing:
    bonus = chasing["matchup_bonus"]
    print(f"Matchup bonuses: {bonus:+.0f} runs (from favorable H2H)")
```

---

## Decision Framework

### Win Probability Interpretation

```python
wp = prediction["win_probability"]

if wp >= 0.70:
    confidence = "HIGH CONFIDENCE"
    action = "Proceed with planned strategy"
elif wp >= 0.55:
    confidence = "MODERATE CONFIDENCE"
    action = "Execute planned strategy with flexibility"
elif wp >= 0.45:
    confidence = "BALANCED"
    action = "Prepare contingency plans"
else:
    confidence = "UNDERDOG"
    action = "Focus on key moments, exploit weaknesses"

print(f"Win Probability: {wp:.1%} ({confidence})")
print(f"Recommended: {action}")
```

### Runs Estimate Interpretation

```python
runs = prediction["adjusted_runs_estimate"]
error_band = 0.16  # 16% mean error

lower_bound = runs * (1 - error_band)
upper_bound = runs * (1 + error_band)

print(f"Runs Estimate: {runs:.1f}")
print(f"Confidence Range (±16%): {lower_bound:.0f}-{upper_bound:.0f}")

# Target-setting for chasing
if scenario == "chasing":
    # Use lower bound as minimum target
    min_target = lower_bound
    print(f"Minimum target to chase: {min_target:.0f}")
    print(f"Comfortable target: {runs:.0f}")
    print(f"Challenging target: {upper_bound:.0f}")
```

---

## Batch Processing

### Load All Predictions

```python
import json
from pathlib import Path

predictions = {}

# Load all match predictions
matches_dir = Path("matches")
for match_dir in matches_dir.iterdir():
    if match_dir.is_dir():
        pred_file = match_dir / "prediction" / "prediction.json"
        if pred_file.exists():
            with open(pred_file) as f:
                predictions[match_dir.name] = json.load(f)

print(f"Loaded {len(predictions)} predictions")

# Analyze across matches
avg_runs = sum(p["adjusted_runs_estimate"] for p in predictions.values()) / len(predictions)
avg_wp = sum(p["win_probability"] for p in predictions.values()) / len(predictions)

print(f"Average runs estimate: {avg_runs:.1f}")
print(f"Average win probability: {avg_wp:.1%}")
```

### Filter by Confidence

```python
# High-confidence predictions (±20%)
high_conf = {
    k: v for k, v in predictions.items()
    if 0.56 <= v["win_probability"] <= 0.73  # Roughly ±20% on 50/50 baseline
}

print(f"High-confidence predictions: {len(high_conf)} of {len(predictions)}")

# Use these for critical decisions
for match_id, pred in high_conf.items():
    print(f"{match_id}: {pred['adjusted_runs_estimate']:.0f} runs, "
          f"{pred['win_probability']:.1%} WP")
```

---

## Error Handling

### Missing Data

```python
def safe_load_prediction(match_id):
    """Load prediction with error handling"""
    try:
        with open(f"matches/{match_id}/prediction/prediction.json") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Prediction not found for {match_id}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid prediction file for {match_id}")
        return None

# Use safely
pred = safe_load_prediction("ind_sl_tvm2_20251114")
if pred:
    print(f"Runs: {pred['adjusted_runs_estimate']:.1f}")
else:
    print("Using fallback strategy")
```

### Missing Matchups

```python
# Handle cases where some matchups may be missing
matchups = prediction.get("key_matchups", [])

if matchups:
    print(f"Found {len(matchups)} matchups")
else:
    print("No H2H data available - use general analysis")
```

---

## Advanced: Custom Analysis

### Calculate Expected Value

```python
def calculate_expected_value(prediction, risk_factor=1.0):
    """
    Calculate expected value considering uncertainty.
    risk_factor: 0.8 = conservative, 1.0 = neutral, 1.2 = aggressive
    """
    runs = prediction["adjusted_runs_estimate"]
    error = 0.16  # 16% mean error
    
    # Adjust error band by risk factor
    adjusted_error = error * risk_factor
    lower = runs * (1 - adjusted_error)
    upper = runs * (1 + adjusted_error)
    
    return {
        "conservative": lower,
        "expected": runs,
        "optimistic": upper
    }

pred = safe_load_prediction("ind_sl_tvm2_20251114")
if pred:
    scenarios = calculate_expected_value(pred, risk_factor=0.9)
    print(f"Conservative estimate: {scenarios['conservative']:.0f} runs")
    print(f"Expected estimate: {scenarios['expected']:.0f} runs")
    print(f"Optimistic estimate: {scenarios['optimistic']:.0f} runs")
```

### Compare Scenarios

```python
def scenario_comparison(prediction):
    """Compare batting first vs chasing scenarios"""
    bf = prediction["batting_first_scenario"]
    ch = prediction["chasing_scenario"]
    
    return {
        "batting_first": {
            "runs": bf["adjusted_runs_estimate"],
            "wp": bf["win_probability"],
            "advantage": bf["adjusted_runs_estimate"] - ch["adjusted_runs_estimate"]
        },
        "chasing": {
            "runs": ch["adjusted_runs_estimate"],
            "wp": ch["win_probability"],
            "advantage": ch["adjusted_runs_estimate"] - bf["adjusted_runs_estimate"]
        }
    }

if prediction["scenario"] == "pre_toss_blended":
    comparison = scenario_comparison(prediction)
    print("Scenario Analysis:")
    for scenario, data in comparison.items():
        print(f"  {scenario}: {data['runs']:.0f} runs, {data['wp']:.1%} WP")
        print(f"    Advantage: {data['advantage']:+.0f} runs")
```

---

## Performance Expectations

### Accuracy by Range

Expect predictions to fall within:
- **±10%**: ~39% of predictions
- **±20%**: ~67% of predictions  ← Most reliable range
- **±30%**: ~100% of predictions

### Scenario-Specific Accuracy

- **Batting First**: ~18.4% mean error (more variable)
- **Chasing**: ~14.4% mean error (more predictable)

Use this knowledge when prioritizing strategy.

---

## Summary

**Key Integration Points**:
1. Load predictions from `matches/{match_id}/prediction/prediction.json`
2. Use `adjusted_runs_estimate` and `win_probability` for primary decisions
3. Reference scenario-specific predictions (batting_first vs chasing)
4. Leverage strategic recommendations (XI, batting order, bowling plan)
5. Analyze matchups for tactical advantages
6. Consider enhancement details (momentum, penalties, bonuses)
7. Account for ±16% mean error in confidence intervals

**Decision Framework**:
- WP > 70%: High confidence
- WP 55-70%: Moderate confidence
- WP 45-55%: Balanced/contingency planning
- WP < 45%: Underdog - focus on key moments

---

**Model Version**: wt20-oracle-v2.3-phase2  
**Mean Error**: 16.0%  
**Confidence Range**: ±20% at 67% coverage
