# OECD — Database on Immigrants in OECD Countries (DIOC)

## File
`OECD_DIOC.csv` — Cross-national data on immigrant occupational distribution and STEM participation (~900 KB)

## Source
**OECD** — Organisation for Economic Co-operation and Development  
Database: DIOC — Database on Immigrants in OECD Countries  
Website: [https://www.oecd.org/migration/dioc.htm](https://www.oecd.org/migration/dioc.htm)

## Description
The OECD DIOC compiles harmonized, cross-national data on the **stock of immigrants** living in OECD member countries, with a focus on their **educational attainment and occupational characteristics**. It draws from national population censuses and registers and provides the most internationally comparable snapshot of skilled immigrant populations across member states.

This dataset complements the microdata sources (IPUMS, Eurostat LFS) by providing pre-harmonized, cross-country aggregates for OECD nations, making it ideal for **international benchmarking**.

## Key Variables
| Variable | Description |
|----------|-------------|
| `Country` | Destination OECD country |
| `Country_of_birth` | Origin country of the immigrant |
| `Education` | Educational level (low / medium / high) |
| `Occupation` | Occupation category (ISCO-based) |
| `Field_of_study` | Academic field (incl. STEM, health, social sciences) |
| `Employment_status` | Employed, unemployed, or inactive |
| `N` or `OBS_VALUE` | Count/share of immigrants in that category |

## Coverage
- **Geography:** ~35 OECD member countries (destination) × all countries of origin
- **Time Period:** Latest available waves (circa 2015–2021, varies by country)
- **Unit of Analysis:** Country-pair aggregates by education/occupation/field

## Project Role
> **Supporting Dataset — Research Objectives 1 & 2**

This dataset is used to:
1. **The Innovation Dividend:** Quantify the share of immigrants working in STEM and healthcare fields across OECD countries — providing the broadest international comparison in the project.
2. **The "Brain Waste" Analysis:** Identify mismatches between immigrants' field of education and their current occupation category across OECD nations.
3. **Cross-Regional Comparison:** Bridges US and EU analysis by providing a common OECD framework for comparing skill utilization across both regions.

## Usage Notes
- Check whether values represent raw counts or percentage shares; column headers may vary.
- For STEM classification, use the `Field_of_study` variable aligned with ISCED-F 2013 codes (04 = Natural Sciences, Computing; 05 = Engineering, Manufacturing; 06 = ICT).
- Data for some smaller OECD countries may have suppressed cells due to small sample sizes.
- Complements the Eurostat LFS microdata for EU countries; use DIOC for the broader OECD view.
