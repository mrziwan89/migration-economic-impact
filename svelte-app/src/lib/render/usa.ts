import { aggregateNational, blankPlot, mapScale, trendLayout, themeColors, PLACE_COLORS, PLACE_COLORS_DARK, addSelectedYearIndicator } from "./common";
import type { CsvRow } from "../data/csv";
import type { LoadedData } from "../data/load";
import type { UsaTopic } from "../data/topics";

export function renderUsaMap(
  target: HTMLElement,
  cfg: UsaTopic,
  data: LoadedData,
  period: string,
  isDark: boolean
): { mapRows: CsvRow[]; mapNote: string; rankingNote: string } {
  const mapRows = data.usa[cfg.mapKey].filter((row) => row.period === period && row.state);
  const values = mapRows.map((row) => row[cfg.value] as number | null);
  const scale = mapScale(values, cfg.isGap);
  const colors = themeColors(isDark);

  if (!mapRows.length) {
    blankPlot(target, cfg.title, "No state data available for this selection.");
  } else {
    window.Plotly.newPlot(
      target,
      [
        {
          type: "choropleth",
          locationmode: "USA-states",
          locations: mapRows.map((row) => row.state),
          z: values,
          text: mapRows.map((row) => row.state_name),
          customdata: mapRows.map((row) => [row[cfg.foreign as string], row[cfg.us as string]]),
          colorscale: cfg.isGap ? "RdBu" : "Blues",
          reversescale: cfg.isGap,
          zmin: scale.zmin,
          zmax: scale.zmax,
          marker: { line: { color: colors.lineColor, width: 0.7 } },
          colorbar: { title: cfg.units, tickfont: { color: colors.textColor } },
          hovertemplate: cfg.isGap
            ? "<b>%{text}</b><br>Gap: %{z:.1f} " +
              cfg.units +
              "<br>Foreign-born: %{customdata[0]:.1f}<br>US-born: %{customdata[1]:.1f}<extra></extra>"
            : "<b>%{text}</b><br>Rate: %{z:.1f}%<extra></extra>"
        }
      ],
      {
        title: { text: `${cfg.title} - ${period}`, font: { color: colors.textColor } },
        geo: { 
          scope: "usa", 
          projection: { type: "albers usa" },
          bgcolor: colors.paperBg,
          lakecolor: colors.paperBg
        },
        margin: { l: 0, r: 0, t: 45, b: 0 },
        paper_bgcolor: colors.paperBg,
        plot_bgcolor: colors.plotBg
      },
      { responsive: true }
    );
  }

  return {
    mapRows,
    mapNote: cfg.note,
    rankingNote: cfg.isGap
      ? "Ranking uses the selected period. Positive gaps mean the foreign-born rate is higher than the US-born rate."
      : "Ranking uses the selected period."
  };
}

export function renderUsaRanking(
  target: HTMLElement,
  cfg: UsaTopic,
  rows: CsvRow[],
  selectedPlaces: Set<string>,
  isDark: boolean,
  onSelect?: (place: string) => void
): void {
  const allRows = rows
    .filter((row) => row[cfg.value] != null)
    .sort((a, b) => (b[cfg.value] as number) - (a[cfg.value] as number));
  
  const topRows = allRows.slice(0, 10);
  
  // Ensure selected places appear in the ranking even if not in top 10
  const extraRows = selectedPlaces.size > 0
    ? allRows.filter(row => selectedPlaces.has(row.state as string) && !topRows.includes(row)).slice(0, 5)
    : [];
  const rankingRows = [...topRows, ...extraRows].reverse();

  if (!rankingRows.length) {
    blankPlot(target, "State ranking", "No ranking data available.");
    return;
  }

  const colors = themeColors(isDark);
  const hasSelection = selectedPlaces.size > 0;
  const barColors = rankingRows.map(row => 
    selectedPlaces.has(row.state as string) ? colors.accent : (hasSelection ? colors.lineColor : colors.accent)
  );
  const opacities = rankingRows.map(row =>
    hasSelection ? (selectedPlaces.has(row.state as string) ? 1 : 0.32) : 1
  );

  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        orientation: "h",
        y: rankingRows.map((row) => row.state),
        x: rankingRows.map((row) => row[cfg.value]),
        text: rankingRows.map((row) => row.state_name),
        marker: { color: barColors, opacity: opacities },
        hovertemplate: "<b>%{text}</b><br>%{x:.1f} " + cfg.units + "<extra></extra>"
      }
    ],
    {
      title: { text: `Highest states - ${cfg.title}`, font: { color: colors.textColor } },
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
      margin: { l: 60, r: 20, t: 45, b: 50 },
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
        const clickedState = eventData.points[0].y;
        if (clickedState) {
          onSelect(clickedState);
        }
      }
    });
  }
}

