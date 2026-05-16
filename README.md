# wt20-oracle

Next-best-action decision support system for the **India Women's cricket team**
at the **ICC Women's T20 World Cup 2026** (England & Wales, June 13 – July 5).

## What it does

Two operating modes:

| Mode | When to run | Output |
|------|-------------|--------|
| `prematch` | Night before / morning of match | Squad selection, batting order, bowling plan, strategy brief |
| `live` | Between overs during the match | Bowling change, field placement, pinch-hitter call, win probability |

## Quick start

```bash
pip install -e ".[dev]"

# Pre-match brief vs Australia at Edgbaston
wt20-oracle prematch --opponent australia --venue edgbaston

# Live recommendation (over 14, India bowling, 87/3 after 13 overs)
wt20-oracle live --match-state match_state.json
```

## Project structure

```
wt20_oracle/
  schemas.py          — all enums and TypedDicts (the data contract)
  state.py            — shared LangGraph state
  pre_match_graph.py  — pre-match pipeline
  live_graph.py       — in-match pipeline
  agents/
    shared/           — opponent_node, pressure_node, narrator_node
    pre_match/        — squad_selector, batting_order, bowling_plan, strategy
    live/             — live_state, bowling_change, field_placement, pinch_hitter, momentum
  optimisation/       — monte_carlo, milp_lineup, matchup_matrix
  data/               
    players/          — 12 team squads with T20I statistics
    matchups.json     — 39,277 batter-bowler head-to-head records
    analyst_insights.json — curated form, injury, psychological assessments
    venues.json       — tournament venues with pitch profiles
    schedule.json     — group stage and knockout structure
    teams.json        — all 12 teams with H2H history
  io/                 — loader, live_input, formatter, analyst_loader
```

## Data sources

### Quantitative Data
- [CricSheet](https://cricsheet.org) — ball-by-ball T20I, WPL, WBBL, The Hundred (4,705 matches)
- [ESPN Cricinfo Statsguru](https://stats.espncricinfo.com) — career statistics, phase splits
- [ICC](https://icc-cricket.com) — tournament schedule, venue details

### Qualitative Data (Analyst Insights)
- `wt20_oracle/data/analyst_insights.json` — curated form, injury, psychological, vs-opponent assessments
- Sources: Cricinfo articles, team scouts, coaching staff notes
- See `docs/ANALYST_INSIGHTS_GUIDE.md` for curation guide

### Coverage
- **Players:** 178/180 (98.9%) with T20I statistics
- **Matchups:** 39,277 batter-bowler pairs with reliability tiers
- **Analyst Insights:** India squad fully annotated; other squads partial
- **Form Windows:** last-5-matches, last-6-months, last-12-months per player

## Tournament facts

- **Host:** England and Wales
- **Dates:** June 13 – July 5, 2026
- **Final:** Lord's, London
- **India's group (A):** Australia, South Africa, Pakistan, Bangladesh, Netherlands
- **Venues:** Lord's · Old Trafford · Headingley · Edgbaston · Rose Bowl · The Oval · Bristol
