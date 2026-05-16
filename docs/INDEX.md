# Documentation Index

Complete guide to all wt20-oracle documentation. Choose your learning path based on your role and goals.

---

## 🚀 Quick Navigation

### New to the Project? Start Here
1. [Getting Started (GETTING_STARTED.md)](GETTING_STARTED.md) - Installation & first command
2. [Glossary (Glossary.md)](Glossary.md) - Cricket terms explained
3. [Architecture (Architecture.md)](Architecture.md) - How the system works

### Want to Use the System?
- [CLI Usage Guide (CLI-Usage.md)](CLI-Usage.md) - All commands with examples
- [Data Schema (Data-Schema.md)](Data-Schema.md) - Data file formats
- [Contributing (CONTRIBUTING.md)](CONTRIBUTING.md) - Bug reports, data updates

### Interested in Decision Logic?
- [Opponent Analysis (OPPONENT_ANALYSIS.md)](OPPONENT_ANALYSIS.md) - How we analyze opponents
- [Squad Selector (SQUAD_SELECTOR.md)](SQUAD_SELECTOR.md) - How we pick the best 11
- [Batting Order (BATTING_ORDER.md)](BATTING_ORDER.md) - How we optimize batting order
- [Bowling Plan (BOWLING_PLAN.md)](BOWLING_PLAN.md) - How we create bowling strategy

### Technical Deep Dives
- [Technical Architecture (TECHNICAL_ARCHITECTURE.md)](TECHNICAL_ARCHITECTURE.md) - System design details
- [Analyst Insights Guide (ANALYST_INSIGHTS_GUIDE.md)](ANALYST_INSIGHTS_GUIDE.md) - Adding domain expertise

---

## 📚 All Documentation by Category

### Getting Started (Beginner)
| Document | Purpose | Read Time |
|----------|---------|-----------|
| [Getting Started](GETTING_STARTED.md) | Installation, verification, first command | 15 min |
| [Glossary](Glossary.md) | Cricket terminology for beginners | 20 min |
| [Architecture](Architecture.md) | High-level system overview | 15 min |

### Usage & Reference
| Document | Purpose | Read Time |
|----------|---------|-----------|
| [CLI Usage](CLI-Usage.md) | Command reference with examples | 20 min |
| [Data Schema](Data-Schema.md) | JSON data file formats | 25 min |
| [Contributing](CONTRIBUTING.md) | How to contribute to the project | 20 min |

### Core Decision Algorithms
| Document | Purpose | Read Time |
|----------|---------|-----------|
| [Opponent Analysis](OPPONENT_ANALYSIS.md) | 8 techniques for opponent intelligence | 30 min |
| [Squad Selector](SQUAD_SELECTOR.md) | 8 techniques for squad selection | 30 min |
| [Batting Order](BATTING_ORDER.md) | 8 techniques for batting optimization | 30 min |
| [Bowling Plan](BOWLING_PLAN.md) | 8 techniques for bowling strategy | 30 min |

### Technical & Deep Dives
| Document | Purpose | Read Time |
|----------|---------|-----------|
| [Technical Architecture](TECHNICAL_ARCHITECTURE.md) | System design, data flow, algorithms | 45 min |
| [Analyst Insights Guide](ANALYST_INSIGHTS_GUIDE.md) | Adding expert domain knowledge | 25 min |

---

## 🎯 Learning Paths

### Path 1: I Want to Run It (Non-Technical User)
**Goal:** Get the system running and use it

1. **[Getting Started](GETTING_STARTED.md)** (15 min)
   - Install Python
   - Navigate to project
   - Run `pip install`
   - Verify installation

2. **[CLI Usage](CLI-Usage.md)** (20 min)
   - Learn pre-match command syntax
   - Learn live match command syntax
   - Try 3-4 example commands

3. **[Glossary](Glossary.md)** (20 min)
   - Understand cricket terms used in output
   - Understand strike rates, economies, etc.

**Total Time: ~55 minutes**

---

### Path 2: I Want to Understand How It Works (Technical User)
**Goal:** Understand the system architecture and decision logic

1. **[Getting Started](GETTING_STARTED.md)** (15 min)
   - Installation