export function renderUsaTrend(
  target: HTMLElement,
  cfg: UsaTopic,
  data: LoadedData,
  topic: string,
  places: string[],
  selectedYear: number,
  isDark: boolean,
  onYearSelect?: (year: number) => void
): { trendNote: string } {
  const rows = data.usa[cfg.trendKey];
  const colors = themeColors(isDark);
  const palette = isDark ? PLACE_COLORS_DARK : PLACE_COLORS;

  if (!rows.length) {
    blankPlot(target, cfg.title, "No trend data available.");
    return { trendNote: "" };
  }

  if (!cfg.isGap && topic === "lang") {
    const national = aggregateNational(rows, cfg.trendValue, null);
    const traces: Array<Record<string, unknown>> = [
      {
        type: "scatter",
        mode: "lines+markers",
        name: "National",
        x: national.map((row) => row.year),
        y: national.map((row) => row.value),
        line: { color: colors.lineColor, width: 2 }
      }
    ];
    places.forEach((place, i) => {
      const stateRows = rows
        .filter((row) => row.state === place)
        .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));
      traces.push({
        type: "scatter",
        mode: "lines+markers",
        name: place,
        x: stateRows.map((row) => row.YEAR),
        y: stateRows.map((row) => row[cfg.trendValue]),
        line: { dash: "dot", color: palette[i % palette.length], width: 2 }
      });
    });
    const layout = trendLayout(`${cfg.title} over time`, "%");
    addSelectedYearIndicator(layout, selectedYear, isDark, colors);
    window.Plotly.newPlot(target, traces, layout, { responsive: true });
    
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
  } else {
    const national = aggregateNational(rows, cfg.trendValue, "nativity_group");
    const traces: Array<Record<string, unknown>> = ["Foreign-born", "US-born"].map((group, index) => {
      const groupRows = national.filter((row) => row.group === group);
      return {
        type: "scatter",
        mode: "lines+markers",
        name: `National ${group}`,
        x: groupRows.map((row) => row.year),
        y: groupRows.map((row) => row.value),
        line: { color: index === 0 ? colors.accent : colors.lineColor, width: 2 }
      };
    });

    places.forEach((place, i) => {
      const stateRows = rows
        .filter((row) => row.state === place)
        .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));
      ["Foreign-born", "US-born"].forEach((group, gIdx) => {
        const groupRows = stateRows.filter((row) => row.nativity_group === group);
        traces.push({
          type: "scatter",
          mode: "lines",
          name: `${place} ${group}`,
          x: groupRows.map((row) => row.YEAR),
          y: groupRows.map((row) => row[cfg.trendValue]),
          line: { dash: "dot", color: palette[i % palette.length], width: gIdx === 0 ? 2 : 1.5 }
        });
      });
    });
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

  const placeStr = places.length ? places.join(", ") : "none";
  return { trendNote: `Solid lines show national trends; dotted lines show ${placeStr}.` };
}

