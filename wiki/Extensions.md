# Extensions Documentation

Complete guide to wt20-oracle extensions and agent nodes.

---

## Overview

wt20-oracle uses a modular architecture with **agent nodes** as extensions. Each node handles a specific decision-making task, and they work together in a graph to produce comprehensive recommendations.

---

## Extension Categories

### Pre-Match Extensions
Extensions that run before a match to help with squad selection and strategy.

### Live Extensions  
Extensions that run during a match to provide real-time decision support.

### Shared Extensions
Extensions that provide common functionality used across both pre-match and live modes.

---

## Pre-Match Extensions

### Squad Selector Node
**File:** `agents/pre_match/squad_selector_node.py`

**Purpose:** Selects the best 11 players from a squad of 15 based on:
- Player form and recent performance
- Matchup advantages against opponent
- Venue suitability
- Role balance (batters, bowlers, all-rounders)

**Inputs:**
- Squad of 15 players
- Opponent team
- Venue characteristics
- Match conditions

**Outputs:**
- Selected XI (11 players)
- Selection reasoning for each player

---

### Batting Order Node
**File:** `agents/pre_match/batting_order_node.py`

**Purpose:** Determines the optimal batting order (1-11) based on:
- Player strike rates in different phases
- Matchup records against opponent bowlers
- Left-right combination
- Finisher capabilities
- Anchor vs aggressor roles

**Inputs:**
- Selected XI players
- Opponent bowling attack
- Venue pitch characteristics

**Outputs:**
- Batting order (positions 1-11)
- Reasoning for each position
- Phase-specific recommendations

---

### Bowling Plan Node
**File:** `agents/pre_match/bowling_plan_node.py`

**Purpose:** Creates a bowling strategy that specifies:
- Which bowlers to use in which phases
- Optimum over allocation
- Death over specialists
- PowerPlay bowling options
- Matchup-based bowling changes

**Inputs:**
- Selected XI bowlers
- Opponent batting lineup
- Venue conditions
- Match scenario (batting/bowling first)

**Outputs:**
- Phase-wise bowling plan
- Over allocation for each bowler
- Key matchups to exploit
- Death over specialists

---

### Strategy Node
**File:** `agents/pre_match/strategy_node.py`

**Purpose:** Generates comprehensive tactical strategy including:
- Overall game approach
- Phase-specific tactics
- Field placement suggestions
- Bowling change triggers
- Batting acceleration points
- Win probability estimation

**Inputs:**
- All pre-match analysis outputs
- Venue and opponent data
- Historical patterns

**Outputs:**
- Strategy brief (plain English)
- Tactical flags
- Key matchups
- Scenario report
- Win probability

---

## Live Extensions

### Bowling Change Node
**File:** `agents/live/bowling_change_node.py`

**Purpose:** Recommends when to change bowlers based on:
- Current bowler's economy rate
- Batter-bowler matchups
- Match phase requirements
- Wicket-taking opportunities
- Pressure situations

**Inputs:**
- Current match state
- Bowler performance metrics
- Batter strengths/weaknesses
- Phase of play

**Outputs:**
- Bowling change recommendation
- Suggested replacement bowler
- Reasoning for change

---

### Field Placement Node
**File:** `agents/live/field_placement_node.py`

**Purpose:** Suggests optimal field placements based on:
- Batter's scoring zones
- Bowler's line and length
- Required run rate
- Wicket preservation needs
- Match situation

**Inputs:**
- Current batter and bowler
- Match state
- Phase of play
- Required run rate

**Outputs:**
- Field placement suggestions
- Aggressive vs defensive setup
- Specific fielder positions

---

### Live State Node
**File:** `agents/live/live_state_node.py`

**Purpose:** Tracks and analyzes live match state including:
- Current score and run rate
- Wickets in hand
- Balls remaining
- Momentum assessment
- Win probability updates

**Inputs:**
- Live match data
- Ball-by-ball updates
- Historical context

**Outputs:**
- Current match state analysis
- Momentum indicator
- Updated win probability
- Phase assessment

---

### Momentum Node
**File:** `agents/live/momentum_node.py`

**Purpose:** Analyzes match momentum based on:
- Recent run rates
- Wicket fall patterns
- Boundary frequency
- Over-by-over progression
- Historical momentum shifts

**Inputs:**
- Recent over data
- Wicket information
- Boundary patterns
- Match phase

**Outputs:**
- Momentum assessment (positive/neutral/negative)
- Momentum shift indicators
- Tactical implications

---

### Pinch Hitter Node
**File:** `agents/live/pinch_hitter_node.py`

**Purpose:** Identifies situations where a pinch hitter (aggressive batter) should be sent in based on:
- Required run rate pressure
- Wickets in hand
- Match phase
- Opponent bowling weakness
- Historical success patterns

**Inputs:**
- Current match situation
- Available batters
- Required run rate
- Opponent bowlers

**Outputs:**
- Pinch hitter recommendation
- Suggested player
- Timing for change
- Expected impact

---

## Shared Extensions

### Narrator Node
**File:** `agents/shared/narrator_node.py`

**Purpose:** Generates human-readable explanations and commentary for:
- Pre-match recommendations
- Live match analysis
- Decision reasoning
- Strategy explanations

**Inputs:**
- Analysis outputs
- Decision data
- Match context

