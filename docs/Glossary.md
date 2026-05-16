# Glossary: Cricket & Technical Terms

Quick reference for terms used in wt20-oracle.

---

## Cricket Terminology

### Match Structure

| Term | Definition | Example |
|------|-----------|---------|
| **T20** | 20-over cricket match format (super fast-paced) | Total of 120 balls per team |
| **Over** | Sequence of 6 balls bowled by one bowler | "Over 5" = overs 5.0 to 5.5 |
| **Inning** | One team's turn to bat | India's inning vs Australia's inning |
| **PowerPlay** | First 6 overs where hitting is aggressive | Overs 1-6 |
| **Middle Overs** | Middle phase of batting (overs 7-16) | Strategic accumulation |
| **Death Overs** | Final 4 overs (17-20) where high scoring is attempted | Aggressive hitting |
| **Phase** | General time period in the match | PowerPlay, Middle, Death |

### Batting

| Term | Definition | Example |
|------|-----------|---------|
| **Batter** | Player trying to hit the ball and score runs | Smriti Mandhana, Alyssa Healy |
| **Strike Rate (SR)** | Runs scored per 100 balls | If a batter scores 50 runs off 40 balls, SR = 125 |
| **Average** | Average runs scored per innings | If a batter scored 100, 50, 75 in 3 matches, average = 75 |
| **Dot Ball** | A ball where batter scores 0 runs | Ball delivered but no runs |
| **Wicket** | When a batter is eliminated from the game | Getting out |
| **Opening Pair** | First two batters | Shafali and Smriti in India |
| **Middle Order** | Batters at positions 3-6 | Most important positions |
| **Lower Order** | Batters at positions 7-11 (mostly bowlers) | Bowlers who can also bat |
| **Accumulator** | Batter who focuses on consistent scoring | Safe player, lower strike rate |
| **Aggressor** | Batter who plays aggressive shots | Higher strike rate, more risk |
| **WK (Wicket Keeper)** | Specialist fielder behind the stumps (can bat) | Richa Ghosh for India |

### Bowling

| Term | Definition | Example |
|------|-----------|---------|
| **Bowler** | Player who throws the ball (like pitcher) | Jhulan Goswami, Renuka Singh |
| **Economy Rate** | Runs given per over | 6.2 economy = bowler gives 6.2 runs per over |
| **Wicket** | When a bowler gets a batter out | "Took 2 wickets" |
| **Pace Bowler** | Fast bowler (throwing 120+ km/h) | Jhulan Goswami |
| **Spin Bowler** | Bowler using wrist/finger rotation | Ravindra (leg-spin), Axar (off-spin) |
| **Yorker** | Ball at the base of the stumps | Hardest to hit |
| **Bouncer** | Short-pitched ball aiming at head | Intimidating delivery |
| **Dot Ball** | Over delivered by bowler, batter scores 0 | Pressure bowling |
| **Maiden Over** | Over where bowler gives 0 runs | Tight bowling |
| **Death Bowler** | Specialist in final overs (17-20) | Needs accuracy under pressure |

### Head-to-Head (Matchups)

| Term | Definition | Example |
|------|-----------|---------|
| **Matchup** | Historical record between one batter and one bowler | Smriti vs Megan Schutt |
| **Reliability** | How confident we are in a stat | "High" = 20+ balls of data, "Low" = <6 balls |
| **vs Pace** | Record against fast bowlers | Smriti's strike rate vs pace = 125 |
| **vs Spin** | Record against spin bowlers | Smriti's strike rate vs spin = 118 |
| **Recent Form** | Last 5 matches, last 6 months, last 12 months | How a player is performing lately |

### Tournament

| Term | Definition | Example |
|------|-----------|---------|
| **ICC** | International Cricket Council (governing body) | ICC Women's T20 World Cup 2026 |
| **World Cup** | Major international tournament | Highest level of cricket |
| **Group Stage** | Initial round where teams play multiple matches | India vs Australia, Pakistan, SA, BD, Netherlands |
| **Knockout** | Elimination matches (one loss = out) | Semi-finals, finals |
| **Venue** | Stadium where match is played | Lords, Edgbaston, Old Trafford |
| **Pitch** | Cricket field / playing surface | Can be "batting-friendly" or "bowler-friendly" |
| **Dew Factor** | Evening moisture affecting ball movement | Important in day-night matches |

---

## Player Positions & Roles

| Position | Role | Characteristics |
|----------|------|-----------------|
| **#1, #2 (Openers)** | Start the inning | Need quick starts, aggressive |
| **#3 (Captain)** | Middle order stabilizer | Balance: aggressive + defensive |
| **#4** | Flexible batter | Adapt to match situation |
| **#5-6** | Lower-middle order | Hitters, finishers |
| **#7-11** | Bowling roles | Mostly specialist bowlers |

---

## wt20-oracle Technical Terms

### System Components

