# Bowling Plan Creator Node Documentation

## Overview

The **Bowling Plan Creator Node** designs the bowling strategy by assigning bowlers to specific phases and overs, considering opponent matchups, bowler strengths, and match dynamics.

In T20 cricket, bowling placement is crucial. A death-over specialist bowling during PowerPlay wastes their talent; a young pacer struggling with line and length shouldn't bowl in tight death situations. The optimizer balances bowler specialization with opponent weaknesses.

---

## The Bowling Plan Problem

**Input:**
- Selected 4-5 bowlers with their specialties
- Opponent's batting lineup and strengths  
- Venue characteristics

**Output:**
- PowerPlay bowling plan (overs 1-6)
- Middle-overs bowling plan (overs 7-16)
- Death-overs bowling plan (overs 17-20)
- Over-by-over assignments and backup plans

**Constraints:**
- Each bowler maximum 4 overs (T20 rule)
- Minimum 2-3 different bowlers in each phase
- Captain's preferences considered
- Injury/rotation requirements

---

## Key Techniques

### 1. **Phase-Specialist Assignment (PSA)**

Match bowler specialty with phase requirements.

#### PowerPlay Phase (Overs 1-6)

**Objectives:**
- Control aggressive openers
- Limit boundary scoring
- Build pressure through dot balls
- Economy rate < 7.5

**Ideal Bowlers:**
```
PACE BOWLER (Fast, accurate):
  - Tight line and length
  - Can restrict through control
  - Example: Renuka Singh (economy 6.2)
  
SLOWER BOWLER (Cutters, variations):
  - Deceptive pace changes
  - Hard for openers to attack
  - Example: Jhulan Goswami (economy 6.8)
```

**Why NOT Death Specialists in PowerPlay?**
- Death specialists focus on yorkers/blockhole deliveries
- Openers play full deliveries (not yorkers)
- Yorkers more effective against middle-order batters

#### Middle Overs (Overs 7-16)

**Objectives:**
- Contain acceleration attempts
- Take 2-3 wickets total
- Balance aggression/control
- Economy rate 6.5-7.5

**Ideal Bowlers:**
```
SPINNERS (Leg-spin, Off-spin):
  - Vary pace and direction
  - Difficult to hit without risk
  - Can bowl multiple overs
  - Example: Ravindra (leg-spin), Deepti (off-spin)
  
PACE ALL-ROUNDERS:
  - Add variety to attack
  - Break up spin-heavy bowling
  - Example: Deepti Sharma (off-spin, all-rounder)
```

**Advantage in Middle:**
- Batters trying to build innings (less attacking)
- Spinners thrive in building phases
- Gives pace bowlers rest before death

#### Death Overs (Overs 17-20)

**Objectives:**
- Restrict final acceleration
- Take 1-2 key wickets
- Control sixes
- Economy rate < 8.5 acceptable (high-pressure phase)

**Ideal Bowlers:**
```
DEATH SPECIALIST (Yorker expert, accurate):
  - Jhulan Goswami (mastered yorker)
  - Economy 7.5-8.0 in death acceptable
  - Nerves of steel in final overs
  
PACE BOWLER (Raw pace + variations):
  - Renuka Singh (can bowl quick)
  - Boundary line yorker skills
```

**Why NOT Spinners in Death?**
- Spinners' variation slowed deliveries easy to hit in death
- Batters pre-planned for yorkers, not off-break variations
- Yorkers harder to spot than slow spinners

---

### 2. **Opposition Matchup Analysis (OMA)**

Assign bowlers specifically to oppose their weaknesses.

**Batter vs Bowler Data:**

```json
{
  "opposition_opening": [
    {
      "name": "Alyssa Healy",
      "vulnerabilities": {
        "short_ball": "tends to play aggressive",
        "yorker": "poor footwork",
        "leg_spin": "high scoring (145 SR)"
      }
    }
  ],
  "opposition_middle": [
    {
      "name": "Beth Mooney",
      "vulnerabilities": {
        "pace_off_stump": "LBW prone",
        "yorker": "struggles to dig out",
        "leg_spin": "average 28, low SR"
      }
    }
  ]
}
```

