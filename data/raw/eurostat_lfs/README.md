# Eurostat — Labour Force Survey (LFS): Migrant Integration

## File
`eurostat_lfs_employment.csv` — Employment and over-qualification rates by country of birth, across EU member states

## Source
**Eurostat** — Statistical Office of the European Union  
Dataset code: `lfsa_ergan` (Employment rates of immigrants by country of birth)  
Website: [https://ec.europa.eu/eurostat](https://ec.europa.eu/eurostat/databrowser/view/lfsa_ergan/)

## Description
This dataset is derived from the EU **Labour Force Survey (LFS)**, the primary source of comparable employment statistics across all EU member states. The specific extract (`lfsa_ergan`) tracks employment and **over-qualification rates** broken down by:
- Country of birth (native-born vs. foreign-born)
- Country of origin (EU-born vs. non-EU-born)
- Sex, age group, and education level

The dataset is the European counterpart to the IPUMS ACS data and forms the foundation of all EU-side labor market analysis in the project.

## Key Variables
| Variable | Description |
|----------|-------------|
| `geo` | Country (EU member state, 2-letter ISO code) |
| `TIME_PERIOD` | Year of survey |
| `c_birth` | Country of birth category (NAT = native, EU27_2020 = EU-born, NEU27_2020 = non-EU-born) |
| `sex` | Gender (M / F / T) |
| `age` | Age group (typically Y20-64 for working age) |
| `isced11` | Education level (ISCED 2011 classification) |
| `OBS_VALUE` | The employment or over-qualification rate value (%) |

## Coverage
- **Geography:** 27 EU member states + EEA countries
- **Time Period:** 2014–2023 (custom extract)
- **Unit of Analysis:** Country-year aggregates for working-age population (20–64)

## Project Role
> **Core Dataset — Research Objectives 1 & 2**

This dataset is used to:
1. **The Innovation Dividend:** Measure immigrant employment rates across EU countries to identify where immigrants are successfully integrating into the labour market.
2. **The "Brain Waste" Analysis:** The over-qualification sub-indicator reveals the gap between immigrant education levels and the skill level of their jobs — the primary EU measurement of brain waste.
3. **Cross-Regional Comparison:** Directly compared against US ACS data to contrast the European Social Model with the American Dream model.

## Usage Notes
- The raw file uses Eurostat's long-format structure with semicolons or commas as delimiters; verify separator before loading.
- Values marked `:` indicate missing or suppressed data for that country-year combination.
- Population weights are pre-applied; data represents weighted survey estimates at the national level.
- Over-qualification is defined as tertiary-educated workers in medium/low-skilled jobs.
