# wt20-oracle Technical Architecture

Complete explanation of features, algorithms, and system flow.

---

## 1. System Overview

### Two Operating Modes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          wt20-oracle                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  PRE-MATCH MODE                          LIVE MODE                       │
│  (Night before / morning)                (Between overs during match)   │
│                                                                           │
│  INPUT:                                  INPUT:                          │
│  - Opponent team                         - Live match state JSON         │
│  - Venue                                 - Current score, wickets        │
│  - Tournament stage                      - Over number, phase            │
│                                          - Batter at crease              │
│  OUTPUT:                                 OUTPUT:                         │
│  ✓ Squad selection (15 players)          ✓ Bowling change recommendation │
│  ✓ Batting order (optimal 11)            ✓ Field placement               │
│  ✓ Bowling plan (bowler roles)           ✓ Pinch-hitter call            │
│  ✓ Strategy brief (narrative)            ✓ Win probability update        │
│                                          ✓ Next-over tactic              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Architecture

### Core Data Files (Input)

```
wt20_oracle/data/
├── players/
│   ├── india.json           ← 15 players with T20I stats + analyst insights
│   ├── australia.json       ← Opponent squad profiles
│   └── [10 more teams]      ← All participating teams
│
├── matchups.json            ← 39,277 batter-bowler head-to-head records
│   └── Example: {smriti_mandhana vs megan_schutt: {balls: 23, runs: 38, ...}}
│
├── analyst_insights.json    ← Qualitative player assessments
│   └── Form, injury, psychology, vs-opponent notes per player
│
├── venues.json              ← 7 tournament venues
│   └── Pitch type, dew factor, boundary dimensions
│
├── schedule.json            ← Group stage + knockout structure
│
├── teams.json               ← All 12 teams with H2H history
│   └── {india: {vs_australia: {played: 24, won: 6, lost: 18}}}
│
└── raw/cricsheet/           ← Source data (not used at runtime)
    ├── t20s_female.zip
    ├── wpl_female.zip
    ├── wbbl_female.zip
    └── hundred_female.zip
```

### Player Statistics Structure (Per Team)

Each player in `india.json`:

```json
{
  "id": "harmanpreet_kaur",
  "name": "Harmanpreet Kaur",
  "role": "batter",
  "caps": 132,
  "t20i_stats": {
    "batting": {
      "matches": 132,
      "runs": 3115,
      "strike_rate": 111.17,
      "phase_splits": {
        "powerplay": { "balls": 335, "runs": 250, "strike_rate": 74.63 },
        "middle":    { "balls": 1220, "runs": 1069, "strike_rate": 87.62 },
        "death":     { "balls": 559, "runs": 796, "strike_rate": 142.4 }
      },
      "vs_pace": { "strike_rate": 109.84, "dot_ball_pct": 20.3, "dismissal_rate": 0.08 },
      "vs_spin": { "strike_rate": 113.2, "dot_ball_pct": 15.1, "dismissal_rate": 0.07 },
      "form_windows": {
        "last_5_matches": { "matches": 5, "runs": 156, "balls": 124, "strike_rate": 125.8 },
        "last_6_months": { "matches": 18, "runs": 487, "balls": 410, "strike_rate": 118.8 },
        "last_12_months": { "matches": 31, "runs": 812, "balls": 675, "strike_rate": 120.3 }
      },
      "icc_tournament_record": { "matches": 12, "runs": 289, "strike_rate": 128.3 }
    },
    "bowling": { /* similar structure */ }
  },
  "analyst_insights": {
    "form_rating": "exceptional",
    "concerns": null,
    "injury_status": "fit"
  }
}
```

### Matchup Matrix Entry

```json
{
  "batter_id": "smriti_mandhana",
  "bowler_id": "megan_schutt",
  "balls_faced": 23,
  "runs": 38,
  "strike_rate": 165.22,
  "by_phase": {
    "powerplay": { "balls": 8, "runs": 12, "dismissals": 0 },
    "middle":    { "balls": 10, "runs": 18, "dismissals": 0 },
    "death":     { "balls": 5, "runs": 8, "dismissals": 1 }
  },
  "statistical_reliability": "high"
}
```