2. **[Architecture](Architecture.md)** (15 min)
   - System overview
   - Pre-match pipeline
   - Live mode components

3. **[Opponent Analysis](OPPONENT_ANALYSIS.md)** (30 min)
   - 8 opponent analysis techniques
   - Data structures
   - Real-world example

4. **[Squad Selector](SQUAD_SELECTOR.md)** (30 min)
   - 8 squad selection techniques
   - Optimization algorithm
   - Real-world example

5. **[Batting Order](BATTING_ORDER.md)** (30 min)
   - 8 batting optimization techniques
   - Phase-appropriate positioning
   - Real-world example

6. **[Bowling Plan](BOWLING_PLAN.md)** (30 min)
   - 8 bowling strategy techniques
   - Over-by-over planning
   - Real-world example

7. **[Technical Architecture](TECHNICAL_ARCHITECTURE.md)** (45 min)
   - Deep dive into algorithms
   - Data flow diagrams
   - Integration points

**Total Time: ~3 hours**

---

### Path 3: I Want to Contribute Data (Cricket Expert)
**Goal:** Add domain expertise to improve recommendations

1. **[Getting Started](GETTING_STARTED.md)** (15 min)
   - Installation

2. **[Glossary](Glossary.md)** (20 min)
   - Terminology

3. **[Data Schema](Data-Schema.md)** (25 min)
   - Understand data file formats
   - JSON structures
   - Player statistics

4. **[Analyst Insights Guide](ANALYST_INSIGHTS_GUIDE.md)** (25 min)
   - How to add expert opinions
   - Player insights format
   - Tactical notes

5. **[Contributing](CONTRIBUTING.md)** (20 min)
   - How to submit data changes
   - Testing guidelines
   - Pull request process

**Total Time: ~2 hours**

---

### Path 4: I Want to Contribute Code (Developer)
**Goal:** Add new features or fix bugs

1. **[Getting Started](GETTING_STARTED.md)** (15 min)
   - Installation with dev tools

2. **[Technical Architecture](TECHNICAL_ARCHITECTURE.md)** (45 min)
   - System design
   - Code structure
   - Integration points

3. **[Opponent Analysis](OPPONENT_ANALYSIS.md)** (30 min)
   - Understand one agent node deeply
   - Data structures
   - Implementation patterns

4. **[Contributing](CONTRIBUTING.md)** (20 min)
   - Development setup
   - Code style
   - Testing
   - Pull request process

5. **[Data Schema](Data-Schema.md)** (25 min)
   - Data file formats
   - JSON structures
   - Validation rules

**Total Time: ~2.5 hours**

---

## 📖 Documentation Structure

### Getting Started Documents
**For complete beginners with no cricket or coding knowledge**

- Step-by-step guides
- Simple language
- Visual diagrams where helpful
- Example outputs

### Reference Documents
**For users who want to look up specific information**

- Command reference with all options
- Data schema with JSON examples
- Troubleshooting guides
- Tips & tricks

### Technical Documents
**For developers and architects**

- Algorithm explanations
- Implementation patterns
- Data flow diagrams
- Real-world examples

### Decision Logic Documents
**For understanding how recommendations are made**

- 8-technique deep dives
- Real-world examples
- Integration with other nodes
- Performance metrics

---

## 🔄 Document Relationships

```
Getting Started
    ↓
    ├── Glossary (understand terms)
    │
    ├── Architecture (understand how system works)
    │   ↓
    │   ├── Opponent Analysis (first agent)
    │   ├── Squad Selector (second agent)
    │   ├── Batting Order (third agent)
    │   ├── Bowling Plan (fourth agent)
    │   └── [Strategy Node - coming soon]
    │
    ├── CLI Usage (how to run it)
    │
    ├── Data Schema (understand data)
    │   ↓
    │   └── Analyst Insights Guide (add your own data)
    │
    ├── Technical Architecture (deep dive)
    │   ↓
    │   └── Contributing (help improve code)
    │
    └── Contributing (report issues, suggest features)
```

---

## 📊 By Document

