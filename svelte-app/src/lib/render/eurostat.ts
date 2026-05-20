import type { CsvRow } from "../data/csv";
import type { LoadedData } from "../data/load";
import type { EurostatTopic } from "../data/topics";
import { EU_TREND_GROUPS } from "../data/lookups";
import { blankPlot, mapScale, trendLayout, themeColors, PLACE_COLORS, PLACE_COLORS_DARK, addSelectedYearIndicator } from "./common";
import { CITIZEN_ORDER } from "../data/lookups";
const CITIZEN_ORDER_LOCAL = CITIZEN_ORDER;

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
  period: string,
  isDark: boolean
): { rows: CsvRow[]; mapNote: string; rankingNote: string } {
  const rows = eurostatOutcomeRowsForSelection(cfg, data, period);
  const values = rows.map((row) => row[cfg.value] as number | null);
  const scale = mapScale(values, Boolean(cfg.isGap));
  const colors = themeColors(isDark);
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
          marker: { line: { color: colors.lineColor, width: 0.6 } },
          colorbar: { title: cfg.units, tickfont: { color: colors.textColor } },
          hovertemplate
        }
      ],
      {
        title: { text: `${cfg.title} - ${period}`, font: { color: colors.textColor } },
        geo: {
          scope: "europe",
          projection: { type: "natural earth" },
          showland: true,
          landcolor: isDark ? "#1e293b" : "#eef2f4",
          showcountries: true,
          countrycolor: colors.lineColor,
          bgcolor: colors.paperBg
        },
        margin: { l: 0, r: 0, t: 45, b: 0 },
        paper_bgcolor: colors.paperBg,
        plot_bgcolor: colors.plotBg
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

export function renderEurostatOutcomeRanking(
  target: HTMLElement,
  cfg: EurostatTopic,
  rows: CsvRow[],
  selectedPlaces: Set<string>,
  isDark: boolean,
  onSelect?: (place: string) => void
): void {
  const allRows = rows
    .filter((row) => row[cfg.value] != null)
    .sort((a, b) =>
      cfg.rankDirection === "ascending"
        ? (a[cfg.value] as number) - (b[cfg.value] as number)
        : (b[cfg.value] as number) - (a[cfg.value] as number)
    );

  const topRows = allRows.slice(0, 12);
  const extraRows = selectedPlaces.size > 0
    ? allRows.filter(row => selectedPlaces.has(row.country_key as string) && !topRows.includes(row)).slice(0, 5)
    : [];
  const rankingRows = [...topRows, ...extraRows].reverse();

  if (!rankingRows.length) {
    blankPlot(target, "Country ranking", "No ranking data available.");
    return;
  }

  const colors = themeColors(isDark);
  const hasSelection = selectedPlaces.size > 0;
  const barColors = rankingRows.map(row =>
    selectedPlaces.has(row.country_key as string) ? colors.accent : (hasSelection ? colors.lineColor : colors.accent)
  );
  const opacities = rankingRows.map(row =>
    hasSelection ? (selectedPlaces.has(row.country_key as string) ? 1 : 0.32) : 1
  );

  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        orientation: "h",
        y: rankingRows.map((row) => row.country),
        x: rankingRows.map((row) => row[cfg.value]),
        customdata: rankingRows.map((row) => outcomeCoverageLabel(row)),
        marker: { color: barColors, opacity: opacities },
        hovertemplate:
          cfg.units === "ratio"
            ? "<b>%{y}</b><br>%{x:.2f}x<br>%{customdata}<extra></extra>"
            : "<b>%{y}</b><br>%{x:.1f} " + cfg.units + "<br>%{customdata}<extra></extra>"
      }
    ],
    {
      title: { 
        text: `${cfg.rankDirection === "ascending" ? "Largest disadvantages" : "Highest countries"} - ${cfg.title}`, 
        font: { color: colors.textColor } 
      },
      xaxis: { 
        title: { text: cfg.units, font: { color: colors.textColor } }, 
        tickfont: { color: colors.textColor },
        gridcolor: colors.gridColor,
        zerolinecolor: colors.lineColor,
        zeroline: true 
      },
      yaxis: { 
        title: "", 
        tickfont: { color: colors.textColor } 
      },
      margin: { l: 135, r: 20, t: 45, b: 50 },
      paper_bgcolor: colors.paperBg,
      plot_bgcolor: colors.plotBg
    },
    { responsive: true }
  );

  if (onSelect) {
    if ((target as any).removeAllListeners) {
      (target as any).removeAllListeners("plotly_click");
    }
    (target as any).on("plotly_click", (eventData: any) => {
      if (eventData?.points?.[0]) {
        const clickedPlaceName = eventData.points[0].y;
        const found = rankingRows.find(row => row.country === clickedPlaceName);
        if (found && found.country_key) {
          onSelect(found.country_key as string);
        }
      }
    });
  }
}

