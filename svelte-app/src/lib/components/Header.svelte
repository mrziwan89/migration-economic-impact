<script lang="ts">
  let { isDark = $bindable(false) } = $props<{ isDark?: boolean }>();

  function toggleDark() {
    isDark = !isDark;
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("dark", isDark);
    }
  }
</script>

<header>
  <div>
    <h1>The Immigrant Engine</h1>
    <p>
      Official ACS/IPUMS and Eurostat LFS aggregates for comparing migrant employment, skill-use,
      access, and institutionalization indicators across the United States and Europe.
    </p>
  </div>
  <div class="header-right">
    <button class="dark-toggle" onclick={toggleDark} aria-label="Toggle dark mode">
      {#if isDark}
        <span class="toggle-icon">☀️</span> Light Mode
      {:else}
        <span class="toggle-icon">🌙</span> Dark Mode
      {/if}
    </button>
    <div class="pills">
      <span class="pill">USA + Europe</span>
      <span class="pill">ACS/IPUMS</span>
      <span class="pill">Eurostat</span>
    </div>
  </div>
</header>
