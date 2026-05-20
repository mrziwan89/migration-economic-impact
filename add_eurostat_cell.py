"""
add_eurostat_cell.py
====================
Injects two cells into notebooks/test.ipynb:
  Cell A – Rebuilds eurostat_insights.csv from raw files (extends to 2025).
  Cell B – Updated Bubble Map visualization using the refreshed data.

Run from project root:
  python add_eurostat_cell.py
"""

import json

NOTEBOOK_PATH = "notebooks/test.ipynb"

# ── Cell A: Rebuild eurostat_insights.csv ─────────────────────────────────
REBUILD_CODE = """\
import pandas as pd
import os

# ── Paths (relative to notebooks/) ───────────────────────────────────────
RAW  = "../data/raw/eurostat_lfs"
OUT  = "../data/processed/eurostat_insights.csv"

EMPL_FILE = f"{RAW}/lfsa_ergaedn.csv"
TEMP_FILE = f"{RAW}/lfsa_etpgan.csv"
POV_FILE  = f"{RAW}/ilc_peps05.csv"

# ── Citizenship code → cohort label mappings ──────────────────────────────
EMPL_COH = {"EU27_2020_FOR": "EU_Migrant", "NEU27_2020_FOR": "Extra_EU_Migrant", "NAT": "Native"}
TEMP_COH = {"EU27_2020_FOR": "EU_Migrant", "NEU27_2020_FOR": "Extra_EU_Migrant", "NAT": "Native"}
POV_COH  = {"EU27_2020_FOR": "EU_Migrant", "NEU27_2020_FOR": "Extra_EU_Migrant", "NAT": "Native"}


def pivot_to_cohorts(df, year_col, geo_col, citizen_col, value_col, cohort_map, metric_name):
    df = df[df[citizen_col].isin(cohort_map.keys())].copy()
    df["Cohort"] = df[citizen_col].map(cohort_map)
    df = df.rename(columns={year_col: "Year", geo_col: "Country", value_col: "Value"})
    df = df[["Year", "Country", "Cohort", "Value"]].dropna(subset=["Value"])
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    pivoted = df.pivot_table(
        index=["Year", "Country"], columns="Cohort", values="Value", aggfunc="mean"
    ).reset_index()
    pivoted.columns.name = None

    for col in ["EU_Migrant", "Extra_EU_Migrant", "Native"]:
        if col not in pivoted.columns:
            pivoted[col] = float("nan")

    pivoted["Total_Migrant"] = pivoted[["EU_Migrant", "Extra_EU_Migrant"]].mean(axis=1)
    pivoted["Gap_ExtraEU_vs_Native_PP"]      = pivoted["Extra_EU_Migrant"] - pivoted["Native"]
    pivoted["Gap_EU_vs_Native_PP"]           = pivoted["EU_Migrant"]       - pivoted["Native"]
    pivoted["Ratio_TotalMigrant_vs_Native"]  = (
        pivoted["Total_Migrant"] / pivoted["Native"].replace(0, float("nan"))
    )
    pivoted["Metric"] = metric_name
    return pivoted[["Year","Country","Metric","EU_Migrant","Extra_EU_Migrant","Native",
                    "Total_Migrant","Gap_ExtraEU_vs_Native_PP","Gap_EU_vs_Native_PP",
                    "Ratio_TotalMigrant_vs_Native"]]


# ── 1. Employment (Highly Educated, ED5-8, age Y20-64 or Y15-64, sex T) ──
print("Processing employment …")
df_empl = pd.read_csv(EMPL_FILE, low_memory=False)
df_empl = df_empl[
    (df_empl["isced11"] == "ED5-8") &
    (df_empl["sex"] == "T") &
    (df_empl["age"].isin(["Y20-64", "Y15-64"])) &
    (df_empl["citizen"].isin(EMPL_COH))
]
empl_panel = pivot_to_cohorts(df_empl, "TIME_PERIOD", "geo", "citizen",
                               "OBS_VALUE", EMPL_COH, "Highly_Educated_Employment_Rate")
print(f"  → {len(empl_panel):,} rows  {int(empl_panel.Year.min())}–{int(empl_panel.Year.max())}")


# ── 2. Temporary Contracts (age Y15-64 or Y20-64, sex T) ─────────────────
print("Processing temporary contracts …")
df_temp = pd.read_csv(TEMP_FILE, low_memory=False)
df_temp = df_temp[
    (df_temp["sex"] == "T") &
    (df_temp["age"].isin(["Y15-64", "Y20-64"])) &
    (df_temp["citizen"].isin(TEMP_COH))
]
temp_panel = pivot_to_cohorts(df_temp, "TIME_PERIOD", "geo", "citizen",
                               "OBS_VALUE", TEMP_COH, "Temporary_Contract_Rate")
print(f"  → {len(temp_panel):,} rows  {int(temp_panel.Year.min())}–{int(temp_panel.Year.max())}")


# ── 3. Poverty (age Y18-64 or similar working-age, sex T) ────────────────
print("Processing poverty …")
df_pov = pd.read_csv(POV_FILE, low_memory=False)
df_pov = df_pov[
    (df_pov["sex"] == "T") &
    (df_pov["age"].isin(["Y18-64", "Y18-59", "Y20-64", "Y18-54", "Y_GE18"])) &
    (df_pov["citizen"].isin(POV_COH))
]
pov_panel = pivot_to_cohorts(df_pov, "TIME_PERIOD", "geo", "citizen",
                              "OBS_VALUE", POV_COH, "Poverty_Rate")
print(f"  → {len(pov_panel):,} rows  {int(pov_panel.Year.min())}–{int(pov_panel.Year.max())}")


# ── 4. Combine, filter to real ISO-2 country codes, save ─────────────────
import re
combined = pd.concat([empl_panel, temp_panel, pov_panel], ignore_index=True)
combined = combined[combined["Country"].str.match(r"^[A-Z]{2}$")]
combined = combined.sort_values(["Year", "Country", "Metric"]).reset_index(drop=True)
combined.to_csv(OUT, index=False)

print(f"\\n✅ Saved {len(combined):,} rows → {OUT}")
print("\\n📊 Year range per metric:")
for metric, grp in combined.groupby("Metric"):
    print(f"  {metric:<42} {int(grp.Year.min())}–{int(grp.Year.max())}")
"""

