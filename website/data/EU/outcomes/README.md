# EU Outcomes Visualization Data

These CSVs are the browser-facing format generated from `website/data/new-eu-data/eurostat_insights.csv`.

## Files

- `eu_outcomes_country_year.csv`: annual rows for trend charts.
- `eu_outcomes_country_period.csv`: period-pooled rows for maps and rankings.
- `eu_outcomes_country_latest.csv`: latest usable row per country and metric for default maps.

## Shape

The visualization format is a flat tidy CSV:

- one row per `country_key` + `metric_key` + year or period
- ISO3 `country_key` and `iso3` for Plotly maps
- `is_aggregate` for EU / euro area rows that should not be mapped
- cohort columns: `native_value`, `eu_migrant_value`, `extra_eu_migrant_value`
- comparison columns: `gap_extra_eu_vs_native_pp`, `ratio_foreign_vs_native`

This keeps the dashboard simple: maps and rankings read the period/latest files, while trend charts read the yearly file.

## Poverty Caveat

The processed poverty rows mix percentage rates and counts from 2015 onward in this copy of the data. The generated visualization files therefore keep poverty rows only through 2014.
