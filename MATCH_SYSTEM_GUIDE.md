# Match System Guide
## File Organization for Multi-Match Analysis

This guide explains the consolidated file structure for running wt20-oracle across multiple cricket matches.

---

## 📁 Directory Structure

```
/Users/performek5/Desktop/Code/wt20-oracle/
├── wt20_oracle/                          # Core prediction engine
│   ├── data/
│   ├── graphs/
│   ├── io/
│   └── ...
├── testing/                              # Testing framework
│   ├── data_collection/
│   ├── prediction_pipeline/
│   ├── validation/
│   ├── orchestration/
│   └── create_match_structure.py          # NEW: Match initialization
├── matches/                              # NEW: Match-specific data (root directory)
│   ├── india_vs_sa_20260427/            # Example match [TEAM1_vs_TEAM2_YYYYMMDD]
│   │   ├── metadata.json                 # Match tracking & accuracy scores
│   │   ├── prediction/
│   │   │   ├── prediction.json           # Full prediction output
│   │   │   └── prediction_summary.md     # Executive summary
│   │   ├── actual/
│   │   │   └── actual_result.json        # Actual match result
│   │   ├── validation/
│   │   │   ├── validation_report.md
│   │   │   ├── gap_analysis.md
│   │   │   └── improvement_roadmap.md
│   │   ├── analysis/
│   │   │   ├── pre_match_analysis.md
│   │   │   └── pitch_analysis.md
│   │   └── logs/
│   │       └── execution.log
│   ├── templates/                        # NEW: Reusable templates
│   │   └── MATCH_TEMPLATE.md
│   └── [other_matches]/
├── shared_data/                          # NEW: Reference data across matches
│   ├── venue_reference.json              # Venue characteristics
│   ├── team_profiles/
│   │   ├── india.json
│   │   ├── south_africa.json
│   │   ├── england.json
│   │   └── ...
│   ├── player_stats/
│   └── historical/
│       ├── matches.jsonl
│       └── performance.jsonl
├── config/
│   └── venues.json
├── docs/
└── README.md
```

---

## 🎯 Key Features

### 1. Match Isolation
Each match is completely self-contained in its own directory:
- **Predictions**: Isolated from other matches
- **Actual results**: Separate from predictions
- **Validation**: Match-specific metrics
- **Analysis**: Independent of other matches

### 2. Scalability
Create as many match directories as needed:
```
matches/
├── india_vs_sa_20260427/
├── australia_vs_england_20260515/
├── pakistan_vs_westindies_20260620/
├── bangladesh_vs_afghanistan_20260705/
└── ... (n matches)
```

### 3. Shared Reference Data
Common data accessible to all matches:
- Venue characteristics (pitch behavior, historical stats)
- Team profiles (recent form, key players)
- Player statistics (career performance)
- Historical match data

### 4. Automated Pipeline
Scripts handle:
- Directory structure creation
- Metadata initialization
- Prediction generation
- Validation execution
- Gap analysis

---

## 🚀 Quick Start

### Step 1: Create Match Structure

```bash
cd /Users/performek5/Desktop/Code/wt20-oracle

# Create directory structure for a new match
python testing/orchestration/create_match_structure.py \
  --team1 "Pakistan" \
  --team2 "West Indies" \
  --date "2026-06-20" \
  --venue "Brian Lara Stadium" \
  --country "Trinidad and Tobago"
```

Output:
```
✓ MATCH STRUCTURE CREATED
Match ID: pakistan_vs_westindies_20260620
Location: /Users/performek5/Desktop/Code/wt20-oracle/matches/pakistan_vs_westindies_20260620

Directory Structure:
  pakistan_vs_westindies_20260620/
    ├── prediction/
    ├── actual/
    ├── validation/
    ├── analysis/
    ├── logs/
    └── metadata.json
```

### Step 2: Generate Prediction

