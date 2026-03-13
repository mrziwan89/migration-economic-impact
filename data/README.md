# Data Directory — The Immigrant Engine

This directory contains all primary and supporting datasets used in **"The Immigrant Engine: Mapping the Multi-Dimensional Impact of Global Talent on Western Growth."**

Each dataset lives in its own subfolder under `raw/`, and every subfolder contains a `README.md` with a full description of the dataset, its source, variables, coverage, and its specific role in the project.

---

## Directory Structure

```
data/
└── raw/
    ├── ipums_acs/          # US Census ACS Microdata (3.5M+ records)
    ├── eurostat_lfs/       # EU Labour Force Survey — Migrant Integration
    ├── oecd_dioc/          # OECD Database on Immigrants in OECD Countries
    ├── bjs_nps/            # BJS National Prisoner Statistics (ICPSR 38871)
    ├── space_i/            # Council of Europe Annual Penal Statistics (2024)
    ├── mipex/              # Migrant Integration Policy Index (2007–2024)
    ├── eu_policy/          # EU Policy Indicator Scores (2020–2024)
    └── founders/           # Fortune 500 & EU Tech Startup Founder Origins
```

---

## Dataset Overview

| Folder | Dataset | Source | Research Objective |
|--------|---------|--------|--------------------|
| `ipums_acs/` | ACS Census Microdata | IPUMS USA | Objectives 1 & 2 |
| `eurostat_lfs/` | EU Labour Force Survey | Eurostat | Objectives 1 & 2 |
| `oecd_dioc/` | Immigrants in OECD Countries | OECD | Objectives 1 & 2 |
| `bjs_nps/` | National Prisoner Statistics | BJS / ICPSR | Objective 4 |
| `space_i/` | Annual Penal Statistics (EU) | Council of Europe | Objective 4 |
| `mipex/` | Integration Policy Index | MIPEX / MPG | Objective 3 |
| `eu_policy/` | EU Policy Indicator Scores | European Commission | Objective 3 |
| `founders/` | Fortune 500 & EU Startup Founders | AIC / NFAP / Various | Objective 1 |

---

## Research Objectives

| # | Objective | Key Datasets |
|---|-----------|-------------|
| 1 | **The Innovation Dividend** — Immigrant share in STEM and high-growth sectors | `ipums_acs`, `eurostat_lfs`, `oecd_dioc`, `founders` |
| 2 | **The "Brain Waste" Analysis** — Education vs. actual job roles | `ipums_acs`, `eurostat_lfs`, `oecd_dioc` |
| 3 | **Policy vs. Prosperity** — Do welcoming laws produce economic returns? | `mipex`, `eu_policy` |
| 4 | **Fact-Checking Safety** — Incarceration rates by citizenship status | `bjs_nps` |

---

## Data Volume Summary

| Dataset | Format | Size |
|---------|--------|------|
| IPUMS ACS | `.csv.gz` | ~1.1 GB compressed |
| Eurostat LFS | `.csv` | ~5.3 MB |
| OECD DIOC | `.csv` | ~900 KB |
| BJS NPS | `.tsv` + `.pdf` + `.xlsx` | ~6 MB total |
| SPACE I | `.pdf` | ~6 MB |
| MIPEX | `.xlsx` (×2) | ~4 MB total |
| EU Policy Indicators | `.xlsx` | ~950 KB |
| Founders | `.csv` (×3) | ~3.5 KB total |

---

*For detailed variable descriptions, usage notes, and sourcing for each dataset, see the `README.md` inside each subfolder.*
