# Squad Selector Node Documentation

## Overview

The **Squad Selector Node** is a critical component of the wt20-oracle pre-match pipeline. It takes a pool of available players (typically 15) and selects the optimal 11 players to play against a specific opponent at a specific venue.

This node operates after the Opponent Analysis Node has completed and uses the opponent's weaknesses and the venue characteristics to build a balanced, matchup-aware squad.

---

## Input

The Squad Selector receives state from:

1. **Opponent Analysis** (from OpponentAnalysisNode):
   - Opponent's key strengths/weaknesses
   - Preferred batting/bowling strategies
   - Vulnerable player matchups
   - Phase-specific vulnerabilities

2. **Venue Analysis** (from venue data):
   - Pitch characteristics (batsman-friendly vs bowler-friendly)
   - Dew factor (day-night matches)
   - Historical conditions
   - Weather patterns

3. **Available Squad**:
   - 15 eligible players with their stats
   - Recent form data
   - Previous tournament records

4. **Team Constraints**:
   - Balance requirements (minimum bowlers, maximum batting-heavy)
   - Captain designation
   - Player availability/injuries

---

## Techniques for Squad Selection

### 1. **Optimal Balance Constraint (OBC)**

The node ensures the selected 11 has proper structure:

```
Balanced Squad = {
  Batters: 5-7 players
  Bowlers: 4-5 players
  All-rounders: 1-3 players
  Wicket-keeper: 1 player
}
```

**Why?** T20 requires flexibility. Too many batters risks weak bowling; too many bowlers weakens batting depth.

**Implementation Pattern:**
```python
def validate_squad_balance(squad):
    batter_count = sum(1 for p in squad if p['role'] == 'batter')
    bowler_count = sum(1 for p in squad if p['role'] == 'bowler')
    allrounder_count = sum(1 for p in squad if p['role'] == 'all-rounder')
    
    assert 5 <= batter_count <= 7, "Batting strength imbalanced"
    assert 4 <= bowler_count <= 5, "Bowling strength imbalanced"
    return True
```

---

### 2. **Matchup-Aware Selection (MAS)**

Prioritize players who have favorable matchups against the opponent's key bowlers/batters.

**Data Source:** `matchups.json`
```json
{
  "batter": "Smriti Mandhana",
  "bowler": "Megan Schutt",
  "meetings": 25,
  "vs_pace": {
    "runs": 125,
    "balls": 100,
    "strike_rate": 125.0
  },
  "reliability": "high"
}
```

**Selection Logic:**
```
Score(Player) = Base_Form * 0.40 + 
                Venue_Performance * 0.30 + 
                Matchup_Advantage * 0.30

Where:
  - Base_Form = recent average (last 5 matches)
  - Venue_Performance = strike rate at this venue (if available)
  - Matchup_Advantage = score vs opponent's key bowlers
```

**Example:**
```
Smriti Mandhana vs Australia:
  - Base form (last 5): 125 SR
  - At Edgbaston: 118 SR
  - vs Australia pace attack: 125 SR (avg vs Schutt/Starc)
  
  Combined Score = (125 * 0.40) + (118 * 0.30) + (125 * 0.30) = 122.1
  
Recommendation: ✓ Select Smriti
```

---

### 3. **Opponent Weakness Exploitation (OWE)**

Select players who can exploit the opponent's identified weaknesses.

**If opponent is weak vs leg-spin:** Prioritize leg-spinners in bowling selections

**If opponent struggles in PowerPlay:** Ensure aggressive openers are selected

**Data Flow:**
```
Opponent Analysis Output:
  "weaknesses": [
    "Struggles vs leg-spin (avg 28 SR)",
    "Weak against yorkers (13% dot ball rate)"
  ]

Squad Selector Decision:
  → Include Arundhati Reddy (yorker specialist) 
  → Include Ravindra (leg-spinner)
  → Include Smriti (aggressive vs pace in PowerPlay)
```

---

### 4. **Form Window Weighted Selection (FWS)**

Prioritize in-form players using time-weighted averaging.

**Formula:**
```
Form_Score = (Recent_Form * 0.50) + 
             (Last_6M * 0.30) + 
             (Last_12M * 0.20)

Where:
  - Recent_Form = average of last 5 matches
  - Last_6M = average of matches in last 6 months
  - Last_12M = average of matches in last 12 months
```

**Example (Batting Average):**
```
Player: Harmanpreet Kaur

Last 5 matches: [35, 42, 28, 51, 38]      → avg = 38.8
Last 6 months (20 matches): [32, 35, ...]  → avg = 34.2
Last 12 months (35 matches): [30, ...]     → avg = 32.1

Form_Score = (38.8 * 0.50) + (34.2 * 0.30) + (32.1 * 0.20)
           = 19.4 + 10.26 + 6.42
           = 36.08 (Current form)
```

