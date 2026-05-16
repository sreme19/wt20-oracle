# CLI Usage Guide

Complete guide to using wt20-oracle from the command line.

---

## Table of Contents
1. [Pre-Match Mode](#pre-match-mode)
2. [Live Mode](#live-mode)
3. [Common Options](#common-options)
4. [Examples](#examples)
5. [Troubleshooting](#troubleshooting)

---

## Pre-Match Mode

Use this the night before or morning of a match to get:
- Best 11 players selection
- Optimal batting order
- Bowling plan
- Strategy brief

### Basic Syntax

```bash
wt20-oracle prematch --opponent <TEAM> --venue <VENUE>
```

### Required Arguments

| Argument | What it is | Example |
|----------|-----------|---------|
| `--opponent` | Which team India is playing | `australia`, `pakistan`, `bangladesh` |
| `--venue` | Where the match is | `edgbaston`, `old trafford`, `lords` |

### Optional Arguments

| Argument | Purpose | Default |
|----------|---------|---------|
| `--squad-size` | How many players to select (usually 11) | `11` |
| `--format` | Output format | `text` |
| `--verbose` | Show detailed reasoning | `false` |

### Valid Opponents

```
australia, south africa, pakistan, bangladesh,
netherlands, england, west indies, ireland,
new zealand, afghanistan, scotland, zimbabwe
```

### Valid Venues

```
lords, old trafford, headingley, edgbaston,
rose bowl, the oval, bristol
```

### Example Usage

**Simple pre-match recommendation:**
```bash
wt20-oracle prematch --opponent australia --venue edgbaston
```

**Output:**
```
═══════════════════════════════════════════════════════════════
              INDIA VS AUSTRALIA AT EDGBASTON
                    Pre-Match Recommendation
═══════════════════════════════════════════════════════════════

SQUAD SELECTION (Best 11)
──────────────────────────
 1. Shafali Verma      (Opener, bat)
 2. Smriti Mandhana    (Opener, bat)
 3. Harmanpreet Kaur   (Middle, bat - Captain)
 4. Jemimah Rodrigues  (Middle, bat)
 5. Richa Ghosh        (Lower-middle, bat/wk)
 6. Deepti Sharma      (All-rounder)
 7. Axar Patel         (Spinner)
 8. Renuka Singh       (Pace bowler)
 9. Jhulan Goswami     (Pace bowler)
10. Ravindra           (Spinner)
11. Poonam Yadav       (Spinner)

BATTING ORDER (Optimized)
──────────────────────────
Position  Player                  Role
────────  ─────────────────────   ───────────────
#1        Shafali Verma          PowerPlay aggressor
#2        Smriti Mandhana        Consistent accumulator
#3        Harmanpreet Kaur       Middle-order pivot
#4        Jemimah Rodrigues      Flexible batter
#5        Richa Ghosh            Death hitter / WK
#6        Deepti Sharma          All-rounder
#7        Axar Patel             Lower-order support
#8        Renuka Singh           Pace bowler
#9        Jhulan Goswami         Pace bowler
#10       Ravindra               Spinner
#11       Poonam Yadav           Spinner

BOWLING PLAN
──────────────────────────
Phase           Bowlers              Role
────────────────────────────────────────────
PowerPlay (1-6) Renuka Singh (pace)   Early wickets, tight bowling
                Jhulan Goswami (pace) Swing bowling
                
Middle (7-16)   Ravindra (spin)      Pressure, slowing rate
                Axar Patel (spin)     Variations
                
Death (17-20)   Poonam Yadav (spin)  yorkers
                Jhulan Goswami (pace) Experience under pressure

STRATEGY BRIEF
──────────────────────────
Australia's Strengths:
  • Powerful opening pair (Healy, Mooney)
  • Death bowling expertise
  • Balanced team

Australia's Weaknesses:
  • Struggle vs leg-spin (Ravindra)
  • Middle order can collapse under pressure

INDIA'S APPROACH:
  • Aggressive PowerPlay: Use Shafali's strike rate (138) to
    dominate Alyssa Healy's opening spell
    
  • Spin pressure in middle: Ravindra vs Beth Mooney (88 SR vs spin)
    should restrict scoring
    
  • Balanced death batting: Richa Ghosh at #5 gives flexibility
    to accelerate if needed in overs 18-20

Win Probability (Based on History): 28% (Australia favored)

Recommendation: Focus on spin pressure in middle overs and use
opening aggression to score 160+ target.
```

**With verbose mode:**
```bash
wt20-oracle prematch --opponent australia --venue edgbaston --verbose
```

Shows detailed reasoning for each selection and order placement.

---

## Live Mode

Use this **during** a match to get instant recommendations:
- Should we change the bowler?
- Where should we place fielders?
- Should we send a pinch-hitter?
- What's our win probability?

### Basic Syntax

```bash
wt20-oracle live --match-state <JSON_FILE>
```

### Required Arguments

| Argument | What it is |
|----------|-----------|
| `--match-state` | Path to JSON file with current match situation |

### Match State JSON Format

Create a file (e.g., `india_vs_australia_over14.json`) with this structure:

```json
{
  "match_id": "wt20-2026-india-australia",
  "opponent": "australia",
  "venue": "edgbaston",
  "stage": "group",
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

### Example Usage

**Get live recommendation:**
```bash
wt20-oracle live --match-state india_vs_australia_over14.json
```

**Output:**
```
═══════════════════════════════════════════════════════════════
         LIVE MATCH RECOMMENDATION
         Over 14 | India batting: 87/3 | Need 63 from 36 balls
═══════════════════════════════════════════════════════════════

WIN PROBABILITY UPDATE
──────────────────────
Current: 45% → 48% (improving!)
Trend: Positive (Jemimah batting well)

RECOMMENDED ACTION
──────────────────
Next bowler: Bring on Megan Schutt (Pace)

Reason:
  • Jemimah Rodrigues has weak record vs left-arm pace
  • Her strike rate drops from 128 overall to 95 vs Schutt
  • Jess Jonassen (current) has conceded 28 runs in 3.5 overs (8.0 economy)
  • Fresh bowler can tighten the screws

Expected Outcome:
  • Reduce scoring rate from 8.0 to 6.5 per over
  • Increase pressure for potential wicket

FIELD PLACEMENT SUGGESTION
──────────────────────────
Setup: Defensive (protecting against 6s)

     Mid-wicket
         |
    Point  |  Square-leg
   /       |       \
F        (bowler)    F
   \       |       /
    Cover |  Fine-leg
         |

Reasoning: Jemimah tends to play through covers and square-leg.
Place fielders to block these areas and take catches.

NEXT 5 OVERS FORECAST
──────────────────────
Overs 15-20 (Death): Plan to accelerate
  • Target: 13-15 runs per over
  • Strategy: Rotate strike vs Schutt, then attack Jonassen

Current Run Rate: 5.8 per over
Required Rate: 6.2 per over
Status: ✓ On track (0.4 above required, healthy buffer)
```

---

## Common Options

### Output Formats

```bash
# Default (human-readable text)
wt20-oracle prematch --opponent australia --venue edgbaston

# JSON format (for other programs to read)
wt20-oracle prematch --opponent australia --venue edgbaston --format json

# CSV format (for spreadsheets)
wt20-oracle prematch --opponent australia --venue edgbaston --format csv
```

### Verbose/Debug Mode

```bash
# Show detailed reasoning for every decision
wt20-oracle prematch --opponent australia --venue edgbaston --verbose

# Show even more debugging info
wt20-oracle prematch --opponent australia --venue edgbaston --debug
```

### Help

```bash
# General help
wt20-oracle --help

# Help for specific command
wt20-oracle prematch --help
wt20-oracle live --help
```

---

## Examples

### Example 1: India vs Pakistan at Old Trafford

```bash
wt20-oracle prematch --opponent pakistan --venue "old trafford"
```

### Example 2: India vs South Africa at Lords (Verbose)

```bash
wt20-oracle prematch --opponent "south africa" --venue lords --verbose
```

### Example 3: Live Update During Match

First, create `match_state.json`:
```json
{
  "match_id": "wt20-2026-india-sa",
  "opponent": "south africa",
  "venue": "lords",
  "our_innings": {
    "batting_team": true,
    "current_score": 95,
    "wickets": 2,
    "overs": 15,
    "balls_faced": 90,
    "target": 145
  },
  "opponent_innings": {
    "score": 142,
    "wickets": 8,
    "overs": 20
  },
  "current_batter": {
    "name": "Harmanpreet Kaur",
    "runs_this_innings": 42,
    "balls_faced": 28,
    "strike_rate": 150
  },
  "current_bowler": {
    "name": "Marizanne Kapp",
    "overs_bowled": 3,
    "runs_given": 18,
    "wickets": 0,
    "economy": 6.0
  },
  "phase": "death",
  "momentum": "positive"
}
```

Then run:
```bash
wt20-oracle live --match-state match_state.json
```

---

## Troubleshooting

### Error: "Unknown opponent: australia"

**Problem:** You might have a typo or the system doesn't recognize the name.

**Solution:**
```bash
# Use exact team name (lowercase):
wt20-oracle prematch --opponent australia --venue edgbaston
# NOT: wt20-oracle prematch --opponent "Australia" --venue edgbaston
# NOT: wt20-oracle prematch --opponent "aus" --venue edgbaston
```

### Error: "Invalid venue: edgebaston"

**Problem:** Typo in venue name.

**Solution:** Check the [Valid Venues section](#valid-venues) above for exact spelling.

### Error: "File not found: india_vs_australia.json"

**Problem:** The match state file doesn't exist or is in the wrong folder.

**Solution:**
```bash
# Make sure you're in the right directory
ls -la india_vs_australia.json

# Or provide full path
wt20-oracle live --match-state /full/path/to/india_vs_australia.json
```

### Error: "Invalid JSON in match_state.json"

**Problem:** The JSON file has a syntax error.

**Solution:**
```bash
# Check your JSON file for:
# - Missing commas
# - Missing quotes
# - Mismatched brackets {}
# 
# Use a JSON validator: https://jsonlint.com/
```

### Command returns empty output

**Problem:** System is loading data or there's an issue.

**Solution:**
```bash
# Try verbose mode to see what's happening:
wt20-oracle prematch --opponent australia --venue edgbaston --verbose

# Check if data files exist:
ls wt20_oracle/data/players/
```

---

## Tips & Tricks

### Save output to a file

```bash
# Save pre-match recommendation to file
wt20-oracle prematch --opponent australia --venue edgbaston > recommendation.txt

# Save as JSON
wt20-oracle prematch --opponent australia --venue edgbaston --format json > recommendation.json
```

### Chain with other commands (for advanced users)

```bash
# Get JSON output and process with jq (JSON query tool)
wt20-oracle prematch --opponent australia --venue edgbaston --format json | jq '.squad'
```

### Running multiple analyses

```bash
# Create a script to run multiple matches:

#!/bin/bash
for opponent in australia pakistan bangladesh; do
  echo "Analyzing India vs $opponent at Edgbaston"
  wt20-oracle prematch --opponent $opponent --venue edgbaston
  echo "---"
done
```

---

## Next Steps

- **Understand the system:** [Architecture Overview](Architecture.md)
- **See all cricket terms:** [Glossary](Glossary.md)
- **Learn about the data:** [Data Schema](Data-Schema.md)
