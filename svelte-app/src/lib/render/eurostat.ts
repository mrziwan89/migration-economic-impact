import type { CsvRow } from "../data/csv";
import type { LoadedData } from "../data/load";
import type { EurostatTopic } from "../data/topics";
import { EU_TREND_GROUPS } from "../data/lookups";
import { blankPlot, mapScale, trendLayout } from "./common";

export function eurostatRowsForMap(
  cfg: EurostatTopic,
  data: LoadedData,
  period: string,
  sex: string,
  age: string
): CsvRow[] {
  if (cfg.kind === "gap") {
    return data.eurostat.gapPeriod.filter(
      (row) =>
        row.period === period &&
        row.sex === sex &&
        row.age === age &&
        row.comparison_group === cfg.comparisonGroup &&
        row.is_aggregate === 0 &&
        row.iso3
    );
  }
  return data.eurostat.countryPeriod.filter(
    (row) =>
      row.period === period &&
      row.sex === sex &&
      row.age === age &&
      row.citizen_group === cfg.citizenGroup &&
      row.is_aggregate === 0 &&
      row.iso3
  );
}

export function eurostatOutcomeRowsForSelection(
  cfg: EurostatTopic,
  data: LoadedData,
  period: string,
  includeAggregates = false
): CsvRow[] {
  const sourceRows = period === "Latest available" ? data.eurostat.outcomeLatest : data.eurostat.outcomePeriod;
  return sourceRows.filter(
    (row) =>
      row.metric_key === cfg.metricKey &&
      row[cfg.value] != null &&
      (includeAggregates || (row.is_aggregate === 0 && row.iso3))
  );
}

function outcomeCoverageLabel(row: CsvRow): string {
  if (row.YEAR != null) {
    return String(row.YEAR);
  }
  if (row.year_start != null && row.year_end != null) {
    const obs = Number(row.years_observed);
    const suffix = row.years_observed
      ? `, ${row.years_observed} observed year${obs === 1 ? "" : "s"}`
      : "";
    return `${row.year_start}-${row.year_end}${suffix}`;
  }
  return (row.period as string) || "";
}

export function renderEurostatOutcomeMap(
  target: HTMLElement,
  cfg: EurostatTopic,
  data: LoadedData,
  period: string
): { rows: CsvRow[]; mapNote: string; rankingNote: string } {
  const rows = eurostatOutcomeRowsForSelection(cfg, data, period);
  const values = rows.map((row) => row[cfg.value] as number | null);
  const scale = mapScale(values, Boolean(cfg.isGap));
  const hovertemplate =
    cfg.metricKey === "incarceration"
      ? "<b>%{text}</b><br>Ratio: %{z:.2f}x<br>Foreign-citizen share: %{customdata[2]:.1f}%<br>National-citizen share: %{customdata[0]:.1f}%<br>Coverage: %{customdata[3]}<extra></extra>"
      : "<b>%{text}</b><br>Gap: %{z:.1f} pp<br>Extra-EU migrant: %{customdata[2]:.1f}%<br>EU migrant: %{customdata[1]:.1f}%<br>Native-born: %{customdata[0]:.1f}%<br>Coverage: %{customdata[3]}<extra></extra>";

  if (!rows.length) {
    blankPlot(target, cfg.title, "No country data available for this selection.");
  } else {
    window.Plotly.newPlot(
      target,
      [
        {
          type: "choropleth",
          locationmode: "ISO-3",
          locations: rows.map((row) => row.iso3),
          z: values,
          text: rows.map((row) => row.country),
          customdata: rows.map((row) => [
            row.native_value,
            row.eu_migrant_value,
            row.extra_eu_migrant_value,
            outcomeCoverageLabel(row)
          ]),
          colorscale: cfg.colorscale || "RdBu",
          reversescale: Boolean(cfg.reversescale),
          zmin: scale.zmin,
          zmax: scale.zmax,
          marker: { line: { color: "white", width: 0.6 } },
          colorbar: { title: cfg.units },
          hovertemplate
        }
      ],
      {
        title: `${cfg.title} - ${period}`,
        geo: {
          scope: "europe",
          projection: { type: "natural earth" },
          showland: true,
          landcolor: "#eef2f4",
          showcountries: true,
          countrycolor: "white"
        },
        margin: { l: 0, r: 0, t: 45, b: 0 },
        paper_bgcolor: "white",
        plot_bgcolor: "white"
      },
      { responsive: true }
    );
  }

  const periodNote =
    period === "Latest available"
      ? "Map uses each country's latest usable year."
      : "Period values are means across available annual observations.";
  return {
    rows,
    mapNote: `${cfg.note} ${periodNote}`,
    rankingNote:
      cfg.rankDirection === "ascending"
        ? "Ranking highlights the most negative gaps first."
        : "Ranking highlights the highest values first."
  };
}

