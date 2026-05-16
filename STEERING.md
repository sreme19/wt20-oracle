# Steering Document — wt20-oracle

Design rationale for algorithm choices and architectural decisions.
Read this before refactoring any core node or optimisation module.

## Why two graphs (pre_match_graph + live_graph)?

The decision spaces are fundamentally different:

- **Pre-match** has full information and time to optimise. MILP and Monte Carlo
  can run exhaustively across all lineup permutations.
- **Live** is time-constrained (captain needs a recommendation in < 30 seconds
  between overs). Agents must use pre-computed matchup tables and fast heuristics,
  not re-running full optimisation.

A single graph with conditional routing would work, but two separate graphs keeps
each pipeline readable and independently testable.

## Why MILP for batting order (pre-match)?

Batting order is a combinatorial assignment problem: assign players to positions
to maximise expected total score given constraints (WK must be in playing XI,
no more than 4 overseas, etc.). MILP via PuLP with CBC solver handles this cleanly
and is already used in ipl-oracle. The objective function is expected runs
weighted by phase-split strike rates and dismissal probabilities.

Alternative considered: simulated annealing. Rejected — MILP gives an exact
solution for a problem this size (15 choose 11, ~3000 permutations) in < 1 second.

## Why Monte Carlo for win probability (live)?

Win probability during an innings depends on: current score, wickets in hand,
overs remaining, required rate, and the quality of batting still to come.
This is a stochastic sequential process — Monte Carlo simulation across remaining
overs is the natural fit. We simulate 10,000 innings completions per query using
the batting order and phase-split strike rates / dismissal rates.

POMDP (used in dhurandhar-oracle) was considered but rejected: the state space
(score × wickets × over) is fully observable in cricket, so the belief-state
tracking POMDP provides is unnecessary overhead.

## Why separate matchup_matrix.py?

Batter vs bowler expected value is the single most-called computation in live mode
(every bowling change decision reads it). Isolating it lets us cache the full
matrix at startup and serve lookups in O(1) rather than re-deriving from raw data
on each agent call.

## Why Claude only in narrator_node?

All numerical decisions (bowling change, field placement, batting order) are
computed deterministically from data. Claude receives the completed recommendation
dict and converts it to a plain-English brief. This keeps Claude on the narrative
path and ensures recommendations are reproducible and auditable — the same input
state always produces the same optimal action regardless of model temperature.

## Women's cricket data sparsity — how we handle it

Players with < 20 T20I caps are flagged `statistical_reliability: low` or `medium`.
For these players, domestic T20 stats (WPL, WBBL, The Hundred) are blended in
with a downweight factor (default 0.6×) to represent the quality gap between
domestic and international. This is configurable per player in `players/{team}.json`.

Matchup pairs with < 6 balls faced are marked `reliability: low` and the system
falls back to the bowler's generic economy + the batter's generic strike rate
rather than using the specific head-to-head figure.
