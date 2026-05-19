import type { CsvRow } from "../data/csv";
import type { LoadedData } from "../data/load";
import type { UsaTopic } from "../data/topics";
import { aggregateNational, blankPlot, mapScale, trendLayout } from "./common";

export function renderUsaMap(
  target: HTMLElement,
  cfg: UsaTopic,
  data: LoadedData,
  period: string
): { mapRows: CsvRow[]; mapNote: string; rankingNote: string } {
  const mapRows = data.usa[cfg.mapKey].filter((row) => row.period === period && row.state);
  const values = mapRows.map((row) => row[cfg.value] as number | null);
  const scale = mapScale(values, cfg.isGap);

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
          marker: { line: { color: "white", width: 0.7 } },
          colorbar: { title: cfg.units },
          hovertemplate: cfg.isGap
            ? "<b>%{text}</b><br>Gap: %{z:.1f} " +
              cfg.units +
              "<br>Foreign-born: %{customdata[0]:.1f}<br>US-born: %{customdata[1]:.1f}<extra></extra>"
            : "<b>%{text}</b><br>Rate: %{z:.1f}%<extra></extra>"
        }
      ],
      {
        title: `${cfg.title} - ${period}`,
        geo: { scope: "usa", projection: { type: "albers usa" } },
        margin: { l: 0, r: 0, t: 45, b: 0 },
        paper_bgcolor: "white",
        plot_bgcolor: "white"
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

export function renderUsaRanking(target: HTMLElement, cfg: UsaTopic, rows: CsvRow[]): void {
  const rankingRows = rows
    .filter((row) => row[cfg.value] != null)
    .sort((a, b) => (b[cfg.value] as number) - (a[cfg.value] as number))
    .slice(0, 10)
    .reverse();

  if (!rankingRows.length) {
    blankPlot(target, "State ranking", "No ranking data available.");
    return;
  }

  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        orientation: "h",
        y: rankingRows.map((row) => row.state),
        x: rankingRows.map((row) => row[cfg.value]),
        text: rankingRows.map((row) => row.state_name),
        marker: { color: "#116466" },
        hovertemplate: "<b>%{text}</b><br>%{x:.1f} " + cfg.units + "<extra></extra>"
      }
    ],
    {
      title: `Highest states - ${cfg.title}`,
      xaxis: { title: cfg.units, zeroline: true },
      yaxis: { title: "" },
      margin: { l: 60, r: 20, t: 45, b: 50 },
      paper_bgcolor: "white",
      plot_bgcolor: "white"
    },
    { responsive: true }
  );
}

export function renderUsaTrend(
  target: HTMLElement,
  cfg: UsaTopic,
  data: LoadedData,
  topic: string,
  place: string
): { trendNote: string } {
  const rows = data.usa[cfg.trendKey];

  if (!rows.length) {
    blankPlot(target, cfg.title, "No trend data available.");
    return { trendNote: "" };
  }

  if (!cfg.isGap && topic === "lang") {
    const national = aggregateNational(rows, cfg.trendValue, null);
    const stateRows = rows
      .filter((row) => row.state === place)
      .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));
    window.Plotly.newPlot(
      target,
      [
        {
          type: "scatter",
          mode: "lines+markers",
          name: "National",
          x: national.map((row) => row.year),
          y: national.map((row) => row.value),
          line: { color: "#116466" }
        },
        {
          type: "scatter",
          mode: "lines+markers",
          name: place,
          x: stateRows.map((row) => row.YEAR),
          y: stateRows.map((row) => row[cfg.trendValue]),
          line: { color: "#c44536" }
        }
      ],
      trendLayout(`${cfg.title} over time`, "%"),
      { responsive: true }
    );
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
        line: { color: index === 0 ? "#116466" : "#6f7f8f" }
      };
    });
    const stateRows = rows
      .filter((row) => row.state === place)
      .sort((a, b) => Number(a.YEAR) - Number(b.YEAR));
    ["Foreign-born", "US-born"].forEach((group, index) => {
      const groupRows = stateRows.filter((row) => row.nativity_group === group);
      traces.push({
        type: "scatter",
        mode: "lines",
        name: `${place} ${group}`,
        x: groupRows.map((row) => row.YEAR),
        y: groupRows.map((row) => row[cfg.trendValue]),
        line: { dash: "dot", color: index === 0 ? "#c44536" : "#9a8c70" }
      });
    });
    window.Plotly.newPlot(target, traces, trendLayout(`${cfg.title} over time`, cfg.units), {
      responsive: true
    });
  }

  return { trendNote: "Solid lines show national trends; dotted lines show the selected state." };
}