---

## 3. Pre-Match Pipeline

### Execution Flow

```
                    INPUT: opponent, venue, stage
                           ↓
            ┌──────────────────────────────┐
            │    LOAD DATA & CONTEXT       │
            ├──────────────────────────────┤
            │ - Squad stats (India + opp)  │
            │ - H2H history                │
            │ - Matchup matrix             │
            │ - Analyst insights           │
            │ - Venue characteristics      │
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │   1. OPPONENT ANALYSIS       │
            ├──────────────────────────────┤
            │ - Recent form (last 5 T20Is) │
            │ - Key player profiles        │
            │ - Bowling attack type        │
            │ - Venue history vs opp       │
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │   2. SQUAD SELECTION         │
            ├──────────────────────────────┤
            │ ALGORITHM: Greedy scoring    │
            │ - Fitness check              │
            │ - Form assessment            │
            │ - Role balance (5-3-7)       │
            │ → Output: 15 players         │
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │   3. BATTING ORDER           │
            ├──────────────────────────────┤
            │ ALGORITHM: Mixed Integer LP  │
            │ - Optimize matchup scores    │
            │ - Apply analyst constraints  │
            │ - Enforce depth rules        │
            │ → Output: 11 players ranked  │
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │   4. BOWLING PLAN            │
            ├──────────────────────────────┤
            │ - Bowler type assignment     │
            │ - Death specialist ID        │
            │ - Powerplay bowlers          │
            │ → Output: roles per bowler   │
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │   5. STRATEGY BRIEF          │
            ├──────────────────────────────┤
            │ ALGORITHM: Claude API        │
            │ - Narrative generation       │
            │ - Analyst insights embedded  │
            │ - Tactical recommendations   │
            │ → Output: Human-readable     │
            └──────────────────────────────┘
                           ↓
                OUTPUT: Squad, order, bowling, strategy
```

---

## 4. Pre-Match Algorithms in Detail

### 4.1 Opponent Analysis Node

**Purpose:** Understand opponent strengths, weaknesses, recent form

**Inputs:**
- Opponent team squad stats
- H2H history (matches played, won/lost)
- Venue information
- Recent match results (last 5 T20Is)

**Computation:**
```python
opponent_profile = {
    "key_batters": rank_by_form(squad, metric="strike_rate", window="last_6m"),
    "key_bowlers": rank_by_form(squad, metric="economy", window="last_6m"),
    "powerplay_strength": avg_runs_first_6_overs(opponent, last_5_matches),
    "death_strength": avg_runs_final_4_overs(opponent, last_5_matches),
    "venue_strength": h2h_at_venue(opponent, venue_id),
    "weaknesses": identify_gaps(opponent_squad),
    "recent_momentum": trend_analysis(opponent, last_5_matches)
}
```

**Output:** Opponent risk/strength profile

---

### 4.2 Squad Selection Node

**Purpose:** Select optimal 15-player squad from available players

**Constraints:**
- Role balance: ~5 batters, ~3 allrounders, ~7 bowlers
- Fitness: exclude injured players
- Form: prioritize recent form (form_windows)
- Analyst concerns: respect injury flags, debut caution

**Algorithm: Greedy + Constraint Satisfaction**

```python
def select_squad(available_players, team_roster, opponent_profile):
    """
    Greedy scoring with constraint satisfaction.
    """
    # Step 1: Calculate player score (form + role + analyst adjustment)
    player_scores = {}
    for player in available_players:
        base_score = calculate_base_score(player)
        # Form adjustment
        form_mod = form_modifier_from_insights(player.analyst_insights)
        base_score *= form_mod
        
        # Injury penalty
        if player.analyst_insights.injury_status == "unfit":
            base_score *= 0.5  # Heavy penalty
        elif player.analyst_insights.injury_status == "fit_with_caution":
            base_score *= 0.85  # Slight penalty
        
        player_scores[player.id] = base_score
    
    # Step 2: Greedy selection by score, respecting role balance
    selected = []
    role_counts = {"batter": 0, "bowler": 0, "allrounder": 0}
    role_targets = {"batter": 5, "bowler": 7, "allrounder": 3}
    
    for player_id in sorted(player_scores, key=lambda x: player_scores[x], reverse=True):
        player = available_players[player_id]
        role = player.role
        
        # Accept if role slot available
        if role_counts[role] < role_targets[role]:
            selected.append(player)
            role_counts[role] += 1
            
            # Early exit
            if len(selected) == 15:
                break
    
    return selected
```

