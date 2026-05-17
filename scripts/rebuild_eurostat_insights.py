"""
rebuild_eurostat_insights.py
============================
Rebuilds data/processed/eurostat_insights.csv directly from the three raw
Eurostat files:
  - lfsa_ergaedn.csv  → Highly-Educated Employment Rate   (up to 2025)
  - lfsa_etpgan.csv   → Temporary Contract Rate           (up to 2025)
  - ilc_peps05.csv    → Poverty Rate (at-risk-of-poverty) (up to 2020)

Output schema (same as existing eurostat_insights.csv):
  Year, Country, Metric, EU_Migrant, Extra_EU_Migrant, Native,
  Total_Migrant, Gap_ExtraEU_vs_Native_PP, Gap_EU_vs_Native_PP,
  Ratio_TotalMigrant_vs_Native

Run from project root:
  python scripts/rebuild_eurostat_insights.py
"""

import pandas as pd
import os

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "data", "raw", "eurostat_lfs")
OUT  = os.path.join(ROOT, "data", "processed", "eurostat_insights.csv")

EMPL_FILE   = os.path.join(RAW, "lfsa_ergaedn.csv")
TEMP_FILE   = os.path.join(RAW, "lfsa_etpgan.csv")
POV_FILE    = os.path.join(RAW, "ilc_peps05.csv")

# ── Cohort / citizenship codes of interest ─────────────────────────────────
# For employment (lfsa_ergaedn): citizen column
EMPL_COH = {
    "EU27_2020_FOR" : "EU_Migrant",       # EU-born foreigner
    "NEU27_2020_FOR": "Extra_EU_Migrant", # Non-EU foreigner
    "NAT"           : "Native",
}

# For temp contracts (lfsa_etpgan): citizen column
TEMP_COH = {
    "EU27_2020_FOR" : "EU_Migrant",
    "NEU27_2020_FOR": "Extra_EU_Migrant",
    "NAT"           : "Native",
}

# For poverty (ilc_peps05): citizen column
POV_COH = {
    "EU27_2020_FOR" : "EU_Migrant",
    "NEU27_2020_FOR": "Extra_EU_Migrant",
    "NAT"           : "Native",
}


def pivot_to_cohorts(df, year_col, geo_col, citizen_col, value_col, cohort_map, metric_name):
    """
    Generic helper: filters to the target citizenship codes, pivots so
    each cohort becomes a column, then computes gap metrics.
    Returns a DataFrame in the eurostat_insights schema.
    """
    # Keep only desired cohorts
    df = df[df[citizen_col].isin(cohort_map.keys())].copy()
    df["Cohort"] = df[citizen_col].map(cohort_map)
    df = df.rename(columns={year_col: "Year", geo_col: "Country", value_col: "Value"})
    df = df[["Year", "Country", "Cohort", "Value"]].dropna(subset=["Value"])
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    # Pivot: one row per (Year, Country), one column per cohort
    pivoted = df.pivot_table(
        index=["Year", "Country"],
        columns="Cohort",
        values="Value",
        aggfunc="mean",  # mean across sex/age subgroups
    ).reset_index()
    pivoted.columns.name = None

    # Ensure all cohort columns exist
    for col in ["EU_Migrant", "Extra_EU_Migrant", "Native"]:
        if col not in pivoted.columns:
            pivoted[col] = float("nan")

    # Compute Total_Migrant as simple average of the two migrant groups
    pivoted["Total_Migrant"] = pivoted[["EU_Migrant", "Extra_EU_Migrant"]].mean(axis=1)

    # Gap metrics (percentage-point differences)
    pivoted["Gap_ExtraEU_vs_Native_PP"]  = pivoted["Extra_EU_Migrant"] - pivoted["Native"]
    pivoted["Gap_EU_vs_Native_PP"]       = pivoted["EU_Migrant"]       - pivoted["Native"]
    pivoted["Ratio_TotalMigrant_vs_Native"] = (
        pivoted["Total_Migrant"] / pivoted["Native"].replace(0, float("nan"))
    )

    pivoted["Metric"] = metric_name
    return pivoted[
        ["Year", "Country", "Metric",
         "EU_Migrant", "Extra_EU_Migrant", "Native", "Total_Migrant",
         "Gap_ExtraEU_vs_Native_PP", "Gap_EU_vs_Native_PP",
         "Ratio_TotalMigrant_vs_Native"]
    ]


