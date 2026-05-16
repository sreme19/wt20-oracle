# wt20-oracle Roadmap

**Status:** MVP with curated analyst insights (Option 1 — Phase 1)

This document outlines future enhancement ideas for integrating qualitative analyst intelligence into the decision-support pipeline.

---

## Phase 2: Advanced Analyst Integration (Post-MVP)

### 2.1 MILP Hard Constraints from Analyst Insights

**Goal:** Convert analyst concerns into hard constraints for batting order optimization.

**Implementation:**
- Add `constraint_from_injury()` and `constraint_from_debut()` logic to `optimisation/milp_lineup.py`
- Map analyst insights to PuLP constraint variables:
  - Injury concerns → position constraints (e.g., "avoid death overs")
  - Debut status → protective ordering (e.g., "not opening batter")
  - Psychological state → acceleration timing (e.g., "late-inning hitter")

**Example:**
```python
# In milp_lineup.py
for player in squad:
    insights = analyst_insights.get(player.id)
    if constraint := constraint_from_injury(insights):
        if constraint == "avoid_death_overs":
            model += pulp.lpSum([death_position[player] for p in death_overs]) <= 0
        elif constraint == "cautious_powerplay":
            model += position[player] >= 2  # Not opening
```

**Timeline:** Post-tournament analysis (learn from MVP data)

---

### 2.2 Live-Match Psychological State Tracking

**Goal:** During a match, update analyst assessment of player psychology in real-time.

**Implementation:**
- Extend `LiveMatchStateSchema` to include `player_psychological_state` (anxiety, confidence, momentum)
- Track: runs scored, wickets lost, pressure moments (e.g., "batter got out, confidence dip")
- Use in `live_graph.py` bowling_change and field_placement nodes
- Example:
  - If Smriti scores 2 runs off first 3 balls: anxiety increases, recommend aggressive bowling
  - If Harmanpreet just hit 2 fours: momentum high, consider defensive field

**Data model:**
```json
{
  "live_psychological_state": {
    "smriti_mandhana": {
      "base_confidence": 0.85,
      "confidence_this_over": 0.75,
      "momentum_factor": -0.10,
      "anxiety_level": "moderate"
    }
  }
}
```

**Timeline:** Implement during live testing (mid-tournament)

---

### 2.3 Semi-Automated Analyst Insight Refresh (LLM-Powered)

**Goal:** Keep analyst insights current without manual daily updates.

**Implementation:**

#### Option A: CricInfo Web Scraping + Claude Summarization
```python
# wt20_oracle/io/analyst_scraper.py

async def refresh_player_insights_from_articles(player_id: str, team: str):
    """
    1. Scrape Cricinfo for recent articles mentioning player
    2. Use Claude API to extract insights
    3. Merge into analyst_insights.json
    """
    articles = scrape_cricinfo_player_coverage(player_id)
    
    if not articles:
        return None
    
    insights = await claude.messages.create(
        model="claude-3-5-sonnet",
        max_tokens=500,
        system="Extract cricket player form, injury status, and tactical notes from articles.",
        messages=[{
            "role": "user",
            "content": f"""Summarize recent form and tactical insights for {player}:

Articles:
{articles_text}

Return JSON matching this schema:
{{
  "overall_form": {{"rating": "strong|weak|improving", "confidence": 0.0-1.0, "notes": "..."}},
  "concerns": "...",
  "injury_status": "...",
  "vs_opponent": {{}}
}}"""
        }]
    )
    
    return parse_json_response(insights)
```

**Requirements:**
- Cricinfo RSS feed subscriptions or web scraping (fragile)
- Claude API integration with Files API for article ingestion
- Scheduler (CronCreate) to run nightly or pre-tournament
- Validation layer (human review before committing changes)

**Timeline:** 2-3 weeks post-MVP

---

### 2.4 Multi-Source Analyst Weighting

**Goal:** Combine insights from multiple analysts with confidence scores.