**Output:** 15-player squad

---

### 4.3 Batting Order Optimization (MILP)

**Purpose:** Rank selected 11 batters to maximize expected runs while respecting:
- Matchup advantage vs opponent bowlers
- Depth (protect weak links)
- Form state (recent confidence)
- Analyst constraints (injuries, debuts)

**Algorithm: Mixed Integer Linear Programming (PuLP + CBC solver)**

**Decision Variables:**
```
position[i, p] ∈ {0, 1}   # Is batter i at position p? (p = 1..11)
```

**Objective Function (Maximize):**
```
Maximize: Σ_i Σ_p [ position[i, p] * score[i, p] ]

where:
  score[i, p] = matchup_score[i] * depth_weight[p] * form_modifier[i]
  
  matchup_score[i] = avg(strike_rate[i vs opp_bowler_j]) for all j
                     weighted by bowler reliability & phase
  
  depth_weight[p] = {
    1.0 if p ∈ [1,2]      # Openers: full weight
    0.95 if p ∈ [3,5]     # Middle-order: slight discount (depth)
    0.80 if p ∈ [6,11]    # Lower-order: heavier discount
  }
```

**Constraints:**

1. **Position exclusivity:** Each batter at most one position
   ```
   Σ_p position[i, p] ≤ 1  ∀ i
   ```

2. **Position filling:** Each position has exactly one batter
   ```
   Σ_i position[i, p] = 1  ∀ p
   ```

3. **Role constraints:**
   ```
   Σ_i∈bowlers position[i, p] ≤ 3  (at most 3 bowlers in top 8)
   Σ_i∈allrounders position[i, p] ≥ 2  (at least 2 allrounders for flexibility)
   ```

4. **Analyst injury constraints:**
   ```
   if player_i.injury == "shoulder":
       Σ_p∈death position[i, p] = 0  (avoid death overs)
   
   if player_i.status == "debut":
       Σ_p∈[1] position[i, p] = 0  (don't open with debut)
   ```

5. **Captain/vice-captain placement:**
   ```
   position[harmanpreet, p] ∈ {p ≥ 2}  (captain not opening)
   position[smriti, p] ∈ {p ∈ [1,3]}  (vice-captain in top 3)
   ```

**Example Output:**
```
Position 1: Shafali Verma (SR: 98.5, form: strong)
Position 2: Smriti Mandhana (SR: 142.3, form: exceptional)
Position 3: Harmanpreet Kaur (SR: 111.2, captain)
Position 4: Jemimah Rodrigues (SR: 125.1)
Position 5: Nandini Sharma (SR: 85.2, debut, protected)
Positions 6-11: Allrounders + bowlers
```

---

### 4.4 Bowling Plan Node

**Purpose:** Assign bowler roles based on:
- Bowling style (pace vs spin)
- Phase specialization (powerplay, death)
- Opponent batting profile
- Recent economy rate

**Algorithm: Role Assignment + Pattern Matching**

```python
def assign_bowling_roles(bowling_squad, opponent_profile):
    """
    Assign bowlers to roles: opening, middle, death, spinner, etc.
    """
    roles = {
        "powerplay_bowlers": [],
        "middle_overs_bowlers": [],
        "death_specialists": [],
        "primary_spinner": None,
        "secondary_spinner": None
    }
    
    # Rank bowlers by phase specialization
    powerplay_ranked = rank_bowlers(
        bowling_squad, 
        metric="economy",
        phase="powerplay",
        window="last_12m"
    )
    
    death_ranked = rank_bowlers(
        bowling_squad,
        metric="economy",
        phase="death",
        window="last_12m"
    )
    
    # Assign roles
    roles["powerplay_bowlers"] = powerplay_ranked[:2]  # Top 2 for powerplay
    roles["death_specialists"] = death_ranked[:2]      # Top 2 for death
    
    # Identify spinners
    spinners = [b for b in bowling_squad if b.bowling_style in SPIN_STYLES]
    if spinners:
        roles["primary_spinner"] = spinners[0]
        if len(spinners) > 1:
            roles["secondary_spinner"] = spinners[1]
    
    # Match vs opponent
    if opponent_profile["key_batters"] are_weak_vs_"short_pitch":
        roles["short_pitch_specialist"] = find_bowler(style="short_pitch")
    
    return roles
```

