<script lang="ts">
  import { onMount } from "svelte";
  import { geoMercator, geoPath } from "d3-geo";
  import type { LoadedData } from "../data/load";
  import { USA_TOPICS, EUROSTAT_TOPICS } from "../data/topics";
  import { eurostatRowsForMap, eurostatOutcomeRowsForSelection } from "../render/eurostat";
  import { STATE_NAMES, MAX_SELECTIONS } from "../data/lookups";

  // ─── Props ────────────────────────────────────────────────────────────────────
  let {
    region = $bindable(),
    topic = $bindable(),
    period = $bindable(),
    sex = $bindable(),
    age = $bindable(),
    places = $bindable(),
    isDark = false,
    data
  } = $props<{
    region: "usa" | "eurostat" | "world";
    topic: string;
    period: string;
    sex: string;
    age: string;
    places: string[];
    isDark?: boolean;
    data: LoadedData;
  }>();

  // ─── Static lookup tables ─────────────────────────────────────────────────────
  const STATE_NAME_TO_USPS: Record<string, string> = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
    "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC"
  };

  const EUROPE_ISO3 = new Set([
    "AUT", "BEL", "BGR", "BIH", "CHE", "CYP", "CZE", "DEU", "DNK", "EST", "GRC", "ESP", "FIN", "FRA",
    "HRV", "HUN", "IRL", "ITA", "LTU", "LUX", "LVA", "MKD", "MLT", "MNE", "NLD", "NOR", "POL", "PRT",
    "ROU", "SWE", "SVN", "SVK", "SRB", "TUR", "GBR", "ALB", "ISL"
  ]);

  const EUROPE_ISO3_TO_NAME: Record<string, string> = {
    AUT: "Austria", BEL: "Belgium", BGR: "Bulgaria", BIH: "Bosnia and Herzegovina",
    CHE: "Switzerland", CYP: "Cyprus", CZE: "Czech Republic", DEU: "Germany", DNK: "Denmark",
    EST: "Estonia", GRC: "Greece", ESP: "Spain", FIN: "Finland", FRA: "France", HRV: "Croatia",
    HUN: "Hungary", IRL: "Ireland", ITA: "Italy", LTU: "Lithuania", LUX: "Luxembourg",
    LVA: "Latvia", MKD: "North Macedonia", MLT: "Malta", MNE: "Montenegro", NLD: "Netherlands",
    NOR: "Norway", POL: "Poland", PRT: "Portugal", ROU: "Romania", SWE: "Sweden",
    SVN: "Slovenia", SVK: "Slovakia", SRB: "Serbia", TUR: "Turkey", GBR: "United Kingdom",
    ALB: "Albania", ISL: "Iceland"
  };

  // ─── Reactive GeoJSON state ───────────────────────────────────────────────────
  let worldGeo = $state.raw<any>(null);
  let usStatesGeo = $state.raw<any>(null);
  let tooltipData = $state<{ x: number; y: number; visible: boolean; title: string; content: string }>({
    x: 0, y: 0, visible: false, title: "", content: ""
  });
  let hoveredMacro = $state<"usa" | "europe" | null>(null);

  // Selection set for quick lookups
  const selectedSet = $derived(new Set(places));

  // ─── Property helpers ─────────────────────────────────────────────────────────
  function getProp(properties: any, keys: string[]): any {
    if (!properties) return undefined;
    for (const key of keys) {
      if (properties[key] !== undefined) return properties[key];
    }
    return undefined;
  }
  /**
   * Get ISO-3 code from a GeoJSON feature.
   * Natural Earth uses ISO_A3 = "-99" for countries with overseas territories
   * (e.g., France, Norway). We fall back to ISO_A3_EH then ADM0_A3 in that case.
   */
  function getIso3(f: any): string {
    const p = f?.properties;
    if (!p) return "";
    // Try standard field first; if it's the sentinel -99, keep trying fallbacks
    for (const key of ["ISO_A3", "iso_a3", "ISO_A3_EH", "ADM0_A3", "adm0_a3"]) {
      const val = p[key];
      if (val && val !== "-99") return val;
    }
    return "";
  }
  const getName  = (f: any) => getProp(f?.properties, ["NAME",    "name",    "NAME_LONG","name_long"]);
  const getAdmin = (f: any) => getProp(f?.properties, ["ADMIN",   "admin"]);

  // ─── SVG viewport & projection ────────────────────────────────────────────────
  const VW = 960;
  const VH = 480;

  const projection = geoMercator()
    .scale(180)
    .center([-30, 42])
    .translate([VW / 2, VH / 2]);

  const pathGenerator = geoPath().projection(projection);

  // ─── Data load ────────────────────────────────────────────────────────────────
  onMount(async () => {
    try {
      const [worldRes, statesRes] = await Promise.all([
        fetch("/data/geo/world.json"),
        fetch("/data/geo/us-states.json")
      ]);
      worldGeo    = await worldRes.json();
      usStatesGeo = await statesRes.json();
    } catch (err) {
      console.error("Error loading geographic assets", err);
    }
  });

  // ─── Derived data values ──────────────────────────────────────────────────────
  const usaStateValues = $derived.by(() => {
    if (region !== "usa" || !data) return new Map<string, number>();
    const cfg = USA_TOPICS[topic];
    if (!cfg) return new Map<string, number>();
    const rows = data.usa[cfg.mapKey]?.filter((r: any) => r.period === period && r.state) || [];
    const m = new Map<string, number>();
    rows.forEach((r: any) => { if (r.state && r[cfg.value] != null) m.set(r.state as string, Number(r[cfg.value])); });
    return m;
  });

  const eurostatCountryValues = $derived.by(() => {
    if (region !== "eurostat" || !data) return new Map<string, number>();
    const cfg = EUROSTAT_TOPICS[topic];
    if (!cfg) return new Map<string, number>();
    const m = new Map<string, number>();
    if (cfg.source === "outcomes") {
      eurostatOutcomeRowsForSelection(cfg, data, period).forEach((r: any) => {
        if (r.iso3 && r[cfg.value] != null) m.set(r.iso3 as string, Number(r[cfg.value]));
      });
    } else {
      eurostatRowsForMap(cfg, data, period, sex, age).forEach((r: any) => {
        if (r.iso3 && r[cfg.value] != null) m.set(r.iso3 as string, Number(r[cfg.value]));
      });
    }
    return m;
  });

  const minMax = $derived.by(() => {
    if (!data || region === "world") return { min: -10, max: 10 };

    let vals: number[] = [];
    let isGap = false;

    if (region === "usa") {
      const cfg = USA_TOPICS[topic];
      if (cfg) {
        isGap = cfg.isGap;
        const rows = data.usa[cfg.mapKey]?.filter((r: any) => r.state) || [];
        vals = rows.map((r: any) => Number(r[cfg.value])).filter(Number.isFinite);
      }
    } else if (region === "eurostat") {
      const cfg = EUROSTAT_TOPICS[topic];
      if (cfg) {
        isGap = Boolean(cfg.isGap);
        if (cfg.source === "outcomes") {
          const rows = data.eurostat.outcomePeriod?.filter((r: any) => 
            r.metric_key === cfg.metricKey && r.country_key && Number(r.is_aggregate) === 0
          ) || [];
          vals = rows.map((r: any) => Number(r[cfg.value])).filter(Number.isFinite);
        } else {
          const source = cfg.kind === "gap" ? data.eurostat.gapPeriod : data.eurostat.countryPeriod;
          const rows = source?.filter((r: any) => 
            r.is_aggregate === 0 && r.iso3
          ) || [];
          const filteredRows = rows.filter((r: any) => {
            if (cfg.kind === "gap") {
              return r.comparison_group === cfg.comparisonGroup;
            } else {
              return r.citizen_group === cfg.citizenGroup;
            }
          });
          vals = filteredRows.map((r: any) => Number(r[cfg.value])).filter(Number.isFinite);
        }
      }
    }

    if (!vals.length) return { min: -10, max: 10 };

    if (isGap) {
      const mx = Math.max(1, ...vals.map(Math.abs));
      return { min: -mx, max: mx };
    }
    return { min: Math.min(0, ...vals), max: Math.max(1, ...vals) };
  });

  // ─── Colorblind-safe palette ──────────────────────────────────────────────────
  const baseColor      = $derived(isDark ? "#1e293b" : "#f8fafc");
  const nullColor      = $derived(isDark ? "#263348" : "#e8edf2");
  const highColor      = $derived(isDark ? "#EE7733" : "#D4521A");
  const lowColor       = $derived(isDark ? "#0077BB" : "#006093");

  // World overview colours
  const worldStroke        = $derived(isDark ? "#1a2536" : "#ffffff");
  const hotspotFill        = $derived(isDark ? "#334155" : "#c8d8e8");
  const hotspotHoverFill   = $derived(isDark ? "#3b6b9e" : "#4fa8d0");
  const hotspotBorder      = $derived(isDark ? "#60a5fa" : "#0077BB");
  const worldInactiveFill  = $derived(isDark ? "#283850" : "#e9edf2");

  const detailStrokeSelected = $derived(isDark ? "#ffffff" : "#0f172a");
  const detailStrokeNormal   = $derived(isDark ? "#1a2536" : "#ffffff");

  // ─── Legend gradient ──────────────────────────────────────────────────────────
  const legendGradient = $derived.by(() => {
    if (region === "usa") {
      return USA_TOPICS[topic]?.isGap
        ? `${lowColor}, ${baseColor}, ${highColor}`
        : `${baseColor}, ${highColor}`;
    }
    if (region === "eurostat") {
      const cfg = EUROSTAT_TOPICS[topic];
      if (Boolean(cfg?.isGap)) {
        return cfg?.reversescale
          ? `${highColor}, ${baseColor}, ${lowColor}`
          : `${lowColor}, ${baseColor}, ${highColor}`;
      }
      return `${baseColor}, ${highColor}`;
    }
    return `${baseColor}, ${highColor}`;
  });

  // ─── Hex interpolator ─────────────────────────────────────────────────────────
  function lerpHex(c1: string, c2: string, t: number): string {
    const r1 = parseInt(c1.slice(1, 3), 16), g1 = parseInt(c1.slice(3, 5), 16), b1 = parseInt(c1.slice(5, 7), 16);
    const r2 = parseInt(c2.slice(1, 3), 16), g2 = parseInt(c2.slice(3, 5), 16), b2 = parseInt(c2.slice(5, 7), 16);
    const r = Math.round(r1 + (r2 - r1) * t);
    const g = Math.round(g1 + (g2 - g1) * t);
    const b = Math.round(b1 + (b2 - b1) * t);
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  }

  // ─── Choropleth fill ──────────────────────────────────────────────────────────
  function getPathColor(key: string): string {
    if (region === "usa") {
      const val = usaStateValues.get(key);
      if (val == null) return nullColor;
      const cfg = USA_TOPICS[topic];
      if (cfg?.isGap) {
        if (val === 0) return baseColor;
        return val > 0
          ? lerpHex(baseColor, highColor, Math.min(1, val / minMax.max))
          : lerpHex(baseColor, lowColor,  Math.min(1, Math.abs(val) / Math.abs(minMax.min)));
      }
      return lerpHex(baseColor, highColor, Math.min(1, val / minMax.max));
    }
    if (region === "eurostat") {
      const val = eurostatCountryValues.get(key);
      if (val == null) return nullColor;
      const cfg = EUROSTAT_TOPICS[topic];
      if (Boolean(cfg?.isGap)) {
        if (val === 0) return baseColor;
        if (val > 0) {
          const end = cfg?.reversescale ? lowColor : highColor;
          return lerpHex(baseColor, end, Math.min(1, val / minMax.max));
        } else {
          const end = cfg?.reversescale ? highColor : lowColor;
          return lerpHex(baseColor, end, Math.min(1, Math.abs(val) / Math.abs(minMax.min)));
        }
      }
      return lerpHex(baseColor, highColor, Math.min(1, val / minMax.max));
    }
    return nullColor;
  }

  // ─── Multi-select interaction handlers ────────────────────────────────────────
  function handleMacroClick(macroRegion: "usa" | "europe") {
    if (macroRegion === "usa") {
      region = "usa";
      places = ["CA"];
    } else {
      region = "eurostat";
      places = ["DEU"];
    }
    hoveredMacro = null;
    hideTooltip();
  }

  function togglePlace(key: string) {
    if (selectedSet.has(key)) {
      // Deselect
      places = places.filter((p: string) => p !== key);
    } else if (places.length < MAX_SELECTIONS) {
      // Add (max 3)
      places = [...places, key];
    }
    // If at max, ignore click (visual feedback via tooltip could be added)
  }

  function handleDetailClick(feature: any) {
    if (region === "usa") {
      const usps = STATE_NAME_TO_USPS[getName(feature)];
      if (usps) togglePlace(usps);
    } else if (region === "eurostat") {
      const iso3 = getIso3(feature);
      if (EUROPE_ISO3.has(iso3)) togglePlace(iso3);
    }
  }

  function showMacroTooltip(e: MouseEvent, macroRegion: "usa" | "europe") {
    const svgEl = (e.currentTarget as SVGGraphicsElement).ownerSVGElement;
    if (!svgEl) return;
    const svgRect  = svgEl.getBoundingClientRect();
    const pathRect = (e.currentTarget as SVGGraphicsElement).getBoundingClientRect();
    const tx = pathRect.left - svgRect.left + pathRect.width / 2;
    const ty = pathRect.top  - svgRect.top  - 8;

    hoveredMacro = macroRegion;
    if (macroRegion === "usa") {
      tooltipData = { x: tx, y: ty, visible: true, title: "United States", content: "Click to explore state-level economic indicators and brain waste statistics." };
    } else {
      tooltipData = { x: tx, y: ty, visible: true, title: "Europe", content: "Click to explore country-level employment gap, poverty risk, and precarious contract statistics." };
    }
  }

  function showDetailTooltip(e: MouseEvent, feature: any) {
    const svgEl = (e.currentTarget as SVGGraphicsElement).ownerSVGElement;
    if (!svgEl) return;
    const svgRect  = svgEl.getBoundingClientRect();
    const pathRect = (e.currentTarget as SVGGraphicsElement).getBoundingClientRect();
    const tx = pathRect.left - svgRect.left + pathRect.width / 2;
    const ty = pathRect.top  - svgRect.top  - 8;

    if (region === "usa") {
      const stateName = getName(feature);
      const usps = STATE_NAME_TO_USPS[stateName];
      const val = usps ? usaStateValues.get(usps) : null;
      const units = USA_TOPICS[topic]?.units || "";
      const selMarker = selectedSet.has(usps) ? " ✓" : "";
      tooltipData = { x: tx, y: ty, visible: true, title: `${stateName}${selMarker}`, content: `${USA_TOPICS[topic]?.label}: ${val != null ? val.toFixed(1) + " " + units : "No data"}` };
    } else if (region === "eurostat") {
      const iso3 = getIso3(feature);
      const name = EUROPE_ISO3_TO_NAME[iso3] || getName(feature) || iso3;
      const val = eurostatCountryValues.get(iso3);
      const units = EUROSTAT_TOPICS[topic]?.units || "";
      const selMarker = selectedSet.has(iso3) ? " ✓" : "";
      tooltipData = { x: tx, y: ty, visible: true, title: `${name}${selMarker}`, content: `${EUROSTAT_TOPICS[topic]?.label}: ${val != null ? val.toFixed(1) + " " + units : "No data"}` };
    }
  }

  function hideTooltip() { tooltipData.visible = false; hoveredMacro = null; }

  function resetToWorld() { region = "world"; places = []; hideTooltip(); }

  function clearSelection() { places = []; }

  // ─── Compute centroid for checkmark pins ──────────────────────────────────────
  function getCentroid(feature: any): [number, number] | null {
    const c = pathGenerator.centroid(feature);
    if (c && isFinite(c[0]) && isFinite(c[1])) return c;
    return null;
  }

  // ─── Zoom transform ───────────────────────────────────────────────────────────
  // CSS `translate(tx,ty) scale(s)` applies RIGHT-TO-LEFT: first scale, then translate.
  // tx = screenCX - regionCX * s, ty = screenCY - regionCY * s
  //
  // US center (including Alaska + Hawaii) ≈ (213.0, 240) → s=2.0 → tx=-9.8, ty=-240
  // Core Europe centroid                  ≈ (612.0, 170.8) → s=2.3 → tx=-927.6, ty=-152.8
  const transformStyle = $derived.by(() => {
    // Scale 2.0 (was 2.3) to pull Hawaii into view; adjust ty to keep Alaska visible.
    if (region === "usa")      return "transform: translate(-9.0px, -218px) scale(2.0);"
    if (region === "eurostat") return "transform: translate(-927.6px, -152.8px) scale(2.3);"
    return "transform: translate(0px, 0px) scale(1);";
  });

  // Helper: is a us-states.json feature a US state?
  function isUSState(feature: any): boolean {
    const admin = getAdmin(feature);
    return admin === "United States of America" || admin === "United States";
  }
