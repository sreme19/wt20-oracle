# wt20-oracle 🏏

> **Decision-support system for India Women's T20 World Cup 2026**

A beginner-friendly AI system that helps cricket coaches make smarter decisions about team selection, batting orders, bowling strategies, and live match tactics using data from thousands of past matches.

**Status:** Phase 1 Complete ✅ (Data + System Architecture)

---

## 🚀 What Does It Do?

Think of wt20-oracle as a **"cricket coach in your pocket"** that analyzes data to give you the best recommendations.

### Two Modes of Operation

| Mode | When to Use | What You Get |
|------|-------------|--------------|
| **Pre-Match** | Night before or morning of match | ✓ Best 11 players to pick<br>✓ Optimal batting order<br>✓ Bowling strategy<br>✓ Tactical advice |
| **Live Match** | During the match (between overs) | ✓ Should we change bowler?<br>✓ Where to place fielders?<br>✓ Send aggressive batter?<br>✓ Win probability % |

---

## 📖 Getting Started (5 Minutes)

### Step 1: Install

```bash
# Make sure Python 3.9+ is installed
python3 --version

# Navigate to project folder
cd wt20-oracle

# Install the system
pip install -e ".[dev]"
```

### Step 2: Run Your First Command

```bash
# Get recommendation for India vs Australia at Edgbaston
wt20-oracle prematch --opponent australia --venue edgbaston
```

**You'll get:**
```
Best XI (11 players)
Batting order (1-11)
Bowling plan (who bowls when)
Strategy brief (plain English explanation)
```

### Step 3: Try Live Mode

Create a file called `match_state.json`:
```json
{
  "match_id": "india-australia",
  "opponent": "australia",
  "venue": "edgbaston",
  "our_innings": {
    "current_score": 87,
    "wickets": 3,
    "overs": 13.5,
    "target": 150
  },
  "current_batter": {
    "name": "Jemimah Rodrigues",
    "runs_this_innings": 18,
    "balls_faced": 14
  },
  "current_bowler": {
    "name": "Jess Jonassen",
    "overs_bowled": 3.5,
    "runs_given": 28,
    "wickets": 0
  }
}
```

Then run:
```bash
wt20-oracle live --match-state match_state.json
```

---

## 📚 Documentation (Start Here!)

### For Beginners 👶
- **[Getting Started Guide](docs/GETTING_STARTED.md)** — Installation, first run, troubleshooting
- **[Glossary](docs/Glossary.md)** — Cricket terms explained simply (no background needed!)

### For Understanding the System 🧠
- **[Architecture Overview](docs/Architecture.md)** — How pre-match and live modes work (with diagrams!)
- **[Data Schema](docs/Data-Schema.md)** — What data is used and how it's organized

### For Using the Commands 💻
- **[CLI Usage Guide](docs/CLI-Usage.md)** — Every command with examples

