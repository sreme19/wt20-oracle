# wt20-oracle Wiki 🏏

Welcome to the complete guide for **wt20-oracle** — the decision-support system for India Women's T20 World Cup 2026!

## 📚 What Is This?

**wt20-oracle** is an AI system that helps cricket coaches make smarter decisions using data from thousands of past matches. 

Think of it as having a team of experts analyzing:
- Which 11 players to pick
- What order they should bat in
- When to change bowlers
- Where to place fielders
- Whether you'll win

All based on real cricket data, not just guessing!

---

## 🎯 Choose Your Path

### 👶 I'm Brand New (No Cricket Knowledge!)

Start here:
1. **[Quick Start (5 min)](1-Quick-Start.md)** — Get it running in 5 minutes
2. **[Cricket Glossary](Cricket-Glossary.md)** — What all these terms mean
3. **[How It Works](How-It-Works.md)** — Simple explanation with diagrams

**Time to understand:** 30 minutes

---

### 💻 I'm a Beginner Coder

Start here:
1. **[Installation Guide](Installation.md)** — Step-by-step setup
2. **[Architecture Explained](Architecture-Explained.md)** — How the system is built
3. **[Command Reference](Commands.md)** — Every command with examples
4. **[Contributing Guide](Contributing.md)** — How to help with code

**Time to get working:** 1 hour  
**Time to make first change:** 2 hours

---

### 🏏 I Know Cricket (But Not Code)

Start here:
1. **[Cricket Concepts](Cricket-Concepts.md)** — T20, phases, matchups explained
2. **[Data & Statistics](Data-Statistics.md)** — Where data comes from
3. **[Player Insights Guide](Player-Insights.md)** — How to add expert opinions
4. **[Decision Logic](Decision-Logic.md)** — Why the system recommends certain things

**Time to understand:** 1 hour  
**Time to contribute insights:** 2 hours

---

### 🔬 I'm a Data Scientist / Analyst

Start here:
1. **[Data Architecture](Data-Architecture.md)** — All about the dataset
2. **[Statistical Models](Statistical-Models.md)** — MILP, Monte Carlo, matchups
3. **[Optimization Algorithms](Algorithms.md)** — How decisions are optimized
4. **[Contributing Data](Contributing-Data.md)** — Add new player stats or insights

**Time to understand:** 2-3 hours

---

### 🏗️ I'm a DevOps / Infrastructure Person

Start here:
1. **[Project Structure](Project-Structure.md)** — All files explained
2. **[Deployment Guide](Deployment.md)** — How to deploy this
3. **[Testing & CI/CD](Testing.md)** — Test pipeline setup
4. **[Configuration](Configuration.md)** — Settings and environment

**Time to understand:** 1 hour

---

## 📖 All Wiki Pages

### Getting Started
- **[Quick Start (5 min)](1-Quick-Start.md)** — Run your first command
- **[Installation](Installation.md)** — Detailed setup guide
- **[First Run](First-Run.md)** — What happens when you first run it

### Learning the System
- **[How It Works](How-It-Works.md)** — System overview (no code)
- **[Architecture Explained](Architecture-Explained.md)** — System design for coders
- **[Extensions](Extensions.md)** — All agent nodes and extensions
- **[Pre-Match Mode](Pre-Match-Mode.md)** — Deep dive: squad selection
- **[Live Mode](Live-Mode.md)** — Deep dive: in-match decisions

### Commands & Usage
- **[Command Reference](Commands.md)** — Every command with examples
- **[Match State JSON](Match-State-JSON.md)** — Live mode input format
- **[Output Examples](Output-Examples.md)** — What the system returns

### Understanding Cricket
- **[Cricket Glossary](Cricket-Glossary.md)** — All cricket terms (beginner level)
- **[Cricket Concepts](Cricket-Concepts.md)** — Deeper cricket explanation
- **[Game Phases](Game-Phases.md)** — PowerPlay, Middle, Death overs

### Data & Analysis
- **[Data Architecture](Data-Architecture.md)** — All about the dataset
- **[Player Statistics](Player-Statistics.md)** — What stats we track
- **[Matchup Analysis](Matchup-Analysis.md)** — Batter vs bowler records
- **[Data Sources](Data-Sources.md)** — Where data comes from
- **[Contributing Data](Contributing-Data.md)** — Add or update data