**Output:**
```json
{
  "bowling_plan": {
    "opening_bowler": "Renuka Singh",
    "opening_partner": "Arundhati Reddy",
    "primary_spinner": "Radha Yadav",
    "death_specialist": "Deepti Sharma",
    "backup_bowlers": ["Shreyanka Patil", "Kranti Gaud"]
  }
}
```

---

### 4.5 Strategy Narrative Node (Claude API)

**Purpose:** Generate human-readable strategy brief with tactical recommendations

**Algorithm: Prompt-based text generation (Claude 3.5 Sonnet)**

**Input to Claude:**
```python
strategy_context = {
    "opponent": {
        "key_batters": ["Alyssa Healy", "Beth Mooney"],
        "key_bowlers": ["Megan Schutt", "Ellyse Perry"],
        "recent_form": "strong (3 wins in last 5)",
        "weaknesses": "vulnerable to spin in middle overs"
    },
    "squad": {
        "batting_order": [...],
        "bowling_plan": {...},
        "analyst_notes": [...insights...]
    },
    "venue": {
        "name": "Edgbaston",
        "pitch_type": "fast and bouncy",
        "dew_factor": 0.2
    }
}

prompt = f"""
You are a cricket strategy advisor for India Women's T20 team.

Opponent: {strategy_context['opponent']}
Our Squad: {strategy_context['squad']}
Venue: {strategy_context['venue']}

Generate a strategic brief with:
1. Key match-ups to exploit (our strengths vs their weaknesses)
2. Batting strategy (approach, phase-by-phase tactics)
3. Bowling strategy (line, length, field placements)
4. Risk management (avoid these mistakes)
5. Momentum points (when to attack, when to consolidate)

Reference analyst insights when available. Be specific about player matchups.
Keep to 300-400 words, conversational tone.
"""
```

**Claude Output:**
```
STRATEGY BRIEF: India vs Australia, Edgbaston

BATTING APPROACH:
Australia's pace attack (Schutt, Perry, McGrath) is elite but predictable.
Key insight: Schutt has struggled vs left-handed batters (Smriti 3 ducks in 5).
→ Counter: Open with Shafali instead, play aggressive vs spinners.

PHASE-BY-PHASE:
• Powerplay (0-6): Accumulation. Perry likely to open; expect short-pitched.
  Action: Shafali to rotate strike, Smriti aggressive on the off-side.
• Middle (7-15): Acceleration window. Australia brings spinners here.
  Action: Smriti thrives vs off-spin (SR 145+); target Ecclestone early.
• Death (16-20): Powerplay against death bowlers. Harmanpreet's phase.
  Action: Captain to take charge; 15+ runs per over expected.

BOWLING STRATEGY:
Australia's strengths: Powerplay batting (Healy aggressive), death hitting.
→ Renuka to bowl tight lines in powerplay; expect short boundaries at Edgbaston.
→ Deepti to attack in middle vs right-handers; field slip for catches.
→ Death: Radha Yadav to use variations; expect aggressive batting.

RISK MANAGEMENT:
❌ Avoid: Giving Healy width early; committing to aggressive field vs Perry.
✓ Do: Bowl tight lines; use short-pitched strategically only after settling.
```

---

## 5. Live Match Pipeline

### Execution Flow

