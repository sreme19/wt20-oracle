# Analyst Insights Curation Guide

**Location:** `wt20_oracle/data/analyst_insights.json`

**Purpose:** Maintain qualitative assessments of player form, injury status, tactical patterns, and vs-opponent performance to inform strategic recommendations.

---

## Quick Start

### 1. Structure Overview

Each player entry has:

```json
{
  "player_id": {
    "overall_form": {
      "rating": "strong|weak|exceptional|emerging",
      "confidence": 0.0-1.0,
      "notes": "Human-readable justification"
    },
    "strengths": ["list", "of", "strengths"],
    "concerns": "string or null",
    "injury_status": "fit|fit_with_caution|unfit",
    "psychological_state": "string describing mentality",
    "phase_performance": {
      "powerplay": { "assessment": "...", "notes": "..." },
      "middle": { "assessment": "...", "notes": "..." },
      "death": { "assessment": "...", "notes": "..." }
    },
    "vs_opponent": {
      "australia": {
        "assessment": "struggle|adequate|strong|excellent",
        "confidence": 0.0-1.0,
        "specific_bowler_notes": "e.g., '3 ducks vs Schutt'",
        "recommendation": "tactical advice"
      }
    },
    "recent_events": "null or string",
    "last_updated": "YYYY-MM-DD",
    "analyst": "name of analyst/source",
    "notes": "optional context"
  }
}
```

### 2. Confidence Scores

| Range | Meaning | Example |
|-------|---------|---------|
| 0.90-1.0 | Very high confidence; backed by strong evidence | "3 ducks in 5 meetings vs Schutt" (recent, consistent pattern) |
| 0.70-0.89 | Good confidence; multiple data points | "Strong domestic form over 10+ matches" |
| 0.50-0.69 | Moderate confidence; emerging pattern | "Debut player; limited data but aggressive in domestic" |
| 0.30-0.49 | Low confidence; anecdotal or single match | "One recent poor series" |
| <0.30 | Very low; avoid using unless noting extreme edge case | N/A |

---

## Filling Out a Player Entry

### Field: `overall_form`

**Rating options:** `strong`, `weak`, `exceptional`, `emerging_talent`, `improving`, `unproven_but_talented`

**Confidence:** How sure are you? Based on:
- Number of recent matches
- Consistency of performance
- Quality of opposition
- Recency (recent > old)

**Notes:** 1-2 sentences with justification.

```json
"overall_form": {
  "rating": "strong",
  "confidence": 0.85,
  "notes": "3 consecutive 40+ scores in last T20I series. Confident stroke-play against pace."
}
```

---

### Field: `strengths` & `concerns`

**Strengths:** List 3-5 key strengths as bullet points.

```json
"strengths": [
  "Excellent against pace bowlers",
  "Aggressive mindset, thrives under pressure",
  "Strong off-side play",
  "Strike rotation vs spin"
]
```

**Concerns:** Single string describing the main concern, or null if none.

```json
"concerns": "Occasional inconsistency vs quality off-spinners on turning pitches"
```

---

### Field: `phase_performance`

Break down performance by match phase. Phases are:
- **Powerplay:** Overs 0-5 (aggressive start?)
- **Middle:** Overs 6-14 (scoring phase)
- **Death:** Overs 15-19 (finishing or defending)

For each phase:

```json
"phase_performance": {
  "powerplay": {
    "assessment": "strong",
    "notes": "Prefers boundary hitting; SR 95+ in last 12 months"
  },
  "middle": {
    "assessment": "excellent",
    "notes": "Best phase for Smriti; aggressive acceleration"
  },
  "death": {
    "assessment": "elite",
    "notes": "SR 145+ in last 12 months; world-class executioner"
  }
}
```

**Assessment options:** `struggling`, `developing`, `adequate`, `strong`, `excellent`, `elite`, `unknown`

---

### Field: `vs_opponent`

