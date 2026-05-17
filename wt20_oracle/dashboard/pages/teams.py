"""Teams page — radar chart, phase comparison bar, ICC ranking table."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def render(df: pd.DataFrame) -> None:
    st.header("Team Comparison")

    if df.empty:
        st.warning("No team data found.")
        return

    # ── ICC Ranking bar ────────────────────────────────────────────────────────
    st.subheader("ICC T20I Rankings")
    rank_df = df.dropna(subset=["icc_ranking"]).sort_values("icc_ranking")
    if not rank_df.empty:
        fig = px.bar(
            rank_df,
            x="name",
            y="icc_ranking",
            color="group",
            text="icc_ranking",
            labels={"name": "", "icc_ranking": "ICC Ranking", "group": "Group"},
            color_discrete_map={"A": "#3498db", "B": "#e67e22"},
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=340, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Phase batting run rate ────────────────────────────────────────────────
    st.subheader("Batting Run Rate by Phase")
    rr_cols = {"bat_pp_rr": "Powerplay", "bat_md_rr": "Middle", "bat_dt_rr": "Death"}
    rr_data = []
    for _, row in df.iterrows():
        for col, label in rr_cols.items():
            val = row.get(col)
            if pd.notna(val):
                rr_data.append({"team": row["name"], "phase": label, "run_rate": val})

    if rr_data:
        rr_df = pd.DataFrame(rr_data)
        fig2 = px.bar(
            rr_df,
            x="team",
            y="run_rate",
            color="phase",
            barmode="group",
            labels={"team": "", "run_rate": "Run Rate", "phase": "Phase"},
            color_discrete_map={"Powerplay": "#2980b9", "Middle": "#27ae60", "Death": "#c0392b"},
        )
        fig2.update_layout(height=340, xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Bowling economy by phase ──────────────────────────────────────────────
    st.subheader("Bowling Economy by Phase")
    econ_cols = {"bowl_pp_econ": "Powerplay", "bowl_md_econ": "Middle", "bowl_dt_econ": "Death"}
    econ_data = []
    for _, row in df.iterrows():
        for col, label in econ_cols.items():
            val = row.get(col)
            if pd.notna(val):
                econ_data.append({"team": row["name"], "phase": label, "economy": val})

    if econ_data:
        ec_df = pd.DataFrame(econ_data)
        fig3 = px.bar(
            ec_df,
            x="team",
            y="economy",
            color="phase",
            barmode="group",
            labels={"team": "", "economy": "Economy Rate", "phase": "Phase"},
            color_discrete_map={"Powerplay": "#2980b9", "Middle": "#27ae60", "Death": "#c0392b"},
        )
        fig3.update_layout(height=340, xaxis_tickangle=-30)
        st.plotly_chart(fig3, use_container_width=True)

    # ── Radar chart ───────────────────────────────────────────────────────────
    st.subheader("Team Profile Radar")
    st.caption("Normalised 0–10 across batting run rates and bowling economies.")

    radar_cols = {
        "bat_pp_rr": "PP Bat RR", "bat_md_rr": "Mid Bat RR", "bat_dt_rr": "Death Bat RR",
        "bowl_pp_econ": "PP Bowl Econ", "bowl_md_econ": "Mid Bowl Econ", "bowl_dt_econ": "Death Bowl Econ",
    }
    radar_df = df[["name"] + list(radar_cols.keys())].dropna(how="any")
    if not radar_df.empty:
        # Normalise each column to 0–10
        for col in radar_cols:
            mn, mx = radar_df[col].min(), radar_df[col].max()
            if mx > mn:
                if "econ" in col:
                    # Lower economy = better → invert
                    radar_df[col] = 10 - (radar_df[col] - mn) / (mx - mn) * 10
                else:
                    radar_df[col] = (radar_df[col] - mn) / (mx - mn) * 10

        sel_teams = st.multiselect(
            "Teams to compare",
            radar_df["name"].tolist(),
            default=radar_df["name"].tolist()[:4],
            key="radar_teams",
        )
        categories = list(radar_cols.values())

        fig4 = go.Figure()
        for _, row in radar_df[radar_df["name"].isin(sel_teams)].iterrows():
            vals = [row[c] for c in radar_cols] + [row[list(radar_cols.keys())[0]]]
            fig4.add_trace(go.Scatterpolar(
                r=vals,
                theta=categories + [categories[0]],
                fill="toself",
                name=row["name"],
                opacity=0.6,
            ))
        fig4.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            height=480,
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ── Data table ────────────────────────────────────────────────────────────
    st.subheader("Team Data")
    show = ["name", "group", "icc_ranking", "captain",
            "bat_pp_rr", "bat_dt_rr", "bowl_pp_econ", "bowl_dt_econ"]
    st.dataframe(df[[c for c in show if c in df.columns]], use_container_width=True, hide_index=True)
