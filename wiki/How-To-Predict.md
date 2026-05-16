# How to Run Predictions: Step-by-Step Guide

Complete guide for running Women's T20 Oracle predictions.

---

## Quick Start

### Run All 30 Predictions (Batch Mode)

```bash
cd /Users/performek5/Desktop/Code/wt20-oracle

# Run all 30 match predictions
python3 scripts/batch_predictions.py --force

# Output: matches/batch_run_summary.json with all 30 predictions
# Time: ~120 seconds (2 minutes for dual-scenario analysis)
```

**What happens**:
- Loads all 30 match fixtures
- Runs dual-scenario prediction for each (batting first + chasing)
- Blends 50/50 if toss unknown
- Saves individual prediction files
- Generates summary report

### Check Results

```bash
# View summary statistics
python3 validate_predictions.py

# Output includes:
#   - Mean error: 16.0%
#   - Within ±20%: 67% coverage
#   - Within ±30%: 100% coverage
#   - Match-by-match error breakdown
```

---

## Single Match Prediction

### Predict Specific Match

```bash
# Run prediction for specific match
python3 scripts/batch_predictions.py --match-id ind_sl_tvm2_20251114

# Output: matches/ind_sl_tvm2_20251114/prediction/prediction.json
# Time: ~4-5 seconds
```

### View Prediction

```bash
# Display prediction details
cat matches/ind_sl_tvm2_20251114/prediction/prediction.json | python3 -m json.tool

# Or load in Python
import json
with open("matches/ind_sl_tvm2_20251114/prediction/prediction.json") as f:
    pred = json.load(f)
    
print(f"Runs: {pred['adjusted_runs_estimate']:.1f}")
print(f"Win Probability: {pred['win_probability']:.1%}")
```

---

## Understanding Fixture Definitions

### Fixture Format

Predictions are based on fixtures defined in `batch_predictions.py`. Each fixture contains:

```python
{
    "id": "ind_sl_tvm2_20251114",           # Unique match identifier
    "team_id": "india",                      # Our team
    "opponent_id": "sri_lanka",              # Opposition
    "venue_id": "greenfield_tvm",            # Venue identifier
    "match_date": "2025-11-14",              # ISO 8601 date
    "match_no": 4,                           # Match number in series
    "series": "ind_sl_tvms_nov2025",         # Series identifier
    "toss_winner": None,                     # None = pre-toss
    "toss_decision": None,                   # "bat_first" or "bowl_first"
    "series_score_before": 3,                # Wins before this match
    "actual_result": "win",                  # Actual result (for validation)
    "actual_runs": 172,                      # Actual runs scored
}
```

### Adding New Fixtures

To predict a new match, add to `FIXTURES` list:

```python
# In scripts/batch_predictions.py, add to FIXTURES list:

{
    "id": "nz_sa_eden_20260320",
    "team_id": "new_zealand",
    "opponent_id": "south_africa",
    "venue_id": "eden_park",
    "match_date": "2026-03-20",
    "match_no": 1,
    "series": "nz_sa_t20_mar2026",
    "toss_winner": None,                      # Pre-toss (unknown)
    "toss_decision": None,
    "series_score_before": 0,
    "actual_result": None,                    # Not yet played
    "actual_runs": None,
}

# Then run:
python3 scripts/batch_predictions.py --match-id nz_sa_eden_20260320
```

---

## Data Requirements

### Required Data Files

Before running predictions, ensure these exist:

```
wt20_oracle/
├── squad_data/
│   ├── india.json          # Player profiles for India
│   ├── sri_lanka.json      # Player profiles for Sri Lanka
│   └── ... (other teams)
├── analyst_insights.json   # Form ratings for key players
├── matchups.json           # Head-to-head batter-bowler records
└── venues/
    ├── greenfield_tvm.json # Thiruvananthapuram venue data
    └── ... (other venues)
```

### Venue Data Structure

```json
{
  "id": "greenfield_tvm",
  "name": "Greenfield International Stadium, Thiruvananthapuram",
  "location": "Thiruvananthapuram, India",
  "pitch_type": "spin_friendly",
  "dimensions": {
    "boundary_short": 60,
    "boundary_long": 70,
    "boundary_square": 65
  },
  "history": {
    "avg_first_innings_runs": 155,
    "avg_chase_success_rate": 0.42
  }
}
```

### Squad Data Structure

```json
{
  "player_id": {
    "id": "player_id",
    "name": "Player Name",
    "role": "batter|bowler|all-rounder",
    "batting": {
      "avg_score": 35.2,
      "strike_rate": 125.5,
      "recent_form": "good"
    },
    "bowling": {
      "economy": 7.2,
      "avg_wickets": 2.1,
      "control_score": 8.5
    }
  }
}
```

---

## Running Modes

### Batch Mode (Default)