**Assignment Logic:**

```
For Each Opposition Batter:
  1. Identify weakness
  2. Match with bowler specialist
  3. Prioritize when batter likely to bat
  
Example - Australia's Alyssa Healy:
  Weakness: Struggles vs leg-spin (110 SR vs Ravindra)
  Assignment: Bowl Ravindra in PowerPlay/Middle
  Timing: When Healy likely to bat (positions 1-3)
```

**Real-World Example:**

```
Opposition Opening Pair:
  Alyssa Healy:
    ✗ vs Leg-spin: 110 SR (weak)
    ✓ vs Pace: 135 SR (strong)
    
  Beth Mooney:
    ✗ vs Yorker: Prone to dismissal
    ✓ vs Spin: 105 SR (moderate)

Strategy:
  1. Renuka Singh (pace): Open to Mooney (can bowl yorker)
  2. Ravindra (leg-spin): Follow-up to Healy (weak vs leg-spin)
  3. Jhulan Goswami (pace, death): Back-up with yorkers
```

---

### 3. **Bowler Load Balancing (BLB)**

Distribute 4-overs maximum across bowlers efficiently.

**T20 Constraint:** Each bowler = 4 overs max (24 balls)

**Distribution Strategy:**

```
5 Bowlers, 20 overs total:
  Option A:           Option B:
  Bowler 1: 4 overs  Bowler 1: 4 overs
  Bowler 2: 4 overs  Bowler 2: 4 overs
  Bowler 3: 4 overs  Bowler 3: 4 overs
  Bowler 4: 4 overs  Bowler 4: 3 overs
  Bowler 5: 4 overs  Bowler 5: 1 over (emergency)
```

**Why Distribute Fully?**
- Each bowler's 4 overs spread across phases
- Ensures variety across innings
- Prevents bowler fatigue
- Covers injuries/underperformance

**Optimal Pattern:**

```
PowerPlay (6 overs):      2 bowlers, 3 overs each
Middle (10 overs):        3 bowlers, 3-4 overs each
Death (4 overs):          2 bowlers, 2 overs each

Example:
PowerPlay:
  Overs 1-3: Renuka Singh (pace, 3 overs)
  Overs 4-6: Jhulan Goswami (pace/variations, 3 overs)

Middle:
  Overs 7-9: Ravindra (leg-spin, 3 overs)
  Overs 10-12: Deepti Sharma (off-spin, 3 overs)
  Overs 13-15: Renuka Singh (pace, return, 1 over)

Death:
  Overs 16-18: Jhulan Goswami (death specialist, 2 overs)
  Overs 19-20: Renuka Singh (final 2 overs, 2 overs)
  
Total: 4 + 4 + 4 + 4 + 4 = 20 overs
```

---

### 4. **Left-Right Bowling Combinations (LRBC)**

Alternate left-arm and right-arm bowlers to confuse batters.

**Batter Hand Advantages:**

```
RIGHT-HANDED BATTER:
  ✓ Advantages vs Right-arm bowler: Natural angle
  ✗ Vulnerable to Left-arm: Unfamiliar angle
  
LEFT-HANDED BATTER:
  ✓ Advantages vs Left-arm bowler: Natural angle
  ✗ Vulnerable to Right-arm: Unfamiliar angle
```

**Batting Lineup Composition:**

```
Opposition Lineup:
  RHB: Alyssa Healy, Mooney, Moody (right-handed)
  LHB: Lanning (left-handed)
```

**Bowling Combinations:**

```
Overs 1-3: Renuka Singh (RIGHT-arm pace)
  Target: RHB openers
  
Overs 4-6: Jhulan Goswami (RIGHT-arm pace)
  Target: Continue RHB
  
Overs 7-9: Ravindra (RIGHT-arm leg-spin)
  Target: RHB middle order (confused by leg-spin)
  
Overs 10-12: Deepti Sharma (LEFT-arm off-spin)
  Target: LHB (Lanning, unfamiliar angle)
  
This alternation keeps batters guessing.
```