```
                INPUT: Live match state JSON
                (current score, wickets, over, batter, bowler)
                           ↓
            ┌──────────────────────────────┐
            │   PARSE MATCH STATE          │
            ├──────────────────────────────┤
            │ - Score, wickets, RRR        │
            │ - Current batter/bowler      │
            │ - Balls faced in inning      │
            │ - Phase (powerplay/mid/death)│
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │  1. LIVE STATE ASSESSMENT    │
            ├──────────────────────────────┤
            │ - Momentum (last 3 overs)    │
            │ - Pressure on batting team   │
            │ - Match situation (favored?) │
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │  2. WIN PROBABILITY          │
            ├──────────────────────────────┤
            │ ALGORITHM: Monte Carlo       │
            │ - Simulate remaining overs   │
            │ - 10,000 iterations          │
            │ → Output: P(win | current)   │
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │  3. BOWLING CHANGE           │
            ├──────────────────────────────┤
            │ ALGORITHM: Expected value    │
            │ - Next 6 balls: which bowler?│
            │ - Matchup vs batter          │
            │ - Field adjustment           │
            │ → Output: bowler recommendation
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │  4. FIELD PLACEMENT          │
            ├──────────────────────────────┤
            │ - Batter profile             │
            │ - Phase-specific strategy    │
            │ - Pressure vs aggression     │
            │ → Output: 11-player field    │
            └──────────────────────────────┘
                           ↓
            ┌──────────────────────────────┐
            │  5. NARRATIVE UPDATE         │
            ├──────────────────────────────┤
            │ - Next over tactic           │
            │ - Probability commentary     │
            │ - Risk/opportunity points    │
            │ → Output: Human-readable     │
            └──────────────────────────────┘
                           ↓
        OUTPUT: Bowling change, field, probability, narrative
```

---

## 6. Live Match Algorithms

### 6.1 Win Probability Calculator (Monte Carlo)

**Purpose:** Estimate India's win probability given current match state

**Algorithm: Monte Carlo Simulation**

```python
def calculate_win_probability(match_state, num_simulations=10000):
    """
    Simulate all possible remaining overs; compute P(India wins).
    """
    wins = 0
    
    for iteration in range(num_simulations):
        # Copy current state
        simulated_state = match_state.copy()
        
        # Simulate remaining overs
        while not match_over(simulated_state):
            # Draw next ball outcome
            ball_outcome = sample_ball_outcome(
                batter=simulated_state.current_batter,
                bowler=simulated_state.current_bowler,
                match_state=simulated_state
            )
            
            # Update score
            simulated_state.runs += ball_outcome.runs
            simulated_state.wickets += ball_outcome.is_wicket
            simulated_state.balls_in_over += 1
            
            # Check for wicket
            if ball_outcome.is_wicket:
                simulated_state.current_batter = next_batter()
        
        # Check final outcome
        if simulated_state.final_score > match_state.target:
            wins += 1
    
    return wins / num_simulations
```

**Ball Outcome Sampling:**

```python
def sample_ball_outcome(batter, bowler, match_state):
    """
    Sample next ball outcome from probability distribution.
    Uses: historical matchup stats + current form + phase.
    """
    # Get matchup data
    matchup = matchups_db.get((batter.id, bowler.id))
    
    # Phase-specific adjustment
    phase = over_to_phase(match_state.over)
    phase_stats = matchup.by_phase[phase]
    
    # Form adjustment
    batter_form = form_modifier_from_insights(batter.analyst_insights)
    bowler_form = form_modifier_from_insights(bowler.analyst_insights)
    
    # Construct probability distribution
    # P(0 runs) = dot_ball_pct
    # P(1 run) = (100 - dot_ball_pct) / 5
    # P(2 runs) = ...
    # P(4 runs) = boundary_pct / 2
    # P(6 runs) = boundary_pct / 2
    # P(wicket) = dismissal_rate
    
    base_sr = matchup.strike_rate
    adjusted_sr = base_sr * batter_form * bowler_form
    
    # Sample outcome
    rand = random.random()
    if rand < dismissal_rate:
        return BallOutcome(runs=0, is_wicket=True)
    elif rand < dot_ball_pct:
        return BallOutcome(runs=0, is_wicket=False)
    elif rand < dot_ball_pct + boundary_pct/2:
        return BallOutcome(runs=4, is_wicket=False)
    elif rand < dot_ball_pct + boundary_pct:
        return BallOutcome(runs=6, is_wicket=False)
    else:
        return BallOutcome(runs=1or2or3, is_wicket=False)
```

