/**
 * Radar chart rendering for multi-metric comparison.
 *
 * Shows one polygon per selected place, with axes for each topic/metric.
 * Values are normalized to 0–100 scale across all places for visual comparison.
 */

import { PLACE_COLORS, PLACE_COLORS_DARK, themeColors } from "./common";
import { USA_TOPICS, EUROSTAT_TOPICS, type UsaTopic, type EurostatTopic } from "../data/topics";
import type { LoadedData } from "../data/load";

declare const Plotly: any;

// ─── Types ────────────────────────────────────────────────────────────────────

interface RadarAxis {
  key: string;        // topic key (e.g., "brain", "inc")
  label: string;      // display label
  unit: string;       // unit string
}

// ─── USA Radar ────────────────────────────────────────────────────────────────

const USA_AXES: RadarAxis[] = [
  { key: "brain",  label: "Brain Waste Gap",  unit: "pp" },
  { key: "inc",    label: "Incarceration Gap", unit: "/100k" },
  { key: "health", label: "Uninsured Gap",     unit: "pp" },
  { key: "lang",   label: "Limited English",   unit: "%" },
];

function getUsaMetricValue(
  data: LoadedData,
  topicKey: string,
  period: string,
  place: string
): number | null {
  const cfg = USA_TOPICS[topicKey];
  if (!cfg) return null;

  const rows = data.usa[cfg.mapKey].filter(
    (r: any) => r.period === period && r.state === place
  );

  if (rows.length === 0) return null;

  const val = Number(rows[0][cfg.value]);
  return Number.isFinite(val) ? val : null;
}

export function renderUsaRadar(
  el: HTMLDivElement,
  data: LoadedData,
  period: string,
  places: string[],
  isDark: boolean
): void {
  const tc = themeColors(isDark);
  const colors = isDark ? PLACE_COLORS_DARK : PLACE_COLORS;

  // Collect raw values for each axis/place
  const rawValues: Map<string, Map<string, number>> = new Map();
  for (const axis of USA_AXES) {
    const axisMap = new Map<string, number>();
    for (const place of places) {
      const val = getUsaMetricValue(data, axis.key, period, place);
      if (val !== null) {
        axisMap.set(place, Math.abs(val)); // Use absolute values for radar
      }
    }
    rawValues.set(axis.key, axisMap);
  }

  // Normalize: find global min/max per axis across ALL states (not just selected)
  const axisRanges: Map<string, { min: number; max: number }> = new Map();
  for (const axis of USA_AXES) {
    const cfg = USA_TOPICS[axis.key];
    if (!cfg) continue;
    const allRows = data.usa[cfg.mapKey].filter((r: any) => r.period === period && r.state);
    const vals = allRows.map((r: any) => Math.abs(Number(r[cfg.value]))).filter(Number.isFinite);
    if (vals.length > 0) {
      axisRanges.set(axis.key, { min: Math.min(...vals), max: Math.max(...vals) });
    }
  }

  // Build traces
  const traces: any[] = [];
  places.forEach((place, i) => {
    const r: number[] = [];
    const theta: string[] = [];
    const hoverText: string[] = [];

    for (const axis of USA_AXES) {
      const raw = rawValues.get(axis.key)?.get(place);
      const range = axisRanges.get(axis.key);
      if (raw !== undefined && range && range.max > range.min) {
        const normalized = ((raw - range.min) / (range.max - range.min)) * 100;
        r.push(Math.round(normalized * 10) / 10);
        hoverText.push(`${axis.label}: ${raw.toFixed(1)} ${axis.unit}`);
      } else if (raw !== undefined) {
        r.push(50);
        hoverText.push(`${axis.label}: ${raw.toFixed(1)} ${axis.unit}`);
      } else {
        r.push(0);
        hoverText.push(`${axis.label}: N/A`);
      }
      theta.push(axis.label);
    }

    // Close the polygon
    r.push(r[0]);
    theta.push(theta[0]);
    hoverText.push(hoverText[0]);

    traces.push({
      type: "scatterpolar",
      r,
      theta,
      fill: "toself",
      fillcolor: colors[i % colors.length].replace(")", ", 0.15)").replace("rgb", "rgba"),
      line: { color: colors[i % colors.length], width: 2 },
      marker: { size: 5, color: colors[i % colors.length] },
      name: place,
      hovertemplate: `<b>${place}</b><br>%{text}<extra></extra>`,
      text: hoverText,
    });
  });

  const layout: any = {
    polar: {
      radialaxis: {
        visible: true,
        range: [0, 105],
        showticklabels: true,
        tickfont: { size: 9, color: tc.muted },
        gridcolor: tc.line,
        linecolor: tc.line,
      },
      angularaxis: {
        tickfont: { size: 11, color: tc.text, family: "'Inter', sans-serif" },
        gridcolor: tc.line,
        linecolor: tc.line,
      },
      bgcolor: "rgba(0,0,0,0)",
    },
    showlegend: places.length > 1,
    legend: {
      font: { size: 11, color: tc.text, family: "'Inter', sans-serif" },
      bgcolor: "rgba(0,0,0,0)",
      x: 1.05,
      y: 1,
    },
    margin: { t: 40, b: 40, l: 60, r: 60 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: "'Inter', sans-serif" },
  };

  Plotly.newPlot(el, traces, layout, {
    responsive: true,
    displayModeBar: false,
  });
}

