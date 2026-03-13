# IPUMS USA — American Community Survey (ACS) Microdata

## File
`usa_00001.csv.gz` — Compressed CSV extract of ACS microdata (~1.1 GB uncompressed)

## Source
**IPUMS USA** — Integrated Public Use Microdata Series, University of Minnesota  
Website: [https://usa.ipums.org](https://usa.ipums.org)

## Description
This is a **custom microdata extract** from the American Community Survey (ACS), covering individual-level census records for residents of the United States. The dataset includes millions of anonymized respondent records with variables covering nativity (immigrant vs. native-born), educational attainment, occupation and industry codes, income, and employment status.

The extract is the backbone of the project's U.S.-side analysis, providing the raw individual-level data from which all aggregated statistics about immigrant labor force participation, STEM representation, and economic outcomes are derived.

## Key Variables
| Variable | Description |
|----------|-------------|
| `NATIVITY` | Whether the respondent was born in the US or abroad |
| `BPL` / `BPLD` | Birthplace (country of origin) |
| `EDUC` / `EDUCD` | Educational attainment level |
| `OCC` / `OCC2010` | Detailed occupation code |
| `IND` | Industry code |
| `INCTOT` / `INCWAGE` | Total personal / wage income |
| `EMPSTAT` | Employment status |
| `YEAR` | Survey year (2014–2023) |
| `PERWT` | Person weight (used for population-level estimates) |

## Coverage
- **Geography:** United States (national level)
- **Time Period:** 2014–2023 (trend analysis window)
- **Unit of Analysis:** Individual respondents (approx. 3–3.5 million records per year)

## Project Role
> **Core Dataset — Research Objectives 1 & 2**

This dataset is used to:
1. **The Innovation Dividend:** Calculate immigrant shares in STEM, healthcare, and high-growth occupations.
2. **The "Brain Waste" Analysis:** Compare the education levels of foreign-born workers with their actual occupational categories to identify over-qualification.
3. **Cross-Regional Comparison:** Provide the U.S. data counterpart to the EU's Eurostat LFS dataset for the *American Dream vs. European Social Model* analysis.

## Usage Notes
- The `.gz` file must be decompressed before use: `gunzip usa_00001.csv.gz`
- IPUMS microdata requires citation; see [IPUMS terms of use](https://usa.ipums.org/usa/terms.shtml).
- Person weights (`PERWT`) **must be applied** to produce representative population-level statistics.
- Occupation codes should be cross-walked with O*NET or BLS SOC codes to classify STEM roles.
