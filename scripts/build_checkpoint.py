"""
build_checkpoint.py
===================
Rebuilds all processed JSON artifacts from the raw IPUMS ACS parquet file.

Run this ONCE to regenerate data/processed/ outputs.
Usage:
    conda activate py
    python build_checkpoint.py

Outputs:
    data/processed/brain_waste_by_state.json
    data/processed/brain_waste_by_region.json
    data/processed/brain_waste_by_country.json     ← NEW (top 20 origins)
    data/processed/income_gap_by_region.json        ← NEW (wage penalty)
    data/processed/occupation_breakdown.json        ← NEW (where are they?)
"""

import pandas as pd
import json
import os

# ──────────────────────────────────────────────
# 0. PATHS
# ──────────────────────────────────────────────
RAW_PARQUET = "../data/raw/ipums_acs/usa_2014_plus.parquet"
OUT_DIR     = "../data/processed"
os.makedirs(OUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# 1. LOAD
# ──────────────────────────────────────────────
print("Loading parquet …")
df = pd.read_parquet(RAW_PARQUET)
print(f"  Rows: {len(df):,}  |  Columns: {df.columns.tolist()}")

# Normalise column names to uppercase
df.columns = df.columns.str.upper()

# ──────────────────────────────────────────────
# 2. BPL MACRO-REGION MAPPING
#    All codes are IPUMS BPL general codes (5-digit ACS style).
#    ─────────────────────────────────────────────────────────
#    IPUMS BPL first digit ≈ continent:
#       1xxxxx = North America
#       2xxxxx = Central America & Caribbean
#       3xxxxx = South America
#       4xxxxx = Europe
#       5xxxxx = Asia
#       6xxxxx = Africa
#       7xxxxx = Pacific / Oceania
#       9xxxxx = Abroad n.s.
#
#    CRITICAL FIX: The previous mapping only captured a narrow
#    slice of Asian BPL codes. The correct ranges are:
#       China / East Asia:  50000–51499
#       SE Asia:            51500–51999
#       South Asia:         52000–52999
#       Middle East:        53000–54999
#    We now map ALL of these to named sub-regions.
# ──────────────────────────────────────────────

def classify_region(bpl):
    """Return a macro-region string for a given IPUMS BPL integer code."""
    b = int(bpl)

    # ── United States (native-born) ──────────────────────────
    if b < 15000:
        return "Native-Born USA"

    # ── North America (non-US, non-Mexico) ──────────────────
    if 15000 <= b <= 19900:
        return "Other North America"

    # ── Mexico ───────────────────────────────────────────────
    if b == 20000:
        return "Mexico & Central America"

    # ── Central America & Caribbean ──────────────────────────
    if 21000 <= b <= 26099:
        return "Mexico & Central America"

    # ── South America ────────────────────────────────────────
    if 30000 <= b <= 39900:
        return "South America"

    # ── Europe ───────────────────────────────────────────────
    if 40000 <= b <= 49900:
        return "Europe"

    # ── East Asia (China, Japan, Korea, Taiwan, Mongolia, HK)
    if 50000 <= b <= 50499:
        return "East Asia"

    # ── Southeast Asia (Philippines, Vietnam, Cambodia, Laos,
    #    Thailand, Indonesia, Malaysia, Myanmar, Singapore …)
    if 50500 <= b <= 51999:
        return "Southeast Asia"

    # ── South Asia (India, Pakistan, Bangladesh, Sri Lanka,
    #    Nepal, Afghanistan …)
    if 52000 <= b <= 52999:
        return "South Asia"

    # ── Middle East / West Asia (Iran, Iraq, Syria, Lebanon,
    #    Jordan, Israel, Saudi Arabia, Turkey, Yemen …)
    if 53000 <= b <= 54999:
        return "Middle East & West Asia"

    # ── Africa ───────────────────────────────────────────────
    if 60000 <= b <= 69900:
        return "Africa"

    # ── Pacific / Oceania ────────────────────────────────────
    if 70000 <= b <= 79900:
        return "Pacific & Oceania"

    # ── Abroad not specified ─────────────────────────────────
    return "Other / Unknown"


# Apply mapping
print("Classifying BPL regions …")
df["MACRO_REGION"] = df["BPL"].apply(classify_region)

# ──────────────────────────────────────────────
# 3. FILTER: adults in labour force, BA or higher
# ──────────────────────────────────────────────
print("Filtering …")

# Adults 25–64 in labour force (EMPSTAT 1=employed, 2=unemployed)
df = df[(df["AGE"] >= 25) & (df["AGE"] <= 64)]
df = df[df["EMPSTAT"].isin([1, 2])]

# Highly educated: EDUCD ≥ 101  (Bachelor's = 101, Master's = 114,
#                                 Professional = 115, PhD = 116)
df_edu = df[df["EDUCD"] >= 101].copy()

print(f"  Educated adults in labour force: {len(df_edu):,}")

# ──────────────────────────────────────────────
# 4. BRAIN WASTE DEFINITION
#    OCC2010 ≥ 3600 → service / manual / low-skill occupations
#    (matches earlier checkpoint definition)
# ──────────────────────────────────────────────
df_edu["IS_BRAIN_WASTE"] = df_edu["OCC2010"] >= 3600

# ──────────────────────────────────────────────
# 5. HELPER: weighted aggregation
# ──────────────────────────────────────────────
def calc_brain_waste(grp):
    total_w   = grp["PERWT"].sum()
    waste_w   = grp.loc[grp["IS_BRAIN_WASTE"], "PERWT"].sum()
    pct       = round(100 * waste_w / total_w, 2) if total_w > 0 else None
    return pd.Series({
        "total_educated_pop": int(total_w),
        "brain_waste_pop":    int(waste_w),
        "brain_waste_pct":    pct,
    })

# ──────────────────────────────────────────────
# 6. OUTPUT A — Brain Waste by US State
#    (immigrants only vs native-born, split)
# ──────────────────────────────────────────────
print("Computing brain waste by state …")
df_edu["IS_IMMIGRANT"] = df_edu["NATIVITY"] == 2  # 2 = foreign-born

state_results = []
for statefip, gstate in df_edu.groupby("STATEFIP"):
    native  = gstate[~gstate["IS_IMMIGRANT"]]
    immig   = gstate[gstate["IS_IMMIGRANT"]]

    row = {"state_fips": int(statefip)}
    if len(native) > 0:
        bw_n = calc_brain_waste(native)
        row["native_educated_pop"]   = bw_n["total_educated_pop"]
        row["native_brain_waste_pop"] = bw_n["brain_waste_pop"]
        row["native_brain_waste_pct"] = bw_n["brain_waste_pct"]
    if len(immig) > 0:
        bw_i = calc_brain_waste(immig)
        row["immigrant_educated_pop"]    = bw_i["total_educated_pop"]
        row["immigrant_brain_waste_pop"] = bw_i["brain_waste_pop"]
        row["immigrant_brain_waste_pct"] = bw_i["brain_waste_pct"]
    state_results.append(row)

out_path = f"{OUT_DIR}/brain_waste_by_state.json"
with open(out_path, "w") as f:
    json.dump(state_results, f, indent=2)
print(f"  ✓ Saved {out_path}  ({len(state_results)} states)")

# ──────────────────────────────────────────────
# 7. OUTPUT B — Brain Waste by Macro-Region
# ──────────────────────────────────────────────
print("Computing brain waste by region …")
region_df = df_edu.groupby("MACRO_REGION").apply(calc_brain_waste).reset_index()
region_df = region_df.sort_values("brain_waste_pct", ascending=False)

out_path = f"{OUT_DIR}/brain_waste_by_region.json"
region_df.to_json(out_path, orient="records", indent=2)
print(f"  ✓ Saved {out_path}")
print(region_df.to_string())

# ──────────────────────────────────────────────
# 8. OUTPUT C — Brain Waste by Top Country of Origin (NEW)
#    Shows top 25 immigrant source countries by educated pop
# ──────────────────────────────────────────────
print("Computing brain waste by country of origin …")

# Only immigrants
df_immig = df_edu[df_edu["NATIVITY"] == 2].copy()

# Map BPL to human-readable country label (key countries)
COUNTRY_LABELS = {
    50000: "China",
    50100: "Japan",
    50200: "Korea",
    50400: "Taiwan",
    50500: "Hong Kong",
    51500: "Philippines",
    51800: "Vietnam",
    51900: "Cambodia",
    51600: "Thailand",
    51700: "Indonesia/Malaysia",
    52100: "India",
    52200: "Pakistan",
    52300: "Bangladesh",
    52400: "Sri Lanka",
    52600: "Nepal",
    53000: "Iran",
    53200: "Iraq",
    53300: "Syria",
    53400: "Lebanon",
    53500: "Jordan",
    53700: "Israel",
    54200: "Turkey",
    54400: "Yemen",
    60010: "Ethiopia",
    60012: "Eritrea",
    60020: "Nigeria",
    60030: "Ghana",
    60040: "Senegal",
    60050: "Kenya",
    60060: "Tanzania",
    60100: "South Africa",
    20000: "Mexico",
    21000: "Guatemala",
    21010: "El Salvador",
    21020: "Honduras",
    21030: "Nicaragua",
    21040: "Costa Rica",
    25000: "Cuba",
    26000: "Dominican Republic",
    26010: "Haiti",
    26020: "Jamaica",
    30005: "Colombia",
    30010: "Ecuador",
    30015: "Peru",
    30020: "Brazil",
    30025: "Venezuela",
    30030: "Argentina",
    40000: "UK",
    41000: "Ireland",
    43300: "Germany",
    45200: "France",
    45600: "Italy",
    45700: "Spain",
    46200: "Poland",
    46500: "Russia",
    46510: "Ukraine",
    46600: "Romania",
    47200: "Greece",
    47400: "Portugal",
}

df_immig["COUNTRY_LABEL"] = df_immig["BPL"].map(COUNTRY_LABELS).fillna("Other")

country_df = (
    df_immig.groupby("COUNTRY_LABEL")
    .apply(calc_brain_waste)
    .reset_index()
    .sort_values("total_educated_pop", ascending=False)
    .head(30)
    .sort_values("brain_waste_pct", ascending=False)
)

out_path = f"{OUT_DIR}/brain_waste_by_country.json"
country_df.to_json(out_path, orient="records", indent=2)
print(f"  ✓ Saved {out_path}")

# ──────────────────────────────────────────────
# 9. OUTPUT D — Income Gap by Region (NEW)
#    Median INCWAGE for educated immigrants vs educated native-born
#    by macro-region — reveals the wage penalty
# ──────────────────────────────────────────────
print("Computing income gap by region …")

# Only employed (EMPSTAT=1), has income > 0
df_income = df_edu[(df_edu["EMPSTAT"] == 1) & (df_edu["INCWAGE"] > 0) & (df_edu["INCWAGE"] < 999998)].copy()

income_results = []
for region, grp in df_income.groupby("MACRO_REGION"):
    native = grp[grp["NATIVITY"] != 2]
    immig  = grp[grp["NATIVITY"] == 2]

    def weighted_median(vals, weights):
        """Compute weighted median."""
        df_s = pd.DataFrame({"v": vals.values, "w": weights.values}).dropna()
        df_s = df_s.sort_values("v")
        cum_w = df_s["w"].cumsum()
        total = df_s["w"].sum()
        idx   = (cum_w >= total / 2).idxmax()
        return float(df_s.loc[idx, "v"])

    row = {"region": region}
    if len(native) > 50:
        row["native_median_wage"] = weighted_median(native["INCWAGE"], native["PERWT"])
    if len(immig) > 50:
        row["immigrant_median_wage"] = weighted_median(immig["INCWAGE"], immig["PERWT"])
    if "native_median_wage" in row and "immigrant_median_wage" in row:
        row["wage_gap_pct"] = round(
            100 * (row["native_median_wage"] - row["immigrant_median_wage"]) / row["native_median_wage"],
            1
        )
    income_results.append(row)

out_path = f"{OUT_DIR}/income_gap_by_region.json"
with open(out_path, "w") as f:
    json.dump(income_results, f, indent=2)
print(f"  ✓ Saved {out_path}")

# ──────────────────────────────────────────────
# 10. OUTPUT E — Occupation Breakdown (NEW)
#     For brain-wasted immigrants by region:
#     what occupation categories are they stuck in?
# ──────────────────────────────────────────────
print("Computing occupation breakdown …")

# OCC2010 bucket labels (simplified)
def occ_category(occ):
    if occ < 500:   return "Management"
    if occ < 1000:  return "Business & Finance"
    if occ < 1300:  return "Computer & Math"
    if occ < 1700:  return "Architecture & Engineering"
    if occ < 2000:  return "Life & Physical Science"
    if occ < 2100:  return "Community & Social Services"
    if occ < 2200:  return "Legal"
    if occ < 2600:  return "Education"
    if occ < 3000:  return "Arts & Media"
    if occ < 3600:  return "Healthcare"
    if occ < 4000:  return "Service — Protective"
    if occ < 4700:  return "Service — Food & Cleaning"
    if occ < 5000:  return "Sales"
    if occ < 5800:  return "Office & Admin"
    if occ < 6200:  return "Farming & Fishing"
    if occ < 7000:  return "Construction & Extraction"
    if occ < 7700:  return "Installation & Repair"
    if occ < 9000:  return "Production / Manufacturing"
    if occ < 9800:  return "Transportation"
    return "Other"

df_wasted = df_edu[(df_edu["IS_BRAIN_WASTE"]) & (df_edu["NATIVITY"] == 2)].copy()
df_wasted["OCC_CATEGORY"] = df_wasted["OCC2010"].apply(occ_category)

occ_df = (
    df_wasted.groupby(["MACRO_REGION", "OCC_CATEGORY"])["PERWT"]
    .sum()
    .reset_index()
    .rename(columns={"PERWT": "weighted_pop"})
)
occ_df["weighted_pop"] = occ_df["weighted_pop"].astype(int)

out_path = f"{OUT_DIR}/occupation_breakdown.json"
occ_df.to_json(out_path, orient="records", indent=2)
print(f"  ✓ Saved {out_path}")

print("\n✅ All checkpoints rebuilt successfully.")
print(f"   Output directory: {OUT_DIR}/")
for fn in os.listdir(OUT_DIR):
    sz = os.path.getsize(f"{OUT_DIR}/{fn}")
    print(f"   {fn}  ({sz:,} bytes)")
