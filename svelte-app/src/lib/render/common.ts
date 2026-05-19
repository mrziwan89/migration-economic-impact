import type { CsvRow } from "../data/csv";

export interface Selection {
  topic: string;
  period: string;
  place: string;
  sex: string;
  age: string;
}

export interface RenderResult {
  mapNote?: string;
  rankingNote?: string;
  trendNote?: string;
  breakdownNote?: string;
}

export function blankPlot(target: HTMLElement, title: string, message: string): void {
  window.Plotly.newPlot(
    target,
    [],
    {
      title,
      annotations: [
        {
          text: message,
          xref: "paper",
          yref: "paper",
          x: 0.5,
          y: 0.5,
          showarrow: false,
          font: { color: "#5d6b7c" }
        }
      ],
      xaxis: { visible: false },
      yaxis: { visible: false },
      margin: { l: 20, r: 20, t: 45, b: 20 },
      paper_bgcolor: "white",
      plot_bgcolor: "white"
    },
    { responsive: true }
  );
}

export function trendLayout(title: string, yTitle: string): Record<string, unknown> {
  return {
    title,
    yaxis: { title: yTitle, zeroline: true },
    xaxis: { title: "Year", dtick: 1 },
    margin: { l: 60, r: 20, t: 45, b: 50 },
    paper_bgcolor: "white",
    plot_bgcolor: "white",
    legend: { orientation: "h", y: -0.22 }
  };
}

export function mapScale(values: Array<number | null | undefined>, isGap: boolean): { zmin: number; zmax: number } {
  const clean = values.filter((value): value is number => value != null && Number.isFinite(value));
  if (!clean.length) {
    return { zmin: 0, zmax: 1 };
  }
  if (isGap) {
    const maxAbs = Math.max(1, ...clean.map((value) => Math.abs(value)));
    return { zmin: -maxAbs, zmax: maxAbs };
  }
  return { zmin: 0, zmax: Math.max(...clean) };
}

export interface AggregatedRow {
  year: number;
  group: string;
  num: number;
  den: number;
  value: number | null;
}

export function aggregateNational(rows: CsvRow[], valueCol: string, groupCol: string | null): AggregatedRow[] {
  const byKey: Record<string, { year: number; group: string; num: number; den: number }> = {};
  rows.forEach((row) => {
    if (row.weighted_numerator == null || row.weighted_denominator == null) {
      return;
    }
    const year = Number(row.YEAR);
    const group = groupCol ? String(row[groupCol] ?? "") : "";
    const key = groupCol ? `${year}|${group}` : `${year}`;
    if (!byKey[key]) {
      byKey[key] = { year, group, num: 0, den: 0 };
    }
    byKey[key].num += Number(row.weighted_numerator);
    byKey[key].den += Number(row.weighted_denominator);
  });
  return Object.values(byKey)
    .map((row) => ({
      ...row,
      value: row.den > 0 ? (row.num / row.den) * (valueCol.includes("per_100k") ? 100000 : 100) : null
    }))
    .sort((a, b) => a.year - b.year);
}

export function uniqueSorted(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.filter((v): v is string => Boolean(v)))).sort((a, b) =>
    String(a).localeCompare(String(b))
  );
}

export function prioritize(values: string[], preferred: string[]): string[] {
  const preferredSet = new Set(preferred);
  return [
    ...preferred.filter((value) => values.includes(value)),
    ...values.filter((value) => !preferredSet.has(value))
  ];
}