**Data model:**
```json
{
  "player": "harmanpreet_kaur",
  "analyst_sources": [
    {
      "analyst": "Harsha Bhogle",
      "affiliation": "Cricinfo",
      "confidence": 0.95,
      "form_rating": "strong",
      "notes": "..."
    },
    {
      "analyst": "India team scout",
      "affiliation": "BCCI",
      "confidence": 0.90,
      "form_rating": "exceptional",
      "notes": "..."
    }
  ],
  "consensus_rating": "strong",
  "consensus_confidence": 0.92
}
```

**Implementation:**
```python
def consensus_form_rating(analyst_sources: List[dict]) -> Tuple[str, float]:
    """
    Aggregate multiple analyst opinions with confidence weighting.
    Returns: (consensus_rating, aggregate_confidence)
    """
    weighted_sum = sum(s['confidence'] for s in analyst_sources)
    rating_votes = {
        "strong": sum(s['confidence'] for s in analyst_sources if "strong" in s['form_rating']),
        "weak": sum(s['confidence'] for s in analyst_sources if "weak" in s['form_rating']),
        # ...
    }
    consensus = max(rating_votes, key=rating_votes.get)
    return consensus, weighted_sum / len(analyst_sources)
```

**Timeline:** Q3 post-tournament (once multiple analysts collaborate)

---

### 2.5 Analyst Confidence Scoring & Validation

**Goal:** Track which analyst predictions were accurate, adjust confidence scores accordingly.

**Implementation:**
- After each match, record:
  - Analyst prediction (e.g., "Smriti will struggle vs Schutt")
  - Actual outcome (runs scored, dismissal)
  - Match confidence (0.0-1.0)
- Post-tournament: compute accuracy per analyst and prediction type
- Adjust future `confidence` scores based on validation

**Data model:**
```json
{
  "validation": {
    "smriti_vs_schutt_prediction": {
      "analyst": "Harsha Bhogle",
      "prediction": "struggle",
      "predicted_confidence": 0.85,
      "actual_outcome": "scored 32 runs",
      "match_date": "2026-06-15",
      "accuracy": false,
      "notes": "Prediction was wrong; Smriti played well vs Schutt"
    }
  }
}
```

**Timeline:** Post-tournament analysis (June-July 2026)

---

### 2.6 Contextual Matchup Scoring

**Goal:** Adjust historical matchup expected values based on analyst's specific context notes.

**Example:**
```python
def score_matchup_with_context(
    batter_id: str,
    bowler_id: str,
    matchup_stats: dict,
    batter_insights: dict,
    venue_id: str,
    pitch_type: str
) -> float:
    """
    Base: historical SR from matchup_stats
    Adjustments:
      1. Specific vs-bowler notes (e.g., "ducks vs Schutt")
      2. Venue context (e.g., "uncomfortable on turning pitches")
      3. Injury/form state from analyst
    """
    base_sr = matchup_stats['strike_rate']
    modifier = 1.0
    
    # Analyst notes specific weakness
    vs_bowler_notes = batter_insights.get('vs_opponent', {}).get(bowler_team)
    if vs_bowler_notes:
        if "ducks" in vs_bowler_notes.lower():
            modifier *= 0.85  # -15%
        elif "excellent record" in vs_bowler_notes.lower():
            modifier *= 1.15  # +15%
    
    # Venue concerns
    if "turning" in pitch_type and "uncomfortable" in batter_insights.get('concerns', ''):
        modifier *= 0.90
    
    # Form state
    form_mod = form_modifier_from_insights(batter_insights)
    modifier *= form_mod
    
    return base_sr * modifier
```

**Integration point:** `optimisation/matchup_matrix.py`

**Timeline:** Phase 2 (mid-tournament if needed for live adjustments)

---

### 2.7 Narrative Enrichment with Analyst Insights

**Goal:** Use analyst insights in `agents/shared/narrator_node.py` to explain *why* recommendations are made.

**Current (bare recommendation):**
```
BATTING ORDER:
1. Smriti Mandhana
2. Shafali Verma
3. Harmanpreet Kaur (captain)
4. Nandini Sharma
```

