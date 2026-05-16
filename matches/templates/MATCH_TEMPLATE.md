# Match Template Structure

This template shows the required directory structure and files for each match analyzed by wt20-oracle.

## Directory Layout

```
matches/
├── [team1_vs_team2_YYYYMMDD]/
│   ├── metadata.json                          # Match metadata
│   ├── prediction/
│   │   ├── prediction.json                    # Full prediction output
│   │   ├── prediction_summary.md              # 1-page executive summary
│   │   └── prediction_details.md              # Extended analysis
│   ├── actual/
│   │   ├── actual_result.json                 # Actual match result
│   │   └── match_scorecard.md                 # Detailed scorecard
│   ├── validation/
│   │   ├── validation_metrics.json            # Accuracy scores
│   │   ├── validation_report.md               # Detailed validation
│   │   ├── gap_analysis.md                    # Root cause analysis
│   │   └── improvement_roadmap.md             # Next iteration improvements
│   ├── analysis/
│   │   ├── pre_match_analysis.md              # Venue, squad, pitch analysis
│   │   ├── pitch_analysis.md                  # Detailed pitch behavior
│   │   └── strategic_insights.md              # Team-specific strategies
│   └── logs/
│       ├── execution.log                      # Pipeline execution log
│       └── errors.log                         # Any errors encountered
```

## Directory Naming Convention

Use format: `[team1_vs_team2_YYYYMMDD]`

Examples:
- `india_vs_sa_20260427`
- `australia_vs_england_20260515`
- `pakistan_vs_westindies_20260620`

## File Requirements

### metadata.json
Required fields:
- `match_id`: Unique identifier
- `match_date`: ISO 8601 format
- `teams`: { team1, team2 }
- `venue`: { name, city, country, venue_id }
- `format`: T20I, T20, etc.
- `status`: pending, completed, cancelled
- `result`: { winner, margin: { value, unit } }
- `pipeline`: { created_at, prediction_time, match_start, match_end }
- `execution`: { prediction_duration_ms, validation_duration_ms, model_version }
- `accuracy`: { overall, squad_selection, batting_order, match_outcome, key_player }

### prediction/prediction.json
Full prediction output from wt20-oracle including:
- Squad selection with confidence scores
- Batting order with SR adjustments
- Bowling plan by phase
- Match outcome (runs, wickets, margin)
- Analyst insights

### actual/actual_result.json
Actual match result including:
- Final teams playing XI
- Batting order with runs, balls, SR
- Phase-wise bowling breakdown
- Final score and margin

### validation/validation_metrics.json
Accuracy calculations:
- Squad selection accuracy (%)
- Batting order correlation
- Runs error (absolute and %)
- Wickets error
- Win prediction (correct/incorrect)
- Overall accuracy score

### validation/gap_analysis.md
Root cause analysis identifying:
- Why predictions differed from actual
- Form modifier impact
- Matchup modifier impact
- External factors (pitch behavior, weather, tactical changes)

## Directory Operations

### Creating a New Match
```bash
# Use the match initialization script
python testing/orchestration/create_match_structure.py \
  --team1 "India" \
  --team2 "South Africa" \
  --date "2026-04-27" \
  --venue "Willowmoore Park Cricket Stadium"
```

### Running Pipeline on Match
```bash
# Prediction, validation, and gap analysis
python testing/orchestration/main.py \
  --match-id "india_vs_sa_20260427" \
  --predict \
  --validate \
  --analyze
```

### Viewing Match Results
```bash
# View metadata
cat matches/india_vs_sa_20260427/metadata.json

# View prediction summary
cat matches/india_vs_sa_20260427/prediction/prediction_summary.md

# View validation report
cat matches/india_vs_sa_20260427/validation/validation_report.md

# View gap analysis
cat matches/india_vs_sa_20260427/validation/gap_analysis.md
```

## Shared Data References

Matches can reference shared data:

```
shared_data/
├── pitch_data.json                    # Venue characteristics
├── team_profiles/
│   ├── india.json
│   ├── south_africa.json
│   └── ...
├── player_stats/
│   └── [player_performance.jsonl]
└── historical/
    ├── matches.jsonl
    └── performance.jsonl
```

## Example Metadata

```json
{
  "match_id": "india_vs_sa_20260427",
  "match_date": "2026-04-27",
  "teams": {
    "team1": "India",
    "team2": "South Africa"
  },
  "venue": {
    "name": "Willowmoore Park Cricket Stadium",
    "city": "Benoni",
    "country": "South Africa",
    "venue_id": "willowmoore_park"
  },
  "format": "T20I",
  "status": "completed",
  "accuracy": {
    "overall": 77.6,
    "squad_selection": 81.8,
    "batting_order": 100.0,
    "match_outcome": 78.8
  }
}
```

## File Organization Benefits

1. **Scalability**: Each match is self-contained and easy to duplicate
2. **Traceability**: All predictions and validations are versioned with match
3. **Comparison**: Easy to compare across multiple matches
4. **Improvement Tracking**: Gap analysis feeds into model improvements
5. **Automation**: Scripts can iterate through all matches for batch analysis