```bash
# Run prediction for the match
python testing/orchestration/main.py \
  --match-id "pakistan_vs_westindies_20260620" \
  --predict \
  --output-to-match-dir
```

Files created:
- `matches/pakistan_vs_westindies_20260620/prediction/prediction.json`
- `matches/pakistan_vs_westindies_20260620/metadata.json` (updated with execution time)

### Step 3: Record Actual Result

Once the match is played, add the actual result:

```bash
# Place actual_result.json in the actual/ directory
cp actual_result.json \
  matches/pakistan_vs_westindies_20260620/actual/actual_result.json
```

File format (actual_result.json):
```json
{
  "match_id": "pakistan_vs_westindies_20260620",
  "status": "completed",
  "result": {
    "winner": "Pakistan",
    "margin": { "value": 8, "unit": "runs" }
  },
  "innings": [
    {
      "team": "Pakistan",
      "runs": 178,
      "wickets": 5,
      "overs": "20"
    },
    {
      "team": "West Indies",
      "runs": 170,
      "wickets": 7,
      "overs": "20"
    }
  ],
  "actual_playing_xi": [...],
  "actual_batting_order": [...],
  "actual_bowling_breakdown": [...]
}
```

### Step 4: Run Validation

```bash
# Validate prediction against actual result
python testing/orchestration/main.py \
  --match-id "pakistan_vs_westindies_20260620" \
  --validate \
  --analyze
```

Files created:
- `matches/pakistan_vs_westindies_20260620/validation/validation_report.md`
- `matches/pakistan_vs_westindies_20260620/validation/gap_analysis.md`
- `matches/pakistan_vs_westindies_20260620/metadata.json` (updated with accuracy scores)

### Step 5: Review Results

```bash
# View match metadata with accuracy scores
cat matches/pakistan_vs_westindies_20260620/metadata.json

# View validation report
cat matches/pakistan_vs_westindies_20260620/validation/validation_report.md

# View gap analysis with improvements
cat matches/pakistan_vs_westindies_20260620/validation/gap_analysis.md
```

---

## 📊 Metadata Structure

Each match has a `metadata.json` file tracking:

```json
{
  "match_id": "pakistan_vs_westindies_20260620",
  "match_date": "2026-06-20",
  "teams": { "team1": "Pakistan", "team2": "West Indies" },
  "venue": { "name": "Brian Lara Stadium", "city": "...", "country": "Trinidad and Tobago" },
  "status": "completed",
  "result": { "winner": "Pakistan", "margin": { "value": 8, "unit": "runs" } },
  "pipeline": {
    "created_at": "2026-06-19T10:00:00Z",
    "prediction_time": "2026-06-19T15:00:00Z",
    "match_start": "2026-06-20T14:00:00Z",
    "match_end": "2026-06-20T22:15:00Z",
    "completed_at": "2026-06-20T22:15:00Z"
  },
  "execution": {
    "prediction_duration_ms": 1240,
    "validation_duration_ms": 340,
    "model_version": "0.1-MVP"
  },
  "accuracy": {
    "overall": 77.6,
    "squad_selection": 81.8,
    "batting_order": 100.0,
    "match_outcome": 78.8
  }
}
```

---

## 🔄 Workflow for Multiple Matches

### Batch Processing

```bash
# Create structures for 5 upcoming matches
for match in \
  "India,South Africa,2026-04-27,Willowmoore Park" \
  "Pakistan,West Indies,2026-06-20,Brian Lara Stadium" \
  "Australia,England,2026-07-15,The Oval" \
  "New Zealand,Afghanistan,2026-08-10,Eden Park" \
  "Sri Lanka,Bangladesh,2026-09-05,R. Premadasa Stadium"
do
  IFS=',' read -r t1 t2 date venue <<< "$match"
  python testing/orchestration/create_match_structure.py \
    --team1 "$t1" --team2 "$t2" --date "$date" --venue "$venue"
done

# Generate predictions for all matches
python testing/orchestration/main.py \
  --batch-dir "matches/" \
  --predict

# After matches complete, add actual results and run validation
python testing/orchestration/main.py \
  --batch-dir "matches/" \
  --validate \
  --analyze

# Generate summary report
python testing/orchestration/generate_batch_report.py \
  --batch-dir "matches/" \
  --output "BATCH_ANALYSIS_REPORT.md"
```

