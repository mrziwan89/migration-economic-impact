# Frontend Development Guide: The Immigrant Engine

This guide provides instructions for setting up, running, and building the interactive Svelte dashboard for **The Immigrant Engine** project.

---

## 🚀 Quick Start

1. **Navigate to the frontend directory:**
   ```bash
   cd svelte-app
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

4. **Access the dashboard:**
   Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🛠 Prerequisites

- **Node.js:** v18.0.0 or higher recommended.
- **npm:** v9.0.0 or higher.

---

## 💻 Development Workflow

### Local Development
The development server includes Hot Module Replacement (HMR), meaning changes to `.svelte`, `.ts`, or `.css` files will reflect instantly in the browser.

```bash
npm run dev
```

### Type Checking
To verify TypeScript and Svelte syntax across the project:
```bash
npm run check
```

---

## 🏗 Production Build

To generate a highly optimized static bundle for deployment (e.g., GitHub Pages, Netlify, Vercel):

1. **Build the project:**
   ```bash
   npm run build
   ```

2. **Preview the production build locally:**
   ```bash
   npm run preview
   ```
   *The output files are generated in the `svelte-app/build/` directory.*

---

## 📊 Dashboard Features

### Radar Plot (Comparative Profile)
Located directly below the main map, the Radar Plot provides a multi-dimensional comparison of selected regions:
- **US Indicators:** Brain Waste Gap, Incarceration Gap, Uninsured Gap, Limited English.
- **EU Pillars:** Brain Waste (Education), Temporary Contracts (Job Quality), Poverty Risk (Economic), Incarceration Ratio (Societal).

### Theme Support
The dashboard fully supports **Dark Mode**. Toggle the theme using the button in the top-right header. All visualizations (including Radar, Trend, and Breakdown charts) adjust their color scales and gridlines automatically.

---

## ❓ Troubleshooting

### 500 Internal Server Error
If you encounter a 500 error on localhost:
1. Ensure all dependencies are installed: `npm install`.
2. Clear the Vite cache: `rm -rf node_modules/.vite`.
3. Restart the dev server: `npm run dev`.

### Missing Data
The dashboard relies on CSV files in `svelte-app/static/data/`. If charts appear empty, verify that these files exist and are not corrupted.