**Output:**
```
Current match state (India batting):
  Score: 87/3 after 13 overs
  Target: 145
  RRR: 11.5

Win Probability: 38% (6,200 wins out of 10,000 simulations)

Top paths to victory:
  1. Harmanpreet scores 35+ runs in overs 14-20 (2,100 sims)
  2. Jemimah + Harmanpreet 100-run partnership (1,800 sims)
  3. Lower-order hitting in death overs (1,200 sims)
```

---

### 6.2 Bowling Change Recommendation

**Purpose:** Recommend next bowler to maximize expected wickets/minimize runs

**Algorithm: Expected Value Optimization**

```python
def recommend_bowling_change(match_state, available_bowlers):
    """
    For each available bowler, compute expected value of next 6 balls.
    Choose bowler with highest EV.
    """
    ev_scores = {}
    
    for bowler in available_bowlers:
        # Get expected value vs current batter
        matchup = matchups_db.get((current_batter.id, bowler.id))
        
        # Compute EV of next 6 balls
        # EV = Σ_outcome [ P(outcome) * value(outcome) ]
        # where value(0 runs) = +1, value(4 runs) = -2, wicket = +10
        
        ev = 0.0
        
        # Dot ball: good
        ev += matchup.dot_ball_pct * 1.0
        
        # 1-run: neutral
        ev += (1 - matchup.dot_ball_pct - matchup.boundary_pct) * matchup.dismissal_rate * 0.0
        
        # 4 runs: bad
        ev -= matchup.boundary_pct * 0.5 * 2.0
        
        # 6 runs: very bad
        ev -= matchup.boundary_pct * 0.5 * 3.0
        
        # Wicket: very good
        ev += matchup.dismissal_rate * 10.0
        
        # Apply phase adjustment
        phase = over_to_phase(match_state.over)
        phase_ev = ev * phase_weight[phase]
        
        # Apply form adjustment
        bowler_form = form_modifier_from_insights(bowler.analyst_insights)
        adjusted_ev = phase_ev * bowler_form
        
        ev_scores[bowler.id] = adjusted_ev
    
    # Also consider overs bowled
    for bowler_id in ev_scores:
        overs_bowled = match_state.overs_bowled_by.get(bowler_id, 0)
        if overs_bowled >= 4:  # Max 4 overs per bowler
            ev_scores[bowler_id] *= 0.1  # Heavy penalty
    
    # Return top recommendation
    best_bowler = max(ev_scores, key=ev_scores.get)
    return {
        "recommendation": best_bowler,
        "ev_score": ev_scores[best_bowler],
        "rationale": f"Highest EV vs {current_batter.name}; matches phase"
    }
```

**Example Output:**
```
BOWLING CHANGE RECOMMENDATION (Over 14)

Current: Renuka Singh (3.2 overs, 21 runs)
Batter: Alyssa Healy (aggressive, SR 145+)
Phase: Death overs (15-19 remaining)

RECOMMENDATION: Deepti Sharma
  Expected Value Score: 3.2/10
  Rationale:
    ✓ vs Healy: 12 balls, 18 runs, 1 dismissal (SR 150)
    ✓ Death specialist: economy 6.8 in death phase
    ✓ Off-spin can exploit any turn on pitch
    ⚠️ Risk: Healy aggressive vs spin

ALTERNATIVES:
  2. Radha Yadav (EV: 2.9) — Left-arm variation
  3. Shreyanka Patil (EV: 2.1) — Young, low experience vs Healy
```

---

### 6.3 Field Placement

**Purpose:** Position 11 fielders optimally given:
- Current batter's strengths
- Bowler's release point
- Score situation (defend vs attack)
- Match phase

**Algorithm: Rule-based + Optimization**