---

## 🔗 Shared Data Usage

### Accessing Venue Data

```python
import json
from pathlib import Path

# Load venue reference
with open("shared_data/venue_reference.json") as f:
    venues = json.load(f)

# Get Willowmoore Park characteristics
willowmoore = venues["venues"]["willowmoore_park"]
print(f"Pace friendly score: {willowmoore['pitch_characteristics']['pace_friendly']}")
# Output: Pace friendly score: 8.0
```

### Accessing Team Profiles

```python
# Load team profile
with open("shared_data/team_profiles/india.json") as f:
    team_india = json.load(f)

print(f"Win rate: {team_india['recent_form']['win_rate']}")
# Output: Win rate: 0.72
```

---

## 📈 Batch Analysis Commands

```bash
# List all matches
ls -1 matches/ | grep -v templates

# View accuracy across all matches
for match_dir in matches/*/; do
  if [ -f "$match_dir/metadata.json" ]; then
    echo "$(basename $match_dir): $(jq '.accuracy.overall' $match_dir/metadata.json)%"
  fi
done

# Extract validation reports for review
mkdir -p reports/
for match_dir in matches/*/validation/; do
  match_name=$(basename $(dirname $(dirname $match_dir)))
  cp "$match_dir/validation_report.md" "reports/${match_name}_validation.md"
done

# Generate improvement summary
python testing/orchestration/extract_improvement_gaps.py \
  --source "matches/" \
  --output "IMPROVEMENT_OPPORTUNITIES.md"
```

---

## ✅ File Checklist for Each Match

| Status | File | Required | Purpose |
|--------|------|----------|---------|
| ✓ | `metadata.json` | Yes | Match tracking & scoring |
| ✓ | `prediction/prediction.json` | Yes | Full prediction output |
| ✓ | `actual/actual_result.json` | After match | Match result data |
| ✓ | `validation/validation_report.md` | After validation | Accuracy metrics |
| ✓ | `validation/gap_analysis.md` | After validation | Improvement opportunities |
| ✓ | `analysis/pre_match_analysis.md` | Optional | Pre-match insights |
| ✓ | `logs/execution.log` | Optional | Pipeline execution details |

---

## 🎓 Best Practices

1. **Consistent Naming**: Always use `team1_vs_team2_YYYYMMDD` format
2. **Metadata First**: Create match structure before generating predictions
3. **Separate Concerns**: Keep prediction, actual, and validation isolated
4. **Reference Data**: Update shared_data when new venues or teams are encountered
5. **Version Control**: Commit matches/ directory to git for tracking
6. **Batch Operations**: Use batch processing scripts for multiple matches
7. **Archiving**: Move old matches to archive/ subdirectory after analysis

---

## 📞 Troubleshooting

### Match directory not created
```bash
# Verify permissions
ls -la matches/
chmod 755 matches/

# Recreate structure manually
mkdir -p matches/team1_vs_team2_YYYYMMDD/{prediction,actual,validation,analysis,logs}
```

### Metadata file missing
```bash
# Create minimal metadata.json
python testing/orchestration/create_match_structure.py --team1 "..." --team2 "..." --date "..." --venue "..."
```

### Actual result file format error
```bash
# Validate JSON
python -m json.tool matches/[match_id]/actual/actual_result.json
```

---

## 🔮 Future Enhancements

- [ ] Web UI for match management
- [ ] Database backend for queries across matches
- [ ] Automated result scraping from ESPN/Cricinfo
- [ ] Real-time match updates
- [ ] Interactive dashboard for batch analysis
- [ ] ML-based improvement priority ranking