### [Getting Started](GETTING_STARTED.md)
- **Level:** Beginner
- **Length:** ~600 lines
- **Time:** 15 minutes
- **Topics:**
  - Python version check
  - Project navigation
  - Installation via pip
  - Verification steps
  - First command walkthrough
  - Troubleshooting
- **Prerequisites:** None
- **Next:** Glossary or CLI Usage

---

### [Glossary](Glossary.md)
- **Level:** Beginner
- **Length:** ~400 lines
- **Time:** 20 minutes
- **Topics:**
  - T20 format basics
  - Batting terms (strike rate, average, boundaries)
  - Bowling terms (economy, wickets, pace vs spin)
  - Game phases (PowerPlay, Middle, Death)
  - Head-to-head concepts
  - Player roles
  - Example walkthroughs
- **Prerequisites:** None
- **Next:** Architecture or Opponent Analysis

---

### [Architecture](Architecture.md)
- **Level:** Beginner-Intermediate
- **Length:** ~550 lines
- **Time:** 15-20 minutes
- **Topics:**
  - System overview
  - Pre-match mode (5 agents)
  - Live mode (6 components)
  - Data flow diagrams
  - Key concepts explained simply
- **Prerequisites:** Getting Started
- **Next:** Specific agent nodes (Opponent, Squad, Batting, Bowling)

---

### [CLI Usage](CLI-Usage.md)
- **Level:** Beginner
- **Length:** ~450 lines
- **Time:** 20 minutes
- **Topics:**
  - Pre-match command syntax
  - Live match command syntax
  - All arguments and options
  - 20+ practical examples
  - JSON/CSV format options
  - Troubleshooting guide
  - Common scenarios
- **Prerequisites:** Getting Started
- **Next:** Any agent node documentation

---

### [Data Schema](Data-Schema.md)
- **Level:** Intermediate
- **Length:** ~550 lines
- **Time:** 25 minutes
- **Topics:**
  - Player statistics structure
  - Matchup matrix explanation
  - Venues data files
  - Schedule and teams
  - Reliability tiers
  - Data quality notes
- **Prerequisites:** Glossary
- **Next:** Analyst Insights Guide or Contributing

---

### [Opponent Analysis](OPPONENT_ANALYSIS.md)
- **Level:** Intermediate-Advanced
- **Length:** ~900 lines
- **Time:** 30-40 minutes
- **Topics:**
  - 8 opponent analysis techniques:
    1. Phase-Based Performance
    2. Opposition-Split Metrics
    3. Form Window Analysis
    4. Head-to-Head Records
    5. Toss Analysis
    6. Tactical Tendency Analysis
    7. Venue-Specific Analysis
    8. NRR Analysis
  - Data structures with JSON examples
  - Implementation patterns
  - Real-world example (India vs Australia)
- **Prerequisites:** Glossary, Architecture
- **Next:** Squad Selector or Technical Architecture

---

### [Squad Selector](SQUAD_SELECTOR.md)
- **Level:** Intermediate-Advanced
- **Length:** ~600 lines
- **Time:** 30-40 minutes
- **Topics:**
  - 8 squad selection techniques:
    1. Optimal Balance Constraint
    2. Matchup-Aware Selection
    3. Opponent Weakness Exploitation
    4. Form Window Weighted Selection
    5. Venue-Specific Selection
    6. Role-Based Depth
    7. Experience & Tournament Form
    8. Captaincy & Leadership
  - Data structures with examples
  - Implementation patterns
  - Real-world example (India vs Australia)
  - Integration with other nodes
- **Prerequisites:** Glossary, Opponent Analysis
- **Next:** Batting Order or Technical Architecture

---

### [Batting Order](BATTING_ORDER.md)
- **Level:** Intermediate-Advanced
- **Length:** ~650 lines
- **Time:** 30-40 minutes
- **Topics:**
  - 8 batting optimization techniques:
    1. Phase-Appropriate Positioning
    2. Opposition Matchup Optimization
    3. Momentum & Partnership Building
    4. Captain's Position Optimization
    5. Wicket-Keeper Positioning
    6. Role-Based Sequencing
    7. Risk Management & Variance Reduction
    8. Form & Confidence Sequencing
  - Complete optimization algorithm
  - Data structures
  - Real-world example with full batting order
  - Performance factors by position
  - Integration with other nodes