For each opponent India faces, provide:

```json
"vs_opponent": {
  "australia": {
    "assessment": "struggle",
    "confidence": 0.85,
    "specific_bowler_notes": "3 ducks in last 5 meetings vs Megan Schutt; uncomfortable vs short-pitched deliveries",
    "recommendation": "avoid Schutt in powerplay if possible; consider aggressive field if Schutt bowls"
  },
  "england": {
    "assessment": "strong",
    "confidence": 0.80,
    "specific_bowler_notes": "Excellent vs Sophie Ecclestone (SR 145+); uncomfortable vs Charlie Dean's variations",
    "recommendation": "target Ecclestone early; cautious vs Dean"
  }
}
```

**Key fields:**
- `assessment`: How does this player perform vs this opponent?
- `confidence`: How sure are you?
- `specific_bowler_notes`: Name-specific patterns if known
- `recommendation`: Tactical advice for captain/coaches

---

### Field: `injury_status`

Options: `fit`, `fit_with_caution`, `unfit`

If `fit_with_caution`, explain in `concerns`:

```json
"injury_status": "fit_with_caution",
"concerns": "Ankle injury (minor); expected to be fit for tournament. Conservative approach early; builds innings gradually."
```

---

### Field: `psychological_state`

Describe mental approach to the game:

```json
"psychological_state": "aggressive, fearless, composed under pressure"
```

Examples:
- "Leader; calms high-stress situations"
- "Young, fearless, plays big shots regardless of situation"
- "Anxious early, builds confidence through strike rotation"
- "Elite decision-maker under pressure"

---

### Field: `last_updated` & `analyst`

- `last_updated`: ISO date (YYYY-MM-DD) — when was this last reviewed?
- `analyst`: Who provided this insight? (name or team name)

```json
"last_updated": "2026-05-15",
"analyst": "Harsha Bhogle"
```

---

## Sources to Draw From

### Tier 1 (High Signal)
- ESPNcricinfo match reports and analysis
- Cricinfo "Player Stats" and "Career Overview" pages
- Team coaching staff notes (internal)
- ICC official assessments
- Recent series commentary (last 2-3 months)

### Tier 2 (Medium Signal)
- Cricket journalist articles
- Podcast commentary (specific tactical insights)
- Social media from credible analysts
- Domestic league performance (especially for debuts)

### Tier 3 (Low Signal)
- Single-match assessments
- Casual social media commentary
- Rumor or speculation
- Very old data (>6 months)

---

## Common Patterns to Capture

### Debut Players

```json
{
  "overall_form": {
    "rating": "unproven_but_talented",
    "confidence": 0.50,
    "notes": "Debut player in international T20. Limited data (2 T20I matches). Strong domestic form."
  },
  "concerns": "Inexperience vs quality international pace attack; limited exposure to variations",
  "psychological_state": "fearless, plays big shots regardless of situation — risky in early innings",
  "notes": "DEBUT PLAYER. Protect in batting order (position 4 or 5). Allow adjustment to international pace."
}
```

### Form Recovery

```json
{
  "overall_form": {
    "rating": "improving",
    "confidence": 0.70,
    "notes": "Poor series followed by 2x 50+ scores in last matches. Confidence returning."
  },
  "concerns": null,
  "psychological_state": "re-gaining confidence; needs a few good starts to settle"
}
```

### Injury Concern

```json
{
  "overall_form": {
    "rating": "strong",
    "confidence": 0.75,
    "notes": "Recent ankle niggle; expected to be fit for tournament."
  },
  "injury_status": "fit_with_caution",
  "concerns": "Ankle injury (minor); may affect movement in first 3-4 balls"
}
```

### Matchup Weakness

```json
{
  "vs_opponent": {
    "australia": {
      "assessment": "struggle",
      "confidence": 0.85,
      "specific_bowler_notes": "3 ducks in 5 meetings vs Megan Schutt",
      "recommendation": "avoid Schutt in powerplay; if unavoidable, plan aggressive field"
    }
  }
}
```