| Term | What it is | Purpose |
|------|-----------|---------|
| **Agent** | Decision-making module | Each agent specializes in one job (Squad selection, Batting order, etc.) |
| **Node** | Type of agent | Technical term for individual decision component |
| **Graph** | Network of connected agents | Shows how agents talk to each other |
| **Pre-match Graph** | Network for pre-match decisions | All 5 agents working together |
| **Live Graph** | Network for live match decisions | Faster, smaller team of agents |
| **State** | Current information (score, players, etc.) | Data shared between agents |
| **Constraint** | A rule that must be followed | "Must have a wicket-keeper", "Can't have more than 3 overseas" |

### Optimization & Algorithms

| Term | What it means | Used for |
|------|--------------|----------|
| **MILP** | Mixed-Integer Linear Programming | Finding best combination of players (Squad selection, Batting order) |
| **Optimizer** | Algorithm that finds the best solution | Picks best XI, best order |
| **Objective Function** | What we're trying to maximize/minimize | Example: "Maximize total expected runs" |
| **Monte Carlo** | Simulate thousands of random scenarios | Win probability calculation |
| **Simulation** | Imagine how the rest of the match could go | 10,000 possible match outcomes |
| **Lookup Table** | Pre-calculated data stored for quick access | Matchup matrix (39,277 batter-bowler records) |

### Data Terms

| Term | Definition | Example |
|------|-----------|---------|
| **Data Point** | One piece of information | One match result |
| **Statistic** | Summary of many data points | Average, strike rate |
| **Form Window** | Recent performance over time | Last 5 matches, last 6 months |
| **Reliability** | How trustworthy a stat is | High (many data points), Low (few data points) |
| **Matchup Matrix** | Table of all batter-bowler combinations | 39,277 pairs with head-to-head records |
| **JSON** | Format for storing structured data | Player stats file format |
| **Schema** | Structure of data (what fields exist) | Player object has: name, role, stats, etc. |

### Scoring/Analysis

| Term | Definition | Example |
|------|-----------|---------|
| **Expected Value** | Average performance if matched up many times | Expected runs if Smriti bats vs Schutt 100 times |
| **Confidence Score** | How sure we are about a recommendation | 0-1, where 1 = very confident |
| **Confidence Interval** | Range of likely outcomes | Win probability 45-55% (not sure about exact value) |
| **Weighting** | Some data counts more than others | Recent matches weighted more heavily than old matches |
| **Modifier** | Adjustment factor based on conditions | If player is injured, multiply strike rate by 0.8 |
| **Form Rating** | Subjective assessment of current form | "Exceptional", "Good", "Average", "Poor" |

---

## Comparison Table: Cricket Formats

| Format | Overs | Balls | Duration | Pace | Example |
|--------|-------|-------|----------|------|---------|
| **Test** | Unlimited | 450+ | 5 days | Slow | Rare, most traditional |
| **ODI** | 50 | 300 | 3 hours | Medium | World Cups |
| **T20** | 20 | 120 | 2-2.5 hours | Fast | Most exciting, what wt20-oracle uses |
| **T10** | 10 | 60 | 1 hour | Very fast | Festival format |

wt20-oracle focuses on **T20** because it's:
- Fast-paced (short duration)
- Tactical (lot of decision points)
- High-scoring (exciting)

---

## Common Abbreviations

| Abbreviation | Stands for | Used in |
|--------------|-----------|---------|
| **SR** | Strike Rate | "Player's SR is 125" = scores 125 runs per 100 balls |
| **WK** | Wicket Keeper | "Richa Ghosh is our WK" |
| **RHB** | Right-Hand Batter | Bats with right hand (most common) |
| **LHB** | Left-Hand Batter | Bats with left hand |
| **MILP** | Mixed-Integer Linear Programming | Optimization math |
| **LLM** | Large Language Model | Claude AI (writes explanations) |
| **json** | JavaScript Object Notation | Data format for match state |
| **CLI** | Command-Line Interface | How you run wt20-oracle |
| **API** | Application Programming Interface | How components communicate |
| **MVP** | Minimum Viable Product | First complete version |

---

## Quick Reference: Metrics to Remember

| Metric | Good | Average | Poor |
|--------|------|---------|------|
| **Strike Rate** | 130+ | 110-130 | <110 |
| **Average** | 40+ | 25-40 | <25 |
| **Economy (Bowler)** | <6.5 | 6.5-7.5 | >7.5 |
| **Wickets per match** | 1.5+ | 0.5-1.5 | <0.5 |
| **Dot ball %** | 40%+ | 30-40% | <30% |

---

## Need More Help?

- **Learning the system:** See [Architecture Overview](Architecture.md)
- **Using commands:** See [CLI Usage Guide](CLI-USAGE.md)
- **Understanding data:** See [Data Schema](Data-Schema.md)
- **Getting started:** See [Getting Started](GETTING_STARTED.md)
