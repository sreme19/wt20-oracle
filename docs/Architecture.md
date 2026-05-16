# Architecture Overview (Beginner's Guide)

This document explains how wt20-oracle works, step-by-step, without assuming you know how software systems are built.

---

## The Big Picture: Two Modes

wt20-oracle has two completely different decision-making workflows:

```
┌─────────────────────────────────────────────────────┐
│              wt20-oracle System                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  PRE-MATCH MODE          →      LIVE MODE          │
│  (Before the game)                (During game)    │
│  - Takes 5-10 minutes      - Takes < 30 seconds    │
│  - Lots of thinking         - Must be fast         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

Let's understand each one.

---

## MODE 1: Pre-Match Recommendations

### Scenario
It's the night before India plays Australia. The captain needs to know:
- Who should play (the 11 best players)?
- What order should they bat in?
- How should we plan the bowling?

### How It Works (Step-by-Step)

```
INPUT
(Opponent: Australia, Venue: Edgbaston)
        ↓
        ├─→ [1] Opponent Analyzer
        │   • Looks at Australia's team
        │   • Finds their strengths & weaknesses
        │   ↓
        ├─→ [2] Squad Selector
        │   • Picks 11 best players from 15
        │   • Avoids weak matchups vs Australia's bowlers
        │   ↓
        ├─→ [3] Batting Order Optimizer
        │   • Arranges the 11 in best order
        │   • Uses complex math to maximize expected score
        │   ↓
        ├─→ [4] Bowling Plan Creator
        │   • Decides which bowler plays which role
        │   • Match each bowler to phases they're best at
        │   ↓
        └─→ [5] Narrator
            • Writes explanation in English
            • "We picked Harmanpreet at #3 because..."

OUTPUT
(Squad selection, batting order, bowling plan, strategy brief)
```

### Key Components (Explained in Detail)

#### [1] Opponent Analyzer
**What it does:** Studies the opposing team.

**Example:**
- Australia's best batters: Alyssa Healy, Beth Mooney
- Australia's bowlers are strong with: pace, death bowling
- Australia historically beats India 70% of the time

**How it gets this info:** Looks at historical match data and recent form

#### [2] Squad Selector
**What it does:** Picks the 11 best players.

**Algorithm:** Think of it like a puzzle:
- We have 15 pieces (players)
- We need to pick 11 pieces that fit together
- Some pieces fit better depending on who the opponent is

**Constraints (rules it must follow):**
- Must have a wicket-keeper
- At least 5 bowlers
- Can't have more than 3 overseas players
- Avoid putting a player at bat order #4 if they're not good at middle-overs batting

**How it decides:** Uses something called "MILP" (Mixed-Integer Linear Programming) — fancy math that finds the best combination. It looks at:
- Past performance against Australia specifically
- Recent form (last 5 matches, last 6 months)
- Which players complement each other

#### [3] Batting Order Optimizer
**What it does:** Arranges the 11 players in the best hitting order.

**Example output:**
```
#1 (PowerPlay)     → Shafali Verma (fast, aggressive)
#2 (PowerPlay)     → Smriti Mandhana (safe, consistent)
#3 (Middle overs)  → Harmanpreet Kaur (captain, flexible)
#4 (Middle overs)  → Jemimah Rodrigues (can hit and defend)
#5 (Death)         → Richa Ghosh (power hitter)
...and so on
```

**Logic:**
- Position 1-2 (PowerPlay): Need fast starters
- Position 3-4 (Middle): Need flexible, all-purpose batters
- Position 5-6 (Death): Need power hitters

**Uses:** Strike rates in different phases (how fast they score in PowerPlay vs Death overs)

#### [4] Bowling Plan Creator
**What it does:** Decides which bowlers should play and their roles.

**Example output:**
```
Pace Bowler (first 6 overs):
  → Renuka Singh (economy 6.2, takes wickets early)