export function renderEurostatOutcomeRanking(target: HTMLElement, cfg: EurostatTopic, rows: CsvRow[]): void {
  const rankingRows = rows
    .filter((row) => row[cfg.value] != null)
    .sort((a, b) =>
      cfg.rankDirection === "ascending"
        ? (a[cfg.value] as number) - (b[cfg.value] as number)
        : (b[cfg.value] as number) - (a[cfg.value] as number)
    )
    .slice(0, 12)
    .reverse();

  if (!rankingRows.length) {
    blankPlot(target, "Country ranking", "No ranking data available.");
    return;
  }

  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        orientation: "h",
        y: rankingRows.map((row) => row.country),
        x: rankingRows.map((row) => row[cfg.value]),
        customdata: rankingRows.map((row) => outcomeCoverageLabel(row)),
        marker: { color: "#116466" },
        hovertemplate:
          cfg.units === "ratio"
            ? "<b>%{y}</b><br>%{x:.2f}x<br>%{customdata}<extra></extra>"
            : "<b>%{y}</b><br>%{x:.1f} " + cfg.units + "<br>%{customdata}<extra></extra>"
      }
    ],
    {
      title: `${cfg.rankDirection === "ascending" ? "Largest disadvantages" : "Highest countries"} - ${cfg.title}`,
      xaxis: { title: cfg.units, zeroline: true },
      yaxis: { title: "" },
      margin: { l: 135, r: 20, t: 45, b: 50 },
      paper_bgcolor: "white",
      plot_bgcolor: "white"
    },
    { responsive: true }
  );
}

export function renderEurostatOutcomeTrend(
  target: HTMLElement,
  cfg: EurostatTopic,
  data: LoadedData,
  place: string
): { trendNote: string } {
  const selectedRows = data.eurostat.outcomeYear
    .filter((row) => row.country_key === place && row.metric_key === cfg.metricKey && row[cfg.value] != null)
    .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));
  const euRows = data.eurostat.outcomeYear
    .filter((row) => row.country_code === "EU" && row.metric_key === cfg.metricKey && row[cfg.value] != null)
    .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));
  const traces: Array<Record<string, unknown>> = [];

  if (selectedRows.length) {
    traces.push({
      type: "scatter",
      mode: "lines+markers",
      name: selectedRows[0].country,
      x: selectedRows.map((row) => row.YEAR),
      y: selectedRows.map((row) => row[cfg.value]),
      line: { color: "#116466" }
    });
  }
  if (place !== "EU" && euRows.length) {
    traces.push({
      type: "scatter",
      mode: "lines+markers",
      name: "EU aggregate",
      x: euRows.map((row) => row.YEAR),
      y: euRows.map((row) => row[cfg.value]),
      line: { dash: "dot", color: "#c44536" }
    });
  }

  if (!traces.length) {
    blankPlot(target, `${cfg.title} over time`, "No trend data available for the selected country.");
  } else {
    window.Plotly.newPlot(target, traces, trendLayout(`${cfg.title} over time`, cfg.units), {
      responsive: true
    });
  }
  return { trendNote: "Trend uses annual rows from the normalized EU outcomes file." };
}

