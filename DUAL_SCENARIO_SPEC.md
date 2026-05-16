# Technical Specification: Dual-Scenario Output

## Overview
Currently, the pre-match CLI outputs predictions for a single scenario: whatever toss outcome is provided. Users must re-run the pipeline with different toss parameters to see alternative scenarios.

This spec proposes **always outputting both scenarios** (batting first + bowling first) in a single run, allowing stakeholders to see the expected outcome regardless of the toss outcome.

---

## Current State

### Architecture
- **State flow**: Single `PreMatchState` (TypedDict) passes through the pipeline
- **Scenario node**: `scenario_node()` in `pre_match_graph.py` determines one scenario based on toss
- **Output**: `_print_text()` in `cli.py` prints strategy brief for the single scenario
- **Data saved**: `_save_prediction()` saves one prediction JSON per match

### Limitations
1. Only one scenario is computed per run
2. To see both outcomes, users must run the CLI twice with different `--toss-decision` flags
3. The prediction JSON stored contains only one scenario's data
4. CLI output doesn't explicitly show what was held constant

---

## Desired State

### User-Facing Behavior
```
SITUATION 1: If AUSTRALIA bats first
├─ Target: ~143 runs
├─ Win Probability: 61%
├─ Top 4 Batters: [list]
├─ Bowling Plan: [summary]
└─ Strategy: Aggressive powerplay...

SITUATION 2: If AUSTRALIA bowls first (chasing)
├─ Target: ~145 runs (chase estimate with penalty)
├─ Win Probability: 58%
├─ Top 4 Batters: [likely chase lineup]
├─ Bowling Plan: [summary]
└─ Strategy: Build partnership, accelerate death overs...
```

### Data Storage
```
matches/{match_id}/
├─ metadata.json
├─ prediction/
│  ├─ prediction.json          # New: contains both scenarios
│  ├─ batting_first.json       # (Optional: granular storage)
│  └─ bowling_first.json       # (Optional: granular storage)
└─ actual/
```

---

## Implementation Approach

### 1. **State Architecture**

#### Option A: Run pipeline twice, merge results (Recommended)
- Generate two complete `PreMatchState` objects: one for each scenario
- Merge into a new `DualScenarioState` container
- Store references to both in top-level state for output

**Pros**: Minimal changes to existing nodes; pipeline logic untouched  
**Cons**: 2x computation (minor, given typical run time ~5-10s)

#### Option B: Modify state to contain dual results
- Extend `PreMatchState` with `batting_first_scenario: Dict` and `chasing_scenario: Dict`
- Modify each node to populate both scenario results simultaneously
- Complex: requires rewriting squad selector, batting order, bowling plan, prediction nodes

**Pros**: Single pipeline run  
**Cons**: Invasive, high refactor risk

**→ Recommended: Option A**

---

### 2. **New Data Structures**

#### `ScenarioResult` (new TypedDict)
```python
class ScenarioResult(TypedDict, total=False):
    scenario: str                           # "batting_first" or "chasing"
    pitch_difficulty: str
    chase_penalty: int
    selected_xi: List[str]
    batting_order: List[str]
    batting_reasoning: Dict[str, str]
    bowling_plan: List[Dict[str, Any]]
    base_runs_estimate: float
    adjusted_runs_estimate: float
    runs_lower: float
    runs_upper: float
    win_probability: float
    key_matchups: List[Dict[str, Any]]
    tactical_flags: List[str]
    strategy_brief: str
```

#### `DualScenarioState` (new)
```python
class DualScenarioState(TypedDict, total=False):
    # Match identifiers
    team_id: str
    opponent_id: str
    venue_id: str
    match_date: str
    
    # Shared context (computed once, reused)
    our_squad: List[Dict[str, Any]]
    opponent_squad: List[Dict[str, Any]]
    venue_data: Dict[str, Any]
    team_data: Dict[str, Any]
    opponent_data: Dict[str, Any]
    analyst_insights: Dict[str, Any]
    
    # Scenario results
    batting_first: ScenarioResult
    chasing: ScenarioResult
    
    # Validation/errors
    errors: List[str]
    warnings: List[str]
```

---

### 3. **Pipeline Changes**

#### New function: `run_dual_scenario_pipeline()`
**Location**: `wt20_oracle/pre_match_graph.py`