Spin Bowler (middle 6 overs):
  → Ravindra (tight bowling, slows down scoring)

Death Bowler (last 4 overs):
  → Jhulan Goswami (experienced, best under pressure)
```

**Uses:** 
- How many runs each bowler gives (economy rate)
- Weakness of Australian batters against pace vs spin
- Past meetings between bowlers and Australian batters

#### [5] Narrator Agent
**What it does:** Explains everything in plain English.

**Example output:**
```
"We selected Harmanpreet Kaur at position #3 because:
  • She has a 125 strike rate in the middle overs
  • Head-to-head vs Australia, she averages 45 runs
  • She's flexible — can accelerate or stabilize depending on match situation"
```

Uses: Claude AI (large language model) to write natural explanations

---

## MODE 2: Live Match Recommendations

### Scenario
It's over #14 of the match. India has scored 87/3 (87 runs, 3 batters out). The captain needs to know:
- Should we bring on a new bowler?
- Where should we place fielders?
- What's our win probability?

### Why It's Different From Pre-Match

**Pre-match:**
- We have time (5-10 minutes)
- We can think deeply
- We can try many options (MILP math)

**Live match:**
- Very limited time (< 30 seconds)
- Captain needs instant recommendation
- Can't recalculate complex math every ball

### How It Works (Step-by-Step)

```
INPUT
(Current score, wickets, bowler info, batter at crease)
        ↓
        ├─→ [1] Live State Updater
        │   • Updates score after each over
        │   • Tracks momentum (swinging our way? Their way?)
        │   ↓
        ├─→ [2] Bowling Change Recommender
        │   • Should we bring a new bowler?
        │   • Look up: How did this batter perform vs this new bowler?
        │   ↓
        ├─→ [3] Field Placement Suggester
        │   • Where should fielders stand?
        │   • Defensive? Aggressive?
        │   ↓
        ├─→ [4] Pinch-Hitter Decision
        │   • Should we send aggressive batter early?
        │   • What's the risk vs reward?
        │   ↓
        ├─→ [5] Win Probability Calculator
        │   • Simulate 10,000 possible match endings
        │   • What % of them does India win?
        │   ↓
        └─→ [6] Narrator
            • Explain the recommendation

OUTPUT
(Bowling suggestion, field placement, win probability)
```

### Key Components

#### Pre-Computed Lookup Table
**What it is:** A giant table of all batter-vs-bowler matchups.

**Example rows:**
```
Smriti Mandhana vs Megan Schutt: 38 runs off 23 balls
Alyssa Healy vs Jhulan Goswami: 12 runs off 18 balls
```

**Why pre-computed?**
- There are 39,277 such matchups
- During a match, we need the answer in < 1 second
- So we calculate them all once before the match and store them
- During the match, we just look them up (like a phone directory)

#### [1] Live State Updater
**What it does:** Tracks the current game situation.

**Updates:**
- Current score (runs scored)
- Wickets (players out)
- Over number (how many 6-ball sequences have happened)
- Phase (PowerPlay: overs 1-6, Middle: 7-16, Death: 17-20)
- Which batter is at the crease now
- Momentum (winning or losing the ball-by-ball battle)

#### [2] Bowling Change Recommender
**What it does:** Should we bring a different bowler?

**Decision logic:**
- Current batter is scoring heavily against current bowler?
- There's a fresh bowler who has a good history vs this batter?
- We have enough bowlers left to spare?

**Example:**
```
Current situation:
- Alyssa Healy (batter) is at 45 runs off 28 balls
- She's scoring against Renuka Singh (bowler) at 150+ strike rate
- Jhulan Goswami is rested and available

Recommendation:
- Bring Jhulan on
- Jhulan vs Healy history: Healy only scores 95 strike rate
- Expected benefit: Reduce scoring by ~15%
```

#### [3] Field Placement
**What it does:** Where should 9 fielders stand?

**Defensive field** (spread out, hard to score):
```
      (bowler)
      |
  F  F | F  F
 F           F
  F       F