**Interpretation:**
- Score 36.08 indicates excellent current form
- Gives more weight to recent matches (more predictive)
- Older performance still matters (consistency indicator)

---

### 5. **Venue-Specific Selection (VSS)**

Adapt squad based on venue characteristics.

**Pitch Type Classification:**
```
Batsman-Friendly Venues:
  - The Oval, Rose Bowl, Edgbaston
  - Action: Include extra batter, reduce bowler count
  - Example: 6 batters instead of 5

Bowler-Friendly Venues:
  - Old Trafford, Headingley
  - Action: Include extra bowler, 4-5 spinners
  - Example: 5 bowlers instead of 4

Spin-Heavy Venues:
  - Edgbaston (spinners often dominant)
  - Action: Include spin-hitting specialists
  - Example: Prefer Jemimah (good vs spin)
```

**Dew Factor Adjustment:**
```
High Dew Venue (evening matches):
  - Bias toward pace bowlers (dew makes bowling harder)
  - Include death bowlers with yorker skills
  - Reduce spinner count

Low Dew Venue:
  - Increase spinner count
  - Can afford slower bowlers
```

---

### 6. **Role-Based Depth (RBD)**

Ensure each position has sufficient depth and competition.

**Position Requirements:**

| Position | Minimum | Preferred | Max | Notes |
|----------|---------|-----------|-----|-------|
| Opening Batter | 2 | 2 | 3 | Fast, aggressive |
| Middle Order | 2 | 3 | 4 | Balanced hitters |
| Lower Order | 1 | 1 | 2 | Bowlers who bat |
| Pace Bowler | 2 | 3 | 4 | Mix of lengths |
| Spinner | 1 | 2 | 3 | Off + Leg variety |
| All-Rounder | 1 | 1 | 3 | Flexible players |
| Wicket-Keeper | 1 | 1 | 1 | Non-negotiable |

**Why?** Injuries can occur; bench strength ensures backup in each role.

---

### 7. **Experience & Tournament Form (ETF)**

Weight recent tournament performance heavily.

**Data Source:** `players.json` with match history
```json
{
  "name": "Richa Ghosh",
  "tournaments": {
    "t20_wc_2026": {
      "matches": 4,
      "runs": 156,
      "average": 39.0,
      "strike_rate": 145.2
    },
    "bilateral_2025": {
      "matches": 15,
      "runs": 320,
      "average": 21.3
    }
  }
}
```

**Selection Priority:**
```
Tournament_Experience_Score = (T20_WC_Performance * 0.60) + 
                              (Recent_Bilateral * 0.40)

Players with strong T20 World Cup form get higher priority.
Players with limited tournament experience get lower priority.
```

---

### 8. **Captaincy & Leadership (CAL)**

Designate captain and ensure leadership distribution.

**Captain Selection Criteria:**
```
Captain = Arg max(
  (Experience * 0.30) +
  (Current_Form * 0.25) +
  (Batting_Ability * 0.25) +
  (Leadership_History * 0.20)
)
```

**Typical Choice:** Harmanpreet Kaur (captain in most India T20 WC squads)

**Vice-Captain Consideration:** All-rounder with leadership qualities (e.g., Deepti Sharma)

---

## Data Structures

### Input: Player Pool

```json
{
  "available_players": [
    {
      "name": "Smriti Mandhana",
      "role": "batter",
      "status": "available",
      "recent_form": {
        "last_5_avg": 35.2,
        "strike_rate": 125.0
      },
      "vs_opponent": {
        "avg": 38.0,
        "sr": 128.0,
        "meetings": 12
      }
    }
  ],
  "squad_size": 15,
  "selection_target": 11
}
```

### Output: Selected Squad

```json
{
  "squad": [
    {
      "position": 1,
      "name": "Shafali Verma",
      "role": "batter",
      "reason": "Highest SR in PowerPlay (142), crucial vs Australia's pace",
      "matchup_confidence": "high",
      "form_score": 38.2
    },
    {
      "position": 2,
      "name": "Smriti Mandhana",
      "role": "batter",
      "reason": "Consistent form (125 SR), 12 meetings vs Schutt avg 128 SR",
      "matchup_confidence": "high",
      "form_score": 36.8
    }
  ],
  "balance_check": {
    "batters": 6,
    "bowlers": 4,
    "all_rounders": 1,
    "wicket_keeper": 1,
    "status": "balanced"
  },
  "exclusions_reasoning": {
    "excluded_player": "Why not selected",
    "Pooja_Vastrakar": "Injured, unavailable"
  }
}
```