```python
def run_dual_scenario_pipeline(
    team_id: str,
    opponent_id: str,
    venue_id: str,
    match_date: str,
    toss_winner: Optional[str] = None,
    toss_decision: Optional[str] = None,
) -> DualScenarioState:
    """
    Run pre-match pipeline for both scenarios: batting first + chasing.
    
    Returns:
        DualScenarioState with both scenario results populated.
    
    Note:
        - Ignores toss_decision parameter (computes both regardless)
        - toss_winner is used only to classify opponent if provided
        - Shared context (squads, venue) is loaded once
    """
    # Load shared context once
    shared_context = {
        "our_squad": ...,
        "opponent_squad": ...,
        "venue_data": ...,
        ...
    }
    
    # Scenario 1: Batting First
    batting_first_state = PreMatchState(
        team_id=team_id,
        opponent_id=opponent_id,
        toss_winner=team_id,        # Force our team to bat first
        toss_decision="bat_first",
        **shared_context,
    )
    batting_first_result = run_pre_match_pipeline(batting_first_state)
    
    # Scenario 2: Chasing (Bowling First)
    chasing_state = PreMatchState(
        team_id=team_id,
        opponent_id=opponent_id,
        toss_winner=opponent_id,    # Force opponent to bat first
        toss_decision="bat_first",  # Opponent bats first → we chase
        **shared_context,
    )
    chasing_result = run_pre_match_pipeline(chasing_state)
    
    # Merge results
    return DualScenarioState(
        team_id=team_id,
        opponent_id=opponent_id,
        venue_id=venue_id,
        match_date=match_date,
        **shared_context,
        batting_first=_extract_scenario_result(batting_first_result),
        chasing=_extract_scenario_result(chasing_result),
        errors=[...],
        warnings=[...],
    )
```

#### Helper: `_extract_scenario_result()`
Converts a `PreMatchState` to a `ScenarioResult` by copying relevant fields.

---

### 4. **CLI Changes**

#### Modify `run_prematch()` in `cli.py`
```python
def run_prematch(args):
    # ... venue resolution logic unchanged ...
    
    # Use new dual-scenario pipeline instead of single-scenario
    state = run_dual_scenario_pipeline(
        team_id=args.team,
        opponent_id=args.opponent,
        venue_id=venue_to_use,
        match_date=args.date,
        # Note: ignore toss_winner, toss_decision
        #       pipeline always computes both scenarios
    )
    
    # ... error handling, save, format as before ...
```

#### New function: `_print_dual_scenario_text()`
**Location**: `cli.py`

```python
def _print_dual_scenario_text(state: DualScenarioState, verbose=False):
    """
    Print strategy brief for both scenarios side-by-side or stacked.
    
    Output format:
        SITUATION 1: If {team} bats first
        ══════════════════════════════════
        [Batting First Strategy Brief]
        
        SITUATION 2: If {team} bowls first (chasing)
        ════════════════════════════════════════════
        [Chasing Strategy Brief]
    """
    team = state.get("team_id").upper()
    opponent = state.get("opponent_id").upper()
    
    bf = state.get("batting_first", {})
    chase = state.get("chasing", {})
    
    print(f"\n{'═' * 70}")
    print(f"SITUATION 1: If {team} bats first")
    print(f"{'═' * 70}")
    print(bf.get("strategy_brief", "(No strategy generated)"))
    
    print(f"\n{'═' * 70}")
    print(f"SITUATION 2: If {team} bowls first (chasing)")
    print(f"{'═' * 70}")
    print(chase.get("strategy_brief", "(No strategy generated)"))
    
    if verbose:
        # Print detailed breakdowns for both scenarios
        _print_scenario_detail(bf, label="BATTING FIRST")
        _print_scenario_detail(chase, label="CHASING")
```

---

### 5. **Data Persistence Changes**