export function renderEurostatOutcomeBreakdown(
  target: HTMLElement,
  cfg: EurostatTopic,
  data: LoadedData,
  period: string,
  place: string
): { breakdownNote: string } {
  const row = eurostatOutcomeRowsForSelection(cfg, data, period, true).find((item) => item.country_key === place);
  if (!row) {
    blankPlot(target, "Selected country detail", "No detail data available.");
    return { breakdownNote: "" };
  }

  const coverage = outcomeCoverageLabel(row);
  const labels =
    cfg.metricKey === "incarceration"
      ? ["National citizens", "Foreign citizens"]
      : ["Native-born", "EU migrant", "Extra-EU migrant"];
  const values =
    cfg.metricKey === "incarceration"
      ? [row.native_value, row.extra_eu_migrant_value]
      : [row.native_value, row.eu_migrant_value, row.extra_eu_migrant_value];

  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        x: labels,
        y: values,
        marker: {
          color: labels.map((label) =>
            label.includes("Native") || label.includes("National") ? "#6f7f8f" : "#116466"
          )
        },
        hovertemplate: "%{x}<br>%{y:.1f}%<extra></extra>"
      }
    ],
    {
      title: `${cfg.title} components - ${row.country}, ${coverage}`,
      yaxis: { title: cfg.componentUnit },
      xaxis: { title: "" },
      margin: { l: 60, r: 20, t: 45, b: 80 },
      paper_bgcolor: "white",
      plot_bgcolor: "white"
    },
    { responsive: true }
  );

  return {
    breakdownNote:
      cfg.metricKey === "incarceration"
        ? "Components show prison-population shares; the map and ranking use the foreign-to-national representation ratio."
        : "Components show cohort rates; the map and ranking use extra-EU migrant value minus native-born value."
  };
}

export function renderEurostatEmploymentMap(
  target: HTMLElement,
  cfg: EurostatTopic,
  data: LoadedData,
  period: string,
  sex: string,
  age: string
): { rows: CsvRow[]; mapNote: string; rankingNote: string } {
  const rows = eurostatRowsForMap(cfg, data, period, sex, age);
  const values = rows.map((row) => row[cfg.value] as number | null);
  const scale = mapScale(values, cfg.kind === "gap");

  if (!rows.length) {
    blankPlot(target, cfg.title, "No country data available for this selection.");
  } else {
    window.Plotly.newPlot(
      target,
      [
        {
          type: "choropleth",
          locationmode: "ISO-3",
          locations: rows.map((row) => row.iso3),
          z: values,
          text: rows.map((row) => row.country),
          customdata: rows.map((row) =>
            cfg.kind === "gap"
              ? [row.comparison_rate_pct, row.reporting_country_rate_pct, row.comparison_label]
              : [row.citizen_label]
          ),
          colorscale: cfg.kind === "gap" ? "RdBu" : "YlGnBu",
          reversescale: cfg.kind === "gap",
          zmin: scale.zmin,
          zmax: scale.zmax,
          marker: { line: { color: "white", width: 0.6 } },
          colorbar: { title: cfg.units },
          hovertemplate:
            cfg.kind === "gap"
              ? "<b>%{text}</b><br>Gap: %{z:.1f} pp<br>%{customdata[2]}: %{customdata[0]:.1f}%<br>Reporting-country citizens: %{customdata[1]:.1f}%<extra></extra>"
              : "<b>%{text}</b><br>%{customdata[0]}: %{z:.1f}%<extra></extra>"
        }
      ],
      {
        title: `${cfg.title} - ${period}`,
        geo: {
          scope: "europe",
          projection: { type: "natural earth" },
          showland: true,
          landcolor: "#eef2f4",
          showcountries: true,
          countrycolor: "white"
        },
        margin: { l: 0, r: 0, t: 45, b: 0 },
        paper_bgcolor: "white",
        plot_bgcolor: "white"
      },
      { responsive: true }
    );
  }
  return {
    rows,
    mapNote: `${cfg.note} Filter: ${sex}, ${age}.`,
    rankingNote:
      cfg.kind === "gap"
        ? "Ranking uses the selected period, age, and sex. Positive gaps mean the comparison group has a higher employment rate."
        : "Ranking uses the selected period, age, and sex."
  };
}

export function renderEurostatEmploymentRanking(target: HTMLElement, cfg: EurostatTopic, rows: CsvRow[]): void {
  const rankingRows = rows
    .filter((row) => row[cfg.value] != null)
    .sort((a, b) => (b[cfg.value] as number) - (a[cfg.value] as number))
    .slice(0, 12)
    .reverse();

  if (!rankingRows.length) {
    blankPlot(target, "Country ranking", "No ranking data available.");
    return;
  }

  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        orientation: "h",
        y: rankingRows.map((row) => row.country),
        x: rankingRows.map((row) => row[cfg.value]),
        marker: { color: "#116466" },
        hovertemplate: "<b>%{y}</b><br>%{x:.1f} " + cfg.units + "<extra></extra>"
      }
    ],
    {
      title: `Highest countries - ${cfg.title}`,
      xaxis: { title: cfg.units, zeroline: true },
      yaxis: { title: "" },
      margin: { l: 135, r: 20, t: 45, b: 50 },
      paper_bgcolor: "white",
      plot_bgcolor: "white"
    },
    { responsive: true }
  );
}

