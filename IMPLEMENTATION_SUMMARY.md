# wt20-oracle MVP Implementation Summary

**Status:** ✓ Complete — Data pipeline + Analyst insights curated JSON (Phase 1)

**Date:** May 16, 2026

---

## 1. Data Pipeline (Completed)

### Sources Ingested
- **T20I:** 1,943 matches (CricSheet `t20s_female.zip`)
- **WPL:** 88 matches (India domestic league)
- **WBBL:** 519 matches (Australia domestic league)
- **The Hundred:** 155 matches (UK domestic league)
- **Total:** 2,705 matches processed

### Player Coverage
- **Target:** 180 players (12 teams × 15 squad size)
- **Achieved:** 178/180 (98.9%)
  - 10 teams: 100% coverage
  - Scotland: 14/15 (missing Maisie Maceira — no CricSheet data)
  - Netherlands: 14/15 (missing Rosalie Lawrence — no CricSheet data)

### Data Quality Improvements Applied
1. ✓ **CricSheet alias mapping** — 125 mappings in `name_map.json`
   - Added: Nandini Sharma → `N Sharma`, Kirstie Gordon → `KL Gordon`, Gabriella Fontenla → `S Ingabire`/`G Ingabire`, Tilly Corteen-Coleman → `MR Corteen-Coleman`

2. ✓ **Form windows** — Computed last-5, last-6m, last-12m for all players
   - Strike rates, averages, match counts per window
   - Date-based bucketing with ISO 8601 timestamps

3. ✓ **Dot ball tracking in splits** — Added `dot_balls` field to vs_pace, vs_spin, vs_left_arm, vs_right_arm accumulators
   - `dot_ball_pct` now calculated (was hardcoded 0.0)

4. ✓ **ICC tournament record segregation** — Only World Cup / Asia Cup matches counted
   - Flag: checks event name contains "world cup" / "asia cup" keywords
   - Example: Ecclestone has 43 total T20I caps but only 18 ICC tournament matches

5. ✓ **Caps field population** — Derived from match count
   - e.g., Harmanpreet Kaur: 132 caps, Nandini Sharma: 6 caps

6. ✓ **Validation logic enhanced** — Now checks both batting_stats and bowling_stats
   - No longer false-flags bowler-only players

### Matchup Matrix
- **Total pairs:** 39,277 (expanded from 23,673 before including domestic leagues)
- **Reliability breakdown:**
  - High (>20 balls): 4,089 pairs
  - Medium (6-20 balls): 15,843 pairs
  - Low (<6 balls): 19,345 pairs

---

## 2. Analyst Insights System (Completed)

### Files Created

#### `wt20_oracle/data/analyst_insights.json` (MVP data store)
- **Purpose:** Curated qualitative assessments of players
- **Structure:** Per-team, per-player entries with:
  - Overall form rating + confidence
  - Strengths & concerns
  - Phase performance (powerplay, middle, death)
  - vs-opponent specific notes
  - Injury status
  - Psychological state
  - Last updated date + analyst attribution

- **Coverage:**
  - India: Full squad (15/15) annotated with detailed insights
  - Other teams: Placeholder structure ready for population

#### `wt20_oracle/io/analyst_loader.py` (Integration module)
- **Functions:**
  - `load_analyst_insights()` — Load JSON
  - `get_player_insights()` — Lookup by player_id + team
  - `form_modifier_from_insights()` — Convert form rating to SR multiplier
  - `matchup_modifier_from_insights()` — Adjust matchup scores based on vs-opponent notes
  - `constraint_from_injury()` — Extract MILP constraints (e.g., "avoid_death_overs")
  - `psychological_notes_for_narrative()` — Extract for narrative generation
  - `vs_opponent_recommendation()` — Get tactical advice
  - `AnalystInsightEnricher` — Context manager for enriching player JSON

#### `docs/ANALYST_INSIGHTS_GUIDE.md` (Curation handbook)
- **Purpose:** Guide for populating analyst_insights.json
- **Contents:**
  - Field-by-field documentation with examples
  - Confidence scoring rubric (0.0-1.0)
  - Common patterns (debut players, form recovery, injury concerns)
  - Sources to draw from (Tier 1: Cricinfo, Tier 2: journalists, Tier 3: social media)
  - Maintenance schedule (pre-tournament weekly, during daily, post one-time)
  - Validation checklist

---

## 3. Future Roadmap (Documented)

### `ROADMAP.md` — Phase 2 & 3 Enhancement Plan

**Phase 2 (Post-MVP, June-September 2026):**
1. MILP hard constraints from analyst injuries (e.g., avoid death overs if shoulder injury)
2. Live-match psychological state tracking (anxiety, confidence, momentum)
3. Semi-automated LLM-powered insight refresh (Cricinfo scraper + Claude summarization)
4. Multi-source analyst weighting (consensus from multiple analysts)
5. Analyst confidence validation post-tournament
6. Contextual matchup scoring (reweight based on venue, pitch, form)
7. Enhanced narrative explanations referencing analyst notes
8. Real-time injury & fitness tracking