**Enhanced (with analyst context):**
```
BATTING ORDER & ANALYST NOTES:

1. Smriti Mandhana (CR: 0.89)
   ✓ Form: Strong (3 consecutive 40+ scores)
   ✓ Strength: Excellent vs pace, aggressive mindset
   ⚠️ Caution: 3 ducks in 5 meetings vs Schutt; uncomfortable vs short-pitched
   → Recommendation: Open aggressively; avoid Schutt in powerplay if possible

2. Shafali Verma (CR: 0.78)
   ✓ Form: Strong (domestic excellence)
   ⚠️ Caution: Ankle niggle; may take 3-4 balls to settle
   → Recommendation: Protective opening; allow adjustment window

3. Harmanpreet Kaur (CR: 0.91) — CAPTAIN
   ✓ Form: Exceptional; captain's knock counts
   ✓ Psychological: Elite under pressure; decision-maker
   ⚠️ Caution: 28 runs in 3 meetings vs Perry; Perry's variations expected to trouble
   → Recommendation: Mid-order slot; accelerate when team needs quick runs; hold vs Perry early

4. Nandini Sharma (CR: 0.62) — DEBUT
   ⚠️ Inexperience: Limited T20I exposure; fearless but risky
   ⚠️ Phase: Weak vs pace bowlers in powerplay
   → Recommendation: Protective position (4 or 5); allow international experience accumulation
```

**Implementation:** Add `analyst_narrative()` function to narrator_node

**Timeline:** Phase 2 (implement after MVP validation)

---

### 2.8 Real-Time Injury & Fitness Tracking

**Goal:** Monitor breaking news on player fitness; auto-update analyst_insights.json

**Implementation:**
- Subscribe to Cricinfo/ESPNcricinfo injury alerts via RSS/API
- On player fitness change:
  - Update `analyst_insights.json` with new status
  - Alert coaching staff (PushNotification)
  - Trigger MILP re-run if constraint affected
- Example: "Harmanpreet ruled out with shoulder injury" → recompute batting order

**Timeline:** Tournament week (June 2026)

---

## Phase 3: Advanced Modelling (Post-Tournament)

### 3.1 Uncertainty Quantification in Recommendations

**Goal:** Express confidence in recommendations, not just point estimates.

**Current:** "Recommend bowler X with win probability 62%"

**Enhanced:** "Recommend bowler X (win prob 62% ± 8%, confidence 0.75)"

**Implementation:**
- Monte Carlo: return percentiles (25th, 50th, 75th) not just mean
- MILP sensitivity analysis: which constraints most affect objective?
- Analyst confidence: weight by historical accuracy

---

### 3.2 Probabilistic Player Performance Models

**Goal:** Instead of fixed stat lines, model player performance as distributions.

**Example:**
```python
# Currently: Smriti's SR is 145.22 in death overs (point estimate)
# Enhanced: Smriti's SR in death is N(145, σ=25)
#          → 68% chance she scores 120-170 SR

def player_performance_distribution(
    player_id: str,
    phase: str,
    vs_bowler_type: str,
    form_modifier: float,
    analyst_adjustment: float
) -> Distribution:
    """
    Return probability distribution of player performance.
    Uses: historical variance, recent form, analyst confidence.
    """
```

**Data:**
- Historical variance per player-phase-bowler combo
- Form windows to estimate recent variance (concentrated vs spread)
- Analyst confidence → adjust variance (high confidence = tighter dist)

---

### 3.3 Multi-Objective Optimization

**Goal:** Balance multiple competing objectives.

**Current:** Maximize matchup score (single objective)

**Enhanced:** Pareto frontier across:
1. Batting order depth (protect weak links, showcase strength)
2. Matchup scores (head-to-head advantage)
3. Allrounder balance (flexibility for late-game changes)
4. Captain placement (morale, leadership when needed)
5. Analyst risk mitigation (avoid known weaknesses)