#### Modify `_save_prediction()` in `cli.py`
```python
def _save_prediction(state: DualScenarioState, ...) -> str:
    """Save both scenarios to prediction.json"""
    
    result = {
        "team": state.get("team_id"),
        "opponent": state.get("opponent_id"),
        "venue": state.get("venue_id"),
        "date": state.get("match_date"),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        
        # Scenario data
        "scenarios": {
            "batting_first": {
                "win_probability": bf.get("win_probability"),
                "runs_estimate": {...},
                "strategy_brief": bf.get("strategy_brief"),
                "batting_order": bf.get("batting_order"),
                "bowling_plan": bf.get("bowling_plan"),
                "key_matchups": bf.get("key_matchups"),
                "tactical_flags": bf.get("tactical_flags"),
            },
            "chasing": {
                "win_probability": chase.get("win_probability"),
                "runs_estimate": {...},
                "strategy_brief": chase.get("strategy_brief"),
                "batting_order": chase.get("batting_order"),
                "bowling_plan": chase.get("bowling_plan"),
                "key_matchups": chase.get("key_matchups"),
                "tactical_flags": chase.get("tactical_flags"),
            }
        },
        "errors": state.get("errors", []),
        "warnings": state.get("warnings", []),
    }
    
    # Write to prediction.json
    with open(match_dir / "prediction" / "prediction.json", "w") as f:
        json.dump(result, f, indent=2)
```

**JSON structure example**:
```json
{
  "team": "australia",
  "opponent": "south_africa",
  "venue": "old_trafford",
  "date": "2026-06-13",
  "generated_at": "2026-05-16T14:30:00Z",
  "scenarios": {
    "batting_first": {
      "win_probability": 0.61,
      "runs_estimate": {
        "base": 142,
        "adjusted": 142,
        "lower": 130,
        "upper": 155
      },
      "strategy_brief": "SITUATION 1: Set par total...",
      ...
    },
    "chasing": {
      "win_probability": 0.58,
      "runs_estimate": {
        "base": 145,
        "adjusted": 138,
        "lower": 125,
        "upper": 150
      },
      "strategy_brief": "SITUATION 2: Build partnership...",
      ...
    }
  }
}
```

---

### 6. **Output Format Options**

#### Option A: Stacked (Recommended)
```
SITUATION 1: If AUSTRALIA bats first
════════════════════════════════════
TARGET: Set a score of ~143 runs
WIN PROBABILITY: 61% (FAIR)
[Full strategy brief]

SITUATION 2: If AUSTRALIA bowls first (chasing)
════════════════════════════════════════════════
TARGET: Chase target of ~145 runs
WIN PROBABILITY: 58% (FAIR)
[Full strategy brief]
```

#### Option B: Comparison table
```
╔════════════════════════╦═════════════════╦═════════════════╗
║ Metric                 ║ Batting First   ║ Bowling First   ║
╠════════════════════════╬═════════════════╬═════════════════╣
║ Win Probability        ║ 61%             ║ 58%             ║
║ Expected Runs          ║ 142 (130-155)   ║ 138 (125-150)   ║
║ Top Scorer             ║ Mooney (SR 124) ║ Litchfield      ║
║ Primary Bowler         ║ Sutherland      ║ Wareham         ║
╚════════════════════════╩═════════════════╩═════════════════╝
```

**→ Recommended: Option A** (easier to implement, clearer for stakeholders)

---

## Implementation Plan

### Phase 1: Core Pipeline
- [ ] Create `ScenarioResult` and `DualScenarioState` TypedDicts in `state.py`
- [ ] Write `run_dual_scenario_pipeline()` in `pre_match_graph.py`
- [ ] Write `_extract_scenario_result()` helper
- [ ] Add imports to `cli.py`

### Phase 2: Output
- [ ] Update `_print_dual_scenario_text()` in `cli.py`
- [ ] Update `_print_json()` to output dual scenarios
- [ ] Wire up in `run_prematch()` to call dual pipeline instead of single

### Phase 3: Persistence
- [ ] Update `_save_prediction()` to save both scenarios
- [ ] Update `PREDICTIONS_INDEX.json` schema (if used)

### Phase 4: Testing
- [ ] Test with existing matches (e.g., `aus_sou_old_20260613`)
- [ ] Verify scenario predictions are independent (no cross-contamination)
- [ ] Verify win probabilities are scenario-appropriate
- [ ] Benchmark runtime (expect ~2x vs. single scenario)

### Phase 5: CLI UX
- [ ] Update help text (scenarios always computed)
- [ ] Deprecate `--toss-decision` (or ignore it)
- [ ] Update error messages if applicable

---

## Backward Compatibility

