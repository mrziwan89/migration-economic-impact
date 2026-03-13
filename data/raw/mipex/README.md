# MIPEX — Migrant Integration Policy Index

## Files
| File | Description |
|------|-------------|
| `mipex_EU_2020-2024.xlsx` | EU-focused MIPEX scores, 2020–2024 wave |
| `mipex_core_2007-2019.xlsx` | Core MIPEX longitudinal dataset, 2007–2019 |

## Source
**MIPEX** — Migrant Integration Policy Index  
Produced by: Migration Policy Group (MPG) & CIDOB Barcelona Centre  
Website: [https://www.mipex.eu](https://www.mipex.eu)

## Description
MIPEX is the world's most comprehensive benchmarking tool for measuring **national integration policies** for migrants. It assesses and scores government policies across **8 policy areas** using 58 policy indicators, producing country scores from 0 (least favourable to integration) to 100 (most favourable). Scores are derived from expert legal analysis of each country's laws and regulations.

The dataset covers up to **56 countries** across multiple waves since 2007. The two files in this folder cover the full project time window (2007–2024), split into a historical core dataset and the most recent EU-focused update.

## Policy Areas Measured
| Policy Area | Description |
|-------------|-------------|
| **Labour Market Mobility** | Right to work, access to professions, equal treatment |
| **Family Reunion** | Rules for reuniting with family members |
| **Education** | Access to and support in national education systems |
| **Political Participation** | Voting rights, political freedoms |
| **Long-Term Residence** | Security of residence, path to permanent status |
| **Access to Nationality** | Pathways to citizenship and naturalization |
| **Anti-Discrimination** | Legal protections against discrimination |
| **Health** | Access to healthcare services |

## Coverage
- **Geography:** Up to 56 countries (EU27 + UK, US, Canada, Australia, and others)
- **Time Period:** 2007, 2010, 2014, 2019 (core waves) + 2020–2024 (EU update)
- **Unit of Analysis:** Country-level policy scores (aggregate and by policy area)

## Project Role
> **Core Dataset — Research Objective 3**

This dataset is the primary source for:
1. **Policy vs. Prosperity:** The MIPEX overall score serves as the key **independent variable** in the project's central analysis — testing whether countries with more welcoming integration policies achieve better economic outcomes from their immigrant populations.
2. **Cross-Regional Comparison:** Enables side-by-side ranking of US and EU countries by policy openness, providing the policy context for the *American Dream vs. European Social Model* comparison.
3. **Trend Analysis:** The split between the historical file (2007–2019) and the recent file (2020–2024) allows tracking how integration policy has changed over the project's full 2014–2024 window.

## Usage Notes
- Both files are in Excel (`.xlsx`) format; use `pandas.read_excel()` or manually export individual sheets to CSV.
- The two files use different Excel sheet structures — inspect each before joining.
- To merge with outcome data: join on `country` (ISO2 or country name) and `year`. Note that MIPEX uses discrete policy wave years; interpolation may be needed for intervening years.
- An **overall MIPEX score** is available as a composite; individual area scores allow more granular policy-specific analysis.
- MIPEX scores reflect the legal framework, not actual implementation — factor this into interpretation.
