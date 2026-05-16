# Quick Start (5 Minutes)

Get wt20-oracle running in 5 minutes, even if you've never used it before.

---

## Step 1: Check Python (30 seconds)

Open your terminal/command prompt and run:

```bash
python3 --version
```

You should see something like: `Python 3.10.12`

**Don't have Python?**
1. Go to [python.org](https://www.python.org)
2. Download Python 3.9 or higher
3. Install it
4. Run the command again

---

## Step 2: Navigate to Project (15 seconds)

```bash
# Change to the wt20-oracle folder
# (replace /path/to with your actual path)
cd /path/to/wt20-oracle

# Verify you're in the right place
ls README.md
# Should show: README.md
```

---

## Step 3: Install (2 minutes)

```bash
pip install -e ".[dev]"
```

**What's happening?**
- `pip install` = Download and install the system
- `-e` = "Editable" mode (changes show up immediately)
- `.[dev]` = Install everything including testing tools

You'll see lots of text scrolling. That's normal. Wait for it to finish.

---

## Step 4: Verify Installation (30 seconds)

```bash
wt20-oracle --help
```

You should see:
```
Usage: wt20-oracle [OPTIONS] COMMAND [ARGS]...

Cricket decision-support system for India Women's T20 World Cup 2026

Commands:
  prematch  Get pre-match recommendations
  live      Get in-match recommendations
```

✅ **Installation complete!**

---

## Step 5: Run Your First Command (1 minute)

Get a pre-match recommendation:

```bash
wt20-oracle prematch --opponent australia --venue edgbaston
```

**You'll see:**
```
═══════════════════════════════════════════════════════════════
              INDIA VS AUSTRALIA AT EDGBASTON
                    Pre-Match Recommendation
═══════════════════════════════════════════════════════════════

SQUAD SELECTION (Best 11)
──────────────────────────
 1. Shafali Verma      (Opener, bat)
 2. Smriti Mandhana    (Opener, bat)
 3. Harmanpreet Kaur   (Middle, bat - Captain)
[... and 8 more players ...]

BATTING ORDER (Optimized)
──────────────────────────
#1 → Shafali Verma (fast aggressive)
#2 → Smriti Mandhana (consistent)
[... rest of order ...]

BOWLING PLAN
──────────────────────────
PowerPlay: Renuka Singh (pace), Jhulan Goswami (pace)
Middle: Ravindra (spin), Axar Patel (spin)
Death: Poonam Yadav (spin), Jhulan Goswami (pace)

STRATEGY BRIEF
──────────────────────────
Australia's Strengths:
  • Powerful opening pair
  • Death bowling expertise

Australia's Weaknesses:
  • Struggle vs leg-spin

[... explanation ...]
```

🎉 **You just got a cricket recommendation using AI!**

---

## What You Just Did

1. ✅ Installed the system
2. ✅ Ran a pre-match analysis
3. ✅ Got recommendations for:
   - Best 11 players to pick
   - Optimal batting order
   - Bowling strategy
   - Tactical advice

---

## Next Steps

### Want to understand what just happened?
→ Read [How It Works](How-It-Works.md) (5 min read)

### Want to learn cricket terms?
→ Check [Cricket Glossary](Cricket-Glossary.md)

### Want to try live mode?
→ Go to [Live Mode Guide](Live-Mode.md)

### Want to explore more commands?
→ See [Commands Reference](Commands.md)

### Want to understand the system?
→ Read [Architecture Explained](Architecture-Explained.md)

---

## Quick Command Reference

### Pre-Match Analysis
```bash
# Basic
wt20-oracle prematch --opponent australia --venue edgbaston

# With detailed explanation
wt20-oracle prematch --opponent australia --venue edgbaston --verbose

# Save as JSON file
wt20-oracle prematch --opponent australia --venue edgbaston --format json > rec.json

# Get help
wt20-oracle prematch --help
```

### Live Match Analysis
```bash
# Live recommendation
wt20-oracle live --match-state match_state.json

# Get help
wt20-oracle live --help
```

### General Help
```bash
wt20-oracle --help
```

---

## Troubleshooting

### "python3: command not found"
```bash
# Try:
python --version

# If that works, use 'python' instead of 'python3'
# In all commands above
```

### "pip: command not found"
```bash
# Try:
python3 -m pip install -e ".[dev]"

# Or if using python:
python -m pip install -e ".[dev]"
```

### "wt20-oracle: command not found"
```bash
# Try running with python:
python -m wt20_oracle.cli prematch --opponent australia --venue edgbaston
```

### "FileNotFoundError: data/players/australia.json"
Your data files might be missing. Try:
```bash
# Check if data folder exists
ls wt20_oracle/data/

# If it exists but is empty, reinstall:
pip install -e ".[dev]" --force-reinstall
```

### Still stuck?
1. Check [Installation Guide](Installation.md)
2. Look at [FAQ](FAQ.md)
3. Check error message in [Commands Reference](Commands.md)

---

## What Opponents Can You Try?

```bash
australia       south_africa    pakistan
bangladesh      netherlands     england
west_indies     ireland         new_zealand
afghanistan     scotland        zimbabwe
```

## What Venues Can You Try?

```bash
lords           old_trafford    headingley
edgbaston       rose_bowl       the_oval
bristol
```

### Try more examples:

```bash
# India vs Pakistan at Old Trafford
wt20-oracle prematch --opponent pakistan --venue old_trafford

# India vs South Africa at Lords
wt20-oracle prematch --opponent south_africa --venue lords

# India vs Bangladesh at The Oval
wt20-oracle prematch --opponent bangladesh --venue the_oval
```

---

## Summary

You just:
1. ✅ Installed wt20-oracle (2 minutes)
2. ✅ Verified it works (30 seconds)
3. ✅ Got your first recommendation (1 minute)
4. ✅ Learned 3 basic commands (1 minute)

**Total time: ~5 minutes**

---

## Ready for More?

- **Understand what you did:** [How It Works](How-It-Works.md)
- **Learn cricket terms:** [Cricket Glossary](Cricket-Glossary.md)
- **Try live mode:** [Live Mode](Live-Mode.md)
- **All commands:** [Commands Reference](Commands.md)
- **Project overview:** [Home](Home.md)

---

🎉 **Welcome to wt20-oracle!**