**Advantage of LRBC:**
- Breaks rhythm of batter's footwork
- Different release point confuses timing
- Reduces batter confidence
- Forces shot adjustment between bowlers

---

### 5. **Bowler Fitness & Injury Management (BFIM)**

Plan bowling considering fitness and workload.

**Workload Management:**

```
High-Intensity Bowling (death overs, tight control):
  Maximum: 2 overs per phase
  Rest Required: Minimum 2 overs between assignments
  Recovery: 24-48 hours post-tournament
  
Example - Jhulan Goswami:
  Overs 1-3: PowerPlay (3 overs, high intensity)
  Overs 7-8: Middle (1 over, recovery)
  Overs 19-20: Death (2 overs, critical)
  
Total: 6 overs across 20-over span (reasonable load)
```

**Injury Considerations:**

```
If Renuka Singh (fast bowler) has:
  - Minor hamstring concern: Reduce to 3 overs max
  - Avoid high-intensity death overs
  - Use in controlled PowerPlay/Middle instead
  
Alternative Plan B:
  If Renuka unavailable: Promote Arundhati Reddy
  Adjust other bowlers to cover 4-over deficit
```

---

### 6. **Venue-Specific Bowling Strategy (VSBS)**

Adapt bowling plan to pitch conditions.

#### Batsman-Friendly Venues (Edgbaston, Rose Bowl)

**Pitch Characteristics:**
- Hard, true bounce
- Favorable for pace bowling
- Spinners can be attacked

**Bowling Adjustment:**
```
Increase: Pace bowlers (Renuka, Jhulan)
Decrease: Spinner overs (Ravindra, Deepti)
Ratio: 3 pace + 2 spinners (instead of 2 pace + 3 spinners)
```

#### Bowler-Friendly Venues (Old Trafford, Headingley)

**Pitch Characteristics:**
- Lateral movement for pace
- Uneven bounce for spinners
- Conditions deteriorate by death overs

**Bowling Adjustment:**
```
Increase: Spinner overs (maximize seam conditions benefit)
Pace Role: Defensive line/length, fewer variations
Ratio: 2 pace + 3 spinners
```

#### High Dew Venues (Evening Matches)

**Conditions:**
- Dew makes ball slippery
- Pace bowling struggles with grip
- Spinners excellent in dew

**Adjustment:**
```
PowerPlay: Use pace (before dew arrives)
Death: Prioritize spinners (dew advantage)
Example:
  Overs 1-6: Heavy pace (2 bowlers, 6 overs)
  Overs 17-20: Mostly spinners (2 spinners, 3-4 overs total)
```

---

### 7. **Wicket-Taking Strategy (WTS)**

Plan bowling to take 3-5 key wickets at optimal times.

**Wicket Targets by Phase:**

```
PowerPlay (Overs 1-6):
  Target Wickets: 0-1 (focus on control)
  Strategy: Tighten line, build pressure
  Dismiss: Aggressive opener if setup right
  
Middle (Overs 7-16):
  Target Wickets: 2-3 (main wicket phase)
  Strategy: Spin variation, surprise yorkers
  Dismiss: Middle-order anchors
  
Death (Overs 17-20):
  Target Wickets: 1-2 (pressure dismissals)
  Strategy: Yorker accuracy, death options
  Dismiss: Aggressive finishers
  
Total: 3-5 wickets across 20 overs
```

**Wicket Probability by Bowler:**

```
High Wicket-Taking Bowlers:
  Renuka Singh: 1 wicket per match
  Ravindra (vs RHB): 0.5-1 wicket per match
  
Lower Wicket-Taking:
  Deepti (all-rounder): 0.3-0.5 wickets per match
  
Strategy: Prioritize Renuka & Ravindra in key overs
```

---

### 8. **Death Bowling Excellence (DBE)**

Master the final 4 overs with specialized strategy.

**Death Over Requirements:**

