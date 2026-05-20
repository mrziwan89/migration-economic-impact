<script lang="ts">
  import { onMount, tick } from "svelte";
  import { fade, slide } from "svelte/transition";
  import Header from "$lib/components/Header.svelte";
  import StatusBanner from "$lib/components/StatusBanner.svelte";
  import PlotCard from "$lib/components/PlotCard.svelte";
  import GeoMap from "$lib/components/Map.svelte";
  import { loadAllData, type LoadedData } from "$lib/data/load";
  import { USA_TOPICS, EUROSTAT_TOPICS, type UsaTopic, type EurostatTopic } from "$lib/data/topics";
  import { DEFAULTS, PERIODS, MAX_SELECTIONS, yearToPeriod } from "$lib/data/lookups";
  import { prioritize, uniqueSorted } from "$lib/render/common";
  import { renderUsaRanking, renderUsaTrend, renderUsaBreakdown } from "$lib/render/usa";
  import { renderUsaRadar, renderEurostatRadar } from "$lib/render/radar";
  import {
    eurostatRowsForMap,
    eurostatOutcomeRowsForSelection,
    renderEurostatOutcomeRanking,
    renderEurostatOutcomeTrend,
    renderEurostatOutcomeBreakdown,
    renderEurostatEmploymentRanking,
    renderEurostatEmploymentTrend,
    renderEurostatEmploymentBreakdown
  } from "$lib/render/eurostat";

  // App States using Svelte 5 runes
  let data = $state.raw<LoadedData | null>(null);
  let bannerState = $state<"loading" | "error" | "hidden">("loading");
  let bannerMessage = $state("Loading dashboard data...");
  let isDark = $state(false);

  let region = $state<"usa" | "eurostat" | "world">("world");
  let topic = $state<string>("brain");
  let period = $state<string>("2020-2024");
  let sex = $state<string>("Total");
  let age = $state<string>("From 15 to 64 years");
  let places = $state<string[]>(["CA"]);

  // Year slider state
  let selectedYear = $state(2024);

  let rankingEl = $state<HTMLDivElement | null>(null);
  let trendEl = $state<HTMLDivElement | null>(null);
  let breakdownEl = $state<HTMLDivElement | null>(null);
  let radarEl = $state<HTMLDivElement | null>(null);

  let rankingNote = $state("");
  let trendNote = $state("");
  let breakdownNote = $state("");
  let radarNote = $state("");

  // Derived states using runes
  let cfg = $derived(
    region === "usa" ? USA_TOPICS[topic] : (region === "eurostat" ? EUROSTAT_TOPICS[topic] : null)
  );

  let topicOptions = $derived(
    Object.entries(region === "usa" ? USA_TOPICS : (region === "eurostat" ? EUROSTAT_TOPICS : {})).map(
      ([value, t]) => ({ value, label: t.label })
    )
  );

  // Compute the allowed period list for choropleth filtering
  let periodOptions = $derived.by(() => {
    if (!cfg) return [] as string[];
    return ((cfg as EurostatTopic).periods || PERIODS[region as "usa" | "eurostat"]) as string[];
  });

  // Compute available discrete years from the trend data
  let availableYears = $derived.by(() => {
    if (!data || region === "world") return [] as number[];
    let yearSet = new Set<number>();
    if (region === "usa") {
      const usaCfg = USA_TOPICS[topic];
      if (usaCfg) {
        data.usa[usaCfg.trendKey].forEach((row: any) => {
          const y = Number(row.YEAR);
          if (Number.isFinite(y)) yearSet.add(y);
        });
      }
    } else if (region === "eurostat") {
      const euCfg = EUROSTAT_TOPICS[topic];
      if (euCfg?.source === "outcomes") {
        data.eurostat.outcomeYear
          .filter((row: any) => row.metric_key === euCfg.metricKey)
          .forEach((row: any) => {
            const y = Number(row.YEAR);
            if (Number.isFinite(y)) yearSet.add(y);
          });
      } else {
        // employment topics
        const src = euCfg?.kind === "gap" ? data.eurostat.gapYear : data.eurostat.countryYear;
        src.forEach((row: any) => {
          const y = Number(row.YEAR);
          if (Number.isFinite(y)) yearSet.add(y);
        });
      }
    }
    return Array.from(yearSet).sort((a, b) => a - b);
  });

  let minYear = $derived(availableYears.length > 0 ? availableYears[0] : 2008);
  let maxYear = $derived(availableYears.length > 0 ? availableYears[availableYears.length - 1] : 2024);

  // Derive period from selectedYear
  $effect(() => {
    if (availableYears.length > 0 && periodOptions.length > 0) {
      period = yearToPeriod(selectedYear, periodOptions);
    }
  });

  // Clamp selectedYear when availableYears change (topic/region switch)
  $effect(() => {
    if (availableYears.length > 0) {
      if (selectedYear > maxYear) selectedYear = maxYear;
      else if (selectedYear < minYear) selectedYear = minYear;
    }
  });

  let showDemographicFilters = $derived(
    region === "eurostat" && Boolean((cfg as EurostatTopic | undefined)?.usesDemographicFilters)
  );

  let placeLabel = $derived(region === "usa" ? "Selected states" : "Selected countries");

  let sexOptions = $derived.by(() => {
    if (!data || region !== "eurostat") return [];
    return prioritize(
      uniqueSorted(data.eurostat.countryYear.map((row) => row.sex as string | null)),
      ["Total", "Females", "Males"]
    );
  });

  let ageOptions = $derived.by(() => {
    if (!data || region !== "eurostat") return [];
    return prioritize(
      uniqueSorted(data.eurostat.countryYear.map((row) => row.age as string | null)),
      [
        "From 15 to 64 years",
        "From 15 to 59 years",
        "From 15 to 39 years",
        "From 15 to 29 years",
        "From 15 to 24 years"
      ]
    );
  });

  let placeOptions = $derived.by(() => {
    if (!data || region === "world") return [];
    return computePlaceOptions(data, region as "usa" | "eurostat", topic, period, sex, age);
  });

  // Sync periodIndex → period removed; now yearToPeriod handles it

  // State transitions (handles switching regions gracefully)
  let lastRegion = "world";
  $effect(() => {
    if (region !== lastRegion) {
      lastRegion = region;
      if (region === "usa") {
        topic = DEFAULTS.usa.topic;
        period = DEFAULTS.usa.period;
        places = [...DEFAULTS.usa.places];
        selectedYear = 2024;
      } else if (region === "eurostat") {
        topic = DEFAULTS.eurostat.topic;
        period = DEFAULTS.eurostat.period;
        places = [...DEFAULTS.eurostat.places];
        sex = DEFAULTS.eurostat.sex;
        age = DEFAULTS.eurostat.age;
        selectedYear = 2023;
      }
    }
  });

  let lastTopic = "";
  $effect(() => {
    if (region !== "world" && topic !== lastTopic) {
      lastTopic = topic;
      if (region === "eurostat") {
        const topicCfg = EUROSTAT_TOPICS[topic];
        const allowedPeriods = topicCfg?.periods || PERIODS.eurostat;
        if (!allowedPeriods.includes(period)) {
          period = allowedPeriods[0];
        }
      } else if (region === "usa") {
        if (!PERIODS.usa.includes(period as any)) {
          period = PERIODS.usa[0];
        }
      }
    }
  });

  // Reactively trigger Plotly rendering
  $effect(() => {
    if (!data || region === "world") return;
    
    // Explicitly track the active selections
    const _topic = topic;
    const _period = period;
    const _sex = sex;
    const _age = age;
    const _places = places;
    const _dark = isDark;
    
    // Explicitly track that the chart containers are loaded
    if (rankingEl && trendEl && breakdownEl && radarEl) {
      tick().then(renderAll);
    }
  });

  function renderAll(): void {
    if (!data || !rankingEl || !trendEl || !breakdownEl || !radarEl) return;
    if (!window.Plotly) return;
    const currentCfg = region === "usa" ? USA_TOPICS[topic] : (region === "eurostat" ? EUROSTAT_TOPICS[topic] : null);
    if (!currentCfg) return;

    const selectedPlaces = new Set(places);

    if (region === "usa") {
      const usaCfg = currentCfg as UsaTopic;
      const mapRows = data.usa[usaCfg.mapKey].filter((row) => row.period === period && row.state);
      
      renderUsaRanking(rankingEl, usaCfg, mapRows, selectedPlaces, isDark);
      const trendResult = renderUsaTrend(trendEl, usaCfg, data, topic, places, isDark);
      const breakdownResult = renderUsaBreakdown(breakdownEl, usaCfg, data, topic, period, places, isDark);
      renderUsaRadar(radarEl, data, period, places, isDark);
      
      rankingNote = usaCfg.isGap
        ? "Ranking uses the selected period. Positive gaps mean the foreign-born rate is higher than the US-born rate."
        : "Ranking uses the selected period.";
      trendNote = trendResult.trendNote;
      breakdownNote = breakdownResult.breakdownNote;
      radarNote = "Comparative profile of all primary indicators for selected states (absolute gap values).";
    } else {
      const euCfg = currentCfg as EurostatTopic;
      if (euCfg.source === "outcomes") {
        const rows = eurostatOutcomeRowsForSelection(euCfg, data, period);
        renderEurostatOutcomeRanking(rankingEl, euCfg, rows, selectedPlaces, isDark);
        const trendResult = renderEurostatOutcomeTrend(trendEl, euCfg, data, places, isDark);
        const breakdownResult = renderEurostatOutcomeBreakdown(breakdownEl, euCfg, data, period, places, isDark);
        renderEurostatRadar(radarEl, data, period, places, isDark);
        
        rankingNote = euCfg.rankDirection === "ascending"
          ? "Ranking highlights the most negative gaps first."
          : "Ranking highlights the highest values first.";
        trendNote = trendResult.trendNote;
        breakdownNote = breakdownResult.breakdownNote;
        radarNote = "Comparative profile across all outcome research pillars (normalized 0-100 scale).";
      } else {
        const rows = eurostatRowsForMap(euCfg, data, period, sex, age);
        renderEurostatEmploymentRanking(rankingEl, euCfg, rows, selectedPlaces, isDark);
        const trendResult = renderEurostatEmploymentTrend(trendEl, euCfg, data, places, sex, age, isDark);
        const breakdownResult = renderEurostatEmploymentBreakdown(breakdownEl, data, period, places, sex, age, isDark);
        renderEurostatRadar(radarEl, data, period, places, isDark);
        
        rankingNote = euCfg.kind === "gap"
          ? "Ranking uses the selected period, age, and sex. Positive gaps mean the comparison group has a higher employment rate."
          : "Ranking uses the selected period, age, and sex.";
        trendNote = trendResult.trendNote;
        breakdownNote = breakdownResult.breakdownNote;
        radarNote = "Detailed outcome pillars profile for the selected country (normalized scale).";
      }
    }
  }

  function computePlaceOptions(
    d: LoadedData,
    r: "usa" | "eurostat",
    t: string,
    p: string,
    s: string,
    a: string
  ): { value: string; label: string }[] {
    if (r === "usa") {
      const topicCfg = USA_TOPICS[t];
      if (!topicCfg) return [];
      const rows = d.usa[topicCfg.mapKey].filter((row) => row.period === p && row.state);
      const byState = new Map<string, string>();
      rows.forEach((row) => {
        const state = row.state as string;
        if (!byState.has(state)) {
          byState.set(state, (row.state_name as string) || state);
        }
      });
      return Array.from(byState.entries())
        .sort((a, b) => a[1].localeCompare(b[1]))
        .map(([value, label]) => ({ value, label: `${value} - ${label}` }));
    }

    const topicCfg = EUROSTAT_TOPICS[t];
    if (!topicCfg) return [];

    if (topicCfg.source === "outcomes") {
      const source = p === "Latest available" ? d.eurostat.outcomeLatest : d.eurostat.outcomePeriod;
      const rows = source.filter(
        (row) => row.metric_key === topicCfg.metricKey && row[topicCfg.value] != null
      );
      const byCountry = new Map<string, { value: string; label: string; aggregate: number }>();
      rows.forEach((row) => {
        const key = row.country_key as string | null;
        if (!key || byCountry.has(key)) return;
        const isAgg = Number(row.is_aggregate) === 1 ? 1 : 0;
        byCountry.set(key, {
          value: key,
          label: isAgg ? `${row.country} (aggregate)` : (row.country as string),
          aggregate: isAgg
        });
      });
      return Array.from(byCountry.values()).sort((a, b) => {
        if (a.aggregate !== b.aggregate) return b.aggregate - a.aggregate;
        return a.label.localeCompare(b.label);
      });
    }

    const mapRows =
      topicCfg.kind === "gap"
        ? d.eurostat.gapPeriod.filter(
            (row) =>
              row.period === p &&
              row.sex === s &&
              row.age === a &&
              row.comparison_group === topicCfg.comparisonGroup &&
              row.is_aggregate === 0 &&
              row.iso3
          )
        : d.eurostat.countryPeriod.filter(
            (row) =>
              row.period === p &&
              row.sex === s &&
              row.age === a &&
              row.citizen_group === topicCfg.citizenGroup &&
              row.is_aggregate === 0 &&
              row.iso3
          );
    const aggregateRows = d.eurostat.countryPeriod.filter(
      (row) => row.period === p && row.sex === s && row.age === a && row.is_aggregate === 1
    );
    const byCountry = new Map<string, { value: string; label: string; aggregate: number }>();
    [...mapRows, ...aggregateRows].forEach((row) => {
      const key = row.country_key as string | null;
      if (!key || byCountry.has(key)) return;
      const isAgg = Number(row.is_aggregate) === 1 ? 1 : 0;
      byCountry.set(key, {
        value: key,
        label: isAgg ? `${row.country} (aggregate)` : (row.country as string),
        aggregate: isAgg
      });
    });
    return Array.from(byCountry.values()).sort((a, b) => {
      if (a.aggregate !== b.aggregate) return b.aggregate - a.aggregate;
      return a.label.localeCompare(b.label);
    });
  }

  onMount(async () => {
    try {
      data = await loadAllData();
      bannerState = "hidden";
    } catch (error) {
      console.error(error);
      bannerState = "error";
      bannerMessage = "Could not load dashboard data. Serve the website folder over HTTP, then reload this page.";
    }
  });