### Decision Models
- **[Statistical Models](Statistical-Models.md)** — MILP, Monte Carlo
- **[Optimization Algorithms](Algorithms.md)** — How decisions are made
- **[Decision Logic](Decision-Logic.md)** — Why certain recommendations

### Contributing
- **[Contributing Guide](Contributing.md)** — How to help
- **[Player Insights](Player-Insights.md)** — Add expert opinions
- **[Code Contribution](Code-Contribution.md)** — Add code features
- **[Testing Guide](Testing.md)** — Write tests

### Project Info
- **[Project Structure](Project-Structure.md)** — All files explained
- **[Deployment Guide](Deployment.md)** — How to deploy
- **[Configuration](Configuration.md)** — Settings
- **[FAQ](FAQ.md)** — Common questions
- **[Roadmap](Roadmap.md)** — Future plans
- **[Design Decisions](Design-Decisions.md)** — Why we built it this way

---

## 🚀 Quick Links

**I want to...**
- **Run it** → [Quick Start](1-Quick-Start.md)
- **Understand how it works** → [How It Works](How-It-Works.md)
- **Contribute code** → [Contributing Guide](Contributing.md)
- **Add cricket insights** → [Player Insights](Player-Insights.md)
- **Understand the data** → [Data Architecture](Data-Architecture.md)
- **Deploy it** → [Deployment Guide](Deployment.md)
- **Learn cricket terms** → [Cricket Glossary](Cricket-Glossary.md)

---

## 📞 Quick Help

**Installation problems?** → [Installation Troubleshooting](Installation.md#troubleshooting)

**Command not working?** → [Command Reference](Commands.md)

**Don't understand cricket?** → [Cricket Glossary](Cricket-Glossary.md)

**Want to help but not sure how?** → [Contributing Guide](Contributing.md)

**Questions?** → [FAQ](FAQ.md)

---

## 🎯 What This System Does

### Pre-Match (Before Game)
Input: Which team you're playing + where
Output:
- ✓ Best 11 players to pick (from 15)
- ✓ Optimal batting order (1-11)
- ✓ Bowling strategy (who bowls when)
- ✓ Tactical advice (in plain English)

### Live (During Game)
Input: Current score, wickets, bowlers, batters
Output:
- ✓ Should we change the bowler?
- ✓ Where should fielders go?
- ✓ Should we send an aggressive batter?
- ✓ What's our win probability?

---

## 📊 By The Numbers

| Metric | Value |
|--------|-------|
| Matches analyzed | 2,705 |
| Players covered | 178/180 (98.9%) |
| Matchup records | 39,277 |
| Tournament teams | 12 |
| Documentation lines | 3,917+ |
| Test files | 7 |
| Agent types | 10+ |

---

## 🏆 Tournament Info

**Tournament:** ICC Women's T20 World Cup 2026  
**Dates:** June 13 – July 5, 2026  
**Host:** England & Wales  
**Final:** Lord's, London  
**India's Group:** Australia, South Africa, Pakistan, Bangladesh, Netherlands

---

## 🔗 External Links

- **[CricSheet](https://cricsheet.org)** — Ball-by-ball match data
- **[ESPN Cricinfo](https://stats.espncricinfo.com)** — Player statistics
- **[ICC](https://icc-cricket.com)** — Tournament info
- **[GitHub](https://github.com/sreme19/wt20-oracle)** — Source code

---

## 📝 Page Map

```
Home (You are here!)
├── Quick Start (5 min)
├── Installation
├── First Run
│
├── How It Works
├── Architecture Explained
├── Extensions
├── Pre-Match Mode
├── Live Mode
│
├── Commands
├── Match State JSON
├── Output Examples
│
├── Cricket Glossary
├── Cricket Concepts
├── Game Phases
│
├── Data Architecture
├── Player Statistics
├── Matchup Analysis
├── Data Sources
├── Contributing Data
│
├── Statistical Models
├── Algorithms
├── Decision Logic
│
├── Contributing Guide
├── Player Insights
├── Code Contribution
├── Testing Guide
│
├── Project Structure
├── Deployment
├── Configuration
├── FAQ
├── Roadmap
└── Design Decisions
```

---

**👉 Start with:** [Quick Start (5 Minutes)](1-Quick-Start.md)

