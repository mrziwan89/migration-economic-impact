<script lang="ts">
  export let state: "loading" | "error" | "hidden" = "loading";
  export let message: string = "Loading dashboard data...";
</script>

{#if state !== "hidden"}
  <div class="status" class:error={state === "error"}>{message}</div>
{/if}
