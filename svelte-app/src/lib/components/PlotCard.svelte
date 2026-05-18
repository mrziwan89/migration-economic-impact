<script lang="ts">
  export let variant: "map" | "ranking" | "trend" | "breakdown";
  export let note: string = "";
  export let full: boolean = false;
  export let el: HTMLDivElement | null = null;
</script>

<div class="card" class:full>
  <div class="plot--{variant}" bind:this={el}></div>
  <div class="note">{note}</div>
</div>