```python
def compute_field_placement(match_state, bowler, batter):
    """
    Place 11 fielders in optimal positions.
    """
    # Phase-specific strategy
    if match_state.phase == "powerplay":
        strategy = "defense"  # Conservative field
        slip_positions = 1
        boundary_fielders = 3
    elif match_state.phase == "death":
        strategy = "attack"  # Aggressive field
        slip_positions = 2
        boundary_fielders = 6
    else:  # middle
        strategy = "balance"
        slip_positions = 1
        boundary_fielders = 4
    
    # Batter-specific adjustments
    if batter.bowling_style == "right_arm" and batter is_left_handed:
        # Left-hander might go to leg side
        field = {
            "slips": slip_positions,
            "gully": 1,
            "short_leg": 1,
            "mid_wicket": 1,
            "square_leg": 1,
            "long_leg": 1,
            "mid_off": 1,
            "deep_mid_wicket": 1,
            "backward_square": boundary_fielders - 1,
            "long_on": boundary_fielders - 1
        }
    else:
        # Right-hander typically goes to off side
        field = {
            "slips": slip_positions,
            "gully": 1,
            "point": 1,
            "extra_cover": 1,
            "mid_off": 1,
            "covers": 1,
            "mid_on": 1,
            "short_fine": 1,
            "third_man": boundary_fielders - 1,
            "deep_backward_square": boundary_fielders - 1
        }
    
    # Score pressure adjustment
    if match_state.win_probability < 0.3:
        # India losing: aggressive attack
        field["slips"] += 1
        field["gully"] += 1
    elif match_state.win_probability > 0.7:
        # India winning: defensive
        field["mid_off"] += 1
        field["mid_on"] += 1
    
    return field
```

**Field Diagram Output:**
```
FIELD PLACEMENT (Over 14, Australia batting)

        Boundary (100m)
    ╔═══════════════════════╗
    ║                       ║
    ║     Third Man         ║  (boundary fielder)
    ║     Deep Backward Sq  ║
    ║       
    ║   Slips (2)           ║
    ║   Gully               ║
    ║       
    ║                       ║
    ║   Short Leg       Point
    ║      Square Leg    Extra Cover
    ║                   Mid Off
    ║                      
    ║                       ║
    ║                       ║
    ║   Mid Wicket      Covers
    ║      Long Leg        Mid On
    ║                      
    ║   Long On            ║
    ║                       ║
    ║                       ║
    ╚═══════════════════════╝
         (Bowler: Deepti)
         (Batter: Healy - Right-hander, aggressive)

STRATEGY: Death overs, attacking field
- 2 slips for catching opportunity
- Boundary fielders: 6 (vs natural hitter)
- Mid-wicket/leg-side loaded (Healy's strength)
```

---

## 7. Analyst Insights Integration

### How Analyst Data Flows Through Decisions

```
analyst_insights.json
    ↓
    ├─→ form_modifier_from_insights()
    │       ↓
    │   [Squad Selection] — Adjust player scores
    │   [Batting Order MILP] — Adjust objective function weights
    │   [Monte Carlo] — Sample ball outcome with form adjustment
    │
    ├─→ constraint_from_injury()
    │       ↓
    │   [MILP] — Add hard constraint: "no death overs"
    │   [Bowling Change] — Exclude if injury prevents role
    │
    ├─→ matchup_modifier_from_insights()
    │       ↓
    │   [Batting Order] — Reweight matchup scores
    │   [Bowling Change] — Adjust EV vs specific bowler
    │
    ├─→ vs_opponent_recommendation()
    │       ↓
    │   [Narrative] — Explain tactical choices
    │   [Field Placement] — Influence field setup
    │
    └─→ psychological_notes_for_narrative()
            ↓
        [Claude API] — Enrich strategy brief

Example: Smriti Mandhana vs Megan Schutt
    insight: "3 ducks in 5 meetings vs Schutt; uncomfortable vs short-pitched"
    ↓
    [Batting Order] → Reduce matchup_score by 0.90x
    [Bowling Change] → Deprioritize Schutt early overs
    [Field Placement] → Prepare aggressive field when Schutt bowls
    [Narrative] → "Avoid Schutt powerplay; Smriti alternative opening"
```

---

## 8. Key Mathematical Concepts

### 8.1 Strike Rate Calculation

**Formula:**
```
Strike Rate (SR) = (Runs / Balls Faced) × 100
```

**Example:**
- Harmanpreet Kaur in death overs: 796 runs / 559 balls × 100 = 142.4 SR
- Means: average 142.4 runs per 100 balls faced (1.42 runs per ball)

### 8.2 Dot Ball Percentage

