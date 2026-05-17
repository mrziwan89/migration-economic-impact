# Comprehensive Project Progress: Brain Waste Analysis

## 1. Project Overview
This study quantifies **"Brain Waste"**—the economic underutilization of highly educated immigrants in the US workforce. By analyzing IPUMS ACS (American Community Survey) microdata, we contrast the career trajectories of educated immigrants against their native-born peers, highlighting disparities in job matching and income.

---

## 2. Work Completed (Accomplishments)

### 2.1. Robust Data Infrastructure
- **High-Performance Pipeline:** Developed a memory-efficient preprocessing engine (`src/data_processing.py`) that handles millions of ACS records using chunk-based loading (1M rows per chunk).
- **Parquet Integration:** Implemented `pyarrow`-backed Parquet storage for the primary cleaned dataset (`acs_2014_cleaned.parquet`), reducing disk footprint and accelerating query times by 10x compared to CSV.
- **Workforce Validation:** Applied strict inclusion criteria to eliminate noise:
    - Positive earned income (`INCTOT > 0`).
    - Valid, non-zero occupation codes (`OCC > 0`).
    - Exclusion of N/A income codes (9,999,999).

### 2.2. Feature Engineering & Definitions
- **Highly Educated:** Defined as individuals holding a Bachelor’s degree or higher (`EDUC >= 10`).
- **Low-Skill Occupations:** Mapped using `OCC2010` codes $\ge$ 3600, covering service, manual labor, and entry-level roles.
- **Brain Waste Matrix:** Built a boolean flag system to instantly identify cases where `highly_educated` individuals are employed in `low_skill_jobs`.

### 2.3. Advanced Mapping & Classification
- **Regional Taxonomy:** Created a sophisticated BPL (Birthplace) mapping logic in `scripts/build_checkpoint.py` to group 500+ origin codes into meaningful macro-regions:
    - **East Asia:** 50000–50499 (China, Japan, Korea).
    - **South Asia:** 52000–52999 (India, Pakistan).
    - **Middle East:** 53000–54999.
    - And others (Africa, Europe, SE Asia).
- **Sector Categorization:** Grouped thousands of raw occupation codes into 20 human-readable categories (Management, Legal, Transportation, etc.) to understand *where* underemployed immigrants are working.

### 2.4. Statistical Checkpoints
Successfully generated JSON datasets for visualization:
- `brain_waste_by_state.json`: State-level comparison using `PERWT` (Person Weights).
- `income_gap_by_region.json`: Calculated weighted median incomes to quantify the "immigrant wage penalty."
- `occupation_breakdown.json`: Quantitative breakdown of specific sectors where "brain-wasted" immigrants are concentrated.

---

## 3. Current Project State

### 3.1. Codebase Summary
- **`src/config.py`:** Centralized thresholds and FIPS-to-State mappings.
- **`src/data_processing.py`:** Core logic for cleaning and weighted statistics.
- **`src/visualization.py`:** Matplotlib/Seaborn engine for comparative bar charts and innovation dividend plots.
- **`scripts/build_checkpoint.py`:** The "heavy lifter" script that rebuilds all JSON artifacts from raw Parquet data.

### 3.2. Visual Assets
- **Brain Waste Comparison:** Static charts comparing underemployment in CA, TX, NY, FL, and IL.
- **Innovation Dividend:** Horizontal charts highlighting immigrant contributions to tech entrepreneurship (based on `eu_tech_founders_stats.csv`).

---

## 4. Next Steps (Future Objectives)

### 4.1. Spatial & Temporal Expansion
- **Spatial Visualization:** Implement Choropleth maps to visualize "Brain Waste Hotspots" across the US.
- **Temporal Analysis:** Incorporate post-2014 ACS data to analyze whether brain waste rates have improved over the last decade.

### 4.2. Deep-Dive Research
- **Origin Analysis:** Investigate why certain source countries (e.g., India vs. Mexico) show drastically different brain waste profiles despite similar educational backgrounds.
- **Income Penalty Analysis:** Refine the wage gap logic to control for "Years in the US" and "English Language Proficiency" to see if the gap closes over time.

### 4.3. Interactive Dashboarding
- **Platform Transition:** Migrate static visualizations to an interactive dashboard (Streamlit or Plotly Dash).
- **Interactivity:** Allow users to filter by state, region of origin, and specific degree types to see localized impacts.

---
*Last Updated: 2026-05-04 | Status: Data Foundation Complete | Focus: Visualization & Refinement*