export function renderEurostatEmploymentTrend(
  target: HTMLElement,
  cfg: EurostatTopic,
  data: LoadedData,
  place: string,
  sex: string,
  age: string
): { trendNote: string } {
  const traces: Array<Record<string, unknown>> = [];

  if (cfg.kind === "gap") {
    const selectedRows = data.eurostat.gapYear
      .filter(
        (row) =>
          row.country_key === place &&
          row.sex === sex &&
          row.age === age &&
          row.comparison_group === cfg.comparisonGroup
      )
      .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));
    const euRows = data.eurostat.gapYear
      .filter(
        (row) =>
          row.country_key === "EU27_2020" &&
          row.sex === sex &&
          row.age === age &&
          row.comparison_group === cfg.comparisonGroup
      )
      .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));

    if (selectedRows.length) {
      traces.push({
        type: "scatter",
        mode: "lines+markers",
        name: selectedRows[0].country,
        x: selectedRows.map((row) => row.YEAR),
        y: selectedRows.map((row) => row.employment_rate_gap_pp),
        line: { color: "#116466" }
      });
    }
    if (place !== "EU27_2020" && euRows.length) {
      traces.push({
        type: "scatter",
        mode: "lines+markers",
        name: "EU27 aggregate",
        x: euRows.map((row) => row.YEAR),
        y: euRows.map((row) => row.employment_rate_gap_pp),
        line: { dash: "dot", color: "#c44536" }
      });
    }
  } else {
    EU_TREND_GROUPS.forEach((group) => {
      const groupRows = data.eurostat.countryYear
        .filter(
          (row) =>
            row.country_key === place &&
            row.sex === sex &&
            row.age === age &&
            row.citizen_group === group
        )
        .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));
      if (!groupRows.length) {
        return;
      }
      traces.push({
        type: "scatter",
        mode: "lines+markers",
        name: groupRows[0].citizen_label,
        x: groupRows.map((row) => row.YEAR),
        y: groupRows.map((row) => row.employment_rate_pct)
      });
    });
  }

  if (!traces.length) {
    blankPlot(target, `${cfg.title} over time`, "No trend data available for the selected country.");
  } else {
    window.Plotly.newPlot(target, traces, trendLayout(`${cfg.title} over time`, cfg.units), {
      responsive: true
    });
  }

  return {
    trendNote:
      cfg.kind === "gap"
        ? "Trend compares the selected country with the EU27 aggregate when both are available."
        : "Trend shows available citizenship groups for the selected country."
  };
}

const CITIZEN_ORDER_LOCAL = [
  "total",
  "reporting_country",
  "foreign_country",
  "non_eu",
  "eu_mobile",
  "eu27_total",
  "stateless",
  "no_response"
];

export function renderEurostatEmploymentBreakdown(
  target: HTMLElement,
  data: LoadedData,
  period: string,
  place: string,
  sex: string,
  age: string
): { breakdownNote: string } {
  const rows = data.eurostat.countryPeriod
    .filter(
      (row) =>
        row.period === period &&
        row.country_key === place &&
        row.sex === sex &&
        row.age === age &&
        row.employment_rate_pct != null
    )
    .sort(
      (a, b) =>
        CITIZEN_ORDER_LOCAL.indexOf(String(a.citizen_group)) -
        CITIZEN_ORDER_LOCAL.indexOf(String(b.citizen_group))
    );

  if (!rows.length) {
    blankPlot(target, "Citizenship breakdown", "No breakdown data available.");
    return { breakdownNote: "" };
  }

  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        x: rows.map((row) => row.citizen_label),
        y: rows.map((row) => row.employment_rate_pct),
        marker: {
          color: rows.map((row) => (row.citizen_group === "reporting_country" ? "#6f7f8f" : "#116466"))
        },
        hovertemplate: "%{x}<br>Employment rate: %{y:.1f}%<extra></extra>"
      }
    ],
    {
      title: `Employment rate by citizenship - ${rows[0].country}, ${period}`,
      yaxis: { title: "% employed" },
      xaxis: { title: "" },
      margin: { l: 60, r: 20, t: 45, b: 130 },
      paper_bgcolor: "white",
      plot_bgcolor: "white"
    },
    { responsive: true }
  );

  return {
    breakdownNote:
      "Period values are means across available annual Eurostat observations; suppressed values remain missing."
  };
}
