# Contributing Guide: How to Help

Welcome! This guide explains how you can contribute to wt20-oracle, even if you're new to programming.

---

## Table of Contents

1. [Ways to Contribute](#ways-to-contribute)
2. [Setting Up for Development](#setting-up-for-development)
3. [Making Code Changes](#making-code-changes)
4. [Testing Your Changes](#testing-your-changes)
5. [Submitting Changes](#submitting-changes)
6. [Common Tasks](#common-tasks)

---

## Ways to Contribute

You don't need to be an expert programmer to help! Here are different ways to contribute:

### 1. Report Bugs 🐛

**What:** Tell us when something doesn't work.

**How:**
```bash
# When you find a bug:
1. Note what you were doing
2. Write down the error message
3. Tell us what you expected to happen
4. Open a GitHub issue with these details
```

**Example:**
```
Title: "prematch command fails when opponent name has space"

Description:
When I ran: wt20-oracle prematch --opponent "south africa" --venue lords
I got error: Unknown opponent: south africa

Expected: Should recognize "south africa" as valid opponent
```

### 2. Improve Documentation 📚

**What:** Fix typos, add examples, clarify confusing parts.

**How:**
```bash
# Find a doc that's confusing
1. Read the file in docs/ folder
2. Note what's unclear
3. Write a clearer version
4. Send us the improved version
```

**No coding needed!** Just improve clarity and examples.

### 3. Add Player Data 📊

**What:** Update player statistics when new matches happen.

**How:**
```bash
# After India plays a match:
1. Find the player's new stats
2. Update wt20_oracle/data/players/india.json
3. Recalculate form_windows using scripts/parse_cricsheet.py
4. Submit the updated file
```

**Example:**
```json
// Update Smriti's stats after she scores 45 runs
"last_5_matches": {
  "matches": 5,
  "runs": 178 → 223,  // Add the 45
  "balls": 142 → 157, // Add the runs she faced
  "strike_rate": 125.4 → 142.0
}
```

### 4. Write Tests ✅

**What:** Create tests to verify code works correctly.

**How:**
```bash
# Look at existing tests in tests/ folder
# Write similar tests for new features

# Example test:
def test_squad_selector_with_injury():
    """Verify squad selector skips injured players"""
    # Set up: Create a scenario with an injured player
    # Run: Call squad selector
    # Check: Injured player not in selected XI
    pass
```

### 5. Code Improvements 💻

**What:** Add new features or improve existing code.

**Who:** For programmers with Python experience.

---

## Setting Up for Development

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd wt20-oracle
```

### Step 2: Create a development branch

```bash
git checkout -b my-feature-name
```

**Naming convention:**
```
feature/squad-selector-improvement
bugfix/live-mode-crash
docs/add-glossary
data/update-player-stats
```

### Step 3: Install in development mode

```bash
pip install -e ".[dev]"
```

This installs the project + development tools (testing, linting, formatting).

### Step 4: Verify setup works

```bash
# Try a simple command
wt20-oracle prematch --opponent australia --venue edgbaston

# Run tests
pytest tests/ -v
```

---

## Making Code Changes

### Where to Make Changes

**Project structure:**
```
wt20_oracle/
├── agents/
│   ├── pre_match/      ← Pre-match decisions
│   ├── live/           ← Live match decisions
│   └── shared/         ← Shared components
├── optimisation/       ← Math algorithms
├── io/                 ← Input/output
├── data/               ← Cricket data
├── schemas.py          ← Data structures
├── state.py            ← Shared state
├── cli.py              ← Command-line interface
└── graph.py / live_graph.py / pre_match_graph.py  ← Agent networks
```

### Code Style (Keep it Simple!)

**Python Code Guidelines:**

1. **Use clear variable names**
   ```python
   # ❌ Don't do this:
   x = p * sr / 100

   # ✅ Do this:
   expected_runs = balls_faced * strike_rate / 100
   ```

2. **Add comments for "why", not "what"**
   ```python
   # ❌ Don't do this:
   runs = runs + 4  # Add 4 to runs

   # ✅ Do this:
   runs = runs + 4  # Boundary hit, add 4 runs (vs 6 boundary)
   ```

3. **Keep functions small**
   ```python
   # If a function does too much, split it:
   def select_squad():
       removed_injured = remove_injured_players()
       ranked = rank_by_form(removed_injured)
       selected = pick_top_11(ranked)
       return selected
   ```

4. **Use type hints (Python 3.9+)**
   ```python
   def calculate_expected_runs(sr: float, balls: int) -> float:
       """Calculate expected runs based on strike rate."""
       return sr * balls / 100
   ```

### Example: Adding a New Feature

Let's say you want to add a "player injury status" check.

**Step 1: Understand the data**
```python
# In wt20_oracle/data/players/india.json:
{
  "injury_status": "fit",  # Add this field
  "injury_details": {      # Optional details
    "type": "shoulder",
    "recovery_date": "2026-06-20"
  }
}
```

**Step 2: Create helper function**
```python
# File: wt20_oracle/io/validator.py

def is_player_fit(player: dict) -> bool:
    """Check if player is fit to play."""
    injury_status = player.get("injury_status", "fit")
    return injury_status == "fit"

def get_fit_players(team_squad: list[dict]) -> list[dict]:
    """Filter squad to include only fit players."""
    return [p for p in team_squad if is_player_fit(p)]
```

**Step 3: Use in agent**
```python
# File: wt20_oracle/agents/pre_match/squad_selector_node.py

def select_squad(full_squad):
    # Remove injured players first
    fit_squad = get_fit_players(full_squad)
    
    # Then select best 11 from fit squad
    selected_11 = pick_best_11(fit_squad)
    
    return selected_11
```

---

## Testing Your Changes

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_squad_selector.py -v

# Run with coverage (see which code is tested)
pytest tests/ --cov=wt20_oracle

# Run only failing tests (for debugging)
pytest tests/ -x  # stops at first failure
```

### Writing Tests

**Example test structure:**
```python
# File: tests/test_squad_selector.py

import pytest
from wt20_oracle.agents.pre_match.squad_selector_node import select_squad

def test_squad_selector_basic():
    """Test that squad selector returns 11 players."""
    # Setup: Create test data
    full_squad = load_test_players()
    
    # Execute: Call the function
    selected = select_squad(full_squad)
    
    # Verify: Check results
    assert len(selected) == 11
    assert all(p["role"] in ["batter", "bowler", "all-rounder"] for p in selected)

def test_squad_selector_includes_captain():
    """Test that captain is always selected."""
    full_squad = load_test_players()
    selected = select_squad(full_squad)
    
    captain_selected = any(p["name"] == "Harmanpreet Kaur" for p in selected)
    assert captain_selected, "Captain should always be selected"

def test_squad_selector_respects_constraints():
    """Test that squad respects cricket constraints."""
    selected = select_squad(load_test_players())
    
    # Must have a wicket keeper
    has_wk = any(p["role"] == "wk" for p in selected)
    assert has_wk, "Squad must include a wicket-keeper"
    
    # Must have at least 5 bowlers
    bowlers = [p for p in selected if p["role"] in ["bowler", "all-rounder"]]
    assert len(bowlers) >= 5, "Squad must have at least 5 bowlers"
```

### Manual Testing

**Before submitting, test manually:**

```bash
# Test pre-match against different opponents
wt20-oracle prematch --opponent australia --venue edgbaston
wt20-oracle prematch --opponent pakistan --venue lords

# Test with verbose mode
wt20-oracle prematch --opponent australia --venue edgbaston --verbose

# Test output formats
wt20-oracle prematch --opponent australia --venue edgbaston --format json
```

---

## Submitting Changes

### Step 1: Format Your Code

```bash
# Auto-format code (makes it look nice)
ruff format wt20_oracle/

# Check for style issues
ruff check wt20_oracle/
```

### Step 2: Run Tests

```bash
# Make sure all tests pass
pytest tests/ -v

# Check test coverage
pytest tests/ --cov=wt20_oracle
```

### Step 3: Write a Clear Commit Message

```bash
git add .
git commit -m "Add injury status check to squad selector"
```

**Good commit messages:**
```
✓ "Add injury status check to squad selector"
✓ "Fix bug where captain wasn't always selected"
✓ "Improve documentation for CLI usage"
✓ "Update player stats for India vs Australia match"

✗ "Fix stuff"
✗ "Changes"
✗ "Update"
```

### Step 4: Push and Create Pull Request

```bash
# Push to your branch
git push origin my-feature-name

# Go to GitHub and create a Pull Request
# Describe what you changed and why
```

**In the Pull Request description, include:**
```
## What changed?
- Added injury status validation
- Injured players no longer selected in XI

## Why?
- Previous system ignored injuries
- Coaches need to know who's unavailable

## Testing
- ✓ All existing tests pass
- ✓ Added 3 new tests for injury validation
- ✓ Manually tested: injured player filtered out

## Screenshots/Examples
[Show example output if applicable]
```

---

## Common Tasks

### Task 1: Update Player Statistics After a Match

**When:** After India plays a match and new stats are available

**Steps:**

1. Find the player in `wt20_oracle/data/players/india.json`
2. Update their stats:
   ```json
   {
     "t20i_stats": {
       "batting": {
         "matches": 88,          // Increment by 1
         "runs": 2,389,          // Add runs scored
         "strike_rate": 123.5    // Recalculate
       }
     }
   }
   ```

3. Recalculate form windows:
   ```bash
   python scripts/parse_cricsheet.py --update-form
   ```

4. Verify changes look correct:
   ```bash
   python -c "import json; print(json.dumps(json.load(open('wt20_oracle/data/players/india.json'))['smriti_mandhana'], indent=2))"
   ```

### Task 2: Add New Analyst Insight

**When:** You learn new info about a player (form, injury, psychology)

**File:** `wt20_oracle/data/analyst_insights.json`

**Structure:**
```json
{
  "india": {
    "smriti_mandhana": {
      "form_rating": "exceptional",
      "form_confidence": 0.95,
      "form_notes": "Scored 45 vs Australia, 38 vs Pakistan. Form peak.",
      "strength s": ["Opening", "Pace hitting", "Left-handed advantage"],
      "concerns": null,
      "injury_status": "fit",
      "vs_opponent": {
        "australia": {
          "notes": "Historically good. 120+ SR vs Healy.",
          "recommendation": "Back her to dominate powerplay"
        }
      },
      "psychological_state": "confident",
      "last_updated": "2026-05-16"
    }
  }
}
```

**How to update:**
```python
import json

# Load insights
with open("wt20_oracle/data/analyst_insights.json") as f:
    insights = json.load(f)

# Update a player
insights["india"]["smriti_mandhana"]["form_rating"] = "exceptional"
insights["india"]["smriti_mandhana"]["last_updated"] = "2026-05-16"

# Save
with open("wt20_oracle/data/analyst_insights.json", "w") as f:
    json.dump(insights, f, indent=2)
```

### Task 3: Fix a Bug

**Example bug:** "Live mode crashes when bowler has 0 wickets"

**Steps:**

1. **Reproduce the bug**
   ```bash
   wt20-oracle live --match-state state_with_zero_wicket_bowler.json
   ```

2. **Find the error in code**
   ```python
   # File: wt20_oracle/agents/live/bowling_change_node.py
   economy = runs_given / wickets  # ❌ Crashes if wickets = 0
   ```

3. **Fix it**
   ```python
   # Safe calculation (avoid division by zero)
   if wickets > 0:
       economy = runs_given / wickets
   else:
       economy = runs_given  # Use runs_given if no wickets yet
   ```

4. **Write a test**
   ```python
   def test_bowling_change_with_zero_wickets():
       """Ensure no crash when bowler has 0 wickets."""
       bowler = {"wickets": 0, "runs_given": 25}
       result = calculate_economy(bowler)
       assert result == 25
   ```

5. **Test the fix**
   ```bash
   pytest tests/test_bowling_change.py::test_bowling_change_with_zero_wickets -v
   wt20-oracle live --match-state state_with_zero_wicket_bowler.json  # Should work now
   ```

---

## Getting Help

**Questions?**

1. Read the relevant documentation:
   - [Architecture Overview](Architecture.md) — How the system works
   - [Data Schema](Data-Schema.md) — What data exists
   - [Glossary](Glossary.md) — Cricket & tech terms

2. Look at existing code:
   - `wt20_oracle/agents/` — See how agents are written
   - `tests/` — See how tests are written

3. Ask in code comments:
   - Add a GitHub issue with your question
   - Be specific about what's confusing

---

## Code Review Checklist

Before submitting, check:

- [ ] Code is formatted (`ruff format`)
- [ ] No style issues (`ruff check`)
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] New tests written for new features
- [ ] Variable names are clear
- [ ] No print statements left in (use logging instead)
- [ ] Comments explain "why", not "what"
- [ ] Commit message is clear
- [ ] PR description explains changes

---

## Learning Resources

### Python
- [Real Python Tutorials](https://realpython.com) — Great for beginners
- [Python Official Docs](https://docs.python.org/3/)

### Testing
- [Pytest Documentation](https://docs.pytest.org/)
- [Real Python: Pytest](https://realpython.com/pytest-python-testing/)

### Cricket Knowledge
- [Glossary](Glossary.md) — Cricket terms explained simply

### Git & GitHub
- [Git Handbook](https://guides.github.com/introduction/git-handbook/)
- [GitHub Guides](https://guides.github.com/)

---

## Summary

**Contributing steps:**
1. Pick a task (bug, docs, feature, test, data)
2. Create a branch: `git checkout -b my-feature`
3. Make changes
4. Test: `pytest tests/ -v`
5. Format: `ruff format wt20_oracle/`
6. Commit: `git commit -m "Clear message"`
7. Push: `git push origin my-feature`
8. Create Pull Request on GitHub
9. Answer review questions
10. Merge when approved!

Thank you for contributing! 🙏

---

## FAQ

**Q: Do I need to know cricket to contribute?**  
A: No! We have [Glossary](Glossary.md) and [Data Schema](Data-Schema.md) to help. You can contribute to code, tests, or documentation without cricket knowledge.

**Q: What if I break something?**  
A: That's okay! Your changes go through review before merging. We'll help fix issues.

**Q: How much time does this take?**  
A: A small bug fix or doc improvement: 30 minutes  
A new feature: 2-4 hours  
You decide!

**Q: Can I contribute if I'm new to programming?**  
A: Absolutely! Start with documentation improvements or data updates. Great way to learn!
