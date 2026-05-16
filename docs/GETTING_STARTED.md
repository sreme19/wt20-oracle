# Getting Started with wt20-oracle

Welcome! This guide will help you install and run wt20-oracle for the first time.

## What is wt20-oracle?

**wt20-oracle** is a decision-support system for the **India Women's Cricket Team** at the **2026 ICC Women's T20 World Cup**.

It helps team captains and coaches make better decisions:
- **Before a match** — Select the best 11 players, decide the batting order, plan bowling strategy
- **During a match** — Suggest which bowler to bring on, where to place fielders, whether to try a risky batting move

Think of it as a "cricket coach in your pocket" that uses data from thousands of past matches to recommend the best next move.

---

## Installation (5 minutes)

### Step 1: Check what you have installed

First, make sure Python is installed on your computer:

```bash
python3 --version
```

You should see something like: `Python 3.10.12` (version 3.9 or higher is fine).

If you don't have Python, download it from [python.org](https://www.python.org).

### Step 2: Navigate to the project folder

```bash
cd /path/to/wt20-oracle
```

(Replace `/path/to/wt20-oracle` with wherever you saved the folder)

### Step 3: Install the project

```bash
pip install -e ".[dev]"
```

**What does this do?**
- `pip install` — Downloads and installs the project and all its "ingredients" (dependencies)
- `-e` — Means "editable" — if you change the code, Python will use the updated version immediately
- `.[dev]` — Install everything, including tools for developers (testing, linting, etc.)

This might take 1-2 minutes. You'll see lines of text scrolling by — that's normal.

### Step 4: Verify installation worked

```bash
wt20-oracle --help
```

You should see a list of commands like:
```
Usage: wt20-oracle [OPTIONS] COMMAND [ARGS]...

  Cricket decision-support system for India Women's T20 World Cup 2026

Commands:
  prematch  Get pre-match recommendations
  live      Get in-match recommendations
```

If you see this, **congratulations!** Installation is complete. 🎉

---

## Your First Run (2 minutes)

### Run a pre-match recommendation

Let's get a recommendation for India vs Australia at Edgbaston:

```bash
wt20-oracle prematch --opponent australia --venue edgbaston
```

This will output:
1. **Best XI** — The 11 players to play
2. **Batting order** — Who should bat 1st, 2nd, 3rd, etc.
3. **Bowling plan** — Which bowlers should play which roles (pace, spin, death bowler)
4. **Strategy brief** — Written explanation in plain English

### Run a live match recommendation

To get a recommendation during a match, you need to create a **match state file** (a JSON file with the current score).

See [Live Mode Guide](CLI-USAGE.md#live-mode) for details.

---

## Project Folder Structure (What's What)

```
wt20-oracle/
├── wt20_oracle/               ← Main code folder
│   ├── agents/                ← The "brains" that make decisions
│   │   ├── pre_match/         ← Pre-match decision makers
│   │   ├── live/              ← Live match decision makers
│   │   └── shared/            ← Helpers used by all agents
│   ├── data/                  ← Cricket data (teams, players, history)
│   ├── optimisation/          ← Math algorithms for optimization
│   └── io/                    ← Input/output helpers
│
├── tests/                     ← Test files (verify code works correctly)
├── docs/                      ← This documentation
├── scripts/                   ← Utility scripts (for data processing)
│
├── README.md                  ← Quick overview
├── STEERING.md                ← Why design decisions were made
└── ROADMAP.md                 ← Future plans
```

**You mainly interact with:**
- `wt20_oracle/` — The code that does the work
- `wt20_oracle/data/` — The cricket statistics data
- `docs/` — Guides like this one

---

## Quick Commands Reference

### Help
```bash
wt20-oracle --help                    # Show all commands
wt20-oracle prematch --help           # Help for pre-match mode
wt20-oracle live --help               # Help for live mode
```

### Pre-match analysis
```bash
# Get recommendation for India vs Australia at Edgbaston
wt20-oracle prematch --opponent australia --venue edgbaston

# Get recommendation for India vs Pakistan at Old Trafford
wt20-oracle prematch --opponent pakistan --venue "old trafford"
```

### Live match analysis
```bash
# Analyze a live match (you need a match_state.json file)
wt20-oracle live --match-state match_state.json
```

---

## What Each Agent Does (Simple Overview)

When you run `wt20-oracle prematch`, here's what happens step-by-step:

1. **Opponent Analyzer** — Looks at what Australia's team can do (their strengths, past form)
2. **Squad Selector** — Picks the best 11 players from India's full squad of 15
3. **Batting Order Optimizer** — Arranges them in the best order (who should bat 1st, 2nd, etc.)
4. **Bowling Plan Creator** — Decides who bowls when (which bowler is best for which phase)
5. **Strategy Writer** — Explains all of this in plain English so coaches can understand

All of these agents look at cricket data (past matches, player statistics, head-to-head records) to make their decisions.

---

## Glossary: Cricket Terms

Don't worry if you don't know cricket! Here are the basic terms:

| Term | What it means |
|------|---------------|
| **T20** | A 20-overs cricket match (super fast-paced) |
| **Batter** | Player trying to hit the ball and score runs |
| **Bowler** | Player throwing the ball (like a pitcher in baseball) |
| **Wicket** | A batter getting "out" (eliminated from the game) |
| **Over** | 6 balls thrown by one bowler |
| **Phase** | PowerPlay (overs 1-6), Middle (7-16), Death (17-20) |
| **Strike Rate** | How fast a batter scores (runs per 100 balls) |
| **Economy** | How slowly a bowler gives runs (runs per over) |
| **Matchup** | History between one batter and one bowler |

---

## Next Steps

1. **Read [Architecture Overview](Architecture.md)** to understand how the system works
2. **Check [CLI Usage](CLI-USAGE.md)** to learn all commands
3. **Look at [Data Guide](Data-Schema.md)** to see what data feeds the system

---

## Troubleshooting

### "wt20-oracle command not found"
```bash
# Try running with python:
python -m wt20_oracle.cli prematch --opponent australia --venue edgbaston
```

### "No module named anthropic"
```bash
# Re-install dependencies:
pip install -e ".[dev]"
```

### "FileNotFoundError: data/players/australia.json"
Your data files might be missing. Check that the `wt20_oracle/data/` folder exists and has JSON files in it.

### Still stuck?
Look at the test files in `tests/` to see examples of how the system works:
```bash
pytest tests/ -v
```

---

## Next: Learn How It Works

👉 **Read next:** [Architecture Overview](Architecture.md) for a deeper understanding of how decisions are made.
