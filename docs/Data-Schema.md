# Data Schema Guide: Understanding the Data

This guide explains what data feeds wt20-oracle and how it's structured.

---

## Table of Contents

1. [Data Sources](#data-sources)
2. [Data Files Overview](#data-files-overview)
3. [Player Statistics Structure](#player-statistics-structure)
4. [Matchup Matrix](#matchup-matrix)
5. [Other Data Files](#other-data-files)
6. [Data Quality & Reliability](#data-quality--reliability)

---

## Data Sources

### Where the data comes from:

| Source | What it provides | Count | Reliability |
|--------|-----------------|-------|-------------|
| **CricSheet** | Ball-by-ball records of T20I matches | 1,943 T20I matches | Very High |
| **WPL** | Indian domestic league (women) | 88 matches | High |
| **WBBL** | Australian domestic league (women) | 519 matches | High |
| **The Hundred** | UK domestic league (women) | 155 matches | High |
| **ESPN Cricinfo** | Player statistics, career records | Career data | Very High |
| **ICC** | Tournament info, schedule, venues | Official data | Very High |
| **Scout Reports** | Expert opinions (analyst insights) | 15 players (India) | Expert-based |

**Total Coverage:**
- 2,705 total matches analyzed
- 178/180 players with statistics (98.9% coverage)
- 39,277 batter-bowler matchups

---

## Data Files Overview

All data is stored in `wt20_oracle/data/` folder:

```
wt20_oracle/data/
├── players/
│   ├── india.json              ← India squad (15 players)
│   ├── australia.json          ← Australia squad
│   ├── pakistan.json           ← Pakistan squad
│   └── [10 more teams]         ← All 12 teams
│
├── matchups.json               ← Head-to-head batter vs bowler records
├── analyst_insights.json       ← Expert qualitative assessments
├── venues.json                 ← Tournament venues
├── schedule.json               ← Match schedule
├── teams.json                  ← Team profiles & history
│
└── raw/                        ← Source data (not used at runtime)
    ├── cricsheet_t20i.csv      ← Processed CricSheet data
    └── [other source files]
```

---

## Player Statistics Structure

### Example: One Player's Data

Each team JSON file contains player objects. Here's what's inside:

```json
{
  "id": "smriti_mandhana",
  "name": "Smriti Mandhana",
  "role": "batter",
  "caps": 87,
  "jersey_number": 10,
  "handedness": "left",
  "t20i_stats": {
    "batting": {
      "matches": 87,
      "runs": 2,341,
      "not_outs": 12,
      "average": 28.9,
      "highest_score": 90,
      "strike_rate": 123.4,
      "centuries": 0,
      "half_centuries": 15,
      
      "phase_splits": {
        "powerplay": {
          "balls": 452,
          "runs": 567,
          "strike_rate": 125.4,
          "dot_ball_pct": 18.3,
          "dismissal_rate": 0.06
        },
        "middle": {
          "balls": 1,203,
          "runs": 1,089,
          "strike_rate": 90.5,
          "dot_ball_pct": 22.1,
          "dismissal_rate": 0.07
        },
        "death": {
          "balls": 389,
          "runs": 685,
          "strike_rate": 176.1,
          "dot_ball_pct": 12.4,
          "dismissal_rate": 0.08
        }
      },
      
      "vs_pace": {
        "balls": 845,
        "runs": 1,045,
        "strike_rate": 123.8,
        "dot_ball_pct": 19.2,
        "dismissal_rate": 0.06
      },
      
      "vs_spin": {
        "balls": 1,199,
        "runs": 1,296,
        "strike_rate": 108.1,
        "dot_ball_pct": 24.5,
        "dismissal_rate": 0.08
      },
      
      "vs_left_arm": {
        "balls": 234,
        "runs": 289,
        "strike_rate": 123.5,
        "dot_ball_pct": 20.1,
        "dismissal_rate": 0.09
      },
      
      "vs_right_arm": {
        "balls": 1,810,
        "runs": 2,052,
        "strike_rate": 123.4,
        "dot_ball_pct": 19.8,
        "dismissal_rate": 0.06
      },
      
      "form_windows": {
        "last_5_matches": {
          "matches": 5,
          "runs": 178,
          "balls": 142,
          "strike_rate": 125.4
        },
        "last_6_months": {
          "matches": 18,
          "runs": 512,
          "balls": 425,
          "strike_rate": 120.5
        },
        "last_12_months": {
          "matches": 32,
          "runs": 889,
          "balls": 725,
          "strike_rate": 122.6
        }
      },
      
      "icc_tournament_record": {
        "matches": 8,
        "runs": 267,
        "strike_rate": 128.4
      }
    },
    
    "bowling": {
      "matches": 34,
      "overs": 45.2,
      "runs_given": 312,
      "wickets": 11,
      "average": 28.4,
      "economy": 6.8,
      "best_figures": "2/18",
      
      "phase_splits": {
        "powerplay": { /* similar structure */ },
        "middle": { /* similar structure */ },
        "death": { /* similar structure */ }
      }
    }
  },
  
  "statistical_reliability": "high",
  "last_updated": "2026-05-15"
}
```

### Understanding the Fields

#### Basic Info
- **id**: Unique identifier (lowercase, underscore-separated)
- **name**: Full player name
- **role**: "batter", "bowler", or "all-rounder"
- **caps**: Number of T20I matches played
- **handedness**: "left" or "right" (hand used for batting)

#### Batting Statistics
- **matches**: Total T20I matches
- **runs**: Total runs scored
- **average**: Runs per match (dividing out dismissals)
- **strike_rate**: Runs per 100 balls (123.4 = scores 123.4 runs per 100 balls)
- **dot_ball_pct**: Percentage of balls with 0 runs (higher = more defensive)
- **dismissal_rate**: How often they get out (0.08 = out once every 12-13 innings)

#### Phase Splits (Most Important!)
Breaks down statistics by time periods:

- **PowerPlay (Overs 1-6)**: Aggressive phase
  - Usually higher strike rate
  - Fewer dot balls (more aggressive)
  - Example: Smriti's SR in PowerPlay (125.4) > Middle (90.5)

- **Middle Overs (7-16)**: Strategic accumulation
  - Medium strike rate
  - Balance between scoring and safety
  - Longest phase (10 overs)

- **Death Overs (17-20)**: Final push
  - Highest strike rate (batters taking risks)
  - Lowest dot ball percentage (almost all aggressive shots)
  - Example: Smriti's Death SR (176.1) is very high

#### vs Pace / vs Spin
- **vs Pace**: Stats specifically when facing fast bowlers (>140 km/h)
- **vs Spin**: Stats when facing slow bowlers (leg-spin, off-spin)

Example: Smriti scores 123.8 vs pace but only 108.1 vs spin = she prefers facing fast bowlers

#### Form Windows
Recent performance (crucial for deciding playing XI):

- **last_5_matches**: Most recent 5 games (freshest data)
- **last_6_months**: Last 6 calendar months
- **last_12_months**: Last 12 months

If a player's last_5_matches SR (125.4) > last_12_months SR (122.6) → Player is **in form**

---

## Matchup Matrix

This is a lookup table of all batter-vs-bowler head-to-head records.

### File Structure

`matchups.json` contains 39,277 entries like:

```json
{
  "smriti_mandhana_vs_megan_schutt": {
    "balls": 23,
    "runs": 38,
    "wickets": 1,
    "dot_balls": 4,
    "economy": 9.9,
    "strike_rate": 165.2,
    "dismissal_rate": 0.04,
    "reliability": "medium",
    "last_meeting": "2024-03-15",
    "meetings": [
      {
        "date": "2024-03-15",
        "venue": "sydney",
        "runs": 18,
        "balls": 12,
        "outcome": "not out"
      },
      {
        "date": "2023-11-22",
        "venue": "mumbai",
        "runs": 20,
        "balls": 11,
        "outcome": "out bowled"
      }
    ]
  }
}
```

### Understanding Matchup Data

| Field | Meaning | Example |
|-------|---------|---------|
| **balls** | Total balls faced by batter vs this bowler | 23 balls |
| **runs** | Total runs scored | 38 runs |
| **strike_rate** | Runs per 100 balls vs this bowler | 165.2 = very good |
| **reliability** | Confidence in this stat | "high" (>20 balls), "medium" (6-20), "low" (<6) |
| **dismissal_rate** | How often batter gets out | 0.04 = once in 25 times |

### Reliability Tiers

The system uses reliability tiers to decide how much to trust a matchup:

| Reliability | Balls | Confidence | Action |
|------------|-------|-----------|--------|
| **High** | 20+ | Very confident | Use actual matchup data |
| **Medium** | 6-20 | Somewhat confident | Use matchup with slight caution |
| **Low** | <6 | Not confident | Fall back to bowler's generic economy + batter's generic SR |

**Example:**
- Smriti vs Megan Schutt: 23 balls = **High reliability** → Use 165.2 SR directly
- Shafali vs unknown spinner: 2 balls = **Low reliability** → Use Shafali's generic SR vs spin instead

---

## Other Data Files

### venues.json

```json
{
  "edgbaston": {
    "city": "Birmingham",
    "country": "England",
    "capacity": 25000,
    "dimensions": {
      "boundary_short": 82,
      "boundary_long": 88
    },
    "pitch_type": "balanced",
    "dew_factor": "low",
    "historical_avg_score": 158,
    "historical_avg_first_innings": 165
  }
}
```

**Fields:**
- **pitch_type**: "batting-friendly", "balanced", "bowling-friendly"
- **dew_factor**: Moisture in evening affects ball swing
- **historical scores**: Average scores at this venue

### schedule.json

```json
{
  "wt20-2026": {
    "tournament_name": "ICC Women's T20 World Cup 2026",
    "dates": {
      "start": "2026-06-13",
      "end": "2026-07-05"
    },
    "group_stage": [
      {
        "match_id": "wt20-india-australia-edgbaston",
        "date": "2026-06-17",
        "team1": "india",
        "team2": "australia",
        "venue": "edgbaston",
        "stage": "group"
      }
    ],
    "knockout": [
      {
        "match_id": "wt20-sf1",
        "type": "semi-final",
        "date": "2026-06-29"
      }
    ]
  }
}
```

### teams.json

```json
{
  "india": {
    "code": "IND",
    "captain": "Harmanpreet Kaur",
    "coach": "Amol Muzumdar",
    "ranking": 2,
    "squad_size": 15,
    "h2h_vs": {
      "australia": {
        "played": 24,
        "won": 6,
        "lost": 18,
        "no_result": 0,
        "win_percentage": 25.0
      }
    }
  }
}
```

### analyst_insights.json

```json
{
  "india": {
    "harmanpreet_kaur": {
      "form_rating": "exceptional",
      "form_confidence": 0.95,
      "form_notes": "Scored 45 vs Australia, 38 vs Pakistan in recent games",
      "strengths": ["Leadership", "Flexibility", "Death hitting"],
      "concerns": null,
      "injury_status": "fit",
      "vs_opponent": {
        "australia": {
          "notes": "Prefers facing pace, struggles slightly vs leg-spin",
          "recommendation": "Avoid Alana King in middle overs"
        }
      },
      "psychological_state": "confident",
      "last_updated": "2026-05-15"
    }
  }
}
```

---

## Data Quality & Reliability

### Coverage Statistics

- **Players:** 178/180 (98.9%) with T20I statistics
  - Missing: Maisie Maceira (Scotland), Rosalie Lawrence (Netherlands)
  - Reason: No CricSheet data available

- **Matchups:** 39,277 pairs
  - High reliability (>20 balls): 4,089 pairs (10.4%)
  - Medium reliability (6-20 balls): 15,843 pairs (40.3%)
  - Low reliability (<6 balls): 19,345 pairs (49.3%)

- **Analyst Insights:** 
  - India: 100% (all 15 players)
  - Other teams: Placeholder structure only

### Data Processing

The data goes through several quality checks:

1. **CricSheet Alias Mapping**
   - Example: "N Sharma" in CricSheet = Nandini Sharma
   - 125 mappings created for consistency

2. **Form Windows**
   - Calculated based on match dates
   - Only recent matches used for "form"

3. **Phase-Based Splits**
   - Overs 1-6 = PowerPlay
   - Overs 7-16 = Middle
   - Overs 17-20 = Death

4. **Validation Checks**
   - Player must have minimum matches
   - Statistics must be numerically sound
   - No negative values, no impossible percentages (>100%)

---

## How Data Flows Through the System

```
Raw Data (CricSheet, Cricinfo)
        ↓
Processing (scripts/parse_cricsheet.py)
  • Extract stats
  • Calculate form windows
  • Build matchup matrix
  • Apply reliability tiers
        ↓
JSON Files (wt20_oracle/data/)
        ↓
Runtime Loading (io/loader.py)
  • Load all data into memory
  • Create lookup tables
        ↓
Agents Use Data
  • Squad Selector: uses player stats
  • Batting Order: uses form windows
  • Bowling Plan: uses bowler economy
  • Live Recommender: uses matchup matrix
        ↓
Output
```

---

## Tips for Understanding the Data

### How to Read a Strike Rate

**124.5 strike rate** means:
- If this player faces 100 balls
- They will score ~124.5 runs
- That's about 2.45 runs per ball (124.5 ÷ 50 balls in a "normal" 50-over match)

### How to Read an Economy Rate

**6.8 economy** means:
- If this bowler bowls 1 over (6 balls)
- They give away ~6.8 runs
- That's a "good" economy in T20

### Dot Ball Percentage

**22% dot balls** means:
- Out of every 100 balls bowled (or faced)
- 22 have 0 runs
- 78 have 1 or more runs
- Higher dot ball % = more defensive / tight bowling

### Dismissal Rate

**0.07 dismissal rate** means:
- This player gets out about once every 14 times they bat
- 0.07 × 14 ≈ 1

---

## Glossary: Data Terms

| Term | Meaning |
|------|---------|
| **Statistic** | Numerical summary of performance |
| **Reliability** | How confident we are in a stat |
| **Phase Split** | Breaking down stats by time period |
| **Matchup** | Head-to-head record |
| **Form Window** | Recent performance |
| **Analyst Insight** | Expert opinion (not data) |
| **Schema** | Structure of how data is organized |
| **Validation** | Checking data quality |

---

## Next Steps

- **Learn how data is used:** [Architecture Overview](Architecture.md)
- **See all cricket terms:** [Glossary](Glossary.md)
- **Get started using the system:** [Getting Started](GETTING_STARTED.md)