</script>

<div class="wrap">
  <Header bind:isDark={isDark} />

  <StatusBanner state={bannerState} message={bannerMessage} />

  <!-- Native 2D Map Canvas (Spans Wide, direct background) -->
  <div class="map-section-wrapper">
    {#if data}
      <GeoMap
        bind:region
        bind:topic
        bind:period
        bind:sex
        bind:age
        bind:places
        isDark={isDark}
        {data}
      />
    {:else}
      <div class="map-skeleton">
        <div class="skeleton-spinner"></div>
        <p>Assembling Geographic Visualizations...</p>
      </div>
    {/if}
  </div>

  <!-- Sticky Controls Bar (lives outside map-section-wrapper so it follows scroll) -->
  {#if region !== "world" && data}
    <div class="sticky-controls-bar">
      <div class="controls-inner">
        <span class="focus-badge">{region === "usa" ? "🇺🇸 United States" : "🇪🇺 Europe"}</span>
        <div class="topic-pill-grid">
          {#each topicOptions as opt}
            <button
              class="topic-pill-btn"
              class:active={topic === opt.value}
              onclick={() => topic = opt.value}
            >
              {opt.label}
            </button>
          {/each}
        </div>

        <!-- Year Slider -->
        {#if availableYears.length > 1}
          <div class="year-slider-panel">
            <span class="year-label">{selectedYear}</span>
            <input
              type="range"
              min={minYear}
              max={maxYear}
              step="1"
              bind:value={selectedYear}
              class="year-slider"
              aria-label="Select year"
            />
            <span class="year-range-label">{minYear}–{maxYear}</span>
            <span class="period-bucket-label">{period}</span>
          </div>
        {:else if availableYears.length === 1}
          <span class="single-period-label">{availableYears[0]}</span>
        {/if}
      </div>

      {#if showDemographicFilters}
        <div class="controls-demographics" transition:slide={{ duration: 200 }}>
          <label class="demo-select-field">
            <span class="demo-label">Sex</span>
            <select bind:value={sex} class="demo-select">
              {#each sexOptions as opt}
                <option value={opt}>{opt}</option>
              {/each}
            </select>
          </label>
          <label class="demo-select-field">
            <span class="demo-label">Age Group</span>
            <select bind:value={age} class="demo-select">
              {#each ageOptions as opt}
                <option value={opt}>{opt}</option>
              {/each}
            </select>
          </label>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Unfolded Detailed Gaps & Downstream Charts Grid -->
  {#if region !== "world" && data}
    <div class="unfolded-dashboard-area" transition:fade={{ duration: 350 }}>

      <!-- Minimal contextual insight notes -->
      {#if topic === "inc" || (region === "eurostat" && cfg && 'metricKey' in cfg && cfg.metricKey === "incarceration")}
        <div class="insight-note" transition:slide>
          This metric uses <strong>institutionalisation rates</strong> (group quarters such as correctional facilities) as a census proxy for incarceration — not direct crime or conviction rates. Interpret nativity disparities with care.
        </div>
      {/if}

      {#if topic === "health"}
        <div class="insight-note" transition:slide>
          Health access is measured as the <strong>Uninsured Gap</strong>: <code>(Foreign-born rate − US-born rate)</code> in percentage points. Positive values indicate higher uninsured rates among foreign-born residents.
        </div>
      {/if}

      <div class="selected-summary-banner">
        {#if places.length === 0}
          Click on the map to select up to <strong>{MAX_SELECTIONS}</strong> {region === "usa" ? "states" : "countries"} for comparison.
        {:else}
          Comparing
          {#each places as p, i}
            <strong>{placeOptions.find(o => o.value === p)?.label || p}</strong>{#if i < places.length - 1}{i === places.length - 2 ? ' and ' : ', '}{/if}
          {/each}
        {/if}
      </div>

      <div class="editorial-charts-grid">
        <!-- Chart 0: Radar Plot (Comparative Profile) -->
        <PlotCard variant="radar" note={radarNote} full bind:el={radarEl} />

        <!-- Chart A: Horizontal Ranking of States/Countries -->
        <PlotCard variant="ranking" note={rankingNote} bind:el={rankingEl} />

        <!-- Chart B: Nativity Citizenship Cohort Breakdown -->
        <PlotCard variant="breakdown" note={breakdownNote} bind:el={breakdownEl} />

        <!-- Chart C: Long-term Historical Trend Comparison -->
        <PlotCard variant="trend" note={trendNote} full bind:el={trendEl} />
      </div>
    </div>
  {/if}
</div>

<style>
  /* Base Layout Adjustments */
  .map-section-wrapper {
    position: relative;
    width: 100%;
    border-radius: 12px;
    margin: 16px 0 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow: hidden;
    transition: all 0.3s ease;
  }

  /* Skeleton Loading State */
  .map-skeleton {
    width: 100%;
    height: 480px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: var(--muted);
  }

  .skeleton-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--line);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* ─── Sticky controls bar ──────────────────────────────────────────────── */
  .sticky-controls-bar {
    position: sticky;
    top: 0;
    z-index: 200;
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 10px 16px;
    margin: 12px 0;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
    transition: box-shadow 0.2s ease;
  }

  .controls-inner {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .focus-badge {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: var(--accent);
    color: white;
    padding: 4px 10px;
    border-radius: 6px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .topic-pill-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    flex: 1;
  }

  .topic-pill-btn {
    font-family: inherit;
    font-size: 12.5px;
    font-weight: 500;
    color: var(--muted);
    background: transparent;
    border: 1px solid transparent;
    padding: 5px 10px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .topic-pill-btn:hover {
    color: var(--text);
    background: rgba(15, 23, 42, 0.04);
  }

  :global(.dark) .topic-pill-btn:hover {
    background: rgba(248, 250, 252, 0.06);
  }

  .topic-pill-btn.active {
    color: var(--text);
    background: white;
    border-color: var(--line);
    box-shadow: 0 2px 4px rgba(15, 23, 42, 0.04);
    font-weight: 600;
  }

  :global(.dark) .topic-pill-btn.active {
    background: var(--bg);
    color: var(--text);
  }

  /* ─── Year slider ──────────────────────────────────────────────────────── */
  .year-slider-panel {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: auto;
    flex-shrink: 0;
    min-width: 260px;
  }

  .year-label {
    font-size: 18px;
    font-weight: 800;
    color: var(--text);
    min-width: 42px;
    text-align: center;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }

  .year-slider {
    flex: 1;
    min-width: 100px;
    accent-color: #0077BB;
    height: 5px;
    cursor: pointer;
  }
  :global(.dark) .year-slider {
    accent-color: #60BBEE;
  }

  .year-range-label {
    font-size: 10px;
    color: var(--muted);
    opacity: 0.6;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }

  .period-bucket-label {
    font-size: 10.5px;
    font-weight: 600;
    color: var(--muted);
    background: var(--bg);
    border: 1px solid var(--line);
    border-radius: 4px;
    padding: 2px 6px;
    white-space: nowrap;
  }

  .single-period-label {
    margin-left: auto;
    font-size: 12px;
    font-weight: 700;
    color: var(--muted);
    white-space: nowrap;
  }

  /* Demographic Sub-Filters */
  .controls-demographics {
    display: flex;
    gap: 16px;
    border-top: 1px solid var(--line);
    margin-top: 8px;
    padding-top: 8px;
  }

  .demo-select-field {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--muted);
  }

  .demo-label {
    font-weight: 600;
    white-space: nowrap;
  }

  .demo-select {
    font-family: inherit;
    font-size: 12px;
    font-weight: 500;
    color: var(--text);
    background: white;
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 3px 6px;
    outline: none;
    cursor: pointer;
  }

  :global(.dark) .demo-select {
    background: var(--bg);
  }

  /* Unfolded Dashboard below the map */
  .unfolded-dashboard-area {
    margin-top: 16px;
  }

  .selected-summary-banner {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13.5px;
    color: var(--text);
    margin-bottom: 24px;
    text-align: center;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02);
  }

  .editorial-charts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }

  /* Make the long-term trend spans full width */
  :global(.editorial-charts-grid > .full) {
    grid-column: 1 / -1;
  }

  /* Minimal contextual insight notes */
  .insight-note {
    font-size: 13px;
    color: var(--muted);
    line-height: 1.55;
    border-left: 3px solid var(--accent);
    padding: 8px 14px;
    margin-bottom: 16px;
    max-width: none;
  }

  .insight-note strong {
    color: var(--text);
  }

  .insight-note code {
    background: rgba(0, 0, 0, 0.04);
    padding: 1px 4px;
    border-radius: 3px;
    font-family: monospace;
    font-size: 12px;
  }

  :global(.dark) .insight-note code {
    background: rgba(255, 255, 255, 0.08);
  }

  /* Responsive styling */
  @media (max-width: 900px) {
    .editorial-charts-grid {
      grid-template-columns: 1fr;
    }
    
    :global(.editorial-charts-grid > .card) {
      grid-column: auto !important;
    }

    .sticky-controls-bar {
      border-radius: 0;
      margin: 0 -24px;
      padding: 8px 16px;
    }

    .controls-inner {
      flex-direction: column;
      align-items: stretch;
    }

    .year-slider-panel {
      margin-left: 0;
    }
  }
</style>
