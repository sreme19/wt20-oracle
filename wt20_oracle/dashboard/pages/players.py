"""Players page — strike rate vs economy scatter, phase heatmap, fitness."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def render(df: pd.DataFrame) -> None:
    st.header("Player Statistics Explorer")

    if df.empty:
        st.warning("No player data found.")
        return

    # ── Sidebar filters ───────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    teams = sorted(df["team"].unique())
    sel_team = col1.multiselect("Team", teams, default=teams, key="pl_team")
    roles = sorted(df["role"].dropna().unique())
    sel_role = col2.multiselect("Role", roles, default=roles, key="pl_role")
    fitness_opts = sorted(df["fitness_status"].dropna().unique())
    sel_fit = col3.multiselect("Fitness", fitness_opts, default=fitness_opts, key="pl_fit")

    filtered = df[
        df["team"].isin(sel_team) &
        df["role"].isin(sel_role) &
        df["fitness_status"].isin(sel_fit)
    ]

    st.caption(f"{len(filtered)} players shown")
    st.divider()

    # ── Strike rate vs economy scatter ────────────────────────────────────────
    st.subheader("Batting Strike Rate vs Bowling Economy")
    st.caption("All-rounders appear in both dimensions. Ideal: high SR, low economy.")

    scatter_df = filtered.dropna(subset=["bat_sr", "bowl_economy"])
    if not scatter_df.empty:
        fig = px.scatter(
            scatter_df,
            x="bat_sr",
            y="bowl_economy",
            color="team_display",
            symbol="role_display",
            size="caps",
            size_max=20,
            hover_name="name",
            hover_data={"team_display": True, "role_display": True,
                        "bat_sr": ":.1f", "bowl_economy": ":.2f", "caps": True},
            labels={"bat_sr": "Batting Strike Rate", "bowl_economy": "Bowling Economy",
                    "team_display": "Team", "role_display": "Role"},
        )
        fig.add_hline(y=scatter_df["bowl_economy"].median(),
                      line_dash="dot", line_color="gray", annotation_text="median econ")
        fig.add_vline(x=scatter_df["bat_sr"].median(),
                      line_dash="dot", line_color="gray", annotation_text="median SR")
        fig.update_layout(height=480)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data with both batting SR and bowling economy.")

    # ── Phase performance heatmap ─────────────────────────────────────────────
    st.subheader("Batting Phase Strike Rate Heatmap")
    phase_df = filtered[["name", "team_display", "bat_pp_sr", "bat_md_sr", "bat_dt_sr"]].dropna(
        subset=["bat_pp_sr", "bat_md_sr", "bat_dt_sr"], how="all"
    )
    if not phase_df.empty:
        team_opt = st.selectbox(
            "Focus team", ["All"] + sorted(phase_df["team_display"].unique()), key="ph_team"
        )
        if team_opt != "All":
            phase_df = phase_df[phase_df["team_display"] == team_opt]

        phase_df = phase_df.set_index("name")[["bat_pp_sr", "bat_md_sr", "bat_dt_sr"]].fillna(0)
        phase_df.columns = ["Powerplay SR", "Middle SR", "Death SR"]

        fig2 = px.imshow(
            phase_df.T,
            color_continuous_scale="RdYlGn",
            aspect="auto",
            labels={"color": "Strike Rate"},
        )
        fig2.update_layout(height=200, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Bowling economy heatmap ───────────────────────────────────────────────
    st.subheader("Bowling Economy by Phase")
    bowl_df = filtered[["name", "team_display", "bowl_pp_econ", "bowl_md_econ", "bowl_dt_econ"]].dropna(
        subset=["bowl_pp_econ", "bowl_md_econ", "bowl_dt_econ"], how="all"
    )
    if not bowl_df.empty:
        team_opt2 = st.selectbox(
            "Focus team", ["All"] + sorted(bowl_df["team_display"].unique()), key="bwl_team"
        )
        if team_opt2 != "All":
            bowl_df = bowl_df[bowl_df["team_display"] == team_opt2]

        bowl_mat = bowl_df.set_index("name")[["bowl_pp_econ", "bowl_md_econ", "bowl_dt_econ"]].fillna(0)
        bowl_mat.columns = ["PP Economy", "Middle Economy", "Death Economy"]

        fig3 = px.imshow(
            bowl_mat.T,
            color_continuous_scale="RdYlGn_r",  # reversed: low econ = green
            aspect="auto",
            labels={"color": "Economy"},
        )
        fig3.update_layout(height=200, xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)

    # ── Fitness status ────────────────────────────────────────────────────────
    st.subheader("Fitness Status by Team")
    fit_counts = (
        filtered.groupby(["team_display", "fitness_status"])
        .size()
        .reset_index(name="count")
    )
    if not fit_counts.empty:
        color_map = {"fit": "#2ecc71", "injured": "#e74c3c",
                     "doubtful": "#f39c12", "unknown": "#95a5a6"}
        fig4 = px.bar(
            fit_counts,
            x="team_display",
            y="count",
            color="fitness_status",
            color_discrete_map=color_map,
            labels={"team_display": "", "count": "Players", "fitness_status": "Status"},
            barmode="stack",
        )
        fig4.update_layout(height=320, xaxis_tickangle=-30)
        st.plotly_chart(fig4, use_container_width=True)

    # ── Full player table ─────────────────────────────────────────────────────
    st.subheader("Player Data Table")
    show_cols = ["name", "team_display", "role_display", "caps",
                 "bat_sr", "bat_average", "bat_runs",
                 "bowl_economy", "bowl_wickets", "fitness_status"]
    tbl = filtered[[c for c in show_cols if c in filtered.columns]].rename(columns={
        "team_display": "team", "role_display": "role",
        "bat_sr": "SR", "bat_average": "avg", "bat_runs": "runs",
        "bowl_economy": "econ", "bowl_wickets": "wkts",
    })
    st.dataframe(tbl, use_container_width=True, hide_index=True)