---

## Maintenance Schedule

### Pre-Tournament (Weekly)
- Review latest Cricinfo articles for each squad
- Update form ratings based on recent domestic/T20I matches
- Note any injury updates
- Refresh confidence scores if new data emerges

### During Tournament (Daily)
- After each match: update opponent vs-match-up notes
- Track fitness: any injuries during tournament?
- Update psychological state: did confidence change?
- Refresh recent_events field

### Post-Tournament (One-time)
- Document lessons learned for next cycle
- Validate which analyst predictions were accurate
- Update confidence scores based on accuracy
- Archive this version with performance data

---

## Integration into System

### What consumes analyst_insights.json?

1. **Pre-match decision support:** Form modifiers, matchup adjustments
2. **Narrative generation:** Explanations for recommendations
3. **MILP constraints:** Hard rules (injuries, debuts)
4. **Live match updates:** Psychological state changes
5. **Validation reports:** Post-tournament accuracy assessment

### Example: Form modifier

```python
# From io/analyst_loader.py
def form_modifier_from_insights(player_insights):
    rating = player_insights["overall_form"]["rating"]
    if "strong" in rating:
        return 1.05  # +5% to strike rate
    elif "weak" in rating:
        return 0.95  # -5%
    return 1.0
```

---

## Validation Checklist

Before committing updates:

- [ ] All required fields filled (or explicitly `null`)
- [ ] Confidence scores in 0.0-1.0 range
- [ ] Assessment ratings use approved keywords
- [ ] `last_updated` is current date
- [ ] Analyst name is specified
- [ ] Specific bowler names match CricSheet names (if applicable)
- [ ] Notes are 1-2 sentences, not essays
- [ ] vs_opponent entries have recommendations

---

## Example: Complete Player Entry

```json
"smriti_mandhana": {
  "overall_form": {
    "rating": "strong",
    "confidence": 0.85,
    "notes": "3 consecutive 40+ scores in last T20I series. Confident stroke-play."
  },
  "strengths": [
    "Excellent against pace bowlers",
    "Aggressive mindset, thrives under pressure",
    "Strong off-side play",
    "Strike rotation vs spin"
  ],
  "concerns": null,
  "injury_status": "fit",
  "psychological_state": "aggressive, fearless, composed under pressure",
  "phase_performance": {
    "powerplay": {
      "assessment": "strong",
      "notes": "Prefers boundary hitting; SR 95+ in last 12 months"
    },
    "middle": {
      "assessment": "excellent",
      "notes": "Best phase for Smriti; aggressive acceleration"
    },
    "death": {
      "assessment": "elite",
      "notes": "SR 145+ in last 12 months; world-class executioner"
    }
  },
  "vs_opponent": {
    "australia": {
      "assessment": "struggle",
      "confidence": 0.85,
      "specific_bowler_notes": "3 ducks in last 5 meetings vs Megan Schutt; uncomfortable vs short-pitched deliveries",
      "recommendation": "avoid Schutt in powerplay if possible; consider aggressive field if Schutt bowls"
    },
    "england": {
      "assessment": "strong",
      "confidence": 0.80,
      "specific_bowler_notes": "Excellent vs Sophie Ecclestone (SR 145+); uncomfortable vs Charlie Dean's variations",
      "recommendation": "target Ecclestone early; cautious vs Dean"
    }
  },
  "recent_events": null,
  "last_updated": "2026-05-15",
  "analyst": "Harsha Bhogle",
  "notes": "Vice-captain; consistent T20I performer. Key to India's aggressive approach."
}
```

---

## Questions?

For questions on structure or examples, refer to:
- `ROADMAP.md` — phase 2 for semi-automated refresh
- `STEERING.md` — design rationale
- `README.md` — overall system architecture