export function renderEurostatOutcomeTrend(
  target: HTMLElement,
  cfg: EurostatTopic,
  data: LoadedData,
  places: string[],
  selectedYear: number,
  isDark: boolean,
  onYearSelect?: (year: number) => void
): { trendNote: string } {
  const palette = isDark ? PLACE_COLORS_DARK : PLACE_COLORS;
  const colors = themeColors(isDark);
  const traces: Array<Record<string, unknown>> = [];

  // Compute cross-country unweighted average per year as a reference line.
  // (No EU aggregate rows exist in the year-level data — all rows are country-level.)
  const allCountryRows = data.eurostat.outcomeYear.filter(
    (row) => row.metric_key === cfg.metricKey && row[cfg.value] != null && Number(row.is_aggregate) === 0
  );
  const yearMap = new Map<number, { sum: number; count: number }>();
  allCountryRows.forEach((row) => {
    const yr = Number(row.YEAR);
    const val = Number(row[cfg.value]);
    if (!Number.isFinite(yr) || !Number.isFinite(val)) return;
    const existing = yearMap.get(yr) || { sum: 0, count: 0 };
    existing.sum += val;
    existing.count += 1;
    yearMap.set(yr, existing);
  });
  const avgRows = Array.from(yearMap.entries())
    .sort(([a], [b]) => a - b)
    .map(([yr, { sum, count }]) => ({ year: yr, avg: sum / count }));
  if (avgRows.length) {
    traces.push({
      type: "scatter",
      mode: "lines",
      name: "EU avg (unweighted)",
      x: avgRows.map((r) => r.year),
      y: avgRows.map((r) => r.avg),
      line: { color: colors.lineColor, width: 1.5, dash: "dot" },
      opacity: 0.7
    });
  }

  places.forEach((place, i) => {
    const selectedRows = data.eurostat.outcomeYear
      .filter((row) => row.country_key === place && row.metric_key === cfg.metricKey && row[cfg.value] != null)
      .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));
    if (selectedRows.length) {
      traces.push({
        type: "scatter",
        mode: "lines+markers",
        name: String(selectedRows[0].country),
        x: selectedRows.map((row) => row.YEAR),
        y: selectedRows.map((row) => row[cfg.value]),
        line: { color: palette[i % palette.length], width: 2 }
      });
    }
  });

  if (!traces.length) {
    blankPlot(target, `${cfg.title} over time`, "No trend data available for the selected country.");
  } else {
    const layout = trendLayout(`${cfg.title} over time`, cfg.units);
    addSelectedYearIndicator(layout, selectedYear, isDark, colors);
    window.Plotly.newPlot(target, traces, layout, {
      responsive: true
    });

    if (onYearSelect) {
      if ((target as any).removeAllListeners) {
        (target as any).removeAllListeners("plotly_click");
      }
      (target as any).on("plotly_click", (eventData: any) => {
        if (eventData?.points?.[0]) {
          const clickedX = Number(eventData.points[0].x);
          if (Number.isFinite(clickedX)) {
            onYearSelect(clickedX);
          }
        }
      });
    }
  }
  return {
    trendNote:
      "Dotted line = unweighted EU country average. Some small countries have fewer data years — their lines end where data coverage stops."
  };
}