**Implementation:** Multi-objective MILP (Gurobi, CPLEX) or evolutionary algorithms (NSGA-II)

---

### 3.4 Learning from Tournament Outcomes

**Goal:** Validate and refine model during the tournament.

**Tracking:**
- Every pre-match recommendation
- Actual match outcome
- Analyst prediction accuracy
- MILP constraint effectiveness

**Post-tournament analysis:**
- Which constraints helped? (hard-code for next tournament)
- Which analyst notes were most predictive?
- Did form_windows accurately forecast recent performance?
- How often did live recommendations improve win probability?

**Example output:**
```
MODEL VALIDATION REPORT (2026 T20 WC)

Recommendation Accuracy:
  - Batting order (MILP): 73% of top-3 recommendations in actual 11
  - Bowling change (Monte Carlo): 68% improved win prob
  - Field placement: 82% contextually sensible

Analyst Insight Accuracy:
  - Form ratings: 81% accurate (Bhogle 89%, scout 76%)
  - vs-opponent notes: 65% predictive (high variance)
  - Injury status: 100% correct

Recommendations for next tournament:
  - Increase weight on allrounder balance (over-optimized for matchups)
  - Add captain's decision-making as hard constraint (soft constraint insufficient)
  - Harsha Bhogle insights outperformed others; prioritize his analysis
```

---

## Implementation Timeline

| Phase | Features | Est. Timeline | Effort |
|-------|----------|---------------|--------|
| **1 (MVP)** | Curated JSON, soft adjustments, narrative | Now | ✓ Done |
| **2a** | MILP hard constraints | Post-MVP (June) | 2 weeks |
| **2b** | Live psychological state | During tournament | 3 weeks |
| **2c** | LLM scraper + refresh | July 2026 | 3 weeks |
| **2d** | Multi-source weighting | Post-tournament | 2 weeks |
| **2e** | Confidence validation | Post-tournament | 2 weeks |
| **2f** | Contextual matchup scoring | Post-tournament | 1 week |
| **2g** | Enhanced narratives | Post-tournament | 1 week |
| **2h** | Real-time fitness tracking | Tournament week | 1 week |
| **3a** | Uncertainty quantification | Oct 2026 | 3 weeks |
| **3b** | Probabilistic models | Oct 2026 | 4 weeks |
| **3c** | Multi-objective optimization | Nov 2026 | 4 weeks |
| **3d** | Tournament learnings | Aug-Sep 2026 | 2 weeks |

---

## Dependencies & Prerequisites

### For Phase 2:
- ✓ MVP curated JSON (DONE)
- ✓ Analyst insights loader (DONE)
- Claude API integration (for scraper)
- Cricinfo RSS/API access
- Scheduler (CronCreate)

### For Phase 3:
- Tournament data (match outcomes, actual performance)
- Statistical validation framework (pytest fixtures)
- Multi-objective solver (Gurobi, CPLEX, or open-source NSGA-II)

---

## Success Criteria

### MVP (Phase 1):
- ✓ Load and apply analyst insights to player JSON
- ✓ Form modifiers affecting form_windows
- ✓ Narrative explanations reference analyst notes
- ✓ Coverage: India squad fully annotated; other squads partially

### Phase 2:
- 80%+ of analyst predictions validated against actual matches
- MILP constraints improve recommendations (vs baseline)
- Real-time updates reduce surprise injuries/form changes
- Narrative quality significantly improves (qualitative feedback)

### Phase 3:
- Multi-objective optimization balances 5+ objectives
- Uncertainty quantification provides actionable confidence intervals
- Post-tournament report demonstrates 10%+ improvement in recommendation accuracy

---

## Notes

- **Manual curation is feature, not bug.** Curated insights are high-signal; automation comes later.
- **Validation is critical.** Don't over-trust LLM summaries; human review required.
- **Iterative learning.** Each tournament teaches the model; sophistication increases over time.
- **Explainability over accuracy.** Better to recommend conservatively with clear reasoning than optimally with mystery.