**Outputs:**
- Plain English explanations
- Commentary text
- User-friendly summaries

---

### Opponent Node
**File:** `agents/shared/opponent_node.py`

**Purpose:** Analyzes opponent strengths and weaknesses including:
- Key players to watch
- Historical performance patterns
- Tactical tendencies
- Weaknesses to exploit

**Inputs:**
- Opponent team data
- Historical match records
- Player statistics

**Outputs:**
- Opponent analysis
- Key threats
- Exploitable weaknesses
- Tactical recommendations

---

### Pressure Node
**File:** `agents/shared/pressure_node.py`

**Purpose:** Assesses pressure situations based on:
- Required run rate vs current rate
- Wickets remaining
- Balls remaining
- Match importance
- Historical pressure outcomes

**Inputs:**
- Match state
- Run rate requirements
- Wicket situation
- Phase of play

**Outputs:**
- Pressure level assessment
- Pressure management recommendations
- Tactical adjustments

---

## Optimization Extensions

### Matchup Matrix
**File:** `optimisation/matchup_matrix.py`

**Purpose:** Builds and analyzes batter-bowler matchup matrices to identify:
- Favorable matchups
- Unfavorable matchups
- Historical performance patterns
- Statistical advantages

**Inputs:**
- Player statistics
- Historical match data
- Ball-by-ball records

**Outputs:**
- Matchup matrix
- Advantage scores
- Key matchup insights

---

### MILP Lineup Optimizer
**File:** `optimisation/milp_lineup.py`

**Purpose:** Uses Mixed Integer Linear Programming to optimize:
- Batting order selection
- Squad composition
- Resource allocation
- Objective maximization

**Inputs:**
- Player statistics
- Constraints (roles, balance)
- Objective function

**Outputs:**
- Optimal lineup
- Optimization results
- Sensitivity analysis

---

### Monte Carlo Simulator
**File:** `optimisation/monte_carlo.py`

**Purpose:** Runs Monte Carlo simulations to estimate:
- Win probabilities
- Score distributions
- Outcome ranges
- Scenario analysis

**Inputs:**
- Team strengths
- Match conditions
- Historical distributions

**Outputs:**
- Win probability estimates
- Score distributions
- Confidence intervals
- Scenario analysis

---

## Adding New Extensions

### Extension Template

```python
"""
Extension Name
==============

Purpose: Brief description of what this extension does
"""

from typing import Dict, Any

def run_extension(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function for the extension
    
    Args:
        input_data: Dictionary containing required inputs
        
    Returns:
        Dictionary containing extension outputs
    """
    # Your extension logic here
    return {
        "output_key": "output_value"
    }
```

### Integration Steps

1. **Create the extension file** in the appropriate directory:
   - Pre-match: `agents/pre_match/`
   - Live: `agents/live/`
   - Shared: `agents/shared/`
   - Optimization: `optimisation/`

2. **Define inputs and outputs** clearly in the docstring

3. **Add to the graph** in the appropriate graph file:
   - Pre-match: `pre_match_graph.py`
   - Live: `live_graph.py`

4. **Test the extension** with sample data

5. **Add documentation** to this wiki page

---

## Extension Best Practices

### Design Principles
- **Single Responsibility:** Each extension should do one thing well
- **Clear Inputs/Outputs:** Define interfaces explicitly
- **Stateless:** Extensions should not maintain internal state
- **Testable:** Write unit tests for each extension
- **Documented:** Include comprehensive docstrings

### Input Validation
- Validate all inputs before processing
- Provide meaningful error messages
- Handle edge cases gracefully

### Output Formatting
- Use consistent output structure
- Include reasoning/justification
- Provide confidence scores where applicable

### Performance
- Optimize for speed (live extensions need to be fast)
- Cache expensive computations
- Use efficient data structures

---

## Extension Dependencies

### Core Dependencies
- `wt20_oracle.schemas` - Data schemas and validation
- `wt20_oracle.state` - State management
- `wt20_oracle.io` - Data loading utilities

### External Dependencies
- `numpy` - Numerical computations
- `pandas` - Data manipulation
- `langchain` - Agent framework
- `langgraph` - Graph orchestration

---

## Testing Extensions

### Unit Tests
```python
def test_extension_name():
    # Arrange
    input_data = {
        "key": "value"
    }
    
    # Act
    result = run_extension(input_data)
    
    # Assert
    assert "expected_key" in result
    assert result["expected_key"] == "expected_value"
```

### Integration Tests
Test extensions within the full graph context to ensure they work correctly with other extensions.

---

## Troubleshooting

### Common Issues

**Extension not found in graph**
- Check that the extension is imported in the graph file
- Verify the extension is added to the graph nodes

**Input validation errors**
- Check that input data matches expected schema
- Verify all required fields are present

**Performance issues**
- Profile the extension code
- Add caching for expensive operations
- Optimize data structures

---

## Related Documentation

- [Architecture Explained](Architecture-Explained.md) - System architecture
- [Commands Reference](Commands.md) - How to use extensions via CLI
- [Contributing Guide](Contributing.md) - How to contribute new extensions
- [Testing Guide](Testing.md) - How to test extensions

---

**Need help?** Check the [FAQ](FAQ.md) or [Contributing Guide](Contributing.md)
