# Bureau of Justice Statistics — National Prisoner Statistics (NPS)

## Files
| File | Description |
|------|-------------|
| `38871-0001-Data.tsv` | Main data file — prisoner counts by state, year, and demographic group |
| `38871-0001-Codebook.pdf` | Full variable definitions and value labels |
| `38871-0001-Questionnaire.pdf` | Original BJS data collection form |
| `38871-0001-Documentation-NPS_Crosswalk_1978_2022.xlsx` | Historical variable crosswalk (1978–2022) |
| `38871-0001-Documentation-notes.zip` | Additional methodology and data notes |

## Source
**Bureau of Justice Statistics (BJS)** — U.S. Department of Justice  
**ICPSR Study #38871** — National Prisoner Statistics Program, 1978–2022  
Distributor: Inter-university Consortium for Political and Social Research (ICPSR)  
Website: [https://www.icpsr.umich.edu/web/ICPSR/studies/38871](https://www.icpsr.umich.edu/web/ICPSR/studies/38871)

## Description
The **National Prisoner Statistics (NPS)** program is the definitive official U.S. government census of state and federal adult prisoners. Conducted annually since 1926, it collects data from all 50 state Departments of Corrections and the Federal Bureau of Prisons (BOP). This extract spans **1978 to 2022** and includes prisoner counts broken down by **citizenship status** (U.S. citizen vs. non-citizen), sex, race/ethnicity, and sentence type.

This is one of the few official government datasets that directly measures incarceration rates by immigration status, making it indispensable for evidence-based fact-checking on this topic.

## Key Variables
| Variable | Description |
|----------|-------------|
| `STATEID` / `STATE` | State FIPS code and name |
| `YEAR` | Reference year (1978–2022) |
| `CUSGT1M` / `CUSGT1F` | Custody count: sentenced > 1 year (male/female) |
| `NONCIT` | Count of non-citizen prisoners |
| `NONCITM` / `NONCITF` | Non-citizen prisoners by sex |
| `TOTUSP` | Total US citizens under prison jurisdiction |
| `RACE` sub-variables | Breakdowns by race/ethnicity |

## Coverage
- **Geography:** All 50 U.S. states + Federal Bureau of Prisons
- **Time Period:** 1978–2022 (annual)
- **Unit of Analysis:** State-year aggregates of adult prisoners

## Project Role
> **Core Dataset — Research Objective 4**

This dataset is the primary source for:
1. **Fact-Checking Safety:** Calculates the **incarceration rate per 100,000** for U.S. citizens versus non-citizens (immigrants), directly countering narratives about immigrant crime. Non-citizen incarceration rates are consistently lower than citizen rates per capita.
2. **Credibility:** As official government data published by the BJS, it provides the highest-credibility evidence base for this sensitive topic.
3. **Trend Analysis:** Tracks changes in non-citizen incarceration over four decades (1978–2022), providing long-term context.

## Usage Notes
- Data is in **tab-separated values (`.tsv`)** format — specify `sep='\t'` when loading with Pandas.
- Per-capita rates must be calculated externally by pairing prisoner counts with ACS population estimates by citizenship status.
- "Non-citizen" in NPS refers to individuals who are not U.S. citizens at time of sentencing; this includes lawful permanent residents (green card holders), visa holders, and undocumented individuals.
- The historical crosswalk (`NPS_Crosswalk_1978_2022.xlsx`) is essential when comparing variables across years, as definitions changed over time.
- Usage is subject to ICPSR terms — citation required; data may not be redistributed.