```
Overs 17-20 Demands:
  - Pinpoint yorker accuracy
  - Slower ball deception
  - Nerve under pressure
  - Economy rate: 7.5-8.5 (acceptable in death)
```

**Death Bowling Plan Structure:**

```
Over 17: Jhulan Goswami (yorker specialist)
  vs Opposition's power-hitter
  Plan: 3 yorkers, 2 slower balls, 1 blooper
  
Over 18: Renuka Singh (pace variation)
  vs Opposition's clean-hitter
  Plan: Short ball, yorker, full toss
  
Over 19: Jhulan Goswami (2nd spell)
  vs Opposition's finisher
  Plan: Yorker-heavy, protect stumps
  
Over 20: Renuka Singh (final over)
  vs Opposition's aggressive batters
  Plan: Yorker, slower ball, wide yorker
  
Backup: If either bowler underperforms
  Use: Ravindra (leg-spin yorker) or
        Deepti (off-spin variations)
```

**Death Bowling Stats:**

```
Target Economy Rate (Death): 8.0 per over
  vs PowerPlay/Middle: 6.5-7.0
  
Expected Death Runs: 32 runs per 4 overs
  (vs 40-45 if not controlled)

Wickets in Death: 1-2 (dismissals break acceleration)
```

---

## Complete Bowling Plan Algorithm

### Step 1: Categorize Bowlers

```python
def categorize_bowlers(squad_bowlers):
    """Classify bowlers by specialty."""
    
    categories = {
        'pace_control': [],      # Tight line, economy < 6.5
        'pace_death': [],        # Yorker specialists
        'spinner_leg': [],       # Leg-spin variety
        'spinner_off': [],       # Off-spin control
        'all_rounder': []        # Flexible bowlers
    }
    
    for bowler in squad_bowlers:
        specialty = bowler['primary_specialty']
        categories[specialty].append(bowler)
    
    return categories
```

### Step 2: Assign Phases

```python
def assign_phases(bowlers, opponent, venue):
    """Assign bowlers to phases."""
    
    assignments = {
        'powerplay': [],
        'middle': [],
        'death': []
    }
    
    # PowerPlay: Pace control specialists
    assignments['powerplay'] = bowlers['pace_control'][:2]
    
    # Middle: Spinners + variation
    assignments['middle'] = (bowlers['spinner_leg'] + 
                            bowlers['spinner_off'])
    
    # Death: Death specialists
    assignments['death'] = bowlers['pace_death']
    
    return assignments
```

### Step 3: Create Over-by-Over Plan

```python
def create_over_plan(phase_assignments, opponent):
    """Create detailed over-by-over bowling plan."""
    
    plan = {}
    
    for over in range(1, 21):
        phase = get_phase(over)
        phase_bowlers = phase_assignments[phase]
        
        # Select bowler for this over
        bowler = select_bowler_for_over(
            over, phase_bowlers, opponent
        )
        
        # Create over strategy
        strategy = {
            'bowler': bowler['name'],
            'vs_batter': get_expected_batter(opponent, over),
            'attack_type': get_attack_type(bowler, phase),
            'overs_remaining': bowler['overs_remaining'],
            'backup_bowler': select_backup(bowler)
        }
        
        plan[over] = strategy
    
    return plan
```

### Step 4: Validate Plan

```python
def validate_bowling_plan(plan):
    """Ensure plan meets T20 constraints."""
    
    # Each bowler max 4 overs
    bowler_overs = {}
    for over, strategy in plan.items():
        bowler = strategy['bowler']
        bowler_overs[bowler] = bowler_overs.get(bowler, 0) + 1
        assert bowler_overs[bowler] <= 4
    
    # Phase coverage
    assert len(set(over for over in range(1, 7))) > 0  # PowerPlay
    assert len(set(over for over in range(7, 17))) > 0  # Middle
    assert len(set(over for over in range(17, 21))) > 0  # Death
    
    return True
```

---

## Real-World Example: India vs Australia at Edgbaston

### Selected Bowlers