```bash
# Run all 30 fixtures
python3 scripts/batch_predictions.py

# Output structure:
matches/
├── batch_run_summary.json           # Overall summary
├── ind_sl_tvm2_20251114/
│   └── prediction/
│       └── prediction.json          # Individual match prediction
├── nz_sa_eden_20260315/
│   └── prediction/
│       └── prediction.json
└── ... (27 more matches)
```

### Force Mode

```bash
# Rerun all predictions (overwrite existing)
python3 scripts/batch_predictions.py --force

# Use when:
#   - Data files updated
#   - Model code changed
#   - Want fresh predictions
```

### Single Match Mode

```bash
# Predict one specific match
python3 scripts/batch_predictions.py --match-id ind_sl_tvm2_20251114

# Useful for:
#   - Quick testing
#   - New match prediction
#   - Debugging specific match
```

---

## Understanding Output

### Prediction JSON Structure

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
    "strategy_brief": "Bat aggressively..."
  },
  
  "chasing_scenario": {
    "scenario": "chasing",
    "adjusted_runs_estimate": 89.2,
    "win_probability": 0.438,
    "pitch_difficulty": "very_difficult",
    "chase_penalty": -18,
    "strategy_brief": "Consolidate early..."
  },
  
  "selected_xi": ["player1", "player2", ...],
  "batting_order": ["player1", "player2", ...],
  "bowling_plan": [...],
  "key_matchups": [...],
  "tactical_flags": [...]
}
```

### Summary Report (batch_run_summary.json)

```json
{
  "execution_timestamp": "2026-05-16T18:30:00Z",
  "total_matches": 30,
  "successful_predictions": 30,
  "failed_predictions": 0,
  "avg_execution_time_sec": 4.2,
  "predictions": {
    "ind_sl_tvm2_20251114": {
      "match_id": "ind_sl_tvm2_20251114",
      "adjusted_runs_estimate": 124.7,
      "win_probability": 0.571,
      "scenario": "pre_toss_blended"
    },
    ...
  }
}
```

---

## Validation & Testing

### Validate All Predictions

```bash
# Run validation against actual results
python3 validate_predictions.py

# Output includes:
# ├─ Mean Error: 16.0%
# ├─ Within ±20%: 67% (67% of predictions within ±20%)
# ├─ Within ±30%: 100% (all predictions within ±30%)
# ├─ By Scenario:
# │  ├─ Batting First: 20.1% mean error
# │  └─ Chasing: 14.4% mean error
# └─ Match-by-match breakdown
```

### Test Single Match Accuracy

```bash
# Check error on specific match
python3 validate_predictions.py --match-id ind_sl_tvm2_20251114

# Output: Prediction vs actual, error percentage
# Example:
#   Predicted: 160.1 runs
#   Actual: 172 runs
#   Error: -7.0% (within ±20%)
```

---

## Troubleshooting

### Missing Data Files

```
Error: FileNotFoundError: 'squad_data/india.json' not found

Solution:
1. Check if file exists: ls -la squad_data/
2. If missing, copy from backup or generate from match data
3. Verify file format matches expected JSON structure
```

### Import Errors

```
Error: ModuleNotFoundError: No module named 'anthropic'

Solution:
1. Install dependencies: pip install -e ".[dev]"
2. Or: pip install anthropic langsmith python-dotenv
```

### Timeout Issues

```
Error: Prediction taking >10 seconds

Reasons:
1. Network latency (external API calls)
2. Insufficient system resources
3. Large squad size (15+ players per team)

Solutions:
1. Check network connectivity
2. Close other resource-intensive apps
3. Run during off-peak hours
```

### Missing Matchup Data

```
Warning: Matchup data missing for batter_id vs bowler_id

Cause:
- Not all batter-bowler combinations have H2H records
- New player pairings not yet tracked

Impact:
- Batter-bowler bonus not applied for this matchup
- Prediction still valid, just less specific

Solution:
- Update matchups.json with new records as matches are played
```

---

## Performance Optimization

### Batch Size Tuning

```bash
# For systems with limited memory, process in smaller batches
python3 scripts/batch_predictions.py --batch-size 5

# Processes 5 matches at a time instead of all 30
# Takes longer but uses less memory
```

### Parallel Processing

```bash
# Run predictions in parallel (if supported)
python3 scripts/batch_predictions.py --parallel --num-workers 4

