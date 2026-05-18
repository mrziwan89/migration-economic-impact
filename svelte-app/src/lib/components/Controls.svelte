<script lang="ts">
  import type { Region } from "$lib/data/lookups";

  export let region: Region;
  export let topic: string;
  export let period: string;
  export let sex: string;
  export let age: string;
  export let place: string;

  export let topicOptions: { value: string; label: string }[] = [];
  export let periodOptions: string[] = [];
  export let sexOptions: string[] = [];
  export let ageOptions: string[] = [];
  export let placeOptions: { value: string; label: string }[] = [];

  export let showDemographicFilters: boolean = false;
  export let placeLabel: string = "Selected state";
</script>

<div class="controls">
  <label>
    Data source
    <select bind:value={region}>
      <option value="usa">USA - ACS/IPUMS</option>
      <option value="eurostat">Europe - Eurostat LFS</option>
    </select>
  </label>

  <label>
    Topic
    <select bind:value={topic}>
      {#each topicOptions as opt (opt.value)}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </label>

  <label>
    Period
    <select bind:value={period}>
      {#each periodOptions as opt (opt)}
        <option value={opt}>{opt}</option>
      {/each}
    </select>
  </label>

  <label class:hidden={!showDemographicFilters}>
    Sex
    <select bind:value={sex}>
      {#each sexOptions as opt (opt)}
        <option value={opt}>{opt}</option>
      {/each}
    </select>
  </label>

  <label class:hidden={!showDemographicFilters}>
    Age
    <select bind:value={age}>
      {#each ageOptions as opt (opt)}
        <option value={opt}>{opt}</option>
      {/each}
    </select>
  </label>

  <label>
    <span>{placeLabel}</span>
    <select bind:value={place}>
      {#each placeOptions as opt (opt.value)}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </label>
</div>
