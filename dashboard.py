"""
dashboard.py
────────────
Streamlit dashboard for Leeds Health Inequalities analysis.

Run with:
    streamlit run dashboard.py

Requires the analysis notebooks to have been run first so the
output/ folder exists with the processed data files.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Leeds Health Inequalities",
    layout="wide",
)

st.title("Leeds Health Inequalities Dashboard")
st.markdown("Analysis of deprivation patterns across 482 Lower Super Output Areas in Leeds — using the English Index of Multiple Deprivation (IMD) 2019.")


@st.cache_data
def load_data():
    health_file = os.path.join("output", "Leeds_IMD_with_Health.csv")
    base_file   = os.path.join("output", "Leeds_IMD_LSOA.csv")

    if os.path.exists(health_file):
        return pd.read_csv(health_file)
    elif os.path.exists(base_file):
        return pd.read_csv(base_file)
    return None


df = load_data()

if df is None:
    st.error("No data found. Run the analysis notebooks first (start with 01_Data_Preparation.ipynb).")
    st.stop()

# ── Column detection ──────────────────────────────────────────────────────────
imd_score_col  = next((c for c in df.columns if 'imd' in c.lower() and 'score' in c.lower()), None)
imd_decile_col = next((c for c in df.columns if 'decile' in c.lower() and 'imd' in c.lower()), None)
lsoa_name_col  = next((c for c in df.columns if 'name' in c.lower() and 'lsoa' in c.lower()), None)

health_cols = [c for c in df.columns if any(t in c.lower() for t in
               ['obesity', 'diabetes', 'life_expectancy', 'smoking',
                'mental_health', 'physical_activity', 'hospital'])]

domain_score_cols = [c for c in df.columns
                     if 'score' in c.lower()
                     and any(d in c.lower() for d in
                             ['income', 'employment', 'education',
                              'health deprivation', 'crime', 'housing', 'environment'])
                     and 'imd' not in c.lower()]

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("Filters")

if imd_decile_col:
    all_deciles = sorted(df[imd_decile_col].dropna().unique().astype(int))
    selected = st.sidebar.multiselect(
        "IMD Decile (1 = most deprived, 10 = least deprived)",
        options=all_deciles,
        default=all_deciles,
    )
    df_filtered = df[df[imd_decile_col].isin(selected)]
else:
    df_filtered = df

# ── Summary metrics ───────────────────────────────────────────────────────────
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

col1.metric("LSOAs selected", f"{len(df_filtered):,}")

if imd_score_col:
    col2.metric("Mean IMD Score", f"{df_filtered[imd_score_col].mean():.1f}")
    col3.metric("Highest IMD Score", f"{df_filtered[imd_score_col].max():.1f}")

if imd_decile_col:
    pct_deprived = (df_filtered[imd_decile_col] <= 2).mean() * 100
    col4.metric("In most deprived 20%", f"{pct_deprived:.1f}%")

# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Deprivation Distribution")

left, right = st.columns(2)

with left:
    if imd_decile_col:
        decile_counts = df_filtered[imd_decile_col].value_counts().sort_index()
        fig = px.bar(
            x=decile_counts.index,
            y=decile_counts.values,
            color=decile_counts.index,
            color_continuous_scale="RdYlGn_r",
            labels={"x": "IMD Decile", "y": "Number of LSOAs", "color": "Decile"},
            title="LSOAs by IMD Decile",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with right:
    if imd_score_col:
        fig = px.histogram(
            df_filtered, x=imd_score_col, nbins=30,
            color_discrete_sequence=["#4C72B0"],
            labels={imd_score_col: "IMD Score"},
            title="Distribution of IMD Scores",
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Domain analysis ───────────────────────────────────────────────────────────
if domain_score_cols:
    st.markdown("---")
    st.subheader("Deprivation Domains")

    domain_means = df_filtered[domain_score_cols].mean().sort_values(ascending=True)
    short_names  = [c.replace(" Score (rate)", "").replace(" Score", "")
                    .replace("Income Deprivation Affecting ", "").replace(" Index (IDACI)", "")
                    for c in domain_means.index]

    fig = px.bar(
        x=domain_means.values,
        y=short_names,
        orientation="h",
        color=domain_means.values,
        color_continuous_scale="Reds",
        labels={"x": "Mean Score", "y": "Domain"},
        title="Mean Score by Deprivation Domain (higher = more deprived)",
    )
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

# ── Health indicators ─────────────────────────────────────────────────────────
if health_cols and imd_score_col:
    st.markdown("---")
    st.subheader("Deprivation vs Health Outcomes")
    st.caption("Note: health indicators are simulated from deprivation scores to illustrate expected relationships. They are not real observed health data.")

    selected_health = st.selectbox("Select health indicator", health_cols)

    fig = px.scatter(
        df_filtered,
        x=imd_score_col,
        y=selected_health,
        color=imd_decile_col if imd_decile_col else None,
        color_continuous_scale="RdYlGn_r",
        opacity=0.6,
        labels={imd_score_col: "IMD Score", selected_health: selected_health.replace("_", " ")},
        title=f"IMD Score vs {selected_health.replace('_', ' ')}",
        hover_data=[lsoa_name_col] if lsoa_name_col else None,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── At-risk LSOAs ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Most Deprived LSOAs")

if imd_score_col:
    display_cols = [c for c in [lsoa_name_col, imd_score_col, imd_decile_col] + health_cols[:3]
                    if c and c in df_filtered.columns]
    top10 = df_filtered.nlargest(10, imd_score_col)[display_cols]
    st.dataframe(top10.reset_index(drop=True), use_container_width=True)

# ── Full data table ───────────────────────────────────────────────────────────
with st.expander("View full dataset"):
    st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)

st.markdown("---")
st.caption("Data: English Index of Multiple Deprivation 2019 — Ministry of Housing, Communities & Local Government")
