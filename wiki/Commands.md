# Commands Reference

Complete guide to all wt20-oracle commands.

---

## Table of Contents
- [Pre-Match Commands](#pre-match-commands)
- [Live Match Commands](#live-match-commands)
- [General Commands](#general-commands)
- [Output Formats](#output-formats)
- [Examples](#examples)

---

## Pre-Match Commands

### Basic Command

```bash
wt20-oracle prematch --opponent TEAM --venue VENUE
```

### Required Arguments

| Argument | Value | Examples |
|----------|-------|----------|
| `--opponent` | Team name (lowercase) | `australia`, `pakistan`, `south_africa` |
| `--venue` | Venue name (lowercase) | `edgbaston`, `lords`, `old_trafford` |

### Optional Arguments

| Argument | Purpose | Values | Default |
|----------|---------|--------|---------|
| `--verbose` | Show detailed reasoning | (no value) | Off |
| `--format` | Output format | `text`, `json`, `csv` | `text` |
| `--squad-size` | Number of players | `11` (or custom) | `11` |

### Valid Opponents

```
australia       pakistan        south_africa
bangladesh      netherlands     england
west_indies     ireland         new_zealand
afghanistan     scotland        zimbabwe
```

### Valid Venues

```
lords           old_trafford    headingley
edgbaston       rose_bowl       the_oval
bristol
```

### Examples

#### Basic Pre-Match
```bash
wt20-oracle prematch --opponent australia --venue edgbaston
```

#### With Verbose Output (More Details)
```bash
wt20-oracle prematch --opponent australia --venue edgbaston --verbose
```

#### Save as JSON
```bash
wt20-oracle prematch --opponent australia --venue edgbaston --format json
```

#### Save to File
```bash
wt20-oracle prematch --opponent australia --venue edgbaston > recommendation.txt
```

#### JSON to File
```bash
wt20-oracle prematch --opponent australia --venue edgbaston --format json > recommendation.json
```

#### Get Help
```bash
wt20-oracle prematch --help
```

---

## Live Match Commands

### Basic Command

```bash
wt20-oracle live --match-state FILE
```

### Required Arguments

| Argument | What It Is | Example |
|----------|-----------|---------|
| `--match-state` | Path to JSON file with match situation | `match_state.json`, `/path/to/state.json` |

### Optional Arguments

| Argument | Purpose | Values | Default |
|----------|---------|--------|---------|
| `--verbose` | Show detailed reasoning | (no value) | Off |
| `--format` | Output format | `text`, `json` | `text` |

### Match State JSON Format

Create a JSON file with this structure:

```json
{
  "match_id": "india-australia-edgbaston",
  "opponent": "australia",
  "venue": "edgbaston",
  "our_innings": {
    "batting_team": true,
    "current_score": 87,
    "wickets": 3,
    "overs": 13.5,
    "balls_faced": 81,
    "target": 150
  },
  "opponent_innings": {
    "score": 145,
    "wickets": 7,
    "overs": 20
  },
  "current_batter": {
    "name": "Jemimah Rodrigues",
    "runs_this_innings": 18,
    "balls_faced": 14,
    "strike_rate": 128.6
  },
  "current_bowler": {
    "name": "Jess Jonassen",
    "overs_bowled": 3.5,
    "runs_given": 28,
    "wickets": 0,
    "economy": 8.0
  },
  "phase": "middle",
  "momentum": "neutral"
}
```

### Examples

#### Basic Live Command
```bash
wt20-oracle live --match-state match_state.json
```

#### Verbose Mode
```bash
wt20-oracle live --match-state match_state.json --verbose
```

#### JSON Output
```bash
wt20-oracle live --match-state match_state.json --format json
```

#### From Different Directory
```bash
wt20-oracle live --match-state /path/to/match_state.json
```

#### Get Help
```bash
wt20-oracle live --help
```

---

## General Commands

### Help

```bash
# General help
wt20-oracle --help

# Help for specific command
wt20-oracle prematch --help
wt20-oracle live --help

# Version info
wt20-oracle --version
```

### Test Installation

```bash
# Verify it's working
wt20-oracle prematch --help

# Should show: Usage: wt20-oracle prematch [OPTIONS]
```

---

## Output Formats

### Text Format (Default)

```bash
wt20-oracle prematch --opponent australia --venue edgbaston --format text
```

Output is human-readable:
```
═══════════════════════════════════════════════════════════════
              INDIA VS AUSTRALIA AT EDGBASTON
                    Pre-Match Recommendation
═══════════════════════════════════════════════════════════════

SQUAD SELECTION (Best 11)
──────────────────────────
[... formatted output ...]
```

### JSON Format

```bash
wt20-oracle prematch --opponent australia --venue edgbaston --format json
```

Output is machine-readable JSON:
```json
{
  "squad": [
    {
      "name": "Smriti Mandhana",
      "position": 2,
      "role": "batter",
      "reasoning": "Strike rate 125 vs Australia"
    }
  ],
  "batting_order": [...],
  "bowling_plan": [...],
  "strategy": "..."
}
```

### CSV Format (Pre-Match Only)

```bash
wt20-oracle prematch --opponent australia --venue edgbaston --format csv
```

Output is comma-separated values (for spreadsheets):
```
name,position,role,reasoning
Smriti Mandhana,2,batter,Strong form
Shafali Verma,1,batter,High strike rate
```

---

## Examples

### Example 1: Pre-Match (India vs Pakistan)

```bash
wt20-oracle prematch --opponent pakistan --venue lords
```

### Example 2: Pre-Match with Details

```bash
wt20-oracle prematch --opponent australia --venue edgbaston --verbose
```

### Example 3: Save Recommendation

```bash
wt20-oracle prematch --opponent australia --venue edgbaston > my_recommendation.txt
```

### Example 4: Live Analysis

```bash
wt20-oracle live --match-state match_state.json
```

### Example 5: Live Analysis with Details

```bash
wt20-oracle live --match-state match_state.json --verbose > live_analysis.txt
```

### Example 6: Get JSON Output

```bash
wt20-oracle prematch --opponent australia --venue edgbaston --format json > data.json
```

### Example 7: Multiple Analyses

```bash
#!/bin/bash
# Analyze India vs all opponents at different venues

for opponent in australia pakistan south_africa; do
  for venue in lords edgbaston old_trafford; do
    echo "Analyzing India vs $opponent at $venue"
    wt20-oracle prematch --opponent $opponent --venue $venue > rec_${opponent}_${venue}.txt
  done
done
```

---

## Common Scenarios

### Scenario 1: Pre-Tournament Planning
```bash
# Get recommendations for all group stage matches

# India vs Australia at Edgbaston
wt20-oracle prematch --opponent australia --venue edgbaston

# India vs Pakistan at Old Trafford
wt20-oracle prematch --opponent pakistan --venue old_trafford

# India vs South Africa at Headingley
wt20-oracle prematch --opponent south_africa --venue headingley

# (and so on for all matches)
```

### Scenario 2: Live Match Support
```bash
# At the start of opponent's innings, create match_state.json
# Then run live analysis

wt20-oracle live --match-state match_state.json

# Update match_state.json after each over
# Re-run to get updated recommendation

wt20-oracle live --match-state match_state.json
```

### Scenario 3: Compare Options
```bash
# Get recommendations in JSON format
# Then compare with custom analysis

wt20-oracle prematch --opponent australia --venue edgbaston --format json > option1.json
wt20-oracle prematch --opponent australia --venue lords --format json > option2.json

# Compare option1.json vs option2.json manually
```

---

## Troubleshooting Commands

### Command Not Found

```bash
# Try with python module syntax
python -m wt20_oracle.cli prematch --opponent australia --venue edgbaston

# Or
python3 -m wt20_oracle.cli prematch --opponent australia --venue edgbaston
```

### Invalid Opponent

```bash
# Make sure opponent is lowercase
# ✓ Correct: wt20-oracle prematch --opponent australia
# ✗ Wrong: wt20-oracle prematch --opponent Australia
```

### Invalid Venue

```bash
# Make sure venue is lowercase
# ✓ Correct: wt20-oracle prematch --venue edgbaston
# ✗ Wrong: wt20-oracle prematch --venue Edgbaston
```

### File Not Found (Live Mode)

```bash
# Make sure match_state.json exists
ls match_state.json

# Or use full path
wt20-oracle live --match-state /absolute/path/to/match_state.json
```

### No Output

```bash
# Try verbose mode to see what's happening
wt20-oracle prematch --opponent australia --venue edgbaston --verbose
```

---

## Tips & Tricks

### Save All Recommendations
```bash
# Create a recommendations folder
mkdir recommendations

# Save each analysis
wt20-oracle prematch --opponent australia --venue edgbaston > recommendations/india_vs_australia_edgbaston.txt
wt20-oracle prematch --opponent pakistan --venue lords > recommendations/india_vs_pakistan_lords.txt
```

### Pipe to Other Tools
```bash
# Use with grep (search for keywords)
wt20-oracle prematch --opponent australia --venue edgbaston | grep "strategy"

# Use with less (paginate long output)
wt20-oracle prematch --opponent australia --venue edgbaston | less

# Use with jq (JSON processing)
wt20-oracle prematch --opponent australia --venue edgbaston --format json | jq '.squad'
```

### Create a Script
```bash
#!/bin/bash
# analyze_all.sh

echo "Getting all pre-match recommendations..."

for opponent in australia pakistan south_africa bangladesh netherlands; do
  for venue in lords edgbaston old_trafford headingley rose_bowl the_oval bristol; do
    echo "Analyzing vs $opponent at $venue..."
    wt20-oracle prematch --opponent $opponent --venue $venue \
      > recs/${opponent}_${venue}.txt 2>&1
  done
done

echo "Done! Check recs/ folder"
```

Then run:
```bash
bash analyze_all.sh
```

---

## Command Summary Table

| What | Command | Example |
|------|---------|---------|
| Pre-match basic | `wt20-oracle prematch --opponent TEAM --venue VENUE` | `wt20-oracle prematch --opponent australia --venue edgbaston` |
| Pre-match verbose | Add `--verbose` | `wt20-oracle prematch --opponent australia --venue edgbaston --verbose` |
| Pre-match JSON | Add `--format json` | `wt20-oracle prematch --opponent australia --venue edgbaston --format json` |
| Live basic | `wt20-oracle live --match-state FILE` | `wt20-oracle live --match-state match_state.json` |
| Live verbose | Add `--verbose` | `wt20-oracle live --match-state match_state.json --verbose` |
| Get help | `wt20-oracle --help` | `wt20-oracle prematch --help` |
| Save to file | Add `> filename.txt` | `wt20-oracle prematch ... > rec.txt` |

---

## Next Steps

- **Learn more about live mode:** [Live Mode Guide](Live-Mode.md)
- **Understand cricket terms:** [Cricket Glossary](Cricket-Glossary.md)
- **See system architecture:** [Architecture Explained](Architecture-Explained.md)