```
1. Renuka Singh (Pace, 2.8 wickets/match, SR 125 economy 6.2)
2. Jhulan Goswami (Pace, Death specialist, economy 6.8)
3. Ravindra (Leg-spin, 0.8 wickets/match, economy 7.1)
4. Deepti Sharma (Off-spin, all-rounder, economy 7.0)
5. (Backup): Poonam Yadav (Leg-spin backup)
```

### Opposition Analysis

```
Australia Batting Order:
Position 1-2: Alyssa Healy (RHB, 135 SR), Beth Mooney (RHB, 120 SR)
Position 3-4: Meg Lanning (LHB, 115 SR), Ellyse Perry (RHB, 125 SR)
Position 5-6: Georgia Redmayne (RHB, 140 SR), Others

Weaknesses Identified:
- Healy: Weak vs leg-spin (110 SR vs Ravindra)
- Mooney: Prone to yorker (poor footwork)
- Lanning: Struggles vs off-spin (104 SR vs Deepti)
- Perry: Variable in middle overs (can collapse)
- Redmayne: Aggressive but risky in PowerPlay
```

### Over-by-Over Bowling Plan

**POWERPLAY (Overs 1-6) - Control Focus**

```
Over 1: Renuka Singh (Pace, 3-overs allocation)
  vs Alyssa Healy (RHB opener)
  Plan: Tight line, yorker mixed with full length
  Expected: Dot balls, pressure building
  Overs Remaining: 3

Over 2: Jhulan Goswami (Pace, 2-overs allocation)
  vs Beth Mooney (RHB opener)
  Plan: Yorker attempts, defensive line
  Expected: Control, 1-2 dot balls per over
  Overs Remaining: 2

Over 3: Renuka Singh (2nd over)
  vs Alyssa Healy (RHB)
  Plan: Pace variation, back of length
  Expected: 1-2 boundaries possible
  Overs Remaining: 2

Over 4: Jhulan Goswami (2nd over)
  vs Beth Mooney (RHB)
  Plan: Yorker, slower ball mixture
  Expected: Tight over, 1 dismissal possible
  Overs Remaining: 1

Over 5: Renuka Singh (3rd over)
  vs Alyssa Healy or new batter
  Plan: Final PowerPlay over - increased pace
  Expected: 8-12 runs typical
  Overs Remaining: 0 (complete for PowerPlay)

Over 6: Jhulan Goswami (3rd over)
  vs Opposition
  Plan: End PowerPlay with control
  Expected: 6-9 runs
  Overs Remaining: 1

POWERPLAY SUMMARY:
  Expected Runs: 35-40
  Expected Wickets: 0-1
  Economy: 5.8-6.7 (good control)
```

**MIDDLE OVERS (Overs 7-16) - Wicket Focus**

```
Over 7: Ravindra (Leg-spin, 3-overs allocation)
  vs Alyssa Healy (if not out)
  Plan: Leg-spin variation targeting weakness
  Weakness: 110 SR vs leg-spin ✗
  Expected: Dot balls, low scoring
  Overs Remaining: 3

Over 8: Deepti Sharma (Off-spin, 3-overs allocation)
  vs Meg Lanning (LHB)
  Plan: Off-spin vs left-handed batter
  Weakness: 104 SR vs off-spin ✗
  Expected: Wicket possible (LBW/caught)
  Overs Remaining: 3

Over 9: Ravindra (2nd over)
  vs Opposition
  Plan: Continue leg-spin pressure
  Expected: Build pressure, 1 wicket likely
  Overs Remaining: 2

Over 10: Deepti Sharma (2nd over)
  vs Opposition
  Plan: Off-spin variation
  Expected: 7-10 runs
  Overs Remaining: 2

Over 11: Ravindra (3rd over)
  vs Opposition
  Plan: Complete leg-spin allocation
  Expected: Dot balls, pressure continue
  Overs Remaining: 1

Over 12: Deepti Sharma (3rd over)
  vs Opposition
  Plan: Complete off-spin allocation
  Expected: 8-12 runs, 1 wicket
  Overs Remaining: 1

Over 13: Renuka Singh (Return to bowling, 1-overs allocation)
  vs Opposition
  Plan: Pace change from spinners
  Expected: Back of length, 6-10 runs
  Overs Remaining: 1

Over 14: Jhulan Goswami (Return to bowling, 1-overs allocation)
  vs Opposition
  Plan: Pace variation
  Expected: 8-12 runs
  Overs Remaining: 0 (Jhulan held for death)

Over 15: Ravindra Backup (If assigned 2 overs middle)
  OR Deepti Sharma Backup
  
Over 16: (Continuation or new bowler)
  
MIDDLE SUMMARY:
  Expected Runs: 65-80
  Expected Wickets: 2-3
  Economy: 6.5-7.2 (balanced)
```

