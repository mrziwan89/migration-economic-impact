"""
patch_cell30_incarceration.py
Replaces Cell 30's source in test.ipynb with an updated version that also
processes incarceration data and appends it to eurostat_insights.csv.

Run with:  /usr/bin/python3 scripts/patch_cell30_incarceration.py
"""
import json
import pathlib

NB_PATH = pathlib.Path(__file__).parent.parent / "notebooks" / "test.ipynb"

NEW_SOURCE = """\
import pandas as pd
import os

# ─── Paths ───────────────────────────────────────────────────────────────────
RAW  = "../data/raw/eurostat_lfs"
OUT  = "../data/processed/eurostat_insights.csv"

EMPL_FILE  = f"{RAW}/lfsa_ergaedn.csv"
TEMP_FILE  = f"{RAW}/lfsa_etpgan.csv"
POV_OLD    = f"{RAW}/ilc_peps05.csv"
POV_NEW    = f"{RAW}/estat_ilc_peps05n_en.csv"
PRIS_FILE  = f"{RAW}/crim_pris_ctz.csv"

# ─── Citizenship mapping (LFS pillars) ──────────────────────────────────────
COH_MAP = {"EU27_2020_FOR": "EU_Migrant", "NEU27_2020_FOR": "Extra_EU_Migrant", "NAT": "Native"}

def pivot_to_cohorts(df, year_col, geo_col, citizen_col, value_col, metric_name):
    df = df[df[citizen_col].isin(COH_MAP.keys())].copy()
    df["Cohort"] = df[citizen_col].map(COH_MAP)
    df = df.rename(columns={year_col: "Year", geo_col: "Country", value_col: "Value"})
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    pivoted = df.pivot_table(
        index=["Year", "Country"], columns="Cohort", values="Value", aggfunc="mean"
    ).reset_index()

    for col in ["EU_Migrant", "Extra_EU_Migrant", "Native"]:
        if col not in pivoted.columns:
            pivoted[col] = float("nan")

    pivoted["Gap_ExtraEU_vs_Native_PP"] = pivoted["Extra_EU_Migrant"] - pivoted["Native"]
    pivoted["Metric"] = metric_name
    return pivoted

# ─── 1. Load and Merge Poverty Data (bridging old + new Eurostat format) ────
print("Merging Poverty datasets...")
df_p1 = pd.read_csv(POV_OLD, low_memory=False)
df_p2 = pd.read_csv(POV_NEW, low_memory=False)
df_pov_full = pd.concat([df_p1, df_p2], ignore_index=True)

df_pov = df_pov_full[
    (df_pov_full["sex"] == "T") &
    (df_pov_full["age"].isin(["Y18-64", "Y20-64", "Y_GE18"]))
]
pov_panel = pivot_to_cohorts(df_pov, "TIME_PERIOD", "geo", "citizen", "OBS_VALUE", "Poverty_Rate")

# ─── 2. Process Employment & Temporary Contracts ─────────────────────────────
df_empl = pd.read_csv(EMPL_FILE, low_memory=False)
empl_panel = pivot_to_cohorts(
    df_empl[(df_empl["isced11"] == "ED5-8") & (df_empl["sex"] == "T")],
    "TIME_PERIOD", "geo", "citizen", "OBS_VALUE", "Highly_Educated_Employment_Rate"
)

df_temp = pd.read_csv(TEMP_FILE, low_memory=False)
temp_panel = pivot_to_cohorts(
    df_temp[df_temp["sex"] == "T"],
    "TIME_PERIOD", "geo", "citizen", "OBS_VALUE", "Temporary_Contract_Rate"
)

# ─── 3. Process Incarceration (Pillar 3) ─────────────────────────────────────
# crim_pris_ctz uses FOR (Foreign) / NAT (National) / TOTAL — not the EU27 split.
# We compute Foreign_Share_Pct = FOR/TOTAL*100 and use TOTAL-FOR as the Native proxy.
print("Processing Incarceration data...")
df_pris = pd.read_csv(PRIS_FILE, low_memory=False)

# Pivot FOR, NAT, TOTAL into columns
df_pris_clean = df_pris[["citizen", "geo", "TIME_PERIOD", "OBS_VALUE"]].copy()
df_pris_clean.columns = ["citizen", "Country", "Year", "Count"]
df_pris_clean["Count"] = pd.to_numeric(df_pris_clean["Count"], errors="coerce")
df_pris_clean["Year"]  = pd.to_numeric(df_pris_clean["Year"],  errors="coerce")

# Keep only 2-letter country codes
df_pris_clean = df_pris_clean[df_pris_clean["Country"].str.match(r"^[A-Z]{2}$", na=False)]

pris_pivot = df_pris_clean[df_pris_clean["citizen"].isin(["FOR", "NAT", "TOTAL"])].pivot_table(
    index=["Year", "Country"],
    columns="citizen",
    values="Count",
    aggfunc="mean"
).reset_index()

# Derive disparity metrics
pris_pivot["Foreign_Share_Pct"]          = (pris_pivot["FOR"] / pris_pivot["TOTAL"]) * 100
pris_pivot["Native_Share_Pct"]           = (pris_pivot["NAT"] / pris_pivot["TOTAL"]) * 100
pris_pivot["Gap_ExtraEU_vs_Native_PP"]   = pris_pivot["Foreign_Share_Pct"] - pris_pivot["Native_Share_Pct"]
# Ratio: how many times more likely are foreign nationals to be imprisoned vs nationals
pris_pivot["Ratio_Foreign_vs_Native"]    = pris_pivot["FOR"] / pris_pivot["NAT"].replace(0, float("nan"))

# Rename to match the standard insights schema
pris_panel = pris_pivot[["Year", "Country",
                          "Foreign_Share_Pct", "Native_Share_Pct",
                          "Gap_ExtraEU_vs_Native_PP",
                          "Ratio_Foreign_vs_Native"]].copy()
pris_panel = pris_panel.rename(columns={
    "Foreign_Share_Pct": "Extra_EU_Migrant",   # Foreign nationals → analogous to Extra-EU
    "Native_Share_Pct":  "Native"
})
pris_panel["EU_Migrant"] = float("nan")        # Not available in this dataset
pris_panel["Metric"]     = "Incarceration_Rate_Per_100k"

# ─── 4. Combine all 4 pillars and Save ───────────────────────────────────────
combined = pd.concat([empl_panel, temp_panel, pov_panel, pris_panel], ignore_index=True)
combined  = combined[combined["Country"].str.match(r"^[A-Z]{2}$", na=False)]
combined.to_csv(OUT, index=False)

# Summary
metric_counts = combined.groupby("Metric").size()
print("\\n✅ eurostat_insights.csv rebuilt with ALL 4 pillars:")
for metric, count in metric_counts.items():
    print(f"   {metric:45s}: {count} rows")
print(f"\\n   Year range : {int(combined.Year.min())} – {int(combined.Year.max())}")
print(f"   Countries  : {combined['Country'].nunique()}")
print(f"   Total rows : {len(combined)}")
"""

# ── Load notebook ─────────────────────────────────────────────────────────────
with open(NB_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Cell 30 is index 29 (0-based)
target_idx = 29
old_src = nb["cells"][target_idx]["source"]
old_preview = ("".join(old_src) if isinstance(old_src, list) else old_src)[:60]

# Sanity check — make sure we're editing the right cell
assert "Merging Poverty datasets" in ("".join(old_src) if isinstance(old_src, list) else old_src), \
    f"Cell {target_idx+1} doesn't look like the ETL cell. Aborting."

nb["cells"][target_idx]["source"] = NEW_SOURCE
nb["cells"][target_idx]["execution_count"] = None   # mark as needing re-run
nb["cells"][target_idx]["outputs"] = []             # clear stale outputs

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"✅ Cell 30 patched successfully.")
print(f"   Old preview : {old_preview!r}...")
print(f"   Cell now includes: Poverty + Employment + Contracts + Incarceration")
print(f"   Outputs cleared — re-run Cell 30 in Jupyter to regenerate eurostat_insights.csv")
