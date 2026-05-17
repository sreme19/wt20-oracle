"""Matchups page — batter vs bowler head-to-head explorer."""

import streamlit as st
import plotly.express as px
import pandas as pd
from wt20_oracle.dashboard.loaders import load_matchups


def render() -> None:
    st.header("Batter–Bowler Matchup Explorer")
    st.caption(
        "Head-to-head records from CricSheet Women's T20I + WPL + WBBL + The Hundred. "
        "Minimum 6 balls faced to appear."
    )

    # ── Filters ───────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    batter_q = col1.text_input("Filter by batter name", placeholder="e.g. Mandhana", key="mu_bat")
    bowler_q = col2.text_input("Filter by bowler name", placeholder="e.g. Schutt", key="mu_bowl")
    min_balls = col3.slider("Min balls faced", 6, 30, 6, key="mu_balls")

    with st.spinner("Loading matchups..."):
        df = load_matchups(
            batter_filter=batter_q or None,
            bowler_filter=bowler_q or None,
            min_balls=min_balls,
        )

    if df.empty:
        st.info("No matchups found for this filter. Try a different name or reduce min balls.")
        return

    st.caption(f"{len(df):,} matchup records")

    # ── View mode ─────────────────────────────────────────────────────────────
    view = st.radio(
        "View", ["Top threat pairs", "Best bowlers vs batter", "Worst bowlers vs batter"],
        horizontal=True, key="mu_view"
    )

    if view == "Top threat pairs":
        # Highest SR for batter (batter dominant)
        top = df.nlargest(20, "strike_rate")[
            ["batter", "bowler", "balls", "runs", "dismissals", "strike_rate", "dot_pct", "boundary_pct"]
        ]
        st.subheader("Batter-dominant matchups (highest SR)")
        fig = px.scatter(
            top,
            x="strike_rate",
            y="dot_pct",
            size="balls",
            color="boundary_pct",
            hover_name="batter",
            hover_data={"bowler": True, "balls": True, "dismissals": True,
                        "strike_rate": ":.1f", "dot_pct": ":.1f"},
            labels={"strike_rate": "Strike Rate", "dot_pct": "Dot Ball %",
                    "boundary_pct": "Boundary %"},
            color_continuous_scale="Reds",
            size_max=25,
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top, use_container_width=True, hide_index=True)

    elif view == "Best bowlers vs batter":
        if not batter_q:
            st.info("Enter a batter name above to see which bowlers trouble them most.")
            return
        # Best bowlers = highest dismissal rate / lowest SR against this batter
        bowl_df = df.copy()
        bowl_df["dismissal_rate"] = bowl_df["dismissals"] / bowl_df["balls"].clip(lower=1)
        best = bowl_df.nsmallest(20, "strike_rate")

        st.subheader(f"Bowlers who trouble '{batter_q}'")
        fig2 = px.bar(
            best.head(15),
            x="bowler",
            y="strike_rate",
            color="dismissal_rate",
            text="dismissals",
            labels={"bowler": "", "strike_rate": "Batter Strike Rate", "dismissal_rate": "Dismissal Rate"},
            color_continuous_scale="Greens",
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(height=360, xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(best[["bowler", "balls", "runs", "dismissals", "strike_rate", "dot_pct"]],
                     use_container_width=True, hide_index=True)

    else:  # Worst bowlers vs batter
        if not batter_q:
            st.info("Enter a batter name above to see which bowlers they hit well.")
            return
        worst = df.nlargest(20, "strike_rate")
        st.subheader(f"Bowlers '{batter_q}' dominates")
        fig3 = px.bar(
            worst.head(15),
            x="bowler",
            y="strike_rate",
            color="boundary_pct",
            text="runs",
            labels={"bowler": "", "strike_rate": "Batter Strike Rate", "boundary_pct": "Boundary %"},
            color_continuous_scale="Reds",
        )
        fig3.update_traces(texttemplate="%{text} runs", textposition="outside")
        fig3.update_layout(height=360, xaxis_tickangle=-30)
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(worst[["bowler", "balls", "runs", "dismissals", "strike_rate", "boundary_pct"]],
                     use_container_width=True, hide_index=True)

    # ── Phase breakdown for selected matchup ─────────────────────────────────
    st.divider()
    st.subheader("Phase Breakdown")
    if not df.empty:
        pairs = df.apply(lambda r: f"{r['batter']} vs {r['bowler']}", axis=1).tolist()
        sel_pair = st.selectbox("Select matchup", pairs[:50], key="mu_pair")
        idx = pairs.index(sel_pair)
        row = df.iloc[idx]

        phase_data = pd.DataFrame({
            "Phase": ["Powerplay", "Middle", "Death"],
            "Balls": [row.get("pp_balls") or 0, row.get("md_balls") or 0, row.get("dt_balls") or 0],
        })
        fig4 = px.pie(phase_data, names="Phase", values="Balls", hole=0.4,
                      color_discrete_map={"Powerplay": "#2980b9", "Middle": "#27ae60", "Death": "#c0392b"})
        fig4.update_layout(height=280)
        c1, c2 = st.columns([1, 2])
        c1.metric("Total Balls", int(row["balls"]))
        c1.metric("Runs", int(row["runs"]))
        c1.metric("Dismissals", int(row["dismissals"]))
        c1.metric("Strike Rate", f"{row['strike_rate']:.1f}")
        c2.plotly_chart(fig4, use_container_width=True)
