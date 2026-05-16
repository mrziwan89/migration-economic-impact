Framework
- Use Plotly.js
- Use choropleth maps, line charts, and bar charts. (feel free to come up with your own ideas)
- Keep one consistent interaction flow across all topics.

Important lecture guidelines (check for yourself! don't rely on these!!)
- Overview first, details on demand.
- Use linked views:
  selecting a state updates all charts.
- Use period-pooled files for maps:
  *_state_period.csv
  *_gap_state_period.csv
- Use yearly files for trend charts:
  *_state_year.csv
- Use rates/gaps, not raw counts.
- Keep the dashboard clean and uncluttered.
- Use clear titles, labels, and tooltips.
- Avoid rainbow colour maps and red-green palettes.
- Use sequential scales for normal rates.
- Use diverging scales only when both positive and negative gaps exist.

Important data notes
- All CSVs are already weighted and aggregated.
- Gap columns mean:
  Foreign-born rate − US-born rate
- Positive healthcare gap:
  foreign-born residents are more uninsured.
- "Foreign-born" means born outside the US, regardless of citizenship.
- Do not display raw weighted numerator/denominator values for now.

Important labels
- Use:
  "Foreign-born"
  "US-born"
  "Naturalized foreign-born"
  "Non-citizen foreign-born"
- Avoid:
  "foreigners"
  "illegal immigrants"

Incarceration topic
- This is NOT a direct crime rate.
- Label it as:
  "Incarceration proxy"
  or
  "Institutionalisation / incarceration proxy"
- Add a visible caveat in the UI.

CSV usage
- *_state_period.csv
  → choropleth maps
- *_gap_state_period.csv
  → gap maps
- *_state_year.csv
  → trend charts
- healthcare_*_citizenship.csv
  → citizenship breakdown chart

Frontend notes
- STATEFIP values must be mapped to state abbreviations (CA, TX, NY, etc.).
- Handle missing values gracefully. (there shouldn't be any, but it's still a good habit to be cautious)
- Do not treat missing values as zero.
- Use hover tooltips with:
  state, period/year, metric, units, and definitions.

Recommended dashboard structure
1. Topic selector
2. Choropleth map
3. State detail panel (to the right of map, showing state rankings and other insightful details at a quick glance)
4. If the user is interested in more details of the state they selected (e.g. they see selected state is worst in insurance gap ranking) they can scroll down to see more info (either in a dashboard form or other, you decide) with more detailed charts on the selected topic, period and  state.
5. rest is up to you, this is just my recommendation. 