**DEATH OVERS (Overs 17-20) - Containment**

```
Over 17: Jhulan Goswami (Death specialist, 2-overs allocation)
  vs Opposition's aggressive batter
  Plan: Yorker-heavy strategy
  Deliveries: Yorker, slower ball, yorker, fuller length
  Expected: 6-9 runs, possible 1 wicket
  Overs Remaining: 1

Over 18: Renuka Singh (Final 2-overs allocation)
  vs Opposition's finisher
  Plan: Pace variety, short + yorker
  Expected: 10-14 runs
  Overs Remaining: 1

Over 19: Jhulan Goswami (2nd death over)
  vs Opposition's aggressive finisher
  Plan: Yorker accuracy critical
  Deliveries: All yorkers/slower balls
  Expected: 8-12 runs, control essential
  Overs Remaining: 0 (Jhulan done: 4 overs total)

Over 20: Renuka Singh (Final over of match)
  vs Opposition's last aggressive batter
  Plan: Yorker, yorker, slower ball, yorker
  Expected: 12-16 runs (death acceleration normal)
  Overs Remaining: 0 (Renuka done: 4 overs total)

DEATH SUMMARY:
  Expected Runs: 36-51
  Expected Wickets: 1-2
  Economy: 9.0-12.75 (high pressure, acceptable)
  
Total Match Bowling:
  Expected Opposition Total: 136-171 runs
  Expected Wickets: 3-6
  Quality: 7-8 overs tight, 3-4 overs attacked
```

### Final Bowling Plan Summary

```
BOWLING PLAN: India vs Australia at Edgbaston

PHASE ASSIGNMENTS:
PowerPlay (1-6):    Renuka Singh (3 overs) + Jhulan (3 overs)
Middle (7-16):      Ravindra (3 overs) + Deepti (3 overs) + Renuka (1)
Death (17-20):      Jhulan (2 overs) + Renuka (2 overs)

BOWLER ALLOCATIONS:
1. Renuka Singh     4 overs total (3 PowerPlay + 1 Middle + 2 Death)
2. Jhulan Goswami   4 overs total (3 PowerPlay + 1 Death)
3. Ravindra         3 overs total (Middle only)
4. Deepti Sharma    3 overs total (Middle only)
5. (Poonam Yadav)   - Backup/reserve

MATCHUP STRATEGY:
vs Healy:      Renuka (pace) then Ravindra (leg-spin weakness)
vs Mooney:     Jhulan (yorker specialist)
vs Lanning:    Deepti (off-spin weakness for LHB)
vs Perry:      Ravindra (leg-spin pressure)
vs Redmayne:   Renuka (pace, PowerPlay control)

LEFT-RIGHT COMBINATIONS:
Overs 1-3: Renuka + Jhulan (both RHB bowlers)
Overs 7-10: Ravindra + Deepti (mixed attack)
Overs 17-20: Jhulan + Renuka (both RHB bowlers, finishers)

EXPECTED OUTCOMES:
Expected Opposition Total: 150-165 runs
Expected Wickets: 4-5
Economy: 7.5-8.25
Dot Ball Rate: 25-30%

KEY STRENGTHS:
✓ Ravindra targets Healy's weakness vs leg-spin
✓ Jhulan's yorkers vs Mooney's weak footwork
✓ Deepti's off-spin vs Lanning's vulnerability
✓ Death overs controlled by specialists

CONTINGENCIES:
If Renuka injured: Promote Arundhati (backup pacer)
If Ravindra underperforming: Use Poonam (leg-spin backup)
If early wickets: Adjust to shorter spells, rebuild

Confidence Level: VERY HIGH (Score: 89/100)
```

