# Opponent Analysis Node: Techniques & Methodology

Complete guide to the techniques used in the Opponent Analysis Node of wt20-oracle.

---

## Table of Contents

1. [Overview](#overview)
2. [Data Sources](#data-sources)
3. [Analysis Techniques](#analysis-techniques)
4. [Key Metrics](#key-metrics)
5. [Strengths & Weaknesses Assessment](#strengths--weaknesses-assessment)
6. [Implementation Details](#implementation-details)
7. [Example Analysis](#example-analysis)

---

## Overview

The **Opponent Analysis Node** studies the opposing team to identify:
- ✓ Batting strengths (which phases they excel in)
- ✓ Bowling strengths (which types of attacks work)
- ✓ Historical performance (win rates, form)
- ✓ Tactical tendencies (set plays, weak links)
- ✓ Venue-specific performance
- ✓ Head-to-head matchup records

This information is then used by downstream agents (Squad Selector, Batting Order Optimizer, Bowling Plan Creator) to make better decisions.

---

## Data Sources

### Team-Level Data

From `wt20_oracle/data/teams.json`:

```json
{
  "id": "australia",
  "name": "Australia",
  "group": "A",
  "icc_ranking": 2,
  "captain": "alyssa_healy",
  
  "batting_phase_performance": {
    "powerplay": {
      "avg_score": 45,
      "run_rate": 7.5,
      "avg_wickets_lost": 0.8,
      "wickets_taken_per_match": 5.2
    },
    "middle": {...},
    "death": {...}
  },
  
  "bowling_phase_performance": {...},
  
  "batting_first": {
    "matches": 24,
    "wins": 16,
    "avg_score": 152,
    "avg_winning_score": 165
  },
  
  "chasing": {
    "matches": 20,
    "wins": 14,
    "avg_target": 142,
    "avg_winning_score": 145
  },
  
  "h2h": {
    "india": {
      "matches": 24,
      "wins": 18,
      "losses": 6,
      "win_percentage": 75.0
    }
  },
  
  "last_12_months": {
    "matches": 18,
    "wins": 14,
    "losses": 4,
    "nrr": +0.85
  },
  
  "set_plays": [
    "powerplay_aggressive_batting",
    "pace_focused_bowling",
    "death_bowling_aggression"
  ],
  
  "weak_links": [
    "middle_order_vs_spin",
    "tail_batting",
    "chasing_on_spinner_friendly_pitches"
  ]
}
```

### Player-Level Data

From `wt20_oracle/data/players/{team}.json`:

```json
{
  "id": "alyssa_healy",
  "name": "Alyssa Healy",
  "team": "australia",
  "role": "wk_batter",
  "caps": 98,
  "t20i_stats": {
    "batting": {
      "matches": 98,
      "runs": 2890,
      "strike_rate": 138.4,
      "phase_splits": {
        "powerplay": {"balls": 520, "runs": 762, "strike_rate": 146.5},
        "middle": {"balls": 1120, "runs": 1240, "strike_rate": 110.7},
        "death": {"balls": 450, "runs": 888, "strike_rate": 197.3}
      },
      "vs_pace": {"strike_rate": 135.2, "dot_ball_pct": 18.5},
      "vs_spin": {"strike_rate": 142.1, "dot_ball_pct": 16.2},
      "form_windows": {
        "last_5_matches": {"matches": 5, "runs": 245, "strike_rate": 152.8},
        "last_6_months": {"matches": 18, "runs": 687, "strike_rate": 141.3}
      }
    },
    "bowling": {...}
  }
}
```

### Matchup Data

From `wt20_oracle/data/matchups.json`:

```json
{
  "smriti_mandhana_vs_megan_schutt": {
    "balls": 32,
    "runs": 38,
    "wickets": 1,
    "strike_rate": 118.75,
    "dismissal_rate": 0.031,
    "reliability": "high",
    "by_phase": {
      "powerplay": {"balls": 12, "runs": 18, "strike_rate": 150.0},
      "middle": {"balls": 15, "runs": 15, "strike_rate": 100.0},
      "death": {"balls": 5, "runs": 5, "strike_rate": 100.0}
    }
  }
}
```

### Venue Data

From `wt20_oracle/data/venues.json`:

```json
{
  "id": "edgbaston",
  "name": "Edgbaston",
  "city": "Birmingham",
  "pitch": {
    "type": "balanced",
    "pace_advantage": true,
    "spin_advantage": false
  },
  "conditions": {
    "dew_factor": "low",
    "typically_day_night": false
  },
  "women_t20_stats": {
    "avg_first_innings_score": 156,
    "pace_economy": 6.2,
    "spin_economy": 7.1
  }
}
```

---

## Analysis Techniques

### 1. Phase-Based Performance Analysis

**What it does:** Breaks down opponent's performance into three distinct phases.

**Phases:**
- **PowerPlay (Overs 1-6):** Aggressive batting phase
- **Middle (Overs 7-16):** Stabilization & accumulation phase
- **Death (Overs 17-20):** Final acceleration phase

**Metrics Calculated:**

For Batting in each phase:
```
avg_score          = total_runs / number_of_matches
run_rate          = runs / overs_in_phase
wickets_lost      = dismissals_per_match
strike_rate       = (runs / balls) × 100
dot_ball_pct      = (dot_balls / total_balls) × 100
```

For Bowling in each phase:
```
economy           = runs / overs_bowled
wickets_per_over  = wickets / overs_bowled
dot_ball_pct      = (dot_balls / total_balls) × 100
maiden_overs_pct  = (maiden_overs / total_overs) × 100
```

**Example Analysis:**
```
Australia vs India at Edgbaston:

Australia's Phase Performance:
┌─────────┬──────────┬──────────┬─────────────┐
│ Phase   │ Run Rate │ Wickets  │ Strike Rate │
├─────────┼──────────┼──────────┼─────────────┤
│ PP (1-6)│ 7.8/over │ 0.8 avg  │ 136%        │ ← Very strong
│ Mid(7-16)│ 6.2/over │ 1.2 avg  │ 115%        │ ← Average
│ Death(17-20)│ 7.5/over │ 1.1 avg  │ 148%        │ ← Strong finishers
└─────────┴──────────┴──────────┴─────────────┘

Insight: Australia excels in PowerPlay & Death
Recommendation: Contain in PP, attack in Middle overs
```

---

### 2. Opposition-Based Metrics (vs Pace/Spin)

**What it does:** Analyzes performance against different bowling types.

**Comparison Matrix:**

```
Opponent Batting vs Different Bowling:

Australia's Batting:
                 vs Pace  vs Spin  Difference
              ────────────────────────────────
Strike Rate     134.2    127.6    +6.6 (better vs pace)
Dot Ball %      18.2%    22.1%    -3.9% (fewer dots vs pace)
Dismissal Rate  0.063    0.048    +0.015 (more outs vs pace)

Interpretation:
  ✓ Australia scores FASTER against pace
  ✗ Australia struggles against spin (lower SR, more dots)
  
Tactical Insight:
  → Use spinners to slow down their scoring
  → Use pace in PowerPlay when they're most aggressive
```

**Implementation:**

```python
def calculate_opposition_split(player_stats, opposition_type):
    """
    opposition_type: "pace" or "spin"
    
    Returns:
      - strike_rate vs that type
      - dot_ball_percentage
      - dismissal_rate
    """
    if opposition_type == "pace":
        metrics = player_stats["vs_pace"]
    else:
        metrics = player_stats["vs_spin"]
    
    return {
        "strike_rate": metrics["strike_rate"],
        "dot_ball_pct": metrics["dot_ball_pct"],
        "dismissal_rate": metrics["dismissal_rate"]
    }
```

---

### 3. Form Window Analysis

**What it does:** Evaluates recency of performance (how a team is playing NOW).

**Three Time Windows:**

1. **Last 5 Matches** (Most recent)
   - Reflects current form
   - Heavily weighted in analysis
   - Can change rapidly

2. **Last 6 Months** (Medium-term)
   - Shows consistency
   - More stable than last-5
   - Accounts for seasonal variation

3. **Last 12 Months** (Long-term)
   - Career baseline
   - Shows overall capability
   - Used as fallback when recent form is limited

**Weighting Strategy:**

```
Form Weight = (
    0.50 × last_5_performance +
    0.30 × last_6_months_performance +
    0.20 × last_12_months_performance
)

Example: Australia's Alyssa Healy
┌──────────────┬─────────┬─────────┐
│ Window       │ SR      │ Weight  │
├──────────────┼─────────┼─────────┤
│ Last 5       │ 152.8   │ × 0.50  │
│ Last 6m      │ 141.3   │ × 0.30  │
│ Last 12m     │ 138.4   │ × 0.20  │
├──────────────┼─────────┼─────────┤
│ Weighted Avg │ 144.8   │ = 1.00  │
└──────────────┴─────────┴─────────┘

Interpretation: Healy is in EXCELLENT form
(144.8 SR is much higher than career 138.4)
```

---

### 4. Head-to-Head (H2H) Record Analysis

**What it does:** Analyzes historical matchups between India and opponent.

**Metrics:**

```json
{
  "india_vs_australia": {
    "matches_played": 24,
    "india_wins": 6,
    "australia_wins": 18,
    "win_percentage": 75.0,
    "india_streak": "loss",
    "india_streak_length": 4,
    "nrr_against_india": +0.45
  }
}
```

**Interpretation:**

```
Australia vs India (All Time):
  Matches: 24
  Australia wins: 18 (75%)
  India wins: 6 (25%)

What it means:
  → Australia DOMINATES this matchup
  → India wins only 1 in 4 times
  → Psychological disadvantage for India
  → Need strong strategy to overcome this trend

Recent Trend:
  India on 4-game losing streak vs Australia
  → Confidence factor: Lower for India
  → Motivation: Higher for India (need redemption)
```

**How It's Used:**

```python
def get_h2h_advantage(opponent_id, our_team_id="india"):
    """
    Calculate psychological/tactical advantage
    """
    h2h_data = teams[opponent_id]["h2h"][our_team_id]
    
    win_pct = h2h_data["india_wins"] / h2h_data["matches_played"]
    
    if win_pct > 0.55:
        advantage = "India favored"
    elif win_pct < 0.45:
        advantage = "Opponent favored"  # ← Australia case
    else:
        advantage = "Evenly matched"
    
    return {
        "historical_advantage": advantage,
        "win_percentage": win_pct,
        "recent_trend": h2h_data.get("india_streak")
    }
```

---

### 5. Toss Analysis

**What it does:** Analyzes how team performs in different toss outcomes.

**Metrics:**

```json
{
  "australia": {
    "toss": {
      "matches_won": 24,
      "times_elected_bat": 16,
      "bat_first_win_pct": 75.0,
      "times_elected_field": 8,
      "field_first_win_pct": 82.5
    }
  }
}
```

**Analysis:**

```
Australia's Toss Performance:

When Australia bats first:
  Matches: 16 | Wins: 12 | Win %: 75%
  → Australia likes batting first
  → Sets targets of ~160+
  → Strong in setting total

When Australia fields first (chases):
  Matches: 8 | Wins: 7 | Win %: 82.5%
  → Even STRONGER when chasing
  → More comfortable in chase mode
  → Good at accelerating in death overs

Insight: Australia is strong in BOTH scenarios
→ Toss advantage: AUSTRALIA
→ Strategy: Expect big totals if they bat; prepare for aggressive chase
```

---

### 6. Tactical Tendency Analysis

**What it does:** Identifies known set plays and weak links.

**Set Plays** (Strengths):

```python
opponent_set_plays = [
    "powerplay_aggressive_batting",      # Early aggression
    "pace_focused_bowling",               # Use fast bowlers
    "death_bowling_aggression",           # Yorker-heavy finish
    "field_placement_attacking"          # Close fielders in death
]

# Each set play has counter-strategies:
Counter_Strategies = {
    "powerplay_aggressive_batting": [
        "Use tight bowling",
        "Set defensive field",
        "Rotate strike bowlers"
    ],
    "pace_focused_bowling": [
        "Play out early overs",
        "Take singles",
        "Accelerate against spin"
    ]
}
```

**Weak Links** (Vulnerabilities):

```python
opponent_weak_links = [
    "middle_order_vs_spin",              # Vulnerable position
    "tail_batting",                      # Poor lower order batting
    "chasing_on_spinner_pitches"        # Weakness vs spin when chasing
]

# Exploitation strategies:
Exploitation = {
    "middle_order_vs_spin": {
        "technique": "Use spinners in middle overs",
        "players": ["Ravindra", "Axar Patel"],
        "expected_outcome": "Restrict scoring, increase pressure"
    },
    "tail_batting": {
        "technique": "Target bowlers with pace",
        "expected_outcome": "Quick wickets, lower final score"
    },
    "chasing_on_spinner_pitches": {
        "technique": "Play spin-friendly venues",
        "advantage": "Reduce opponent's chase confidence"
    }
}
```

---

### 7. Venue-Specific Analysis

**What it does:** Adjusts assessment based on where match is played.

**Key Venue Factors:**

```python
def analyze_opponent_at_venue(opponent, venue):
    """
    Adjust opponent analysis for specific venue
    """
    
    # 1. Pitch characteristics
    pitch_type = venue["pitch"]["type"]
    pace_friendly = venue["pitch"]["pace_advantage"]
    spin_friendly = venue["pitch"]["spin_advantage"]
    
    # 2. Conditions
    dew_factor = venue["conditions"]["dew_factor"]
    day_night = venue["conditions"]["typically_day_night"]
    
    # 3. Historical performance at venue
    historical_avg_score = venue["women_t20_stats"]["avg_first_innings_score"]
    pace_economy = venue["women_t20_stats"]["pace_economy"]
    spin_economy = venue["women_t20_stats"]["spin_economy"]
    
    # 4. Adjust opponent metrics
    if pace_friendly:
        opponent_pace_advantage = 1.15  # +15% boost to pace attack
    else:
        opponent_pace_advantage = 0.85
    
    if dew_factor == "high":
        # Dew helps pace bowling (movement reduction)
        opponent_bowling_adjustment = 1.10
    
    # Example: Australia at Edgbaston
    Analysis = {
        "venue": "Edgbaston",
        "pitch_type": "balanced",
        "pitch_advantage": "slight pace advantage",
        "historical_avg_score": 156,
        "dew_factor": "low",
        "australia_pace_attack_boost": 1.15,
        "india_batting_adjustment": 0.90  # harder to score
    }
```

---

### 8. NRR (Net Run Rate) Analysis

**What it does:** Evaluates goal differential performance.

**NRR Calculation:**

```
NRR = (Total Runs Scored / Overs Faced) - (Total Runs Conceded / Overs Bowled)

Example: Australia
  Scored: 1,460 runs from 240 overs (60 matches × 4 overs avg)
  Conceded: 1,190 runs from 240 overs
  
  NRR = (1,460/240) - (1,190/240)
      = 6.08 - 4.96
      = +1.12

Interpretation:
  Positive NRR (+1.12) = Strong team (scores more, concedes less)
  Benchmark: +0.3 to +0.5 = healthy, +1.0+ = elite
```

---

## Key Metrics Summary

| Metric | What It Shows | Range | Good/Bad |
|--------|---------------|-------|----------|
| **Strike Rate** | Scoring speed | 100-160 | >130: Excellent, <110: Poor |
| **Economy Rate** | Bowling tightness | 5.5-8.0 | <6.5: Excellent, >7.5: Loose |
| **Dot Ball %** | Defensive bowling | 15-35% | 25%+: Tight, <15%: Loose |
| **Dismissal Rate** | Getting out frequency | 0.03-0.10 | <0.05: Solid, >0.08: Risky |
| **Win % (H2H)** | Historical dominance | 0-100% | >60%: Strong advantage |
| **Form (Last 5)** | Current form | Varies | Higher than long-term: Hot form |
| **NRR** | Goal differential | -2 to +2 | >+0.5: Strong, <-0.5: Weak |

---

## Strengths & Weaknesses Assessment

### Systematic Assessment Framework

```python
def comprehensive_opponent_assessment(opponent_team):
    """
    Generate strengths & weaknesses report
    """
    
    assessment = {
        "BATTING STRENGTHS": [],
        "BATTING_WEAKNESSES": [],
        "BOWLING_STRENGTHS": [],
        "BOWLING_WEAKNESSES": [],
        "OVERALL_ADVANTAGE": None
    }
    
    # Batting Analysis
    if opponent_team["batting_phase_performance"]["powerplay"]["run_rate"] > 7.5:
        assessment["BATTING_STRENGTHS"].append(
            "PowerPlay aggression (RR > 7.5)"
        )
    else:
        assessment["BATTING_WEAKNESSES"].append(
            "Slow PowerPlay starts (RR < 7.5)"
        )
    
    # Bowling Analysis
    if opponent_team["bowling_phase_performance"]["death"]["economy"] < 7.0:
        assessment["BOWLING_STRENGTHS"].append(
            "Tight death bowling (Econ < 7.0)"
        )
    else:
        assessment["BOWLING_WEAKNESSES"].append(
            "Loose death bowling (Econ > 7.5)"
        )
    
    # H2H vs India
    h2h = opponent_team["h2h"].get("india", {})
    if h2h.get("win_percentage", 50) > 60:
        assessment["OVERALL_ADVANTAGE"] = f"OPPONENT favored (H2H: {h2h['win_percentage']}%)"
    elif h2h.get("win_percentage", 50) < 40:
        assessment["OVERALL_ADVANTAGE"] = f"INDIA favored (H2H: {100-h2h['win_percentage']}%)"
    else:
        assessment["OVERALL_ADVANTAGE"] = "EVENLY MATCHED"
    
    return assessment
```

---

## Implementation Details

### Data Access Pattern

```python
# File: wt20_oracle/agents/shared/opponent_node.py

from wt20_oracle.io.loader import load_teams, load_players, load_matchups
from wt20_oracle.schemas import TeamSchema

class OpponentAnalysisNode:
    """
    Analyzes opposing team to provide intelligence for squad selection,
    batting order optimization, and bowling plan creation.
    """
    
    def __init__(self):
        self.teams = load_teams()
        self.players = load_players()
        self.matchups = load_matchups()
    
    def analyze(self, opponent_id: str, venue_id: str) -> dict:
        """
        Perform complete opponent analysis
        """
        opponent = self.teams[opponent_id]
        venue = self.venues[venue_id]
        
        return {
            "opponent_id": opponent_id,
            "team_name": opponent["name"],
            "batting_analysis": self._analyze_batting(opponent, venue),
            "bowling_analysis": self._analyze_bowling(opponent, venue),
            "h2h_analysis": self._analyze_h2h(opponent),
            "tactical_analysis": self._analyze_tactics(opponent),
            "strengths": self._identify_strengths(opponent),
            "weaknesses": self._identify_weaknesses(opponent)
        }
    
    def _analyze_batting(self, opponent: TeamSchema, venue: dict) -> dict:
        """Phase-based batting analysis"""
        return {
            "powerplay": opponent["batting_phase_performance"]["powerplay"],
            "middle": opponent["batting_phase_performance"]["middle"],
            "death": opponent["batting_phase_performance"]["death"],
            "venue_adjustment": self._venue_adjustment(venue, batting=True)
        }
    
    def _analyze_bowling(self, opponent: TeamSchema, venue: dict) -> dict:
        """Bowling analysis with venue context"""
        return {
            "powerplay": opponent["bowling_phase_performance"]["powerplay"],
            "middle": opponent["bowling_phase_performance"]["middle"],
            "death": opponent["bowling_phase_performance"]["death"],
            "pace_economy": venue["women_t20_stats"]["pace_economy"],
            "spin_economy": venue["women_t20_stats"]["spin_economy"]
        }
    
    def _analyze_h2h(self, opponent: TeamSchema) -> dict:
        """Head-to-head record vs India"""
        return opponent["h2h"].get("india", {})
    
    def _analyze_tactics(self, opponent: TeamSchema) -> dict:
        """Known set plays and weak links"""
        return {
            "set_plays": opponent["set_plays"],
            "weak_links": opponent["weak_links"]
        }
```

---

## Example Analysis

### Complete Analysis: India vs Australia at Edgbaston

```
═══════════════════════════════════════════════════════════════
           OPPONENT ANALYSIS: AUSTRALIA AT EDGBASTON
═══════════════════════════════════════════════════════════════

1. BATTING ANALYSIS
───────────────────

PowerPlay (Overs 1-6):
  ├─ Run Rate: 7.8 runs/over (VERY STRONG)
  ├─ Wickets Lost: 0.8 per match (SOLID)
  ├─ Strike Rate: 136% (AGGRESSIVE)
  └─ Key Players: Alyssa Healy (146.5 SR), Beth Mooney (118 SR)

Middle (Overs 7-16):
  ├─ Run Rate: 6.2 runs/over (MODERATE)
  ├─ Wickets Lost: 1.2 per match
  ├─ Strike Rate: 115% (ACCUMULATION)
  └─ Weakness: Drop in scoring, potential collapse point

Death (Overs 17-20):
  ├─ Run Rate: 7.5 runs/over (STRONG)
  ├─ Strike Rate: 148% (POWERFUL)
  ├─ Wickets Lost: 1.1 per match
  └─ Pattern: Strong finishers, target 160-170

2. BOWLING ANALYSIS
─────────────────

PowerPlay Bowling:
  ├─ Economy: 6.0 runs/over (TIGHT)
  ├─ Wickets: 1.1 per match
  └─ Strategy: Aggressive upfront, pace-based

Middle Overs Bowling:
  ├─ Economy: 6.4 runs/over (DECENT)
  ├─ Wickets: 1.5 per match
  └─ Strength: Effective middle-phase pressure

Death Bowling:
  ├─ Economy: 6.8 runs/over (LOOSE)
  ├─ Wickets: 0.9 per match
  ├─ Weakness: Concedes in final overs
  └─ Opportunity: Target them in death phase

3. HEAD-TO-HEAD vs INDIA
──────────────────────

Overall Record:
  ├─ Matches: 24
  ├─ Australia Wins: 18 (75%)
  ├─ India Wins: 6 (25%)
  └─ Psychological Edge: STRONGLY IN AUSTRALIA'S FAVOR

Recent Trend:
  ├─ India's streak: 4 consecutive losses
  ├─ NRR against India: +0.45 (Australia stronger)
  └─ Pressure: India needs strong counter-strategy

4. TACTICAL INTELLIGENCE
───────────────────────

Australia's Set Plays (Strengths):
  ✓ PowerPlay aggression (exploit field restrictions)
  ✓ Pace-heavy bowling (exploit favorable pitch conditions)
  ✓ Death-over acceleration (target 160-170+)
  ✓ Attacking field placement in death overs

Australia's Weak Links (Vulnerabilities):
  ✗ Middle order struggles vs leg-spin
    └─ Ravindra's leg-breaks could be effective
  ✗ Tail batting is poor
    └─ Quick pace bowlers can finish quickly
  ✗ Weaknesses in chasing on spin-friendly pitches
    └─ If we can make a big total, their chase becomes harder

5. VENUE CONSIDERATIONS (EDGBASTON)
────────────────────────────────────

Pitch: Balanced (slight pace advantage)
  └─ Helps Australia's pace bowling slightly

Historical Avg Score at Edgbaston: 156
  └─ High-scoring venue favors Australia

Dew Factor: Low
  └─ No advantage to either team (no dew help for bowlers)

Expected Totals:
  ├─ Australia batting first: 160-170 (likely)
  └─ India chasing: Need 165+ to win

6. INDIA'S STRATEGIC RECOMMENDATIONS
─────────────────────────────────────

IF BATTING FIRST:
  ✓ Target: 165+ (neutralize Australia's chasing strength)
  ✓ Avoid: Getting bowled out (Australia's pace is tight)
  ✓ Focus: Use Shafali's SR (138+) in PowerPlay
  ✓ Middle overs: Stabilize, rotate strike vs pace

IF CHASING:
  ✓ Target: Accelerate to 165+ by over 18
  ✓ Danger phase: Overs 7-15 (their tight bowling)
  ✓ Advantage: Use leg-spin on middle order
  ✓ Death: Our death hitters vs their loose bowling

7. FINAL ASSESSMENT
────────────────────

Overall Difficulty: CHALLENGING
  ├─ Opponent Strength: 7.5/10
  ├─ H2H Record: Heavily favors Australia
  └─ Challenge Level: India is underdog

Key Success Factor:
  → EARLY WICKETS (break opening pair) or
  → STRONG POWERPLAY (bat 50+ in PP if batting first) or
  → SPIN PRESSURE (use Ravindra effectively)

Confidence Level for India: MODERATE
  ├─ Precedent: Only won 1 in 4 recent matches
  ├─ But: Edgbaston is neutral venue (not Australia's home)
  └─ Opportunity: Possible to beat them with good execution

═══════════════════════════════════════════════════════════════
```

---

## Output Format

The Opponent Analysis Node outputs this structured data:

```python
OpponentAnalysisOutput = {
    "opponent_id": "australia",
    "opponent_name": "Australia",
    "venue_id": "edgbaston",
    
    # Batting intelligence
    "batting": {
        "powerplay": {...},
        "middle": {...},
        "death": {...},
        "strengths": ["aggressive_pp", "strong_finishers"],
        "weaknesses": ["middle_order_inconsistency"]
    },
    
    # Bowling intelligence
    "bowling": {
        "pace_economy": 6.2,
        "spin_economy": 6.8,
        "strengths": ["tight_pp", "aggressive_death"],
        "weaknesses": ["loose_death", "no_left_arm_spinner"]
    },
    
    # Historical data
    "h2h": {
        "matches": 24,
        "our_wins": 6,
        "opponent_wins": 18,
        "our_win_pct": 25,
        "recent_trend": "losing"
    },
    
    # Tactical insights
    "tactics": {
        "set_plays": ["pp_aggression", "pace_focus"],
        "weak_links": ["vs_legbreak", "tail_batting"],
        "recommended_tactics": [
            "use_legbreak_in_middle",
            "target_tail_with_pace",
            "contain_in_pp"
        ]
    },
    
    # Overall assessment
    "assessment": {
        "difficulty": "challenging",
        "overall_strength": 7.5,
        "psychological_advantage": "opponent_favored",
        "recommended_strategy": "aggressive_start_or_spin_pressure"
    }
}
```

---

## Integration with Other Nodes

The Opponent Analysis output feeds into:

1. **Squad Selector Node**
   - Avoids weak matchups against opponent's bowlers
   - Picks players with good H2H records

2. **Batting Order Optimizer**
   - Places aggressive batters vs opponent's weak bowlers
   - Stacks middle order vs opponent's strength

3. **Bowling Plan Creator**
   - Targets opponent's weak links
   - Matches bowlers to phases where opponent is weakest

4. **Strategy Node**
   - Recommends tactical approach
   - Suggests field placements based on opponent tendencies

---

## Summary

The Opponent Analysis Node uses:

✓ **Phase-based analysis** (PowerPlay, Middle, Death)  
✓ **Opposition splits** (vs Pace, vs Spin)  
✓ **Form windows** (weighted recent performance)  
✓ **H2H records** (historical advantage)  
✓ **Toss analysis** (batting vs chasing patterns)  
✓ **Tactical intelligence** (set plays & weak links)  
✓ **Venue adjustment** (pitch & condition factors)  
✓ **NRR analysis** (overall team strength)  

These techniques combine to provide comprehensive intelligence that feeds into squad selection, batting order, and bowling strategy decisions.