// ─── Eurostat Radar ───────────────────────────────────────────────────────────

const EUROSTAT_OUTCOME_AXES: RadarAxis[] = [
  { key: "brain_waste_gap",       label: "Brain Waste Gap",     unit: "pp" },
  { key: "temporary_contract_gap", label: "Temp Contract Gap",  unit: "pp" },
  { key: "poverty_gap",           label: "Poverty Risk Gap",    unit: "pp" },
  { key: "incarceration_ratio",   label: "Prison Ratio",        unit: "×" },
];

function getEurostatOutcomeValue(
  data: LoadedData,
  topicKey: string,
  period: string,
  place: string
): number | null {
  const cfg = EUROSTAT_TOPICS[topicKey];
  if (!cfg || cfg.source !== "outcomes") return null;

  const source = period === "Latest available"
    ? data.eurostat.outcomeLatest
    : data.eurostat.outcomePeriod;

  const rows = source.filter((r: any) =>
    r.metric_key === (cfg as EurostatTopic).metricKey &&
    r.country_key === place &&
    (period === "Latest available" || r.period === period) &&
    Number(r.is_aggregate) === 0
  );

  if (rows.length === 0) return null;
  const val = Number(rows[0][cfg.value]);
  return Number.isFinite(val) ? val : null;
}

export function renderEurostatRadar(
  el: HTMLDivElement,
  data: LoadedData,
  period: string,
  places: string[],
  isDark: boolean
): void {
  const tc = themeColors(isDark);
  const colors = isDark ? PLACE_COLORS_DARK : PLACE_COLORS;

  // Find a common period that works — for outcome axes, use the current period
  // For axes where the period isn't available, fall back to "Latest available"
  const axes = EUROSTAT_OUTCOME_AXES;

  // Compute global ranges per axis
  const axisRanges: Map<string, { min: number; max: number }> = new Map();
  for (const axis of axes) {
    const cfg = EUROSTAT_TOPICS[axis.key];
    if (!cfg || cfg.source !== "outcomes") continue;

    const source = period === "Latest available"
      ? data.eurostat.outcomeLatest
      : data.eurostat.outcomePeriod;

    const rows = source.filter((r: any) =>
      r.metric_key === (cfg as EurostatTopic).metricKey &&
      (period === "Latest available" || r.period === period) &&
      Number(r.is_aggregate) === 0
    );

    const vals = rows
      .map((r: any) => Math.abs(Number(r[cfg.value])))
      .filter(Number.isFinite);

    if (vals.length > 0) {
      axisRanges.set(axis.key, { min: Math.min(...vals), max: Math.max(...vals) });
    }
  }

  // Build traces
  const traces: any[] = [];
  places.forEach((place, i) => {
    const r: number[] = [];
    const theta: string[] = [];
    const hoverText: string[] = [];

    for (const axis of axes) {
      const raw = getEurostatOutcomeValue(data, axis.key, period, place);
      const absRaw = raw !== null ? Math.abs(raw) : null;
      const range = axisRanges.get(axis.key);

      if (absRaw !== null && range && range.max > range.min) {
        const normalized = ((absRaw - range.min) / (range.max - range.min)) * 100;
        r.push(Math.round(normalized * 10) / 10);
        hoverText.push(`${axis.label}: ${raw!.toFixed(1)} ${axis.unit}`);
      } else if (absRaw !== null) {
        r.push(50);
        hoverText.push(`${axis.label}: ${raw!.toFixed(1)} ${axis.unit}`);
      } else {
        r.push(0);
        hoverText.push(`${axis.label}: N/A`);
      }
      theta.push(axis.label);
    }

    // Close the polygon
    r.push(r[0]);
    theta.push(theta[0]);
    hoverText.push(hoverText[0]);

    // Look up country name from outcome data
    const nameRow = data.eurostat.outcomeLatest.find(
      (r: any) => r.country_key === place && Number(r.is_aggregate) === 0
    );
    const displayName = nameRow?.country || place;

    traces.push({
      type: "scatterpolar",
      r,
      theta,
      fill: "toself",
      fillcolor: colors[i % colors.length].replace(")", ", 0.15)").replace("rgb", "rgba"),
      line: { color: colors[i % colors.length], width: 2 },
      marker: { size: 5, color: colors[i % colors.length] },
      name: displayName as string,
      hovertemplate: `<b>${displayName}</b><br>%{text}<extra></extra>`,
      text: hoverText,
    });
  });

  const layout: any = {
    polar: {
      radialaxis: {
        visible: true,
        range: [0, 105],
        showticklabels: true,
        tickfont: { size: 9, color: tc.muted },
        gridcolor: tc.line,
        linecolor: tc.line,
      },
      angularaxis: {
        tickfont: { size: 11, color: tc.text, family: "'Inter', sans-serif" },
        gridcolor: tc.line,
        linecolor: tc.line,
      },
      bgcolor: "rgba(0,0,0,0)",
    },
    showlegend: places.length > 1,
    legend: {
      font: { size: 11, color: tc.text, family: "'Inter', sans-serif" },
      bgcolor: "rgba(0,0,0,0)",
      x: 1.05,
      y: 1,
    },
    margin: { t: 40, b: 40, l: 60, r: 60 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: "'Inter', sans-serif" },
  };

  Plotly.newPlot(el, traces, layout, {
    responsive: true,
    displayModeBar: false,
  });
}
