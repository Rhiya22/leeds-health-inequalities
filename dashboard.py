"""
dashboard.py
────────────
Streamlit dashboard for Leeds Health Inequalities analysis.
 
Run with:
    streamlit run dashboard.py
 
If the processed output/ files from the notebooks aren't present yet
(e.g. a fresh deployment), this generates output/Leeds_IMD_LSOA.csv
itself from the raw national IMD file - the same filtering and cleaning
steps as 01_Data_Preparation.ipynb - so the dashboard is self-contained
and doesn't require running the notebooks first.
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
 
RAW_IMD_FILE = "File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv"
LOCAL_AUTHORITY = "Leeds"
OUTPUT_FOLDER = "output"
BASE_FILE = os.path.join(OUTPUT_FOLDER, "Leeds_IMD_LSOA.csv")
HEALTH_FILE = os.path.join(OUTPUT_FOLDER, "Leeds_IMD_with_Health.csv")
 
 
def _generate_base_csv():
    """Filter the raw national IMD file down to Leeds, mirroring the exact
    cleaning steps in 01_Data_Preparation.ipynb, and save the result.
 
    Runs in a couple of seconds (32,844 rows -> 482), so this is cheap
    enough to do on every fresh deployment rather than requiring the
    notebooks to be run manually first.
    """
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
 
    encodings = ["utf-8", "latin-1", "cp1252"]
    df = None
    for encoding in encodings:
        try:
            df = pd.read_csv(RAW_IMD_FILE, encoding=encoding, low_memory=False)
            break
        except (UnicodeDecodeError, FileNotFoundError):
            continue
 
    if df is None:
        raise FileNotFoundError(
            f"{RAW_IMD_FILE} not found. The dashboard generates its data from "
            "this raw file on first run, but it needs to be committed to the "
            "repo (see README) since it's sourced from gov.uk, not fetched "
            "automatically."
        )
 
    possible_la_names = [
        "Local Authority District name (2019)",
        "Local Authority District (2019)",
        "Local Authority",
        "LA name",
        "LAD19NM",
    ]
    la_col = next((name for name in possible_la_names if name in df.columns), None)
    if la_col is None:
        raise ValueError("Could not find a Local Authority column in the raw IMD file.")
 
    leeds_df = df[df[la_col].str.contains(LOCAL_AUTHORITY, case=False, na=False)].copy()
    leeds_df = leeds_df.dropna(how="all").drop_duplicates()
 
    numeric_patterns = ["Score", "Rank", "Decile", "Population", "Count", "Rate", "Percent"]
    for col in leeds_df.columns:
        col_lower = col.lower()
        if any(p.lower() in col_lower for p in numeric_patterns):
            if "code" not in col_lower and "name" not in col_lower:
                leeds_df[col] = pd.to_numeric(leeds_df[col], errors="coerce")
 
    leeds_df.to_csv(BASE_FILE, index=False)
    return leeds_df
 
 
@st.cache_data
def load_data():
    if not os.path.exists(HEALTH_FILE) and not os.path.exists(BASE_FILE):
        with st.spinner("First-time setup: preparing the Leeds dataset..."):
            try:
                _generate_base_csv()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Automatic data preparation failed: {exc}")
                st.stop()
 
    if os.path.exists(HEALTH_FILE):
        return pd.read_csv(HEALTH_FILE)
    elif os.path.exists(BASE_FILE):
        return pd.read_csv(BASE_FILE)
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
 