- **Prerequisites:** Glossary, Squad Selector
- **Next:** Bowling Plan or Technical Architecture

---

### [Bowling Plan](BOWLING_PLAN.md)
- **Level:** Intermediate-Advanced
- **Length:** ~900 lines
- **Time:** 30-40 minutes
- **Topics:**
  - 8 bowling strategy techniques:
    1. Phase-Specialist Assignment
    2. Opposition Matchup Analysis
    3. Bowler Load Balancing
    4. Left-Right Bowling Combinations
    5. Bowler Fitness & Injury Management
    6. Venue-Specific Bowling Strategy
    7. Wicket-Taking Strategy
    8. Death Bowling Excellence
  - Complete algorithm
  - Over-by-over planning
  - Real-world example (20-over plan)
  - Matchup targeting
  - Contingency strategies
  - Integration with other nodes
- **Prerequisites:** Glossary, Squad Selector, Batting Order
- **Next:** Technical Architecture

---

### [Technical Architecture](TECHNICAL_ARCHITECTURE.md)
- **Level:** Advanced
- **Length:** ~800 lines
- **Time:** 45-60 minutes
- **Topics:**
  - System design details
  - Pre-match pipeline architecture
  - Live mode architecture
  - Data flow in-depth
  - MILP optimization (squad selection)
  - Monte Carlo simulation (win probability)
  - Matchup analysis algorithms
  - State management with TypedDict
  - LangGraph integration
  - Performance considerations
- **Prerequisites:** Architecture, all agent node docs
- **Next:** Contributing (for code changes)

---

### [Analyst Insights Guide](ANALYST_INSIGHTS_GUIDE.md)
- **Level:** Intermediate
- **Length:** ~500 lines
- **Time:** 25-30 minutes
- **Topics:**
  - How to add expert opinions
  - Player insights format
  - Tactical notes
  - Format validation
  - Common pitfalls
  - Examples from real data
- **Prerequisites:** Data Schema
- **Next:** Contributing

---

### [Contributing](CONTRIBUTING.md)
- **Level:** Intermediate
- **Length:** ~700 lines
- **Time:** 20-30 minutes
- **Topics:**
  - Multiple ways to contribute
  - Development setup
  - Code style guidelines
  - Testing walkthrough
  - Common tasks (bug fixes, data updates)
  - Pull request process
- **Prerequisites:** Getting Started (or Technical Architecture for code)
- **Next:** Specific agent node docs (to understand what to fix)

---

## 🎓 Knowledge Progression

```
BEGINNER LEVEL
└── Getting Started + Glossary + CLI Usage
    ├── Comfortable running commands
    ├── Understanding cricket terminology
    └── Viewing output

INTERMEDIATE LEVEL
├── Architecture + Data Schema
├── Analyst Insights Guide
├── Contributing (data)
└── Can add data, report bugs, suggest features

ADVANCED LEVEL
├── Opponent Analysis + Squad Selector
├── Batting Order + Bowling Plan
├── Technical Architecture
├── Contributing (code)
└── Can modify algorithms, add features, optimize code
```

---

## 📚 Reading Combinations

### "I just want to run it"
→ Getting Started + CLI Usage (~35 min)

### "I want to understand what it's doing"
→ Getting Started + Glossary + Architecture (~50 min)

### "I want to understand the decisions"
→ All agent node docs (Opponent, Squad, Batting, Bowling) (~120 min)

### "I want to contribute data"
→ Getting Started + Glossary + Data Schema + Analyst Insights (~85 min)

### "I want to contribute code"
→ Technical Architecture + any agent node docs + Contributing (~100+ min)

### "I want to become an expert on this system"
→ All documentation in order (~6-8 hours)

---

## 🔍 Find Documentation by Topic

