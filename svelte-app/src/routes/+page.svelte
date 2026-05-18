<script lang="ts">
  import { onMount, tick } from "svelte";
  import Header from "$lib/components/Header.svelte";
  import Controls from "$lib/components/Controls.svelte";
  import StatusBanner from "$lib/components/StatusBanner.svelte";
  import PlotCard from "$lib/components/PlotCard.svelte";
  import { loadAllData, type LoadedData } from "$lib/data/load";
  import { USA_TOPICS, EUROSTAT_TOPICS, type UsaTopic, type EurostatTopic } from "$lib/data/topics";
  import { DEFAULTS, PERIODS, type Region } from "$lib/data/lookups";
  import { prioritize, uniqueSorted } from "$lib/render/common";
  import { renderUsaMap, renderUsaRanking, renderUsaTrend, renderUsaBreakdown } from "$lib/render/usa";
  import {
    renderEurostatOutcomeMap,
    renderEurostatOutcomeRanking,
    renderEurostatOutcomeTrend,
    renderEurostatOutcomeBreakdown,
    renderEurostatEmploymentMap,
    renderEurostatEmploymentRanking,
    renderEurostatEmploymentTrend,
    renderEurostatEmploymentBreakdown
  } from "$lib/render/eurostat";

  let data: LoadedData | null = null;
  let bannerState: "loading" | "error" | "hidden" = "loading";
  let bannerMessage = "Loading dashboard data...";

  let region: Region = "usa";
  let topic: string = DEFAULTS.usa.topic;
  let period: string = DEFAULTS.usa.period;
  let sex: string = DEFAULTS.eurostat.sex;
  let age: string = DEFAULTS.eurostat.age;
  let place: string = DEFAULTS.usa.place;

  let mapEl: HTMLDivElement | null = null;
  let rankingEl: HTMLDivElement | null = null;
  let trendEl: HTMLDivElement | null = null;
  let breakdownEl: HTMLDivElement | null = null;

  let mapNote = "";
  let rankingNote = "";
  let trendNote = "";
  let breakdownNote = "";

  let lastRegion: Region = region;
  let lastTopic: string = topic;

  $: cfg = region === "usa" ? USA_TOPICS[topic] : EUROSTAT_TOPICS[topic];

  $: topicOptions = Object.entries(region === "usa" ? USA_TOPICS : EUROSTAT_TOPICS).map(
    ([value, t]) => ({ value, label: t.label })
  );

  $: periodOptions = (() => {
    if (!cfg) return [];
    return (cfg as EurostatTopic).periods || PERIODS[region];
  })();

  $: showDemographicFilters =
    region === "eurostat" && Boolean((cfg as EurostatTopic | undefined)?.usesDemographicFilters);

  $: placeLabel = region === "usa" ? "Selected state" : "Selected country";

  $: sexOptions = data && region === "eurostat"
    ? prioritize(
        uniqueSorted(data.eurostat.countryYear.map((row) => row.sex as string | null)),
        ["Total", "Females", "Males"]
      )
    : [];

  $: ageOptions = data && region === "eurostat"
    ? prioritize(
        uniqueSorted(data.eurostat.countryYear.map((row) => row.age as string | null)),
        [
          "From 15 to 64 years",
          "From 15 to 59 years",
          "From 15 to 39 years",
          "From 15 to 29 years",
          "From 15 to 24 years"
        ]
      )
    : [];

  $: placeOptions = data ? computePlaceOptions(data, region, topic, period, sex, age) : [];

  function computePlaceOptions(
    d: LoadedData,
    r: Region,
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

    // employment source: gap or rate
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

  $: if (region !== lastRegion) {
    lastRegion = region;
    const d = DEFAULTS[region];
    topic = d.topic;
    period = d.period;
    place = d.place;
    if (region === "eurostat") {
      sex = DEFAULTS.eurostat.sex;
      age = DEFAULTS.eurostat.age;
    }
  }

  $: if (topic !== lastTopic) {
    lastTopic = topic;
    if (region === "eurostat") {
      const topicCfg = EUROSTAT_TOPICS[topic];
      const allowedPeriods = topicCfg?.periods || PERIODS.eurostat;
      if (!allowedPeriods.includes(period)) {
        period = allowedPeriods[0];
      }
    } else {
      if (!PERIODS.usa.includes(period as (typeof PERIODS.usa)[number])) {
        period = PERIODS.usa[0];
      }
    }
  }

  $: if (placeOptions.length && !placeOptions.some((o) => o.value === place)) {
    place = placeOptions[0].value;
  }

  $: if (showDemographicFilters && sexOptions.length && !sexOptions.includes(sex)) {
    sex = sexOptions[0];
  }
  $: if (showDemographicFilters && ageOptions.length && !ageOptions.includes(age)) {
    age = ageOptions[0];
  }

  function renderAll(): void {
    if (!data || !mapEl || !rankingEl || !trendEl || !breakdownEl) return;
    if (!window.Plotly) return;
    const currentCfg = region === "usa" ? USA_TOPICS[topic] : EUROSTAT_TOPICS[topic];
    if (!currentCfg) return;

    if (region === "usa") {
      const usaCfg = currentCfg as UsaTopic;
      const mapResult = renderUsaMap(mapEl, usaCfg, data, period);
      renderUsaRanking(rankingEl, usaCfg, mapResult.mapRows);
      const trendResult = renderUsaTrend(trendEl, usaCfg, data, topic, place);
      const breakdownResult = renderUsaBreakdown(breakdownEl, usaCfg, data, topic, period, place);
      mapNote = mapResult.mapNote;
      rankingNote = mapResult.rankingNote;
      trendNote = trendResult.trendNote;
      breakdownNote = breakdownResult.breakdownNote;
    } else {
      const euCfg = currentCfg as EurostatTopic;
      if (euCfg.source === "outcomes") {
        const mapResult = renderEurostatOutcomeMap(mapEl, euCfg, data, period);
        renderEurostatOutcomeRanking(rankingEl, euCfg, mapResult.rows);
        const trendResult = renderEurostatOutcomeTrend(trendEl, euCfg, data, place);
        const breakdownResult = renderEurostatOutcomeBreakdown(breakdownEl, euCfg, data, period, place);
        mapNote = mapResult.mapNote;
        rankingNote = mapResult.rankingNote;
        trendNote = trendResult.trendNote;
        breakdownNote = breakdownResult.breakdownNote;
      } else {
        const mapResult = renderEurostatEmploymentMap(mapEl, euCfg, data, period, sex, age);
        renderEurostatEmploymentRanking(rankingEl, euCfg, mapResult.rows);
        const trendResult = renderEurostatEmploymentTrend(trendEl, euCfg, data, place, sex, age);
        const breakdownResult = renderEurostatEmploymentBreakdown(breakdownEl, data, period, place, sex, age);
        mapNote = mapResult.mapNote;
        rankingNote = mapResult.rankingNote;
        trendNote = trendResult.trendNote;
        breakdownNote = breakdownResult.breakdownNote;
      }
    }
  }

  $: if (data && mapEl && rankingEl && trendEl && breakdownEl) {
    void region;
    void topic;
    void period;
    void sex;
    void age;
    void place;
    tick().then(renderAll);
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
  <Header />

  <Controls
    bind:region
    bind:topic
    bind:period
    bind:sex
    bind:age
    bind:place
    {topicOptions}
    {periodOptions}
    {sexOptions}
    {ageOptions}
    {placeOptions}
    {showDemographicFilters}
    {placeLabel}
  />

  <StatusBanner state={bannerState} message={bannerMessage} />

  <div class="grid">
    <PlotCard variant="map" note={mapNote} bind:el={mapEl} />
    <PlotCard variant="ranking" note={rankingNote} bind:el={rankingEl} />
    <PlotCard variant="trend" note={trendNote} full bind:el={trendEl} />
    <PlotCard variant="breakdown" note={breakdownNote} full bind:el={breakdownEl} />
  </div>
</div>