---

## Real-World Example: India vs Australia at Edgbaston

### Available Squad (15 players)

```
Batters:
  1. Shafali Verma (SR 142, 12 IPL-equivalent)
  2. Smriti Mandhana (SR 125, 12 WC experience)
  3. Harmanpreet Kaur (Captain, SR 118, leader)
  4. Jemimah Rodrigues (SR 115, vs spin expert)
  5. Richa Ghosh (WK, SR 145, fast hitter)
  6. Yashasvi Jaiswal (SR 130, emergent)

Bowlers:
  7. Renuka Singh (Pace, 20+ wickets)
  8. Jhulan Goswami (Pace, experience, death bowler)
  9. Ravindra (Leg-spin, vs Australia weakness)
  10. Deepti Sharma (All-rounder, off-spin)
  11. Pooja Vastrakar (Pace, all-rounder, INJURED)
  12. Axar Patel (Spin, left-arm)
  13. Poonam Yadav (Leg-spin backup)

Others:
  14. Arundhati Reddy (Pace, yorker specialist)
  15. Shruti Vaidya (Spin, back-up)
```

### Selection Process

**Step 1: Apply Constraints**
```
Required: 1 WK, 5-7 batters, 4-5 bowlers, 1 all-rounder
Remove: Pooja Vastrakar (injured) → 14 available
```

**Step 2: Matchup Analysis**
```
Australia's Key Bowlers:
  - Megan Schutt (pace): Smriti scores 125 SR (12 meetings)
  - Jess Jonassen (spin): Jemimah scores 118 SR (8 meetings)

India's Counter:
  ✓ Smriti (strong vs Schutt)
  ✓ Jemimah (strong vs Jonassen)
  ✓ Shafali (aggressive in PowerPlay)
```

**Step 3: Venue Analysis**
```
Edgbaston Profile:
  - Batsman-friendly (avg 145 total)
  - Spinners historically dominant
  - Dew factor: Moderate

Adjustment:
  → Include 2 spinners (Ravindra + Deepti)
  → Reduce to 4 pace bowlers
  → Boost batting (6 batters)
```

**Step 4: Form Weighting**
```
Top Scorers (Last 5 matches):
  1. Richa Ghosh: 156 runs, 39 avg, 145 SR ✓ Select
  2. Shafali Verma: 178 runs, 35.6 avg, 142 SR ✓ Select
  3. Smriti Mandhana: 162 runs, 32.4 avg, 125 SR ✓ Select
  4. Harmanpreet Kaur: 156 runs, 31.2 avg, 118 SR ✓ Select (Captain)
  5. Jemimah Rodrigues: 145 runs, 29 avg, 115 SR ✓ Select
  6. Yashasvi Jaiswal: 131 runs, 26.2 avg, 130 SR ✓ Select
```

**Step 5: Bowling Selection**
```
Priority Bowlers:
  1. Renuka Singh (Form: 3 wickets/match avg) ✓ Select
  2. Jhulan Goswami (Death specialist, experience) ✓ Select
  3. Ravindra (Leg-spin vs Australia) ✓ Select
  4. Deepti Sharma (All-rounder, off-spin, balance) ✓ Select
  
Excluded:
  - Pooja Vastrakar (injured)
  - Arundhati Reddy (less form than Renuka)
  - Axar Patel (less wickets than Deepti in last window)
```

### Selected Squad (11 players)

```
BATTING ORDER:
 1. Shafali Verma (Opener, aggressive)
 2. Smriti Mandhana (Opener, consistent)
 3. Harmanpreet Kaur (Captain, middle-order)
 4. Jemimah Rodrigues (Middle, vs spin specialist)
 5. Richa Ghosh (WK, aggressive finisher)
 6. Yashasvi Jaiswal (Lower middle, power hitter)
 7. Deepti Sharma (All-rounder, bowler)

BOWLING:
 8. Renuka Singh (Pace, opening bowler)
 9. Jhulan Goswami (Pace, death bowler)
10. Ravindra (Leg-spin, Australia weakness)
11. Poonam Yadav (Leg-spin, backup)

Squad Balance:
  - Batters: 6 (Shafali, Smriti, Harmanpreet, Jemimah, Richa, Yashasvi)
  - Bowlers: 4 (Renuka, Jhulan, Ravindra, Poonam)
  - All-rounders: 1 (Deepti)
  - Wicket-keeper: 1 (Richa)
  ✓ BALANCED
```

---

## Integration with Other Nodes

The Squad Selector outputs a decision that flows to:

1. **Batting Order Optimizer Node**
   - Receives: Selected 11 players
   - Uses: Individual player strengths, venue factors
   - Outputs: Positions 1-11 in batting order

