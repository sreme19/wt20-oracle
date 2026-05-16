# Batting Order Optimizer Node Documentation

## Overview

The **Batting Order Optimizer Node** takes the selected 11 players and arranges them into an optimal batting order (positions 1-11) based on player strengths, match phases, and opponent-specific weaknesses.

In T20 cricket, batting order dramatically impacts match outcomes. An opener suited for PowerPlay aggression might collapse under death-over pressure. The optimizer considers all these factors to maximize expected team runs.

---

## The Batting Order Problem

**Input:** 11 selected players  
**Output:** Positions 1-11 in batting order  
**Constraint:** No player can appear twice; all must be used

**Why It's Complex:**
- Different phases (PowerPlay/Middle/Death) have different optimal players
- Risk of collapse if aggressive players bat early but form a weak middle order
- Momentum matters: early wickets require stable middle-order stabilizers
- Opponent matchups: some batters demolish certain bowlers

---

## Key Techniques

### 1. **Phase-Appropriate Positioning (PAP)**

Different batting positions need different skill sets across T20 phases.

#### PowerPlay (Overs 1-6): Aggression Required

**Desired Player Profile:**
- High strike rate (130+)
- Comfortable against pace
- Aggressive shot selection
- Low ball-dot percentage

**Optimal Positions:** 1, 2
**Example:** Shafali Verma (SR 142), Smriti Mandhana (SR 125)

#### Middle Overs (Overs 7-16): Stability & Acceleration

**Desired Player Profile:**
- Balanced aggression-safety ratio
- Can rotate strike
- Builds partnerships
- Medium-high strike rate (110-130)

**Optimal Positions:** 3, 4, 5, 6
**Example:** Harmanpreet Kaur (Captain, 118 SR), Jemimah Rodrigues (115 SR)

#### Death Overs (Overs 17-20): Power Hitting

**Desired Player Profile:**
- High strike rate (140+)
- Explosive shot-making
- Boundary-hitting ability
- Comfortable under pressure

**Optimal Positions:** 6, 7, 8
**Example:** Richa Ghosh (SR 145), Deepti Sharma (All-rounder flexibility)

**Phase-Based Strike Rate Expectations:**

```
Phase          Position(s)  Required SR  Priority
─────────────────────────────────────────────────
PowerPlay      1-2          130-150      HIGHEST
Middle         3-6          110-130      HIGH
Death          7-8          140-160      HIGHEST
```

---

### 2. **Opposition Matchup Optimization (OMO)**

Arrange batters to face bowlers they score well against.

**Key Principle:** Early batters face opening bowlers; late batters face death bowlers.

**Matchup Data Structure:**
```json
{
  "batter": "Smriti Mandhana",
  "matchup_matrix": {
    "Megan Schutt": {
      "strike_rate": 125,
      "runs": 125,
      "balls": 100,
      "meetings": 12,
      "reliability": "high"
    },
    "Jess Jonassen": {
      "strike_rate": 108,
      "runs": 75,
      "balls": 69,
      "meetings": 8,
      "reliability": "high"
    }
  }
}
```

**Optimization Formula:**

```
Position_Score(Batter) = Σ(
  Matchup_vs_Bowler[i] * Phase_Weight[i]
)

Where:
  - Matchup_vs_Bowler[i] = expected SR vs bowler at phase i
  - Phase_Weight[i] = importance weight for phase i
```

**Example: India vs Australia at Edgbaston**

```
Opening Bowlers (Australia):
  - Schutt (pace): 6 overs expected
  - Starc (pace): 6 overs expected

Best vs Schutt:
  1. Smriti (125 SR, 12 meetings)
  2. Shafali (128 SR, 10 meetings)

Decision: Place Smriti & Shafali at #1-2
Why: Their SR vs Australia openers will maximize PowerPlay runs
```

---

### 3. **Momentum & Partnership Building (MPB)**

Build a batting lineup that maintains momentum through wicket losses.

**Wicket Loss Scenario:** If opener falls in over 3, middle order must stabilize.

**Partnership Strategy:**