**Formula:**
```
Dot Ball % = (Balls with 0 runs / Total Balls) × 100
```

**Significance:** Higher dot % = more pressure, harder to score off

### 8.3 Dismissal Rate

**Formula:**
```
Dismissal Rate = Dismissals / Balls Faced
```

**Example:** If Schutt gets Smriti out 1 in 5 times, dismissal_rate = 1/5 = 0.20 (20%)

### 8.4 Expected Value

**Formula:**
```
EV = Σ [ P(outcome) × value(outcome) ]
```

**Bowling decision:**
```
EV = P(dot) × 1 + P(1-run) × 0 - P(boundary) × 3 + P(wicket) × 10
```

Higher EV = better bowler choice

### 8.5 Optimization (MILP)

**General form:**
```
Maximize:   Σ c_i × x_i
Subject to: Σ a_ij × x_i ≤ b_j  (constraints)
            x_i ∈ {0, 1}        (binary variables)
```

**Batting order MILP:**
- Maximize: total matchup score
- Constraints: position uniqueness, role balance, analyst rules
- Solver: CBC (open-source), finds optimal ordering in <1 second

---

## 9. System Performance Characteristics

### Computational Complexity

| Component | Algorithm | Time | Scalability |
|-----------|-----------|------|-------------|
| Squad Selection | Greedy | O(n log n) | <100ms for 180 players |
| Batting Order | MILP (PuLP+CBC) | O(2^n) | <1s for 11 players |
| Bowling Change | EV ranking | O(m log m) | <10ms for 7 bowlers |
| Win Probability | Monte Carlo | O(s × r) | 1-2s for 10k simulations |
| Field Placement | Rules + opt | O(n) | <50ms for 11 players |
| Narrative | Claude API | ~2-5s | Network-bound |

### Data Quality Metrics

| Metric | Value | Impact |
|--------|-------|--------|
| Player Coverage | 98.9% | Only 2 players missing (no data) |
| Matchup High Reliability | 4,089/39,277 | 10.4% very confident predictions |
| Form Windows | All players | Recency-weighted decision-making |
| Analyst Insights | India 100%, others partial | India squad best-informed decisions |

---

## 10. Decision Output Formats

### Pre-Match Output: JSON

```json
{
  "mode": "prematch",
  "match": "India vs Australia, Edgbaston",
  "generated_at": "2026-06-13T08:00:00Z",
  
  "squad_selection": {
    "selected_11": [
      {"name": "Shafali Verma", "position": 1, "role": "opener"},
      {"name": "Smriti Mandhana", "position": 2, "role": "batter"},
      // ...
    ],
    "bench": ["player_name", ...]
  },
  
  "batting_order": {
    "optimized_order": [...],
    "matchup_scores": {...},
    "expected_runs": 145,
    "confidence": 0.68
  },
  
  "bowling_plan": {
    "powerplay": ["Renuka Singh", "Arundhati Reddy"],
    "middle": ["Radha Yadav", "Deepti Sharma"],
    "death": ["Deepti Sharma"],
    "roles": {...}
  },
  
  "strategy_brief": "Narrative text..."
}
```

### Live Output: JSON

```json
{
  "mode": "live",
  "match_state": {
    "score": 87,
    "wickets": 3,
    "overs": 13.2,
    "phase": "middle"
  },
  
  "analysis": {
    "win_probability": 0.38,
    "momentum": -0.15,
    "pressure_index": 0.42
  },
  
  "recommendations": {
    "bowling_change": {
      "bowler": "Deepti Sharma",
      "rationale": "Best EV vs Healy",
      "ev_score": 3.2
    },
    "field_placement": {...},
    "next_over_tactic": "Defend..."
  }
}
```

---

## Summary

**wt20-oracle** is a multi-layered decision support system combining:

1. **Quantitative layer:** Statistics (39k matchups), Monte Carlo simulation, MILP optimization
2. **Qualitative layer:** Analyst insights (form, injury, psychology, tactics)
3. **Narrative layer:** Claude-generated strategy briefs explaining *why*

**Key innovation:** Blending data-driven optimization with human expertise (analyst insights), ensuring recommendations are both statistically sound AND strategically sensible.