```

**Attacking field** (closer, more likely to get wicket):
```
      (bowler)
      |
F F F | F F F
 F         F
```

**Decides based on:**
- Risk level (are we desperate for a wicket?)
- Batter's style (does Alyssa Healy hit to leg side or off side?)
- Phase of match (PowerPlay: defensive, Death: attacking)

#### [4] Pinch-Hitter Decision
**What it does:** Should we send an aggressive batter early?

**Example:**
```
Match situation: Need 40 runs from 20 balls. Current batter is cautious.

Pinch-hitter analysis:
- Send Richa Ghosh (power hitter) early?
- Richa can score quickly but might get out
- Risk: We lose a wicket with little time left
- Reward: Could score 20 runs in 2 overs instead of 10

Recommendation: YES, send Richa now
```

#### [5] Win Probability Calculator
**What it does:** Simulates the rest of the match 10,000 times.

**Example simulation:**
```
Over 15-20 (6 remaining overs)
- Simulate all possible ball outcomes
- 3 runs? Wicket? 6 runs?
- Repeat 10,000 times with different random outcomes
- Count: "In how many of these 10,000 simulations does India win?"
- Result: India wins in 7,250 simulations = 72.5% win probability
```

**Uses:**
- Batting style (how aggressive?)
- Form (recent performance)
- Remaining batters (how good are they?)

---

## Data Flow: Where Does Information Come From?

```
Raw Data Sources
(CricSheet, ESPN Cricinfo, ICC)
        ↓
┌─────────────────────────────────────────┐
│  Data Processing (scripts/parse_cricsheet.py)
│                                         │
│  • Extract player stats                 │
│  • Calculate form windows               │
│  • Build matchup matrix                 │
│  • Track head-to-head records           │
└─────────────────────────────────────────┘
        ↓
Storage Files (wt20_oracle/data/)
        ├─→ players/india.json (player stats)
        ├─→ matchups.json (batter-vs-bowler records)
        ├─→ teams.json (team profiles)
        ├─→ venues.json (ground characteristics)
        └─→ analyst_insights.json (manual expert opinions)
        ↓
Decision Agents Read This Data
        ├─→ Squad Selector (uses player stats + matchups)
        ├─→ Batting Order (uses player form + phases)
        ├─→ Bowling Plan (uses bowler economy + matchups)
        └─→ Live Recommender (uses matchup lookups)
        ↓
Outputs to Captain/Coach
```

---

## Key Technical Terms (Simple Explanations)

| Term | What it means | Analogy |
|------|---------------|---------|
| **MILP** | Math for finding the best combination of things | Like finding the best 5 ingredients from 10 available to make the perfect dish |
| **Monte Carlo** | Simulating many random scenarios | Like flipping a coin 10,000 times to see how many heads you get |
| **Matchup** | History between one batter and one bowler | Your win record against your friend in chess |
| **Phase** | Time period in the match (PowerPlay, Middle, Death) | Breakfast, lunch, dinner in a day |
| **Reliability** | How confident we are in a stat | Knowing for certain vs guessing |
| **Agent** | A decision-making component | A team member who specializes in one job |

---

## Summary

**wt20-oracle has two modes:**
1. **Pre-match** — 5 agents think deeply, pick best 11, order them, plan bowling
2. **Live** — Smaller team makes fast decisions based on pre-computed lookup tables

**All decisions use:**
- Cricket statistics (past performance)
- Matchup history (batter vs bowler)
- Current form (recent matches)
- Mathematical optimization
- Expert opinions (analyst insights)

**Output is always:**
- A recommendation (squad, order, bowling, field, etc.)
- An explanation in plain English

---

## Next Steps

- **Learn how to use it:** [CLI Usage Guide](CLI-USAGE.md)
- **Understand the data:** [Data Schema](Data-Schema.md)
- **See all terms explained:** [Glossary](Glossary.md)