# ── Cell B: Updated Bubble Map ─────────────────────────────────────────────
BUBBLE_MAP_CODE = """\
import pandas as pd
import plotly.graph_objects as go
import json

# ── Config ────────────────────────────────────────────────────────────────
EU_ISO2_TO_ISO3 = {
    "AT":"AUT","BE":"BEL","BG":"BGR","CY":"CYP","CZ":"CZE",
    "DE":"DEU","DK":"DNK","EE":"EST","ES":"ESP","FI":"FIN",
    "FR":"FRA","GR":"GRC","EL":"GRC","HR":"HRV","HU":"HUN",
    "IE":"IRL","IT":"ITA","LT":"LTU","LU":"LUX","LV":"LVA",
    "MT":"MLT","NL":"NLD","PL":"POL","PT":"PRT","RO":"ROU",
    "SE":"SWE","SI":"SVN","SK":"SVK","UK":"GBR","NO":"NOR",
    "CH":"CHE","IS":"ISL","MK":"MKD","RS":"SRB","ME":"MNE",
    "AL":"ALB","TR":"TUR","BA":"BIH","XK":"XKX",
}

COUNTRY_COORDS = {
    "AUT":(47.8,13.3),"BEL":(50.8,4.4),"BGR":(42.7,25.5),
    "CYP":(35.1,33.4),"CZE":(49.8,15.5),"DEU":(51.2,10.4),
    "DNK":(56.3,9.5),"EST":(58.6,25.0),"ESP":(40.4,-3.7),
    "FIN":(61.9,25.7),"FRA":(46.2,2.2),"GRC":(39.1,21.8),
    "HRV":(45.1,15.2),"HUN":(47.2,19.5),"IRL":(53.4,-8.2),
    "ITA":(41.9,12.6),"LTU":(55.2,23.9),"LUX":(49.8,6.1),
    "LVA":(57.0,24.8),"MLT":(35.9,14.5),"NLD":(52.1,5.3),
    "POL":(51.9,19.1),"PRT":(39.4,-8.2),"ROU":(45.9,24.9),
    "SWE":(60.1,18.6),"SVN":(46.1,14.8),"SVK":(48.7,19.7),
    "GBR":(55.4,-3.4),"NOR":(60.5,8.5),"CHE":(46.8,8.2),
    "ISL":(65.0,-18.6),"MKD":(41.6,21.7),"SRB":(44.0,21.0),
    "MNE":(42.7,19.4),"ALB":(41.2,20.2),"TUR":(39.9,32.9),
    "BIH":(43.9,17.7),"XKX":(42.6,20.9),
}

# ── Load data ─────────────────────────────────────────────────────────────
df = pd.read_csv("../data/processed/eurostat_insights.csv")
df["ISO3"] = df["Country"].map(EU_ISO2_TO_ISO3)
df = df.dropna(subset=["ISO3"])

# Pivot: one row per (Year, Country) with all three metric gaps as columns
pivoted = df.pivot_table(
    index=["Year","ISO3","Country"],
    columns="Metric",
    values="Gap_ExtraEU_vs_Native_PP",
    aggfunc="mean"
).reset_index()
pivoted.columns.name = None

for col in ["Highly_Educated_Employment_Rate","Poverty_Rate","Temporary_Contract_Rate"]:
    if col not in pivoted.columns:
        pivoted[col] = float("nan")

pivoted["lat"] = pivoted["ISO3"].map(lambda x: COUNTRY_COORDS.get(x,(None,None))[0])
pivoted["lon"] = pivoted["ISO3"].map(lambda x: COUNTRY_COORDS.get(x,(None,None))[1])
pivoted = pivoted.dropna(subset=["lat","lon"])

# ── Build animation ───────────────────────────────────────────────────────
START_YEAR = 2005
years = sorted(pivoted["Year"].unique())
years = [y for y in years if y >= START_YEAR]

# Global scale anchors
max_temp = pivoted["Temporary_Contract_Rate"].abs().quantile(0.95)
min_pov  = pivoted["Poverty_Rate"].min(skipna=True)
max_pov  = pivoted["Poverty_Rate"].max(skipna=True)

def make_trace(sub):
    temp_gap = sub["Temporary_Contract_Rate"].fillna(0)
    pov_gap  = sub["Poverty_Rate"]
    empl_gap = sub["Highly_Educated_Employment_Rate"]

    # Size ∝ absolute temp contract gap
    sizes = (temp_gap.abs() / max_temp * 35 + 4).clip(lower=4, upper=45)

    # IMPROVED VISIBILITY: Don't make bubbles transparent after 2020.
    # Use 0.9 for full data, 0.6 for years missing poverty (color) data.
    opacity = pov_gap.notna().map({True: 0.9, False: 0.6})

    customdata = list(zip(
        sub["Country"],
        empl_gap.round(1).fillna("N/A"),
        pov_gap.round(1).fillna("Data Lags (Post-2020)"),
        temp_gap.round(1),
    ))

    return go.Scattergeo(
        lat=sub["lat"],
        lon=sub["lon"],
        mode="markers",
        marker=dict(
            size=sizes,
            color=pov_gap,
            colorscale="Reds",
            cmin=min_pov,
            cmax=max_pov,
            colorbar=dict(title="Poverty Gap (PP)", x=1.02),
            opacity=opacity.values,
            line=dict(width=1, color="rgba(255,255,255,0.6)"),
        ),
        customdata=customdata,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Employment Gap (Educated): <b>%{customdata[1]}pp</b><br>"
            "Poverty Gap (Migrant Risk): <b>%{customdata[2]}pp</b><br>"
            "Temp Contract Gap:          <b>%{customdata[3]}pp</b><br>"
            "<extra></extra>"
        ),
        showlegend=False,
    )

frames = [
    go.Frame(data=[make_trace(pivoted[pivoted["Year"] == y])], name=str(y))
    for y in years
]

first_trace = make_trace(pivoted[pivoted["Year"] == years[0]])

fig = go.Figure(
    data=[first_trace],
    frames=frames,
    layout=go.Layout(
        title=dict(
            text="<b>The Triad of Brain Waste</b> (2005–2023)  ·  Extra-EU Migrants vs. Natives<br>"
                 "<sup>Bubble size = Contract Inequality  ·  Colour = Poverty Gap  ·  Hover = Employment Gap</sup>",
            x=0.5, xanchor="center",
        ),
        geo=dict(
            scope="europe",
            projection_type="natural earth",
            showland=True, landcolor="#1c1e26",
            showocean=True, oceancolor="#0d1117",
            showcountries=True, countrycolor="#3a3d4d",
            showcoastlines=True, coastlinecolor="#3a3d4d",
            showframe=False,
            bgcolor="#0d1117",
        ),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#e0e0e0", family="Inter, sans-serif"),
        height=700,
        margin=dict(r=0, t=100, l=0, b=0),
        updatemenus=[dict(
            type="buttons", showactive=False,
            x=0.1, xanchor="right", y=0, yanchor="top",
            pad={"r":10,"t":70},
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, {"frame":{"duration":800,"redraw":True},
                                  "fromcurrent":True,"transition":{"duration":500}}]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], {"frame":{"duration":0,"redraw":False},
                                    "mode":"immediate","transition":{"duration":0}}]),
            ],
        )],
        sliders=[dict(
            active=0,
            steps=[dict(args=[[str(y)],{"frame":{"duration":800,"redraw":True},
                                         "mode":"immediate",
                                         "transition":{"duration":400}}],
                        label=str(y), method="animate")
                   for y in years],
            x=0.1, xanchor="left",
            y=0, yanchor="top",
            len=0.9,
            currentvalue=dict(prefix="Year: ", font=dict(size=14, color="#e0e0e0")),
            pad={"b":10,"t":50},
            font=dict(color="#e0e0e0"),
        )],
        annotations=[
            dict(
                x=0.5, y=-0.04, xref="paper", yref="paper",
                text="ℹ️ Employment/Contract data available to 2023. Poverty color data unavailable after 2020.",
                font=dict(size=10, color="#888888"),
                showarrow=False, align="center",
            )
        ],
    ),
)

fig.show()
"""


# ── Inject cells into notebook ─────────────────────────────────────────────
def make_cell(code, cell_id):
    lines = code.split("\n")
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id,
        "metadata": {},
        "outputs": [],
        "source": [ln + "\n" if i < len(lines) - 1 else ln for i, ln in enumerate(lines)],
    }


with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Remove any old cells with the same IDs to avoid duplicates
nb["cells"] = [c for c in nb["cells"] if c.get("id") not in ("rebuild_eurostat", "bubble_map_v2")]

nb["cells"].append(make_cell(REBUILD_CODE, "rebuild_eurostat"))
nb["cells"].append(make_cell(BUBBLE_MAP_CODE, "bubble_map_v2"))

with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("✅ Two cells injected into notebooks/test.ipynb:")
print("  [rebuild_eurostat] – rebuilds eurostat_insights.csv from raw files")
print("  [bubble_map_v2]    – updated dark-theme animated bubble map (2005–2025)")