export function renderEurostatOutcomeBreakdown(
  target: HTMLElement,
  cfg: EurostatTopic,
  data: LoadedData,
  period: string,
  places: string[],
  isDark: boolean
): { breakdownNote: string } {
  const palette = isDark ? PLACE_COLORS_DARK : PLACE_COLORS;
  const colors = themeColors(isDark);
  const primaryPlace = places[0] || "";
  const row = eurostatOutcomeRowsForSelection(cfg, data, period, true).find((item) => item.country_key === primaryPlace);
  
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
            label.includes("Native") || label.includes("National") ? colors.lineColor : palette[0]
          )
        },
        hovertemplate: "%{x}<br>%{y:.1f}%<extra></extra>"
      }
    ],
    {
      title: { text: `${cfg.title} components - ${row.country}, ${coverage}`, font: { color: colors.textColor } },
      yaxis: { 
        title: { text: cfg.componentUnit, font: { color: colors.textColor } }, 
        tickfont: { color: colors.textColor },
        gridcolor: colors.gridColor
      },
      xaxis: { 
        title: "", 
        tickfont: { color: colors.textColor } 
      },
      margin: { l: 60, r: 20, t: 45, b: 80 },
      paper_bgcolor: colors.paperBg,
      plot_bgcolor: colors.plotBg
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
  age: string,
  isDark: boolean
): { rows: CsvRow[]; mapNote: string; rankingNote: string } {
  const rows = eurostatRowsForMap(cfg, data, period, sex, age);
  const values = rows.map((row) => row[cfg.value] as number | null);
  const scale = mapScale(values, cfg.kind === "gap");
  const colors = themeColors(isDark);

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
          marker: { line: { color: colors.lineColor, width: 0.6 } },
          colorbar: { title: cfg.units, tickfont: { color: colors.textColor } },
          hovertemplate:
            cfg.kind === "gap"
              ? "<b>%{text}</b><br>Gap: %{z:.1f} pp<br>%{customdata[2]}: %{customdata[0]:.1f}%<br>Reporting-country citizens: %{customdata[1]:.1f}%<extra></extra>"
              : "<b>%{text}</b><br>%{customdata[0]}: %{z:.1f}%<extra></extra>"
        }
      ],
      {
        title: { text: `${cfg.title} - ${period}`, font: { color: colors.textColor } },
        geo: {
          scope: "europe",
          projection: { type: "natural earth" },
          showland: true,
          landcolor: isDark ? "#1e293b" : "#eef2f4",
          showcountries: true,
          countrycolor: colors.lineColor,
          bgcolor: colors.paperBg
        },
        margin: { l: 0, r: 0, t: 45, b: 0 },
        paper_bgcolor: colors.paperBg,
        plot_bgcolor: colors.plotBg
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

export function renderEurostatEmploymentRanking(
  target: HTMLElement,
  cfg: EurostatTopic,
  rows: CsvRow[],
  selectedPlaces: Set<string>,
  isDark: boolean,
  onSelect?: (place: string) => void
): void {
  const allRows = rows
    .filter((row) => row[cfg.value] != null)
    .sort((a, b) => (b[cfg.value] as number) - (a[cfg.value] as number));

  const topRows = allRows.slice(0, 12);
  const extraRows = selectedPlaces.size > 0
    ? allRows.filter(row => selectedPlaces.has(row.country_key as string) && !topRows.includes(row)).slice(0, 5)
    : [];
  const rankingRows = [...topRows, ...extraRows].reverse();

  if (!rankingRows.length) {
    blankPlot(target, "Country ranking", "No ranking data available.");
    return;
  }

  const colors = themeColors(isDark);
  const hasSelection = selectedPlaces.size > 0;
  const barColors = rankingRows.map(row =>
    selectedPlaces.has(row.country_key as string) ? colors.accent : (hasSelection ? colors.lineColor : colors.accent)
  );
  const opacities = rankingRows.map(row =>
    hasSelection ? (selectedPlaces.has(row.country_key as string) ? 1 : 0.32) : 1
  );

  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        orientation: "h",
        y: rankingRows.map((row) => row.country),
        x: rankingRows.map((row) => row[cfg.value]),
        marker: { color: barColors, opacity: opacities },
        hovertemplate: "<b>%{y}</b><br>%{x:.1f} " + cfg.units + "<extra></extra>"
      }
    ],
    {
      title: { text: `Highest countries - ${cfg.title}`, font: { color: colors.textColor } },
      xaxis: { 
        title: { text: cfg.units, font: { color: colors.textColor } }, 
        tickfont: { color: colors.textColor },
        gridcolor: colors.gridColor,
        zerolinecolor: colors.lineColor,
        zeroline: true 
      },
      yaxis: { 
        title: "", 
        tickfont: { color: colors.textColor } 
      },
      margin: { l: 135, r: 20, t: 45, b: 50 },
      paper_bgcolor: colors.paperBg,
      plot_bgcolor: colors.plotBg
    },
    { responsive: true }
  );

  if (onSelect) {
    if ((target as any).removeAllListeners) {
      (target as any).removeAllListeners("plotly_click");
    }
    (target as any).on("plotly_click", (eventData: any) => {
      if (eventData?.points?.[0]) {
        const clickedPlaceName = eventData.points[0].y;
        const found = rankingRows.find(row => row.country === clickedPlaceName);
        if (found && found.country_key) {
          onSelect(found.country_key as string);
        }
      }
    });
  }
}

