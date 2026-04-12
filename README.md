# Leeds Health Inequalities — IMD 2019 Analysis

An analysis of deprivation patterns across Leeds using the English Index of Multiple Deprivation (IMD) 2019 — government data covering 32,844 Lower Super Output Areas (LSOAs) across England, filtered here to the 482 LSOAs that make up Leeds.

I built this because I wanted to understand how deprivation data is actually used in public health analysis. Leeds is a city I know well and it turns out to be a genuinely interesting case — significant pockets of severe deprivation sitting alongside much more affluent areas within a few miles of each other.

---

## What the data shows

**482 LSOAs in Leeds. 114 of them (23.7%) fall in the most deprived 10% nationally.**

That's a striking number. Nearly a quarter of Leeds neighbourhoods are among the most deprived in the entire country, not just in the region. The distribution is heavily skewed — far more LSOAs in decile 1 than any other, which you can see clearly in the bar chart.

The highest IMD score in Leeds is **78.6** (LSOA Leeds 086C). For context, the national average is around 21. The least deprived Leeds LSOA scores just 2.0, so there's an enormous range within a single city.

**What drives deprivation in Leeds?**

From the correlation analysis, income and employment are almost perfectly correlated with the overall IMD score (0.98 and 0.96 respectively). This is consistent with national patterns — deprivation is fundamentally an economic problem. Health deprivation correlates at 0.89, crime at 0.84. The outlier is Barriers to Housing and Services, which only correlates at 0.18 with the overall score — suggesting housing access is a more geographically even problem across Leeds.

---

## Project structure

```
├── 00_Main_Pipeline.ipynb          # runs everything in one go
├── 01_Data_Preparation.ipynb       # filter Leeds from national dataset, clean
├── 02_Exploratory_Analysis.ipynb   # summary stats, decile distribution, domain analysis
├── 04_Visualizations.ipynb         # bar charts, boxplots, correlation heatmap
├── 05_Statistical_Analysis.ipynb   # correlations, top 10 at-risk LSOAs, linear model
├── 06_Insights_Reporting.ipynb     # written insights and policy recommendations
├── 07_Advanced_Analysis.ipynb      # k-means clustering, comparison with Bradford/Wakefield
├── dashboard.py                    # Streamlit dashboard
├── output/                         # generated files (created when you run notebooks)
└── requirements.txt
```

Note on `03_Health_Outcomes.ipynb`: this notebook generates synthetic health indicators (obesity rate, diabetes rate, life expectancy etc.) simulated from deprivation scores. It's excluded here because simulated data doesn't belong in a public analysis — the relationships it shows are mathematically constructed rather than observed. The real IMD data itself includes a Health Deprivation and Disability domain which is a genuine observed measure.

---

## Key findings

**Deprivation is highly concentrated geographically.** The 114 decile-1 LSOAs are not spread evenly — they cluster in specific parts of Leeds (inner south, inner east), while outer areas of the city are substantially less deprived.

**Income and employment explain almost everything.** Correlations of 0.98 and 0.96 with the overall IMD score mean that the other domains — while important — add relatively little additional predictive power once you know the income deprivation rate.

**Children are disproportionately affected.** The Income Deprivation Affecting Children Index (IDACI) correlates at 0.92 with the overall IMD score, with a mean rate of 0.18 across Leeds — meaning 18% of children in the average Leeds LSOA live in income-deprived households.

**Leeds is more deprived than its neighbours.** The advanced analysis compares Leeds against Bradford, Wakefield, Kirklees, and Calderdale. Leeds has a higher mean IMD score than the regional average, driven by the concentration of decile-1 LSOAs in inner-city areas.

---

## How to run

```bash
git clone https://github.com/Rhiya22/leeds-health-inequalities.git
cd leeds-health-inequalities
pip install -r requirements.txt
```

Download the IMD 2019 dataset from [gov.uk](https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019) — specifically `File 7: All IoD2019 Scores, Ranks, Deciles and Population Denominators`. Place it in the same folder as the notebooks.

Then either run `00_Main_Pipeline.ipynb` to run everything at once, or run notebooks 01 through 07 in order.

To launch the dashboard (run the notebooks first to generate the output files):
```bash
streamlit run dashboard.py
```

---

## Stack

Python, pandas, numpy, scikit-learn, matplotlib, seaborn, plotly, streamlit

Data: [English Indices of Deprivation 2019](https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019) — Ministry of Housing, Communities & Local Government (Open Government Licence)