</script>

<div class="map-container">
  <!-- ── Controls bar ──────────────────────────────────────────────────────── -->
  <div class="map-controls-bar">
    {#if region !== "world"}
      <button class="back-btn" onclick={resetToWorld} aria-label="Return to overview">
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Overview
      </button>
    {/if}
    {#if region === "world"}
      <div class="world-hint">
        <span class="hint-dot"></span>
        Click the <strong>US</strong> or <strong>Europe</strong> to zoom in
      </div>
    {/if}
    {#if region !== "world" && places.length > 0}
      <div class="selection-chips">
        {#each places as p}
          <span class="sel-chip">
            {p}
            <button class="chip-remove" onclick={() => togglePlace(p)} aria-label="Deselect {p}">×</button>
          </span>
        {/each}
        {#if places.length > 1}
          <button class="clear-all-btn" onclick={clearSelection}>Clear all</button>
        {/if}
      </div>
      <span class="sel-counter">{places.length}/{MAX_SELECTIONS}</span>
    {/if}
    <div class="region-badge">
      {region === "usa" ? "🇺🇸 United States" : region === "eurostat" ? "🇪🇺 Europe" : "🌍 World Overview"}
    </div>
  </div>

  <!-- ── Map SVG ────────────────────────────────────────────────────────────── -->
  <svg
    viewBox="0 0 {VW} {VH}"
    class="map-svg"
    aria-label="Interactive migration data map"
    role="img"
  >
    <rect width={VW} height={VH} class="ocean-rect" />

    <g
      class="map-group"
      style="{transformStyle} transform-origin: 0 0; transition: transform 0.9s cubic-bezier(0.25, 1, 0.45, 1);"
    >
      <!-- ── BASE WORLD LAYER ────────────────────────────────────────────── -->
      {#if worldGeo}
        <!-- Non-hotspot countries (inactive) -->
        {#each worldGeo.features as feature}
          {@const iso3 = getIso3(feature)}
          {@const isEurope = EUROPE_ISO3.has(iso3)}
          {@const isUSA = iso3 === "USA"}
          {#if !isEurope && !isUSA}
            <path
              d={pathGenerator(feature)}
              class="world-path inactive-path {region !== 'world' ? 'hidden-world' : ''}"
              fill={worldInactiveFill}
              stroke={worldStroke}
              stroke-width="0.5"
            />
          {/if}
        {/each}

        <!-- USA polygon (world.json) as inactive background -->
        {#each worldGeo.features as feature}
          {@const iso3 = getIso3(feature)}
          {#if iso3 === "USA"}
            <path
              d={pathGenerator(feature)}
              class="world-path inactive-path {region !== 'world' ? 'hidden-world' : ''}"
              fill={worldInactiveFill}
              stroke={worldStroke}
              stroke-width="0.5"
            />
          {/if}
        {/each}

        <!-- Europe countries as unified hover hotspot -->
        {#each worldGeo.features as feature}
          {@const iso3 = getIso3(feature)}
          {#if EUROPE_ISO3.has(iso3)}
            <path
              d={pathGenerator(feature)}
              class="world-path hotspot-path {region !== 'world' ? 'hidden-world' : ''}"
              fill={hoveredMacro === "europe" ? hotspotHoverFill : hotspotFill}
              stroke={hotspotBorder}
              stroke-width="1.6"
              role="button"
              tabindex="0"
              onclick={() => handleMacroClick("europe")}
              onkeydown={(e) => e.key === "Enter" && handleMacroClick("europe")}
              onmouseenter={(e) => showMacroTooltip(e, "europe")}
              onmouseleave={hideTooltip}
            />
          {/if}
        {/each}
      {/if}

      <!-- US states as hotspot layer (includes Alaska) -->
      {#if region === "world" && usStatesGeo}
        {#each usStatesGeo.features as feature}
          {#if isUSState(feature)}
            <path
              d={pathGenerator(feature)}
              class="world-path hotspot-path"
              fill={hoveredMacro === "usa" ? hotspotHoverFill : hotspotFill}
              stroke={hotspotBorder}
              stroke-width="1.6"
              role="button"
              tabindex="0"
              onclick={() => handleMacroClick("usa")}
              onkeydown={(e) => e.key === "Enter" && handleMacroClick("usa")}
              onmouseenter={(e) => showMacroTooltip(e, "usa")}
              onmouseleave={hideTooltip}
            />
          {/if}
        {/each}
      {/if}

      <!-- ── USA STATES DETAIL LAYER (after zoom) ────────────────────────── -->
      {#if region === "usa" && usStatesGeo}
        {#each usStatesGeo.features as feature}
          {#if isUSState(feature)}
            {@const stateName  = getName(feature)}
            {@const usps       = STATE_NAME_TO_USPS[stateName]}
            {@const isSelected = selectedSet.has(usps)}
            {@const hasAnySelection = places.length > 0}
            <path
              d={pathGenerator(feature)}
              class="detail-path {isSelected ? 'selected-path' : ''} {hasAnySelection && !isSelected ? 'faded-path' : ''}"
              fill={getPathColor(usps)}
              stroke={isSelected ? detailStrokeSelected : detailStrokeNormal}
              stroke-width={isSelected ? "0.8" : "0.5"}
              role="button"
              tabindex="0"
              onclick={() => handleDetailClick(feature)}
              onkeydown={(e) => e.key === "Enter" && handleDetailClick(feature)}
              onmouseenter={(e) => showDetailTooltip(e, feature)}
              onmouseleave={() => { tooltipData.visible = false; }}
            />
          {/if}
        {/each}
      {/if}

      <!-- ── EUROPE COUNTRY DETAIL LAYER (after zoom) ────────────────────── -->
      {#if region === "eurostat" && worldGeo}
        {#each worldGeo.features as feature}
          {@const iso3 = getIso3(feature)}
          {#if EUROPE_ISO3.has(iso3)}
            {@const isSelected = selectedSet.has(iso3)}
            {@const hasAnySelection = places.length > 0}
            <path
              d={pathGenerator(feature)}
              class="detail-path {isSelected ? 'selected-path' : ''} {hasAnySelection && !isSelected ? 'faded-path' : ''}"
              fill={getPathColor(iso3)}
              stroke={isSelected ? detailStrokeSelected : detailStrokeNormal}
              stroke-width={isSelected ? "0.8" : "0.5"}
              role="button"
              tabindex="0"
              onclick={() => handleDetailClick(feature)}
              onkeydown={(e) => e.key === "Enter" && handleDetailClick(feature)}
              onmouseenter={(e) => showDetailTooltip(e, feature)}
              onmouseleave={() => { tooltipData.visible = false; }}
            />
          {/if}
        {/each}
      {/if}
    </g>
  </svg>

  <!-- ── Legend (focused mode only) ───────────────────────────────────────── -->
  {#if region !== "world"}
    <div class="legend-panel">
      <div class="legend-title">
        {region === "usa" ? USA_TOPICS[topic]?.title : EUROSTAT_TOPICS[topic]?.title}
      </div>
      <div class="scale-bar" style="background: linear-gradient(to right, {legendGradient});"></div>
      <div class="scale-labels">
        <span>{minMax.min.toFixed(1)}</span>
        {#if (region === "usa" ? USA_TOPICS[topic]?.isGap : EUROSTAT_TOPICS[topic]?.isGap)}
          <span>0</span>
        {/if}
        <span>{minMax.max.toFixed(1)}</span>
      </div>
      <div class="legend-note">
        {region === "usa" ? USA_TOPICS[topic]?.units : EUROSTAT_TOPICS[topic]?.units}
      </div>
      <div class="legend-cvd-note">Colorblind-safe (Blue / Orange)</div>
    </div>
  {/if}

  <!-- ── Tooltip ───────────────────────────────────────────────────────────── -->
  {#if tooltipData.visible}
    <div class="map-tooltip" style="left: {tooltipData.x}px; top: {tooltipData.y}px;">
      <div class="tooltip-title">{tooltipData.title}</div>
      <div class="tooltip-body">{tooltipData.content}</div>
      <div class="tooltip-arrow"></div>
    </div>
  {/if}
</div>

<style>
  .map-container {
    position: relative;
    width: 100%;
    max-width: 100%;
    user-select: none;
  }

  .map-controls-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 4px 10px;
    flex-wrap: wrap;
  }

  .region-badge {
    margin-left: auto;
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 0.02em;
  }

  .world-hint {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 12.5px;
    color: var(--muted);
  }

  .hint-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #0077BB;
    animation: pulse-dot 1.8s ease-in-out infinite;
  }

  @keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.45; transform: scale(1.5); }
  }

  .back-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 7px 13px;
    font-family: inherit;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--muted);
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 99px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    transition: all 0.18s ease;
  }
  .back-btn:hover {
    color: var(--text);
    border-color: #0077BB;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(0, 119, 187, 0.15);
  }

  /* ── Selection chips ────────────────────────────────────────────────── */
  .selection-chips {
    display: flex;
    align-items: center;
    gap: 5px;
    flex-wrap: wrap;
  }

  .sel-chip {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 3px 8px;
    background: var(--card);
    border: 1.5px solid #0077BB;
    border-radius: 99px;
    font-size: 11.5px;
    font-weight: 700;
    color: #0077BB;
    letter-spacing: 0.03em;
  }
  :global(.dark) .sel-chip {
    border-color: #60BBEE;
    color: #60BBEE;
  }

  .chip-remove {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 15px;
    height: 15px;
    border: none;
    background: none;
    color: inherit;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    padding: 0;
    line-height: 1;
    opacity: 0.6;
    transition: opacity 0.15s;
  }
  .chip-remove:hover { opacity: 1; }

  .clear-all-btn {
    padding: 3px 8px;
    border: 1px solid var(--line);
    border-radius: 99px;
    background: none;
    font-family: inherit;
    font-size: 11px;
    color: var(--muted);
    cursor: pointer;
    transition: all 0.15s;
  }
  .clear-all-btn:hover {
    border-color: #d44;
    color: #d44;
  }

  .sel-counter {
    font-size: 10.5px;
    color: var(--muted);
    font-weight: 600;
    opacity: 0.7;
  }

  /* ── Map SVG ────────────────────────────────────────────────────────── */
  .map-svg {
    width: 100%;
    height: auto;
    display: block;
    overflow: hidden;
    border-radius: 10px;
  }

  .ocean-rect {
    fill: #d6e8f4;
    pointer-events: none;
  }
  :global(.dark) .ocean-rect {
    fill: #0f1e30;
  }

  .world-path {
    outline: none;
    transition: fill 0.2s ease, opacity 0.35s ease;
  }

  .hotspot-path {
    cursor: pointer;
  }

  .inactive-path {
    opacity: 0.65;
    pointer-events: none;
  }

  .hidden-world {
    opacity: 0 !important;
    pointer-events: none !important;
    transition: opacity 0.4s ease !important;
  }

  .detail-path {
    cursor: pointer;
    outline: none;
    transition: fill 0.3s ease, filter 0.15s ease, opacity 0.3s ease;
  }
  .detail-path:hover {
    filter: brightness(0.88);
  }

  .faded-path {
    opacity: 0.25;
    filter: saturate(0.3) brightness(0.95);
  }
  .faded-path:hover {
    opacity: 0.6;
    filter: saturate(0.6) brightness(0.88);
  }

  .selected-path {
    stroke-linecap: round;
    stroke-linejoin: round;
    opacity: 1;
  }

  /* ── Legend ──────────────────────────────────────────────────────── */
  .legend-panel {
    position: absolute;
    bottom: 18px;
    right: 18px;
    z-index: 10;
    width: 210px;
    background: var(--card);
    backdrop-filter: blur(8px);
    border: 1px solid var(--line);
    border-radius: 9px;
    padding: 10px 13px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.07);
    font-family: inherit;
  }

  .legend-title {
    font-size: 11.5px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 7px;
    text-transform: capitalize;
    line-height: 1.3;
  }

  .scale-bar {
    height: 10px;
    border-radius: 5px;
    width: 100%;
    margin-bottom: 4px;
    border: 1px solid var(--line);
  }

  .scale-labels {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: var(--muted);
    font-weight: 600;
    margin-bottom: 4px;
  }

  .legend-note {
    font-size: 10px;
    color: var(--muted);
    text-align: right;
  }

  .legend-cvd-note {
    font-size: 9.5px;
    color: var(--muted);
    opacity: 0.65;
    margin-top: 5px;
    text-align: right;
    font-style: italic;
  }

  /* ── Tooltip ────────────────────────────────────────────────────── */
  .map-tooltip {
    position: absolute;
    z-index: 100;
    transform: translate(-50%, -100%);
    background: #0f172a;
    color: #fff;
    padding: 9px 13px;
    border-radius: 7px;
    font-size: 12px;
    pointer-events: none;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    min-width: 155px;
    max-width: 235px;
    line-height: 1.4;
  }

  .tooltip-title {
    font-weight: 700;
    margin-bottom: 3px;
    font-size: 12.5px;
    color: #f8fafc;
  }

  .tooltip-body {
    color: #94a3b8;
    font-size: 11px;
  }

  .tooltip-arrow {
    position: absolute;
    bottom: -5px;
    left: 50%;
    transform: translateX(-50%);
    border-width: 5px 5px 0;
    border-style: solid;
    border-color: #0f172a transparent;
    width: 0;
    height: 0;
  }
</style>