```
Strong Openers: Shafali (142 SR), Smriti (125 SR)
    ↓
    │ (If Shafali out by over 3)
    ↓
Stabilizer: Harmanpreet (Captain, 118 SR, experienced)
    ↓
    │ (If Harmanpreet out by over 10)
    ↓
Accelerator: Jemimah (115 SR, aggressive in middle)
    ↓
    │ (If Jemimah out by over 15)
    ↓
Death Hitter: Richa (145 SR, finisher)
```

**Momentum Loss Prevention:**

Position players such that:
1. Never have 3+ weak batters in a row
2. Balance aggressive with stable players
3. Ensure death overs have explosive power

---

### 4. **Captain's Position Optimization (CPO)**

Place the captain strategically for maximum influence.

**Typical Positions:** 3, 4, 5
**Reason:** Allows captain to witness entire match arc before batting

**Example:** Harmanpreet Kaur
- Witness opening pair's dominance or collapse
- Adjust middle-order strategy if needed
- Can stabilize if early wickets fall
- Leads by example in critical moments

**Position #3 Considerations:**
- Can't be too aggressive (need stability)
- Can't be too conservative (need runs)
- Should be experienced leader
- Familiar with all opponent bowlers

---

### 5. **Wicket-Keeper Positioning (WKP)**

Place wicket-keeper balancing batting and fielding duties.

**Position Options:**
- **Early (4-5):** Risky if WK gets out, but maximizes their batting time
- **Mid (5-6):** Balanced approach
- **Late (7):** Conservative, ensures late-order hitting

**For Richa Ghosh (Aggressive WK):**
- High SR (145) → suitable for early positions
- Can build innings in middle overs
- **Optimal Position:** 5-6 (allows full innings with buildup)

---

### 6. **Role-Based Sequencing (RBS)**

Arrange pure bowlers who can bat in order of batting ability.

**Bowler Batting Tiers:**

```
TIER 1 (Can bat like batter):
  - Deepti Sharma (all-rounder, 90+ SR)
  
TIER 2 (Can contribute in partnership):
  - Jhulan Goswami (batting SR 60+)
  
TIER 3 (Tail-enders):
  - Ravindra (SR 40-50)
  - Poonam Yadav (SR 30-40)
```

**Sequencing:**
```
Position 7: Deepti Sharma (all-rounder, TIER 1)
Position 8: Renuka Singh (pace bowler, can bat)
Position 9: Jhulan Goswami (TIER 2, death-bowler value)
Position 10: Ravindra (TIER 3, tail-ender)
Position 11: Poonam Yadav (TIER 3, tail-ender)
```

---

### 7. **Risk Management & Variance Reduction (RM)**

Balance aggressive and conservative players to minimize collapse risk.

**Collapse Risk Definition:**
```
If top 6 all have SR > 130:
  → Very high-variance outcome
  → Great if momentum maintained
  → Disaster if early wickets fall

If top 6 all have SR < 110:
  → Very low variance
  → Slow accumulation
  → Miss PowerPlay opportunity
```

**Optimal Distribution:**

```
Positions 1-2 (Openers):    High SR (130+)      [Aggressive]
Positions 3-4 (Anchors):    Medium SR (115-125) [Balanced]
Positions 5-6 (Builders):   Medium SR (110-120) [Balanced]
Positions 7-8 (Finishers):  High SR (130+)      [Aggressive]
Positions 9-11 (Tail):      Any SR              [Tail-enders]
```

**Variance Smoothing:**
- Never place 3+ conservative batters consecutively
- Alternate aggression patterns to maintain momentum
- Ensure each phase has at least 1 strong hitter

---

### 8. **Form & Confidence Sequencing (FCS)**

Place in-form players in positions that maximize their impact.

**In-Form Metrics:**
```
Player          Last 5 Avg  SR     Form Level
─────────────────────────────────────────────
Richa Ghosh     39.0       145     EXCELLENT
Shafali Verma   35.6       142     EXCELLENT
Smriti Mandhana 32.4       125     VERY GOOD
Harmanpreet     31.2       118     VERY GOOD
Jemimah         29.0       115     GOOD
```