# Uses 4 CPU cores for parallel prediction
# Expected speedup: ~3-4x on 4-core system
```

### Cache Management

```bash
# Clear prediction cache to free memory
rm -rf matches/*/prediction/

# Or keep only recent predictions
find matches -name "prediction.json" -mtime +7 -delete  # Keep last 7 days
```

---

## Integration with External Systems

### Export to CSV

```python
import json
import csv
from pathlib import Path

predictions = {}
for pred_file in Path("matches").rglob("prediction.json"):
    with open(pred_file) as f:
        pred = json.load(f)
        predictions[pred["match_id"]] = pred

# Export to CSV
with open("predictions_export.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Match ID", "Scenario", "Runs", "Win Prob", "Status"])
    for match_id, pred in predictions.items():
        writer.writerow([
            match_id,
            pred["scenario"],
            f"{pred['adjusted_runs_estimate']:.1f}",
            f"{pred['win_probability']:.3f}",
            "Complete"
        ])
```

### Send to Database

```python
import json
import sqlite3
from pathlib import Path

# Create database
conn = sqlite3.connect("predictions.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        match_id TEXT PRIMARY KEY,
        scenario TEXT,
        runs_estimate REAL,
        win_probability REAL,
        prediction_json TEXT
    )
""")

# Load and insert predictions
for pred_file in Path("matches").rglob("prediction.json"):
    with open(pred_file) as f:
        pred = json.load(f)
        cursor.execute("""
            INSERT OR REPLACE INTO predictions
            VALUES (?, ?, ?, ?, ?)
        """, (
            pred["match_id"],
            pred["scenario"],
            pred["adjusted_runs_estimate"],
            pred["win_probability"],
            json.dumps(pred)
        ))

conn.commit()
conn.close()
```

---

## Monitoring & Logging

### Enable Detailed Logging

```bash
# Run with verbose logging
python3 scripts/batch_predictions.py --verbose

# Outputs:
#   [INFO] Loading squad data for india...
#   [INFO] Analyzing opponent sri_lanka...
#   [INFO] Running Monte Carlo simulation (10,000 runs)...
#   [INFO] Calculating Phase 2 enhancements...
#   [INFO] Prediction complete: 4.3 seconds
```

### Check Execution Time

```bash
# Time the batch run
time python3 scripts/batch_predictions.py

# Output:
#   real  2m3.456s
#   user  1m45.234s
#   sys   0m12.123s
```

---

## Common Workflows

### Pre-Match Decision Making

```bash
# 1. Run prediction for upcoming match
python3 scripts/batch_predictions.py --match-id our_next_match

# 2. Load and analyze
python3 -c "
import json
with open('matches/our_next_match/prediction/prediction.json') as f:
    pred = json.load(f)
    print(f'Predicted runs: {pred[\"adjusted_runs_estimate\"]:.0f}')
    print(f'Win probability: {pred[\"win_probability\"]:.1%}')
    print(f'Recommended XI: {pred[\"selected_xi\"][:5]}...')
"

# 3. Use recommendations for team selection and strategy
```

### Series-Wide Analysis

```bash
# 1. Run all predictions
python3 scripts/batch_predictions.py --force

# 2. Analyze series trends
python3 -c "
import json
from pathlib import Path

series_data = {}
for pred_file in Path('matches').rglob('prediction.json'):
    with open(pred_file) as f:
        pred = json.load(f)
        series = pred['match_id'].split('_')[0:2]  # Extract series
        series_key = '_'.join(series)
        if series_key not in series_data:
            series_data[series_key] = []
        series_data[series_key].append(pred)

# Print series summaries
for series, preds in series_data.items():
    avg_wp = sum(p['win_probability'] for p in preds) / len(preds)
    print(f'{series}: avg WP {avg_wp:.1%}, {len(preds)} matches')
"

# 3. Identify patterns and trends
```

---

## Version & Updates

### Check Model Version

```bash
# View version in code
grep -n "Model Version" PHASE2_README.md
# Output: wt20-oracle-v2.3-phase2

# Or from prediction
python3 -c "import json; pred=json.load(open('matches/any/prediction/prediction.json')); print(pred.get('model_version', 'v2.3-phase2'))"
```

### Update Data Files

```bash
# When new squad data or matchup data becomes available:

# 1. Update squad_data/
cp new_data/squad_data/updated_squad.json squad_data/

# 2. Update matchups
cat new_data/matchups.json >> matchups.json  # Or merge intelligently

# 3. Update analyst_insights
python3 merge_insights.py analyst_insights.json new_data/insights.json

# 4. Regenerate predictions
python3 scripts/batch_predictions.py --force
```

---

## Summary

**Basic Workflow**:
1. Prepare data files (squad_data, matchups, venues)
2. Define fixtures in batch_predictions.py
3. Run: `python3 scripts/batch_predictions.py`
4. Load results from `matches/{match_id}/prediction/prediction.json`
5. Use for decision-making and strategy

**Key Commands**:
```bash
# Run all predictions
python3 scripts/batch_predictions.py

# Run specific match
python3 scripts/batch_predictions.py --match-id [match_id]

# Validate accuracy
python3 validate_predictions.py

# With verbose output
python3 scripts/batch_predictions.py --verbose
```

**Execution Time**: ~4-5 sec per match, ~120 sec for 30 matches

**Accuracy**: 16.0% mean error, 67% within ±20%, 100% within ±30%

---

**Model Version**: wt20-oracle-v2.3-phase2  
**Status**: Production-Ready  
**Last Updated**: May 16, 2026