# ── 1. Employment Rate for Highly-Educated ─────────────────────────────────
print("Processing employment data (lfsa_ergaedn) …")
df_empl = pd.read_csv(EMPL_FILE, low_memory=False)
# Keep only highly-educated (ED5-8 = tertiary) and working-age (Y20-64 or Y15-64),
# total sex, target citizenship codes
df_empl = df_empl[
    (df_empl["isced11"] == "ED5-8") &
    (df_empl["sex"]     == "T") &
    (df_empl["age"].isin(["Y20-64", "Y15-64"])) &
    (df_empl["citizen"].isin(EMPL_COH.keys()))
].copy()
empl_panel = pivot_to_cohorts(
    df_empl, "TIME_PERIOD", "geo", "citizen", "OBS_VALUE",
    EMPL_COH, "Highly_Educated_Employment_Rate"
)
print(f"  → {len(empl_panel):,} rows, years {empl_panel['Year'].min()}–{empl_panel['Year'].max()}")


# ── 2. Temporary Contract Rate ─────────────────────────────────────────────
print("Processing temporary contract data (lfsa_etpgan) …")
df_temp = pd.read_csv(TEMP_FILE, low_memory=False)
# Keep working-age (Y15-64 or Y20-64), total sex, target cohorts
df_temp = df_temp[
    (df_temp["sex"].isin(["T"])) &
    (df_temp["age"].isin(["Y15-64", "Y20-64"])) &
    (df_temp["citizen"].isin(TEMP_COH.keys()))
].copy()
temp_panel = pivot_to_cohorts(
    df_temp, "TIME_PERIOD", "geo", "citizen", "OBS_VALUE",
    TEMP_COH, "Temporary_Contract_Rate"
)
print(f"  → {len(temp_panel):,} rows, years {temp_panel['Year'].min()}–{temp_panel['Year'].max()}")


# ── 3. Poverty / At-Risk-of-Poverty Rate ──────────────────────────────────
print("Processing poverty data (ilc_peps05) …")
df_pov = pd.read_csv(POV_FILE, low_memory=False)
# Keep working-age (Y18-64 or Y18-59 or Y20-64), total sex, target cohorts
df_pov = df_pov[
    (df_pov["sex"].isin(["T"])) &
    (df_pov["age"].isin(["Y18-64", "Y18-59", "Y20-64", "Y18-54", "Y_GE18"])) &
    (df_pov["citizen"].isin(POV_COH.keys()))
].copy()
pov_panel = pivot_to_cohorts(
    df_pov, "TIME_PERIOD", "geo", "citizen", "OBS_VALUE",
    POV_COH, "Poverty_Rate"
)
print(f"  → {len(pov_panel):,} rows, years {pov_panel['Year'].min()}–{pov_panel['Year'].max()}")


# ── 4. Combine and save ────────────────────────────────────────────────────
print("Combining and saving …")
combined = pd.concat([empl_panel, temp_panel, pov_panel], ignore_index=True)

# Remove aggregate geo codes (EU, EA, etc.) — keep ISO-2 country codes only
# Real country codes are exactly 2 uppercase letters
import re
combined = combined[combined["Country"].str.match(r"^[A-Z]{2}$")]

combined = combined.sort_values(["Year", "Country", "Metric"]).reset_index(drop=True)
combined.to_csv(OUT, index=False)
print(f"\n✅ Saved {len(combined):,} rows → {OUT}")

# Summary
print("\n📊 Year range per metric:")
for metric, grp in combined.groupby("Metric"):
    print(f"  {metric:<40} {int(grp['Year'].min())}–{int(grp['Year'].max())}")

print("\n📊 Countries included:", sorted(combined["Country"].unique()))