**Placement Strategy:**
1. Highest form → Opening (Richa is WK, so #5-6)
2. Very good form → #2-3 positions
3. Good form → #4-6 positions
4. Average form → #7-9 (lower pressure)

---

## Complete Optimization Algorithm

### Step 1: Classify Players by Role & Phase

```python
def classify_player(player, opponent_data):
    role_class = {
        'opener': player['sr'] > 130,
        'middle_anchor': 115 < player['sr'] <= 130,
        'finisher': player['sr'] >= 140,
        'captain': player['leadership_score'] > 0.8,
        'wicket_keeper': player['role'] == 'wicket_keeper'
    }
    return role_class
```

### Step 2: Calculate Position Scores

```python
def calculate_position_score(player, position, opponent, venue):
    """Score how well this player fits this position."""
    
    phase = get_phase_for_position(position)  # PowerPlay/Middle/Death
    
    phase_fit = score_phase_fit(player, phase)          # 0-100
    matchup_score = score_matchup(player, opponent, position)  # 0-100
    form_score = score_recent_form(player)              # 0-100
    
    total = (
        phase_fit * 0.40 +
        matchup_score * 0.35 +
        form_score * 0.25
    )
    
    return total
```

### Step 3: Assign Using Optimization

```python
def optimize_batting_order(players, opponent, venue):
    """Assign 11 players to 11 positions optimally."""
    
    # Calculate score for each (player, position) pair
    scores = {}
    for player in players:
        for position in range(1, 12):
            score = calculate_position_score(
                player, position, opponent, venue
            )
            scores[(player.id, position)] = score
    
    # Hungarian Algorithm or brute force to find best assignment
    optimal_order = solve_assignment_problem(scores)
    
    return optimal_order
```

### Step 4: Apply Constraints

```python
def apply_constraints(order):
    """Ensure order meets cricket constraints."""
    
    # Constraint 1: Wicket-keeper by position 7
    assert order[0]['role'] == 'wicket_keeper' or \
           any(p['role'] == 'wicket_keeper' for p in order[:7])
    
    # Constraint 2: Avoid 3+ conservative in row
    for i in range(0, 8):
        sr_window = [order[j]['sr'] for j in range(i, min(i+3, 11))]
        assert sum(1 for sr in sr_window if sr < 110) < 3
    
    # Constraint 3: Captain not at 1 or 11
    captain_pos = next(i for i, p in enumerate(order) 
                       if p.get('is_captain'))
    assert 1 <= captain_pos <= 10
    
    return True
```

---

## Real-World Example: India vs Australia at Edgbaston

### Selected Squad

```
1. Shafali Verma (Opener, 142 SR, Form: 38.2)
2. Smriti Mandhana (Opener, 125 SR, Form: 36.8)
3. Harmanpreet Kaur (Captain, 118 SR, Form: 34.5)
4. Jemimah Rodrigues (Middle, 115 SR, Form: 32.1)
5. Richa Ghosh (WK, 145 SR, Form: 39.0)
6. Yashasvi Jaiswal (Lower-middle, 130 SR, Form: 35.2)
7. Deepti Sharma (All-rounder, 110 SR, Form: 33.8)
8. Renuka Singh (Bowler, can bat)
9. Jhulan Goswami (Bowler, death specialist)
10. Ravindra (Spinner)
11. Poonam Yadav (Spinner)
```

### Analysis by Phase

**PowerPlay Expectation (Overs 1-6):**
```
Shafali (Opener 1):
  - vs Schutt (pace): 142 SR, 12 meetings
  - vs Starc (pace): 128 SR, 10 meetings
  - Expected: 40-45 runs in 6 overs

Smriti (Opener 2):
  - vs Jonassen (spin): 108 SR, 8 meetings
  - vs Starc (pace): 125 SR, 6 meetings
  - Expected: 35-40 runs in 6 overs

PowerPlay Target: 75-85 runs (achieved with strong opening)
```

**Middle Overs Expectation (Overs 7-16):**
```
Harmanpreet (#3):
  - Experience: Can stabilize or accelerate
  - vs Australia spinners: Strong record
  - Role: Build partnership, recover if wickets fall
  - Expected: 25-35 runs in 8-10 overs (medium phase)

Jemimah (#4):
  - vs Jonassen (spin): 118 SR (favorable)
  - Role: Continue momentum with Harmanpreet
  - Expected: 20-30 runs

Richa (#5):
  - WK position allows bat time
  - High SR (145) valuable in middle acceleration
  - Expected: 20-25 runs (if playing full middle phase)

Middle Target: 65-90 runs
```

**Death Overs Expectation (Overs 17-20):**
```
Yashasvi (#6, if reaches):
  - 130 SR, good for death aggression
  - Expected: 15-20 runs in 4 overs

Deepti (#7, if reaches):
  - All-rounder flexibility
  - Can handle pressure bowling
  - Expected: 10-15 runs

Death Target: 25-35 runs
```

### Optimized Batting Order

```
FINAL BATTING ORDER: India vs Australia at Edgbaston

#1 Shafali Verma (Opener, 142 SR)
   Rationale: Highest SR, excellent vs Australia pace
   vs Schutt: 142 SR (12 meetings) ✓

#2 Smriti Mandhana (Opener, 125 SR)
   Rationale: Consistent, pairs well with Shafali
   vs Schutt: 125 SR ✓

#3 Harmanpreet Kaur (Captain, 118 SR)
   Rationale: Experienced anchor, stabilizes if wickets fall
   Position: Witnesses opening pair's work before batting
   vs Spinners: Strong historical record

#4 Jemimah Rodrigues (Middle, 115 SR)
   Rationale: Strong vs Jonassen (118 SR), builds partnerships
   Role: Continue middle-order acceleration

#5 Richa Ghosh (WK, 145 SR)
   Rationale: Highest overall SR, explosive hitting
   Position: WK by position 5 (satisfies cricket constraint)
   Role: Boost batting depth, aggressive hitting phase

#6 Yashasvi Jaiswal (Lower-middle, 130 SR)
   Rationale: High SR valuable in death phase
   Role: Finisher if reaches

#7 Deepti Sharma (All-rounder, 110 SR)
   Rationale: Provides all-rounder value, can bat or bowl
   Role: Lower-order stability, tail-end hitting

#8 Renuka Singh (Bowler)
   Role: Tail-ender, can contribute with bat in emergency

#9 Jhulan Goswami (Bowler, death specialist)
   Role: Tail-ender, specialist bowler

#10 Ravindra (Spinner)
    Role: Tail-ender, specialist bowler

#11 Poonam Yadav (Spinner)
    Role: Tail-ender, specialist bowler

PHASE DISTRIBUTION:
┌─────────────┬──────────┬────────────┬─────────┐
│ Phase       │ Overs    │ Position   │ Expected│
├─────────────┼──────────┼────────────┼─────────┤
│ PowerPlay   │ 1-6      │ #1-2       │ 75-85   │
│ Middle      │ 7-16     │ #3-6       │ 65-90   │
│ Death       │ 17-20    │ #6-8       │ 25-35   │
│ TOTAL       │ 1-20     │ All        │ 165-210 │
└─────────────┴──────────┴────────────┴─────────┘

Balance Check:
✓ High SR openers in positions 1-2
✓ Balanced middle order (positions 3-6)
✓ Explosive finishers in positions 6-8
✓ Tail-enders in positions 9-11
✓ No 3+ consecutive low-SR batters
✓ Captain at position 3 (leadership point)
✓ WK at position 5 (within conventional limits)

Expected Team Total: 155-180 runs (based on phase contributions)
```

---

## Performance Factors by Position

| Position | Phase | Required SR | Min Balls | Max Balls | Expected Runs |
|----------|-------|------------|-----------|-----------|---------------|
| 1 | PowerPlay | 130+ | 20 | 36 | 35-45 |
| 2 | PowerPlay/Middle | 125+ | 18 | 36 | 30-40 |
| 3 | Middle | 115+ | 15 | 30 | 20-35 |
| 4 | Middle | 115+ | 12 | 24 | 18-28 |
| 5 | Middle/Death | 120+ | 10 | 20 | 15-25 |
| 6 | Middle/Death | 125+ | 8 | 16 | 12-20 |
| 7 | Death/Tail | 110+ | 6 | 12 | 8-15 |
| 8 | Tail | 80+ | 4 | 8 | 3-8 |
| 9 | Tail | 50+ | 2 | 4 | 1-3 |
| 10 | Tail | 30+ | 1 | 2 | 0-2 |
| 11 | Tail | 20+ | 1 | 2 | 0-1 |

---

## Integration with Other Nodes

### From Squad Selector
- Input: Selected 11 players with their attributes
- Uses: Individual SR, form, matchup data

### To Bowling Plan Node
- Output: Final batting order (for opponent bowling strategy)
- Impact: Opponent knows order, can plan bowl sequences

### To Live Analysis Nodes
- Output: Expected scoring targets by phase
- Impact: Live nodes use these benchmarks for performance evaluation

---

## Implementation Pattern

```python
class BattingOrderNode:
    """Optimizes batting order from selected 11 players."""
    
    def __init__(self, squad_data, opponent, venue):
        self.squad = squad_data
        self.opponent = opponent
        self.venue = venue
    
    def phase_score(self, player, phase):
        """Score player suitability for phase."""
        if phase == 'powerplay':
            return player['sr'] * 0.60 + player['form'] * 0.40
        elif phase == 'middle':
            return player['sr'] * 0.50 + player['form'] * 0.50
        else:  # death
            return player['sr'] * 0.70 + player['form'] * 0.30
    
    def matchup_score(self, player, phase):
        """Score player vs opponent bowlers in phase."""
        expected_bowlers = self._get_phase_bowlers(phase)
        matchup_srs = [
            self._get_matchup_sr(player, bowler)
            for bowler in expected_bowlers
        ]
        return sum(matchup_srs) / len(matchup_srs)
    
    def optimize_order(self):
        """Main optimization function."""
        assignment = {}
        for pos in range(1, 12):
            phase = self._get_phase(pos)
            scores = [
                (self.phase_score(p, phase) + 
                 self.matchup_score(p, phase)) * 100,
                p
            ]
            best_player = max(scores)[1]
            assignment[pos] = best_player
        
        return assignment
```

---

## Typical Output Summary

```
BATTING ORDER ANALYSIS: India vs Australia at Edgbaston

OPTIMIZED ORDER:
1. Shafali Verma (142 SR, Opener)
   Vs Australia: Excellent (142 SR vs Schutt)
   
2. Smriti Mandhana (125 SR, Opener)
   Vs Australia: Excellent (125 SR vs pace)
   
3. Harmanpreet Kaur (118 SR, Captain)
   Stabilizer role in middle order
   
4. Jemimah Rodrigues (115 SR, Middle)
   Strong vs Jonassen (leg-spin)
   
5. Richa Ghosh (145 SR, WK)
   Aggressive finisher in middle/death
   
6. Yashasvi Jaiswal (130 SR, Lower-middle)
   Death-phase power hitting
   
7. Deepti Sharma (110 SR, All-rounder)
   Flexible tail-end option
   
8-11. Bowlers (Renuka, Jhulan, Ravindra, Poonam)
      Tail-end specialists

PHASE PERFORMANCE EXPECTATIONS:
PowerPlay (1-6):   75-85 runs
Middle (7-16):     65-90 runs
Death (17-20):     25-35 runs
─────────────────────────────
Expected Total:    165-210 runs

STRATEGIC INSIGHTS:
✓ Openers set aggressive tone (142+125 SR)
✓ Harmanpreet provides stability & leadership
✓ Richa's aggression boosts middle-order value
✓ Yashasvi & Deepti ready for death acceleration
✓ Balanced risk-reward across all phases

Confidence: VERY HIGH (Score: 88/100)
```

---

## Related Documentation

- [Squad Selector Node](SQUAD_SELECTOR.md)
- [Opponent Analysis Node](OPPONENT_ANALYSIS.md)
- [Bowling Plan Creator](BOWLING_PLAN.md)
- [Data Schema Reference](Data-Schema.md)
- [Game Phases Explained](../wiki/Game-Phases.md)

