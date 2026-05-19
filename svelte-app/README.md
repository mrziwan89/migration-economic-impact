# Migration Economic Impact – SvelteKit port

This folder is a self-contained SvelteKit version of the dashboard that lives in `../` (the
original vanilla HTML/JS site is unchanged). It has its own `package.json`, its own copy of
the data under `static/data/`, and produces a fully static build that can be dropped on any
static host.

## Stack

- SvelteKit 2 + `@sveltejs/adapter-static`
- TypeScript
- Plotly.js loaded from the CDN (`https://cdn.plot.ly/plotly-2.35.2.min.js`) in `src/app.html`
- No CSS framework — the original CSS variables live in `src/lib/styles/global.css`

## Run locally

```
cd svelte-app
npm install
npm run dev
```

then open the URL Vite prints (default `http://localhost:5173`).

## Build a static bundle

```
npm run build
```

Output lands in `svelte-app/build/`. Serve that folder with any static file server
(`npx serve build`, GitHub Pages, Netlify, etc.).

## Type-check

```
npm run check
```

## Layout

```
src/
  app.html                  # CDN Plotly tag + sveltekit head/body slots
  app.d.ts                  # window.Plotly type declaration
  routes/
    +layout.ts              # prerender = true, ssr = false
    +layout.svelte          # global stylesheet import + <slot />
    +page.svelte            # state + reactivity, owns the four plot refs
  lib/
    components/
      Header.svelte         # static title + pills
      Controls.svelte       # 6 dropdowns, two-way bound to page state
      StatusBanner.svelte   # loading / error banner
      PlotCard.svelte       # reusable plot container (used 4 times)
    data/
      files.ts              # CSV URL maps (start with /data/...)
      topics.ts             # USA_TOPICS / EUROSTAT_TOPICS + types
      lookups.ts            # STATE_NAMES, FIPS_TO_STATE, periods, defaults
      csv.ts                # parseCsv + loadCsv
      load.ts               # loadAllData() → typed LoadedData
    render/
      common.ts             # blankPlot, trendLayout, mapScale, aggregateNational
      usa.ts                # 4 USA render fns
      eurostat.ts           # 4 outcomes + 4 employment render fns
    styles/
      global.css            # ported from the original <style> block
static/
  data/                     # CSVs (mirror of ../data/)
```

Render functions take a target `HTMLElement` and pure inputs (config, period, place, …) and
return any note text that needs to appear under the chart. The page is the only place that
mutates `mapNote / rankingNote / trendNote / breakdownNote`.

## Differences from the plan

- Instead of four near-identical chart components, the page uses a single reusable
  `PlotCard` four times. Each chart's "work" is one Plotly call inside `lib/render/*` —
  splitting it into four wrapper components would have added files without adding logic.
- The page does not use Svelte stores; selections are plain reactive `let` variables passed
  down with `bind:` to `Controls`.
