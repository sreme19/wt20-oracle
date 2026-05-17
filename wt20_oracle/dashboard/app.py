"""
wt20-oracle BI Dashboard
========================

Run with:
    pip install streamlit pandas plotly
    streamlit run wt20_oracle/dashboard/app.py

Or from the project root:
    streamlit run wt20_oracle/dashboard/app.py
"""

import sys
from pathlib import Path

# Ensure the project root is on the path when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

st.set_page_config(
    page_title="wt20-oracle  |  BI Dashboard",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("🏏 wt20-oracle")
st.sidebar.caption("India Women T20 World Cup 2026")
st.sidebar.divider()

PAGE_ICONS = {
    "Predictions": "📊",
    "Players": "👤",
    "Teams": "🏳️",
    "Matchups": "⚔️",
}
page = st.sidebar.radio(
    "Navigate",
    list(PAGE_ICONS.keys()),
    format_func=lambda p: f"{PAGE_ICONS[p]}  {p}",
)

st.sidebar.divider()
st.sidebar.caption("Data sources")
st.sidebar.markdown("""
- `matches/*/prediction.json`
- `data/players/*.json`
- `data/teams.json`
- `data/matchups.json`
""")

# ── Load data (cached) ────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading predictions...")
def get_predictions():
    from wt20_oracle.dashboard.loaders import load_predictions
    return load_predictions()

@st.cache_data(show_spinner="Loading player data...")
def get_players():
    from wt20_oracle.dashboard.loaders import load_players
    return load_players()

@st.cache_data(show_spinner="Loading team data...")
def get_teams():
    from wt20_oracle.dashboard.loaders import load_teams
    return load_teams()

# ── Page routing ──────────────────────────────────────────────────────────────

if page == "Predictions":
    from wt20_oracle.dashboard.pages.predictions import render as render_predictions
    pred_df = get_predictions()
    render_predictions(pred_df)

elif page == "Players":
    from wt20_oracle.dashboard.pages.players import render as render_players
    player_df = get_players()
    render_players(player_df)

elif page == "Teams":
    from wt20_oracle.dashboard.pages.teams import render as render_teams
    teams_df = get_teams()
    render_teams(teams_df)

elif page == "Matchups":
    from wt20_oracle.dashboard.pages.matchups import render as render_matchups
    render_matchups()