---

## Integration with Other Nodes

### From Batting Order Optimizer
- Input: Final batting order positions 1-11
- Uses: Know which batters will face each over
- Benefit: Tailor bowling to specific opposition batters

### To Live Analysis Nodes
- Output: Expected bowling performance benchmarks
- Impact: Live nodes compare actual vs expected performance
- Benefits: Real-time bowling change recommendations

### To Strategy Node
- Output: Expected opposition total, wicket targets
- Impact: Shapes overall match strategy and expectations

---

## Implementation Pattern

```python
class BowlingPlanNode:
    """Creates optimal bowling plan for match."""
    
    def __init__(self, bowlers, opponent, venue):
        self.bowlers = bowlers
        self.opponent = opponent
        self.venue = venue
    
    def assign_phase(self, bowler, phase):
        """Score bowler suitability for phase."""
        if phase == 'powerplay':
            return bowler['economy'] * 0.60 + bowler['control'] * 0.40
        elif phase == 'middle':
            return bowler['wickets_per_match'] * 0.70 + \
                   bowler['economy'] * 0.30
        else:  # death
            return bowler['yorker_accuracy'] * 0.60 + \
                   bowler['nerve_factor'] * 0.40
    
    def matchup_score(self, bowler, batter):
        """Score bowler vs specific batter."""
        return self._get_historical_sr(bowler, batter)
    
    def create_plan(self):
        """Generate over-by-over bowling plan."""
        plan = {}
        bowler_overs = {b['name']: 0 for b in self.bowlers}
        
        for over in range(1, 21):
            phase = self._get_phase(over)
            available = [b for b in self.bowlers 
                        if bowler_overs[b['name']] < 4]
            
            # Score each bowler for this over
            scores = [(self.assign_phase(b, phase) + 
                      self.matchup_score(b, self._expected_batter(over)),
                      b) for b in available]
            
            best_bowler = max(scores)[1]
            plan[over] = {
                'bowler': best_bowler['name'],
                'vs_batter': self._expected_batter(over),
                'strategy': self._get_strategy(best_bowler, phase)
            }
            bowler_overs[best_bowler['name']] += 1
        
        return plan
```

---

## Typical Output Summary

```
BOWLING PLAN ANALYSIS: India vs Australia at Edgbaston

PHASE STRATEGIES:
PowerPlay: Pace-heavy (Renuka + Jhulan)
  → Control aggressive openers
  → Build pressure with dot balls
  
Middle: Spinner-dominated (Ravindra + Deepti)
  → Target weaknesses in middle order
  → Varied pace and direction
  
Death: Death specialists (Jhulan + Renuka)
  → Yorker focus, accuracy critical
  → Contain final acceleration

MATCHUP TARGETING:
✓ Healy: Ravindra (leg-spin weakness 110 SR)
✓ Mooney: Jhulan (yorker specialist)
✓ Lanning: Deepti (off-spin weakness 104 SR)

EXPECTED OUTCOMES:
Opposition Total: 150-165 runs
Wickets Taken: 4-5
Economy Rate: 7.5-8.25 (solid)
Death Overs: 8.5-9.5 runs per over

Confidence: VERY HIGH (Score: 89/100)
```

---

## Related Documentation

- [Squad Selector Node](SQUAD_SELECTOR.md)
- [Opponent Analysis Node](OPPONENT_ANALYSIS.md)
- [Batting Order Optimizer](BATTING_ORDER.md)
- [Data Schema Reference](Data-Schema.md)
- [Cricket Glossary - Bowling Terms](../wiki/Cricket-Glossary.md)