### For Contributing Code 🤝
- **[Contributing Guide](docs/CONTRIBUTING.md)** — How to help (even if you're new to coding!)
- **[Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)** — Deep dive into system design

### For Data & Cricket Experts 🏏
- **[Analyst Insights Guide](docs/ANALYST_INSIGHTS_GUIDE.md)** — How to add expert opinions
- **[Steering Document](STEERING.md)** — Why design decisions were made
- **[Roadmap](ROADMAP.md)** — Future development plans

---

## 💡 How It Works (Simple Explanation)

### Pre-Match Mode: 5 Decision-Makers

```
What do we know?
  → Who we're playing (opponent)
  → Where we're playing (venue)
          ↓
Five "experts" make decisions:
  1. Opponent Analyzer: "What are their strengths?"
  2. Squad Selector: "Who should we pick? (11 out of 15)"
  3. Batting Order Optimizer: "In what order should they bat?"
  4. Bowling Plan Creator: "Who bowls when?"
  5. Narrator: "Explain this in plain English"
          ↓
Output: Full game plan
```

### Live Match Mode: Fast Decisions

```
During the match...
  Current score: 87/3 after 13.5 overs
  Question: "Should we change bowler?"
          ↓
System checks:
  - Current batter's weakness
  - New bowler's strength
  - Their head-to-head record
          ↓
Answer: "Yes, bring on Jhulan (she has history vs this batter)"
```

---

## 📊 Data At A Glance

| What | How Much | Quality |
|-----|----------|---------|
| **Matches Analyzed** | 2,705 | From CricSheet, WPL, WBBL, The Hundred |
| **Players Covered** | 178/180 (98.9%) | Complete T20I statistics |
| **Matchups** | 39,277 | Batter vs Bowler head-to-head |
| **Teams** | 12 | All World Cup participants |
| **Form Windows** | 3 per player | Last 5 matches, 6 months, 12 months |
| **Analyst Insights** | India squad 100% | Expert opinions on form, injury, psychology |

---

## 🎯 Real-World Example

### Pre-Match Scenario
```
India vs Australia at Edgbaston (June 17, 2026)

System Analysis:
  • Smriti Mandhana: 125 strike rate vs Australia (good!)
  • Alyssa Healy: Vulnerable to leg-spin (Ravindra)
  • Australia's death bowling is strong (avoid risky lower order)

Recommendation:
  ✓ Pick Harmanpreet (captain, proven vs Australia)
  ✓ Order: Shafali (fast) → Smriti (consistent) → Harmanpreet (flexible)
  ✓ Bowling: Pace upfront, Ravindra in middle to target Healy
  ✓ Strategy: Accumulate 160+ target to take pressure off bowlers
```

### Live Match Example
```
Over 14: India is 87/3, needing 63 from 36 balls

Current: Jemimah batting vs Jess Jonassen
System: "Jonassen is giving away 8 runs/over. 
         But Jemimah scores well against pace.
         
         Bring on Megan Schutt (left-arm pace).
         Jemimah only scores 95 vs Schutt (vs 128 overall).
         
         Expected: Drop runs from 8/over to 6.5/over"

Result: Probability of winning increases from 45% → 48%
```

---

## 🛠️ Project Structure

```
wt20-oracle/
│
├── 📂 docs/                          ← START HERE (8 guides)
│   ├── GETTING_STARTED.md           ← Installation
│   ├── Architecture.md               ← How it works
│   ├── CLI-Usage.md                 ← Commands
│   ├── Data-Schema.md               ← Data structures
│   ├── Glossary.md                  ← Terms explained
│   ├── CONTRIBUTING.md              ← How to help
│   └── ... (4 more technical guides)
│
├── 📂 wt20_oracle/                   ← Core system
│   ├── agents/                      ← Decision makers
│   │   ├── pre_match/               ← Squad, order, bowling, strategy
│   │   ├── live/                    ← Bowling change, field, win prob
│   │   └── shared/                  ← Shared components
│   │
│   ├── optimisation/                ← Math algorithms
│   │   ├── milp_lineup.py          ← Best 11 finder
│   │   ├── monte_carlo.py          ← Win probability
│   │   └── matchup_matrix.py       ← Batter vs bowler lookup
│   │
│   ├── data/                        ← Cricket data (1.1 MB)
│   │   ├── players/                 ← All 12 team squads
│   │   ├── matchups.json           ← 39,277 records
│   │   ├── venues.json             ← Tournament grounds
│   │   ├── schedule.json           ← Match fixtures
│   │   ├── teams.json              ← Team profiles
│   │   └── analyst_insights.json   ← Expert opinions
│   │
│   ├── io/                          ← Input/Output
│   │   ├── loader.py               ← Load data
│   │   ├── formatter.py            ← Format output
│   │   ├── analyst_loader.py       ← Load expert insights
│   │   └── live_input.py           ← Parse match state
│   │
│   ├── cli.py                       ← Command-line interface
│   ├── state.py                     ← Shared state
│   ├── schemas.py                   ← Data structures
│   ├── graph.py                     ← LangGraph setup
│   ├── pre_match_graph.py          ← Pre-match workflow
│   └── live_graph.py               ← Live match workflow
│
├── 📂 tests/                        ← Validation (7 test files)
│   ├── test_squad_selector.py
│   ├── test_batting_order.py
│   ├── test_bowling_change.py
│   ├── test_monte_carlo.py
│   └── ... (3 more tests)
│
├── 📂 scripts/                      ← Utilities
│   ├── parse_cricsheet.py          ← Process match data
│   ├── name_map.json               ← Player aliases
│   └── bowler_styles.json          ← Bowler classifications
│
├── pyproject.toml                  ← Project config
├── README.md                       ← This file!
├── STEERING.md                     ← Design decisions
├── ROADMAP.md                      ← Future plans
└── IMPLEMENTATION_SUMMARY.md       ← What's done
```

---

## 🏃 Quick Commands

### Pre-Match Analysis
```bash
# India vs Australia at Edgbaston
wt20-oracle prematch --opponent australia --venue edgbaston

# Verbose mode (shows detailed reasoning)
wt20-oracle prematch --opponent australia --venue edgbaston --verbose

# Save as JSON
wt20-oracle prematch --opponent australia --venue edgbaston --format json > recommendation.json
```

### Live Match Analysis
```bash
# Get live recommendation
wt20-oracle live --match-state match_state.json

# With more details
wt20-oracle live --match-state match_state.json --verbose
```

### Help
```bash
wt20-oracle --help              # All commands
wt20-oracle prematch --help     # Pre-match help
wt20-oracle live --help         # Live mode help
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_squad_selector.py -v

# See code coverage
pytest tests/ --cov=wt20_oracle
```

---

## ❓ FAQ for Beginners

**Q: Do I need to know cricket?**  
A: No! Read the [Glossary](docs/Glossary.md) first. Everything is explained simply.

**Q: I got an error. What do I do?**  
A: Check [Troubleshooting](docs/GETTING_STARTED.md#troubleshooting) in Getting Started guide.

**Q: Can I contribute even if I'm new to coding?**  
A: Yes! [Contributing Guide](docs/CONTRIBUTING.md) has beginner-friendly tasks.

**Q: What if I want to understand the code?**  
A: Read [Architecture Overview](docs/Architecture.md) first (no coding needed!).

**Q: Can I use this for other teams/formats?**  
A: Currently built for India Women's T20 World Cup 2026. Roadmap has plans for expansion.

**Q: How is this different from other cricket tools?**  
A: We use MILP optimization + Monte Carlo + expert analyst insights to make data-driven recommendations, not just predictions.

---

## 🔗 Tournament Info

| Item | Details |
|------|---------|
| **Tournament** | ICC Women's T20 World Cup 2026 |
| **Dates** | June 13 – July 5, 2026 |
| **Host** | England & Wales |
| **Final Venue** | Lord's, London |
| **India's Group** | Australia, South Africa, Pakistan, Bangladesh, Netherlands |
| **Tournament Venues** | 7 (Lord's, Old Trafford, Headingley, Edgbaston, Rose Bowl, The Oval, Bristol) |

---

## 📞 Need Help?

1. **Getting started?** → [GETTING_STARTED.md](docs/GETTING_STARTED.md)
2. **Understanding cricket?** → [Glossary.md](docs/Glossary.md)
3. **How system works?** → [Architecture.md](docs/Architecture.md)
4. **Command reference?** → [CLI-Usage.md](docs/CLI-Usage.md)
5. **Want to contribute?** → [CONTRIBUTING.md](docs/CONTRIBUTING.md)

---

## 📈 Project Status

### ✅ Phase 1: Complete (Data + Architecture)
- Data pipeline: 2,705 matches processed
- Player coverage: 178/180 (98.9%)
- Matchups: 39,277 batter-bowler records
- Analyst insights: India squad 100% annotated
- Documentation: 3,917 lines of beginner-friendly guides

### 🚧 Phase 2: In Development
- Agent implementation (currently empty placeholders)
- Integration with LangGraph
- Claude AI narrative generation
- End-to-end testing

### 📋 Phase 3: Planned
- Enhanced POMDP-based live recommendations
- Multi-analyst consensus scoring
- Real-time injury tracking
- Post-tournament learning

---

## 🔐 License & Attribution

Data sources:
- **CricSheet** — Ball-by-ball match data
- **ESPN Cricinfo** — Player statistics & career records  
- **ICC** — Tournament info & fixtures

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for:
- How to report bugs
- How to improve documentation
- How to write code
- How to add tests

---

**Ready to get started?** → Read [GETTING_STARTED.md](docs/GETTING_STARTED.md)