- **Existing matches**: Prediction JSONs currently contain single scenario. New schema stores both.
- **Recommendation**: Don't migrate old predictions; regenerate with new pipeline if needed.
- **JSON format change**: Non-breaking if consumers check for `scenarios.batting_first` and `scenarios.chasing` keys.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| 2x runtime | Acceptable (typical run ~5–10s, dual is ~10–20s). Cache shared context. |
| Cross-scenario state leakage | Create fresh `PreMatchState` for each scenario; no shared mutable state. |
| Identical predictions (bug) | Unit test: verify win probabilities differ when scenario differs. |
| JSON schema breaking | Wrap in versioned container: `{ "version": 2, "scenarios": {...} }` |

---

## Success Criteria

1. ✓ CLI outputs both scenarios in single run
2. ✓ Win probabilities differ appropriately (batting first > chasing for most teams)
3. ✓ Strategy briefs reflect scenario differences (e.g., "set par total" vs. "chase target")
4. ✓ Prediction JSON contains both scenarios
5. ✓ Runtime < 30s for typical match
6. ✓ No regression in existing single-scenario behavior (for backward compat if needed)

---

## Files to Modify

| File | Change | Priority |
|------|--------|----------|
| `wt20_oracle/state.py` | Add `ScenarioResult`, `DualScenarioState` | P0 |
| `wt20_oracle/pre_match_graph.py` | Add `run_dual_scenario_pipeline()`, `_extract_scenario_result()` | P0 |
| `wt20_oracle/cli.py` | Update `run_prematch()`, add `_print_dual_scenario_text()`, update `_save_prediction()` | P0 |
| `DUAL_SCENARIO_SPEC.md` | This document (reference) | P1 |

---

## Open Questions

1. **Should we keep the old `run_pre_match_pipeline()` function?** Yes, for backward compatibility and testing.
2. **Should `--toss-decision` be deprecated?** Recommend: keep it but ignore it (print warning: "toss decision ignored; computing both scenarios").
3. **Should we add `--scenario` flag to force single scenario for testing?** Optional; not in MVP.
4. **How to handle missing toss info?** Compute both as "best guess" scenarios, note uncertainty in output.

---

## Appendix: Example Output

```
Pre-match: AUSTRALIA vs SOUTH_AFRICA
Venue: old_trafford

══════════════════════════════════════════════════════════════════════
SITUATION 1: If AUSTRALIA bats first
══════════════════════════════════════════════════════════════════════

STRATEGY BRIEF: AUSTRALIA vs SOUTH_AFRICA at Emirates Old Trafford
TARGET: Set a score of ~143 runs.
  → Aggressive powerplay (target 50+ in 6 overs).
  → Consolidate in middle (build platform overs 7-15).
  → Accelerate death (last 5 overs, target 50+ runs).

WIN PROBABILITY: 61% (FAIR)
PITCH: Balanced

BATTING ORDER (Top 4):
  1. Beth Mooney (SR 124)
  2. Ellyse Perry (SR 114)
  3. Phoebe Litchfield (SR 125)
  4. Georgia Voll (SR 124)

BOWLING PLAN:
  Powerplay: Sutherland, Hamilton, Molineux, Perry, Wareham, Harris
  Middle: [same roster, tactical adjustments]
  Death: [same roster, focus on yorkers/variations]

══════════════════════════════════════════════════════════════════════
SITUATION 2: If AUSTRALIA bowls first (chasing)
══════════════════════════════════════════════════════════════════════

STRATEGY BRIEF: AUSTRALIA vs SOUTH_AFRICA at Emirates Old Trafford (Chasing)
TARGET: Chase target of ~145 runs.
  → Stabilize powerplay (weather opponent's bowling).
  → Build partnership in middle (avoid reckless shots).
  → Accelerate overs 15-20 (score 30-40 runs).

WIN PROBABILITY: 58% (FAIR)
PITCH: Balanced, expect slightly harder chase

BATTING ORDER (Top 4):
  1. Alyssa Healy (SR 132)
  2. Beth Mooney (SR 124)
  3. Ellyse Perry (SR 114)
  4. Phoebe Litchfield (SR 125)

BOWLING PLAN:
  Powerplay: Sutherland, Hamilton, Wareham (defensive lines)
  Middle: [adjust for South African batters' weaknesses]
  Death: Sutherland, Harris (variations, manage line/length)

═════════════════════════════════════════════════════════════════════

💾 Prediction saved: matches/aus_sou_old_20260613/
```

