"""Predictions page — win probability distribution, runs estimates, match table."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def render(df: pd.DataFrame) -> None:
    st.header("Prediction Summary")

    if df.empty:
        st.warning("No predictions found in matches/ directory.")
        return

    # ── Date filter ───────────────────────────────────────────────────────────
    dated = df.dropna(subset=["date"])
    has_dates = not dated.empty

    if has_dates:
        min_date = dated["date"].min().date()
        max_date = dated["date"].max().date()

        fc1, fc2 = st.columns(2)
        date_from = fc1.date_input("From", value=min_date, min_value=min_date,
                                   max_value=max_date, key="pred_date_from")
        date_to   = fc2.date_input("To",   value=max_date, min_value=min_date,
                                   max_value=max_date, key="pred_date_to")

        if date_from > date_to:
            st.error("'From' date must be on or before 'To' date.")
            return

        mask = (
            df["date"].isna() |
            ((df["date"].dt.date >= date_from) & (df["date"].dt.date <= date_to))
        )
        df = df[mask]

        undated = df["date"].isna().sum()
        if undated:
            st.caption(f"{undated} prediction(s) have no match date and are always included.")

    # ── KPI strip ─────────────────────────────────────────────────────────────
    total = df["match_id"].nunique()
    avg_wp = df["win_probability"].mean()
    above_50 = (df["win_probability"] > 0.5).sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Predictions", total)
    col2.metric("Avg Win Probability", f"{avg_wp:.0%}" if pd.notna(avg_wp) else "N/A")
    col3.metric("Favoured to Win", above_50)
    col4.metric("Opponents Covered", df["opponent"].nunique())

    st.divider()

    # ── Win probability by opponent ───────────────────────────────────────────
    st.subheader("Win Probability by Opponent")

    situation_filter = st.radio(
        "Scenario", ["All", "Batting First", "Chasing", "Single"],
        horizontal=True, key="pred_sit"
    )
    filtered = df if situation_filter == "All" else df[df["situation"] == situation_filter]

    if not filtered.empty:
        opp_avg = (
            filtered.groupby("opponent")["win_probability"]
            .mean()
            .reset_index()
            .sort_values("win_probability", ascending=True)
        )
        opp_avg["win_pct"] = (opp_avg["win_probability"] * 100).round(1)
        opp_avg["color"] = opp_avg["win_probability"].apply(
            lambda x: "#2ecc71" if x >= 0.5 else "#e74c3c"
        )

        fig = px.bar(
            opp_avg,
            x="win_pct",
            y="opponent",
            orientation="h",
            color="win_pct",
            color_continuous_scale=["#e74c3c", "#f39c12", "#2ecc71"],
            range_color=[0, 100],
            labels={"win_pct": "Win Probability (%)", "opponent": ""},
            text="win_pct",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.add_vline(x=50, line_dash="dash", line_color="gray", annotation_text="50%")
        fig.update_layout(height=max(300, len(opp_avg) * 35), showlegend=False,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── Win probability distribution ──────────────────────────────────────────
    st.subheader("Win Probability Distribution")
    fig2 = px.histogram(
        filtered.dropna(subset=["win_probability"]),
        x="win_pct",
        nbins=20,
        color="situation",
        barmode="overlay",
        opacity=0.7,
        labels={"win_pct": "Win Probability (%)", "count": "Predictions"},
    )
    fig2.add_vline(x=50, line_dash="dash", line_color="gray")
    fig2.update_layout(height=300)
    st.plotly_chart(fig2, use_container_width=True)

    # ── Runs estimate ranges ──────────────────────────────────────────────────
    st.subheader("Runs Estimate by Opponent")
    runs_df = df[df["situation"].isin(["Batting First", "Single"])].dropna(
        subset=["runs_adjusted"]
    )
    if not runs_df.empty:
        runs_agg = (
            runs_df.groupby("opponent")
            .agg(
                runs_avg=("runs_adjusted", "mean"),
                runs_lower=("runs_lower", "mean"),
                runs_upper=("runs_upper", "mean"),
            )
            .reset_index()
            .sort_values("runs_avg", ascending=False)
        )

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=runs_agg["opponent"],
            y=runs_agg["runs_avg"],
            name="Adjusted Estimate",
            marker_color="#3498db",
            error_y=dict(
                type="data",
                symmetric=False,
                array=(runs_agg["runs_upper"] - runs_agg["runs_avg"]).fillna(0),
                arrayminus=(runs_agg["runs_avg"] - runs_agg["runs_lower"]).fillna(0),
            ),
        ))
        fig3.update_layout(height=320, xaxis_title="", yaxis_title="Projected Runs")
        st.plotly_chart(fig3, use_container_width=True)

    # ── XI frequency ─────────────────────────────────────────────────────────
    st.subheader("Most-Selected Players (XI Frequency)")
    from wt20_oracle.dashboard.loaders import load_xi_frequency
    xi_df = load_xi_frequency()
    if not xi_df.empty:
        top20 = xi_df.head(20)
        fig4 = px.bar(
            top20, x="xi_count", y="player_id", orientation="h",
            labels={"xi_count": "Times in Predicted XI", "player_id": ""},
            color="xi_count", color_continuous_scale="Blues",
        )
        fig4.update_layout(height=max(300, len(top20) * 28),
                           coloraxis_showscale=False, yaxis={"autorange": "reversed"})
        st.plotly_chart(fig4, use_container_width=True)

    # ── Full predictions table ────────────────────────────────────────────────
    st.subheader("All Predictions")
    show_cols = ["match_id", "opponent", "venue", "situation", "win_pct",
                 "pr_runs_batting_team", "pr_runs_chasing_team",
                 "runs_adjusted", "pitch_difficulty", "date"]
    display = df[[c for c in show_cols if c in df.columns]].copy()
    if "date" in display.columns:
        display["date"] = display["date"].dt.strftime("%Y-%m-%d").fillna("")
    st.dataframe(display, use_container_width=True, hide_index=True)