**Phase 3 (October-November 2026):**
1. Uncertainty quantification (confidence intervals on recommendations)
2. Probabilistic player performance models (distributions not point estimates)
3. Multi-objective optimization (balance 5+ competing objectives)
4. Post-tournament learning (validate which insights were most predictive)

---

## 4. Files Modified/Created

### New Files
- ✓ `wt20_oracle/data/analyst_insights.json` (489 lines, 11 KB)
- ✓ `wt20_oracle/io/analyst_loader.py` (276 lines)
- ✓ `docs/ANALYST_INSIGHTS_GUIDE.md` (490 lines)
- ✓ `ROADMAP.md` (600+ lines)
- ✓ `IMPLEMENTATION_SUMMARY.md` (this file)

### Modified Files
- ✓ `scripts/name_map.json` — Added CricSheet aliases for 4 debut players
- ✓ `scripts/parse_cricsheet.py` — Major enhancements:
  - Added ICC_EVENT_KEYWORDS and ICC_EVENT_KEYWORDS constant
  - Added per-match innings tracking for form_windows
  - Fixed dot_balls in split accumulators
  - Enhanced match filtering to include domestic leagues with WC squad players
  - New form_windows computation (last_5_matches, last_6_months, last_12_months)
  - Fixed icc_tournament_record to only count actual ICC events
  - Added _batting_form_windows() and _bowling_form_windows() functions
  - Added "caps" field population
  - Fixed _validate() to check both batting_stats AND bowling_stats
- ✓ `README.md` — Updated with analyst insights section

---

## 5. Integration Points (Ready for Implementation)

### In Pre-Match Graph
- **Form Adjustment:** `form_modifier_from_insights()` → adjust form_windows strike rates
- **Matchup Reweighting:** `matchup_modifier_from_insights()` → reweight MILP objective
- **Narrative:** Add analyst notes to squad_selector and batting_order recommendations

### In Live Graph
- **Constraints:** `constraint_from_injury()` → add to bowling_change MILP
- **Narrative:** `vs_opponent_recommendation()` → explain field placements

### In Narrator Node
- **Context:** Pull psychological, concern, and tactical notes for explanation
- **Caveats:** Flag injuries, debuts, and weak matchups in narrative

---

## 6. Testing & Validation

### Automated Tests (To Be Written)
- Load analyst_insights.json, validate schema
- Test form_modifier_from_insights() with all ratings
- Test matchup_modifier_from_insights() with vs-opponent scenarios
- Test constraint_from_injury() with injury types

### Manual Validation (Completed)
- ✓ Load and display India squad insights
- ✓ Verify all 15 players populated with stats
- ✓ Spot-check form modifiers (strong form → 1.05x multiplier)
- ✓ Verify historical Smriti vs Schutt data (3 ducks in 5 meetings)

---

## 7. Known Limitations (MVP)

### 2 Unpopulated Players (Zero CricSheet Data)
- Maisie Maceira (Scotland)
- Rosalie Lawrence (Netherlands)
→ Can only be populated with manual scout reports or live tournament data

### Analyst Insights Coverage (Initial)
- India: 100% (4 players with domestic league context)
- Other 11 teams: Placeholder structure only
→ Requires curation from team scouts/analysts

### Form Windows Computation
- Currently: Recency-based (last 5 matches, last 6m calendar)
- Future: Weight recent matches higher; account for opponent strength

---

## 8. Next Steps (Recommended Order)

### Immediate (Before Tournament)
1. Populate analyst_insights.json for remaining 11 teams (assign scouts)
2. Write integration tests for analyst_loader.py
3. Implement in pre_match_graph.py: form modifiers + narrative enrichment
4. Test with India vs Australia pre-match scenario

### During Tournament (Group Stage)
1. Validate analyst predictions against actual matches
2. Track which vs-opponent notes were accurate
3. Update psychological state after each match
4. Refine form_windows with live data

### Post-Tournament (Analysis Phase)
1. Validate full prediction accuracy of analyst insights
2. Document which insights were most predictive
3. Plan Phase 2 improvements based on learnings
4. Begin semi-automated refresh (LLM scraper)

---

## 9. Success Criteria (MVP)

✓ **Data:** 98.9% player coverage with complete statistics
✓ **Insights:** India squad fully annotated; guide documented for other teams
✓ **Integration:** analyst_loader.py ready for use in agents
✓ **Roadmap:** Future phases documented with clear timelines and effort estimates

---

## Summary

The MVP combines:
1. **Quantitative foundation** — 2,705 matches, 39,277 matchups, form windows
2. **Qualitative layer** — Curated analyst insights for India squad
3. **Integration ready** — analyst_loader.py provides modifiers, constraints, narratives
4. **Future-proofed** — ROADMAP.md outlines Phase 2 & 3 enhancements

Ready for pre-match agent implementation with analyst-informed decision-making.