### Cricket Concepts
- **Game Phases:** [Glossary](Glossary.md), [Architecture](Architecture.md)
- **Strike Rate, Economy:** [Glossary](Glossary.md), [Data Schema](Data-Schema.md)
- **Head-to-Head:** [Opponent Analysis](OPPONENT_ANALYSIS.md), [Glossary](Glossary.md)
- **Matchups:** [Opponent Analysis](OPPONENT_ANALYSIS.md), [Squad Selector](SQUAD_SELECTOR.md), [Batting Order](BATTING_ORDER.md), [Bowling Plan](BOWLING_PLAN.md)

### Usage Topics
- **Installing the system:** [Getting Started](GETTING_STARTED.md)
- **Running commands:** [CLI Usage](CLI-Usage.md)
- **Understanding output:** [Glossary](Glossary.md), any agent node doc
- **Troubleshooting:** [Getting Started](GETTING_STARTED.md#troubleshooting), [CLI Usage](CLI-Usage.md)

### Data Topics
- **Data files:** [Data Schema](Data-Schema.md)
- **Adding player data:** [Analyst Insights Guide](ANALYST_INSIGHTS_GUIDE.md)
- **Updating statistics:** [Contributing](CONTRIBUTING.md)
- **JSON formats:** [Data Schema](Data-Schema.md)

### Decision Logic Topics
- **How squad is selected:** [Squad Selector](SQUAD_SELECTOR.md)
- **How batting order is optimized:** [Batting Order](BATTING_ORDER.md)
- **How bowling is planned:** [Bowling Plan](BOWLING_PLAN.md)
- **How opponents are analyzed:** [Opponent Analysis](OPPONENT_ANALYSIS.md)
- **How everything fits together:** [Technical Architecture](TECHNICAL_ARCHITECTURE.md), [Architecture](Architecture.md)

### Development Topics
- **System design:** [Technical Architecture](TECHNICAL_ARCHITECTURE.md)
- **Code structure:** [Technical Architecture](TECHNICAL_ARCHITECTURE.md)
- **How to contribute:** [Contributing](CONTRIBUTING.md)
- **Running tests:** [Contributing](CONTRIBUTING.md)

---

## 📖 Documentation Standards

All documentation in this project follows consistent standards:

### Structure
1. **Overview:** What is this?
2. **The Problem:** What challenge does this solve?
3. **Key Techniques:** Multiple detailed techniques (usually 8)
4. **Algorithms:** Implementation patterns with code
5. **Real-World Example:** Concrete India vs Australia example
6. **Integration:** How it fits with other components
7. **Output Summary:** Typical results

### Level Indicators
- **Beginner:** No prior knowledge needed
- **Intermediate:** Some knowledge expected
- **Advanced:** Comfortable with technical concepts

### Accessibility
- Simple language first, technical second
- Cricket terms explained
- Real-world examples in every doc
- Code examples where relevant
- "Why" explained, not just "how"

---

## ✅ Checklist: Finding Your Next Document

1. **Is this your first time?**
   - YES → Start with [Getting Started](GETTING_STARTED.md)
   - NO → Go to question 2

2. **Do you understand cricket terminology?**
   - NO → Read [Glossary](Glossary.md)
   - YES → Go to question 3

3. **What do you want to do?**
   - **Run the system** → [CLI Usage](CLI-Usage.md)
   - **Understand how it works** → [Architecture](Architecture.md)
   - **Add your own data** → [Analyst Insights Guide](ANALYST_INSIGHTS_GUIDE.md)
   - **Contribute code** → [Technical Architecture](TECHNICAL_ARCHITECTURE.md)
   - **Understand decisions** → [Opponent Analysis](OPPONENT_ANALYSIS.md)

---

## 🎯 Next Steps

**Found the document you want?**
→ Click it from the navigation links above

**Can't find what you're looking for?**
→ Check [Contributing](CONTRIBUTING.md#troubleshooting) or [CLI Usage](CLI-Usage.md#troubleshooting)

**Want to suggest a documentation improvement?**
→ See [Contributing](CONTRIBUTING.md)

**Stuck on a concept?**
→ Check [Glossary](Glossary.md) for cricket terms or [Architecture](Architecture.md) for system overview

---

**Last Updated:** 2026-05-16  
**Total Documentation:** 12 guides, ~6,500 lines, ~4-8 hours reading time