export function renderUsaBreakdown(
  target: HTMLElement,
  cfg: UsaTopic,
  data: LoadedData,
  topic: string,
  period: string,
  places: string[],
  isDark: boolean
): { breakdownNote: string } {
  const colors = themeColors(isDark);
  const palette = isDark ? PLACE_COLORS_DARK : PLACE_COLORS;
  const primaryPlace = places[0] || "";

  if (topic === "health") {
    // For health, show first selected place's citizenship breakdown
    const rows = data.usa.healthCitPeriod
      .filter((row) => row.period === period && row.state === primaryPlace)
      .sort((a, b) => (b.uninsured_rate_pct as number) - (a.uninsured_rate_pct as number));
    window.Plotly.newPlot(
      target,
      [
        {
          type: "bar",
          x: rows.map((row) => row.citizenship_group),
          y: rows.map((row) => row.uninsured_rate_pct),
          marker: { color: palette[0] },
          hovertemplate: "%{x}<br>Uninsured: %{y:.1f}%<extra></extra>"
        }
      ],
      {
        title: { text: `Healthcare access by citizenship - ${primaryPlace}, ${period}`, font: { color: colors.textColor } },
        yaxis: { 
          title: { text: "% uninsured", font: { color: colors.textColor } }, 
          tickfont: { color: colors.textColor },
          gridcolor: colors.gridColor
        },
        xaxis: { 
          title: "", 
          tickfont: { color: colors.textColor } 
        },
        margin: { l: 60, r: 20, t: 45, b: 120 },
        paper_bgcolor: colors.paperBg,
        plot_bgcolor: colors.plotBg
      },
      { responsive: true }
    );
    return {
      breakdownNote: "Healthcare citizenship detail comes from the period-pooled ACS/IPUMS aggregate file."
    };
  }

  // For gap/rate topics: show grouped bars for each selected place
  if (cfg.isGap) {
    const traces: Array<Record<string, unknown>> = [];
    places.forEach((place, i) => {
      const row = data.usa[cfg.mapKey].find((item) => item.period === period && item.state === place);
      if (!row) return;
      traces.push({
        type: "bar",
        name: place,
        x: ["Foreign-born", "US-born"],
        y: [row[cfg.foreign as string], row[cfg.us as string]],
        marker: { color: palette[i % palette.length] },
        hovertemplate: `<b>${place}</b> %{x}<br>%{y:.1f}<extra></extra>`
      });
    });

    if (!traces.length) {
      blankPlot(target, "Selected state detail", "No detail data available.");
      return { breakdownNote: "" };
    }

    window.Plotly.newPlot(
      target,
      traces,
      {
        title: { text: `${cfg.title} components - ${period}`, font: { color: colors.textColor } },
        yaxis: { 
          title: { text: cfg.units.replace("percentage points", "%"), font: { color: colors.textColor } }, 
          tickfont: { color: colors.textColor },
          gridcolor: colors.gridColor
        },
        xaxis: { title: "", tickfont: { color: colors.textColor } },
        barmode: "group",
        margin: { l: 60, r: 20, t: 45, b: 60 },
        paper_bgcolor: colors.paperBg,
        plot_bgcolor: colors.plotBg,
        legend: { orientation: "h", y: -0.15, font: { color: colors.textColor } }
      },
      { responsive: true }
    );
    return { breakdownNote: "The gap is foreign-born rate minus US-born rate." };
  }

  // Non-gap: compare selected places vs national
  const national = aggregateNational(
    data.usa[cfg.mapKey].filter((item) => item.period === period),
    cfg.value,
    null
  )[0];

  const xLabels = [...places, "National"];
  const yValues = places.map(place => {
    const row = data.usa[cfg.mapKey].find((item) => item.period === period && item.state === place);
    return row ? row[cfg.value] : null;
  });
  yValues.push(national ? national.value : null);

  const barCols = places.map((_, i) => palette[i % palette.length]);
  barCols.push(colors.lineColor);

  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        x: xLabels,
        y: yValues,
        marker: { color: barCols },
        hovertemplate: "%{x}<br>%{y:.1f}%<extra></extra>"
      }
    ],
    {
      title: { text: `${cfg.title} detail - ${period}`, font: { color: colors.textColor } },
      yaxis: { 
        title: { text: "%", font: { color: colors.textColor } }, 
        tickfont: { color: colors.textColor },
        gridcolor: colors.gridColor
      },
      xaxis: { title: "", tickfont: { color: colors.textColor } },
      margin: { l: 60, r: 20, t: 45, b: 60 },
      paper_bgcolor: colors.paperBg,
      plot_bgcolor: colors.plotBg
    },
    { responsive: true }
  );
  return { breakdownNote: "National comparison is weighted from the period-pooled state file." };
}