export function renderEurostatEmploymentTrend(
  target: HTMLElement,
  cfg: EurostatTopic,
  data: LoadedData,
  places: string[],
  sex: string,
  age: string,
  selectedYear: number,
  isDark: boolean,
  onYearSelect?: (year: number) => void
): { trendNote: string } {
  const palette = isDark ? PLACE_COLORS_DARK : PLACE_COLORS;
  const colors = themeColors(isDark);
  const traces: Array<Record<string, unknown>> = [];

  if (cfg.kind === "gap") {
    // EU27 aggregate as reference
    const euRows = data.eurostat.gapYear
      .filter(
        (row) =>
          row.country_key === "EU27_2020" &&
          row.sex === sex &&
          row.age === age &&
          row.comparison_group === cfg.comparisonGroup
      )
      .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));
    if (euRows.length) {
      traces.push({
        type: "scatter",
        mode: "lines+markers",
        name: "EU27 aggregate",
        x: euRows.map((row) => row.YEAR),
        y: euRows.map((row) => row.employment_rate_gap_pp),
        line: { color: colors.lineColor, width: 2 }
      });
    }

    places.forEach((place, i) => {
      if (place === "EU27_2020") return;
      const selectedRows = data.eurostat.gapYear
        .filter(
          (row) =>
            row.country_key === place &&
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
          line: { color: palette[i % palette.length], width: 2 }
        });
      }
    });
  } else {
    // For rate topics, show citizen groups for each place
    places.forEach((place, placeIdx) => {
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
        if (!groupRows.length) return;
        traces.push({
          type: "scatter",
          mode: "lines+markers",
          name: `${place} ${groupRows[0].citizen_label}`,
          x: groupRows.map((row) => row.YEAR),
          y: groupRows.map((row) => row.employment_rate_pct),
          line: { color: palette[placeIdx % palette.length] }
        });
      });
    });
  }

  if (!traces.length) {
    blankPlot(target, `${cfg.title} over time`, "No trend data available for the selected country.");
  } else {
    const layout = trendLayout(`${cfg.title} over time`, cfg.units);
    addSelectedYearIndicator(layout, selectedYear, isDark, colors);
    window.Plotly.newPlot(target, traces, layout, {
      responsive: true
    });

    if (onYearSelect) {
      if ((target as any).removeAllListeners) {
        (target as any).removeAllListeners("plotly_click");
      }
      (target as any).on("plotly_click", (eventData: any) => {
        if (eventData?.points?.[0]) {
          const clickedX = Number(eventData.points[0].x);
          if (Number.isFinite(clickedX)) {
            onYearSelect(clickedX);
          }
        }
      });
    }
  }

  return {
    trendNote:
      cfg.kind === "gap"
        ? "Trend compares the selected countries with the EU27 aggregate."
        : "Trend shows available citizenship groups for the selected countries."
  };
}

export function renderEurostatEmploymentBreakdown(
  target: HTMLElement,
  data: LoadedData,
  period: string,
  places: string[],
  sex: string,
  age: string,
  isDark: boolean
): { breakdownNote: string } {
  const primaryPlace = places[0] || "";
  const rows = data.eurostat.countryPeriod
    .filter(
      (row) =>
        row.period === period &&
        row.country_key === primaryPlace &&
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

  const colors = themeColors(isDark);
  const palette = isDark ? PLACE_COLORS_DARK : PLACE_COLORS;

  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        x: rows.map((row) => row.citizen_label),
        y: rows.map((row) => row.employment_rate_pct),
        marker: {
          color: rows.map((row) => (row.citizen_group === "reporting_country" ? colors.lineColor : palette[0]))
        },
        hovertemplate: "%{x}<br>Employment rate: %{y:.1f}%<extra></extra>"
      }
    ],
    {
      title: { text: `Employment rate by citizenship - ${rows[0].country}, ${period}`, font: { color: colors.textColor } },
      yaxis: { 
        title: { text: "% employed", font: { color: colors.textColor } }, 
        tickfont: { color: colors.textColor },
        gridcolor: colors.gridColor
      },
      xaxis: { 
        title: "", 
        tickfont: { color: colors.textColor } 
      },
      margin: { l: 60, r: 20, t: 45, b: 130 },
      paper_bgcolor: colors.paperBg,
      plot_bgcolor: colors.plotBg
    },
    { responsive: true }
  );

  return {
    breakdownNote:
      "Period values are means across available annual Eurostat observations; suppressed values remain missing."
  };
}