export function renderUsaBreakdown(
  target: HTMLElement,
  cfg: UsaTopic,
  data: LoadedData,
  topic: string,
  period: string,
  place: string
): { breakdownNote: string } {
  if (topic === "health") {
    const rows = data.usa.healthCitPeriod
      .filter((row) => row.period === period && row.state === place)
      .sort((a, b) => (b.uninsured_rate_pct as number) - (a.uninsured_rate_pct as number));
    window.Plotly.newPlot(
      target,
      [
        {
          type: "bar",
          x: rows.map((row) => row.citizenship_group),
          y: rows.map((row) => row.uninsured_rate_pct),
          marker: { color: "#c44536" },
          hovertemplate: "%{x}<br>Uninsured: %{y:.1f}%<extra></extra>"
        }
      ],
      {
        title: `Healthcare access by citizenship - ${place}, ${period}`,
        yaxis: { title: "% uninsured" },
        xaxis: { title: "" },
        margin: { l: 60, r: 20, t: 45, b: 120 },
        paper_bgcolor: "white",
        plot_bgcolor: "white"
      },
      { responsive: true }
    );
    return {
      breakdownNote: "Healthcare citizenship detail comes from the period-pooled ACS/IPUMS aggregate file."
    };
  }

  const row = data.usa[cfg.mapKey].find((item) => item.period === period && item.state === place);
  if (!row) {
    blankPlot(target, "Selected state detail", "No detail data available.");
    return { breakdownNote: "" };
  }

  if (cfg.isGap) {
    window.Plotly.newPlot(
      target,
      [
        {
          type: "bar",
          x: ["Foreign-born", "US-born"],
          y: [row[cfg.foreign as string], row[cfg.us as string]],
          marker: { color: ["#116466", "#6f7f8f"] },
          hovertemplate: "%{x}<br>%{y:.1f}<extra></extra>"
        }
      ],
      {
        title: `${cfg.title} components - ${place}, ${period}`,
        yaxis: { title: cfg.units.replace("percentage points", "%") },
        xaxis: { title: "" },
        margin: { l: 60, r: 20, t: 45, b: 60 },
        paper_bgcolor: "white",
        plot_bgcolor: "white"
      },
      { responsive: true }
    );
    return { breakdownNote: "The gap is foreign-born rate minus US-born rate." };
  }

  const national = aggregateNational(
    data.usa[cfg.mapKey].filter((item) => item.period === period),
    cfg.value,
    null
  )[0];
  window.Plotly.newPlot(
    target,
    [
      {
        type: "bar",
        x: [place, "National"],
        y: [row[cfg.value], national ? national.value : null],
        marker: { color: ["#116466", "#6f7f8f"] },
        hovertemplate: "%{x}<br>%{y:.1f}%<extra></extra>"
      }
    ],
    {
      title: `${cfg.title} detail - ${place}, ${period}`,
      yaxis: { title: "%" },
      xaxis: { title: "" },
      margin: { l: 60, r: 20, t: 45, b: 60 },
      paper_bgcolor: "white",
      plot_bgcolor: "white"
    },
    { responsive: true }
  );
  return { breakdownNote: "National comparison is weighted from the period-pooled state file." };
}
