# Founder Origin Data — Fortune 500 & European Tech Startups

## Files
| File | Description |
|------|-------------|
| `us_fortune500_immigrant_trend_2014-2024.csv` | Annual % of Fortune 500 companies with immigrant or second-generation founders, 2014–2024 |
| `us_notable_immigrant_companies.csv` | Notable US companies with immigrant founders: details on founder origin, industry, revenue, and employees |
| `eu_tech_founders_stats.csv` | Summary statistics on immigrant tech founders in Germany, UK, and broader Europe (2022–2024) |

## Sources
| File | Primary Source |
|------|---------------|
| `us_fortune500_immigrant_trend_2014-2024.csv` | American Immigration Council (AIC) — *New American Fortune 500* Annual Reports (2014–2024) |
| `us_notable_immigrant_companies.csv` | AIC 2024 Report + National Foundation for American Policy (NFAP) 2022 |
| `eu_tech_founders_stats.csv` | OECD Missing Entrepreneurs 2023, Defiance Capital Unicorn Founder DNA Report 2024, Startup Heatmap Survey 2023, Antler Europe 2023, Beauhurst 2023, Migrant Founders Monitor 2025 |

## Description

### `us_fortune500_immigrant_trend_2014-2024.csv`
A longitudinal dataset tracking the share of Fortune 500 companies founded or co-founded by **immigrants or their children (2nd generation)** each year from 2014 to 2024. Includes total revenue (USD trillions) and total employees (millions) where available, allowing quantification of the economic weight of immigrant-founded firms. The 2024 data point shows that **46% of Fortune 500 companies** were founded by immigrants or their U.S.-born children, generating **$8.6 trillion in revenue** and employing **15.5 million people**.

### `us_notable_immigrant_companies.csv`
A curated, company-level dataset listing well-known US companies with documented immigrant founders. Each row includes the company name, 2024 Fortune 500 rank, founder name and country of origin, industry, founding year, annual revenue, employee count, and immigrant generation (1st or 2nd gen). Companies range from Apple and Google to Pfizer and AT&T — spanning technology, pharma, consumer goods, and fintech.

### `eu_tech_founders_stats.csv`
A cross-country summary of key statistics on immigrant founders in the European tech ecosystem. Each row represents one data point sourced from a specific report, identifying the country/region, year, metric name (e.g., `unicorns_with_immigrant_founder`), numeric value, unit, source, and explanatory notes. Covers Germany, the UK, and Europe broadly across unicorn startups, fastest-growing businesses, and new tech founders.

## Coverage
- **Geography:** United States + Germany, UK, Europe (broad)
- **Time Period:** 2014–2024 (US trend); 2022–2025 (EU stats)
- **Unit of Analysis:** Company-level (notable companies), annual aggregate % (Fortune 500 trend), country-metric (EU stats)

## Project Role
> **Core Dataset — Research Objective 1 (Innovation Dividend)**

This collection of files is used to:
1. **The Innovation Dividend:** Provide the most direct, high-visibility evidence of immigrants' entrepreneurial impact — the Fortune 500 companies they founded generate trillions in revenue and employ tens of millions.
2. **Cross-Regional Comparison:** The EU stats file allows a parallel narrative on the European side, showing that immigrant founders are equally vital to European unicorn ecosystems.
3. **Narrative Anchoring:** The notable companies file supplies the recognizable brand names (Apple, Google, Tesla, Zoom) that make abstract statistics concrete and compelling for general audiences.

## Usage Notes
- The Fortune 500 trend file has several missing values (`pct_immigrant_only`, `new_american_companies`, `total_employees_millions`) for earlier years — treat with care in trend visualizations.
- Percentages in `us_fortune500_immigrant_trend_2014-2024.csv` refer to companies with **at least one** immigrant or 2nd-gen immigrant founder.
- The `us_notable_immigrant_companies.csv` data has some formatting irregularities (e.g., multiple founders in one cell for some rows) — clean before use.
- EU stats in `eu_tech_founders_stats.csv` are **point-in-time statistics from external reports**, not a continuous longitudinal dataset; treat each row as a separate cited fact rather than a time series.
