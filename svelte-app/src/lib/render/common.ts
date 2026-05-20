import type { CsvRow } from "../data/csv";

export interface Selection {
  topic: string;
  period: string;
  places: string[];
  sex: string;
  age: string;
}

export interface RenderResult {
  mapNote?: string;
  rankingNote?: string;
  trendNote?: string;
  breakdownNote?: string;
}

export interface ThemeColors {
  paperBg: string;
  plotBg: string;
  textColor: string;
  gridColor: string;
  lineColor: string;
  accent: string;
}

export function themeColors(isDark: boolean): ThemeColors {
  return {
    paperBg: isDark ? "#1e293b" : "white",
    plotBg: isDark ? "#1e293b" : "white",
    textColor: isDark ? "#f8fafc" : "#18212f",
    gridColor: isDark ? "#334155" : "#e2e8f0",
    lineColor: isDark ? "#475569" : "#cbd5e1",
    accent: isDark ? "#60BBEE" : "#0077BB"
  };
}

// Colorblind-safe palette for up to 3 selected places (plus national)
export const PLACE_COLORS = ["#0077BB", "#EE7733", "#009988"];
export const PLACE_COLORS_DARK = ["#60BBEE", "#EE7733", "#33BBAA"];

export function blankPlot(target: HTMLElement, title: string, message: string): void {
  const isDark = typeof document !== "undefined" && document.documentElement.classList.contains("dark");
  const colors = themeColors(isDark);
  window.Plotly.newPlot(
    target,
    [],
    {
      title: { text: title, font: { color: colors.textColor } },
      annotations: [
        {
          text: message,
          xref: "paper",
          yref: "paper",
          x: 0.5,
          y: 0.5,
          showarrow: false,
          font: { color: colors.textColor }
        }
      ],
      xaxis: { visible: false },
      yaxis: { visible: false },
      margin: { l: 20, r: 20, t: 45, b: 20 },
      paper_bgcolor: colors.paperBg,
      plot_bgcolor: colors.plotBg
    },
    { responsive: true }
  );
}

export function trendLayout(title: string, yTitle: string): Record<string, unknown> {
  const isDark = typeof document !== "undefined" && document.documentElement.classList.contains("dark");
  const colors = themeColors(isDark);
  return {
    title: { text: title, font: { color: colors.textColor } },
    yaxis: { 
      title: { text: yTitle, font: { color: colors.textColor } }, 
      tickfont: { color: colors.textColor },
      gridcolor: colors.gridColor,
      zerolinecolor: colors.lineColor,
      zeroline: true 
    },
    xaxis: { 
      title: { text: "Year", font: { color: colors.textColor } }, 
      tickfont: { color: colors.textColor },
      gridcolor: colors.gridColor,
      linecolor: colors.lineColor,
      dtick: 1 
    },
    margin: { l: 60, r: 20, t: 45, b: 50 },
    paper_bgcolor: colors.paperBg,
    plot_bgcolor: colors.plotBg,
    legend: { orientation: "h", y: -0.22, font: { color: colors.textColor } }
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

export function addSelectedYearIndicator(
  layout: Record<string, any>,
  selectedYear: number,
  isDark: boolean,
  colors: ThemeColors
): void {
  if (!selectedYear) return;

  layout.shapes = [
    ...(layout.shapes || []),
    {
      type: "line",
      x0: selectedYear,
      x1: selectedYear,
      y0: 0,
      y1: 1,
      yref: "paper",
      line: {
        color: colors.accent,
        width: 2,
        dash: "dashdot"
      }
    }
  ];

  layout.annotations = [
    ...(layout.annotations || []),
    {
      x: selectedYear,
      y: 1.02,
      yref: "paper",
      text: `<b>${selectedYear}</b>`,
      showarrow: false,
      font: {
        family: "'Inter', sans-serif",
        size: 11,
        color: isDark ? "#ffffff" : "#0f172a"
      },
      bgcolor: colors.paperBg,
      bordercolor: colors.accent,
      borderwidth: 1.5,
      borderpad: 4,
      yshift: 10
    }
  ];
}