2. **Bowling Plan Node**
   - Receives: Selected bowlers (positions 8-11)
   - Uses: Opponent's batting order, phases
   - Outputs: Bowling assignments per phase

3. **Strategy Node**
   - Receives: Full squad composition
   - Uses: Overall balance, vs opponent analysis
   - Outputs: Tactical recommendations

---

## Implementation Pattern

```python
class SquadSelectorNode:
    """Selects optimal 11 from 15 available players."""
    
    def __init__(self, opponent_analysis, venue_data):
        self.opponent = opponent_analysis
        self.venue = venue_data
    
    def score_player(self, player, opponent, venue):
        """Calculate selection score using weighted factors."""
        base_form = self._calculate_form_score(player)
        matchup_score = self._calculate_matchup_score(
            player, opponent
        )
        venue_score = self._calculate_venue_score(player, venue)
        
        return (
            base_form * 0.40 +
            matchup_score * 0.35 +
            venue_score * 0.25
        )
    
    def validate_squad(self, squad):
        """Ensure squad meets balance constraints."""
        batter_count = sum(1 for p in squad if p['role'] == 'batter')
        bowler_count = sum(1 for p in squad if p['role'] == 'bowler')
        
        assert 5 <= batter_count <= 7
        assert 4 <= bowler_count <= 5
        return True
    
    def select_squad(self, available_players):
        """Main selection logic."""
        # Score all players
        scores = [
            (self.score_player(p, self.opponent, self.venue), p)
            for p in available_players
        ]
        
        # Sort by score
        scores.sort(reverse=True)
        
        # Select top 11 with balance constraints
        squad = []
        for score, player in scores:
            squad.append(player)
            if len(squad) == 11:
                break
        
        # Validate balance
        self.validate_squad(squad)
        
        return squad
```

---

## Key Metrics

| Metric | Interpretation | Range |
|--------|---|---|
| **Selection Score** | Overall suitability for match | 0-100 |
| **Matchup Confidence** | Expected performance vs bowler | low/medium/high |
| **Form Score** | Recent performance level | 20-50 |
| **Venue Fit** | Historical performance at venue | 0-100 |
| **Balance Index** | Squad structure score | 0-100 |

---

## Typical Output Summary

```
SQUAD SELECTION ANALYSIS: India vs Australia at Edgbaston

Selected 11:
✓ Shafali Verma (Opener, Form: 38.2, Matchup: High)
✓ Smriti Mandhana (Opener, Form: 36.8, Matchup: High)
✓ Harmanpreet Kaur (Captain, Form: 34.5, Matchup: Medium)
✓ Jemimah Rodrigues (Middle, Form: 32.1, Matchup: High)
✓ Richa Ghosh (WK, Form: 39.0, Matchup: Medium)
✓ Yashasvi Jaiswal (Lower, Form: 35.2, Matchup: Medium)
✓ Deepti Sharma (All-rounder, Form: 33.8, Matchup: Low)
✓ Renuka Singh (Bowler, Recent wickets: 3.2/match)
✓ Jhulan Goswami (Bowler, Death specialist, Experience)
✓ Ravindra (Spinner, High vs Australia, Form: 32.1)
✓ Poonam Yadav (Spinner, Backup, Form: 30.5)

Squad Balance: EXCELLENT
  - Batting Depth: 6 strong batters
  - Bowling Strength: 4 quality bowlers
  - All-rounder Value: 1 (Deepti provides flexibility)
  - Wicket-keeper: 1 (Richa - explosive finisher)

Key Exclusions:
✗ Pooja Vastrakar - Injured, unavailable
✗ Arundhati Reddy - Less form than Renuka (2.8 vs 3.2 w/m)
✗ Axar Patel - Reduces spinner variety balance

Matchup Advantage vs Australia:
✓ Smriti + Shafali outmatch opening bowlers
✓ Jemimah strong vs Jonassen (leg-spin)
✓ Ravindra targets weakness vs leg-spin
✓ Richa's aggression vs Starc in death overs

Venue Advantage (Edgbaston):
✓ Batsman-friendly pitch → 6 batters appropriate
✓ Spinner-dominant venue → 2 spinners included
✓ Historical dew → Jhulan (death specialist) crucial

Confidence Level: VERY HIGH (Score: 87/100)
```

---

## Related Documentation

- [Opponent Analysis Node](OPPONENT_ANALYSIS.md)
- [Batting Order Optimizer](BATTING_ORDER.md)
- [Bowling Plan Creator](BOWLING_PLAN.md)
- [Data Schema Reference](Data-Schema.md)
- [Pre-Match Mode Guide](../wiki/Pre-Match-Mode.md)

