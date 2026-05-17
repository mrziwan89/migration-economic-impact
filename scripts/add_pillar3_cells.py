"""
add_pillar3_cells.py
Appends Pillar 3 (Incarceration) cells to notebooks/test.ipynb using only
the built-in json module — no third-party packages required.

Run with:  /usr/bin/python3 scripts/add_pillar3_cells.py
"""
import json
import pathlib
import uuid

NB_PATH = pathlib.Path(__file__).parent.parent / "notebooks" / "test.ipynb"


def cid():
    return uuid.uuid4().hex[:8]


# ── Cell source strings ───────────────────────────────────────────────────────

MARKDOWN_SRC = (
    "## Pillar 3: Incarceration Disparities — Foreign vs. Native Prison Populations\n"
    "\n"
    "### Overview\n"
    "This pillar examines the over-representation of foreign-citizenship individuals in "
    "the prison systems of EU member states. Using Eurostat's `crim_pris_ctz` dataset, "
    "we compute the **Foreign Share (%)** of the total prison population and compare it "
    "across countries and over time (2008–2024).\n"
    "\n"
    "### Methodology & Proxy\n"
    "Eurostat reports prisoner counts by citizenship (`FOR` = Foreign, `NAT` = National, "
    "`TOTAL`). We use **Foreign Share (%)** as the primary disparity indicator:\n"
    "\n"
    "> `Foreign_Share_Pct = (FOR / TOTAL) × 100`\n"
    "\n"
    "A higher value signals structural over-representation of non-nationals, often driven "
    "by socioeconomic marginalization, discriminatory practices, or migration precarity.\n"
    "\n"
    "### Data Source\n"
    "* Eurostat `crim_pris_ctz` — Prison population by citizenship\n"
    "* `citizen` codes: `FOR` (Foreign), `NAT` (National), `TOTAL`\n"
    "* Timeline: 2008–2024\n"
)

ETL_SRC = """\
import pandas as pd

# ─── 1. Load Raw Prison Data ─────────────────────────────────────────────────
PRISON_FILE = '../data/raw/eurostat_lfs/crim_pris_ctz.csv'
df_raw = pd.read_csv(PRISON_FILE, low_memory=False)

# ─── 2. Keep only relevant columns ──────────────────────────────────────────
df = df_raw[['citizen', 'geo', 'TIME_PERIOD', 'OBS_VALUE']].copy()
df.columns = ['citizen', 'Country', 'Year', 'Count']
df['Count'] = pd.to_numeric(df['Count'], errors='coerce')
df['Year']  = pd.to_numeric(df['Year'],  errors='coerce')

# Keep only 2-letter country codes (drop EU-wide aggregates like EU27_2020)
df = df[df['Country'].str.match(r'^[A-Z]{2}$', na=False)]

# ─── 3. Pivot so FOR, NAT, TOTAL become columns ──────────────────────────────
df_pivot = df[df['citizen'].isin(['FOR', 'NAT', 'TOTAL'])].pivot_table(
    index=['Year', 'Country'],
    columns='citizen',
    values='Count',
    aggfunc='mean'
).reset_index()

# ─── 4. Compute Foreign Share (%) ────────────────────────────────────────────
df_pivot['Foreign_Share_Pct'] = (df_pivot['FOR'] / df_pivot['TOTAL']) * 100

df_prison = df_pivot.dropna(subset=['Foreign_Share_Pct']).copy()

# ─── 5. Map ISO2 → ISO3 for Plotly ──────────────────────────────────────────
eu_iso2_to_iso3 = {
    'AT': 'AUT', 'BE': 'BEL', 'BG': 'BGR', 'CY': 'CYP', 'CZ': 'CZE',
    'DE': 'DEU', 'DK': 'DNK', 'EE': 'EST', 'EL': 'GRC', 'ES': 'ESP',
    'FI': 'FIN', 'FR': 'FRA', 'HR': 'HRV', 'HU': 'HUN', 'IE': 'IRL',
    'IT': 'ITA', 'LT': 'LTU', 'LU': 'LUX', 'LV': 'LVA', 'MT': 'MLT',
    'NL': 'NLD', 'PL': 'POL', 'PT': 'PRT', 'RO': 'ROU', 'SE': 'SWE',
    'SI': 'SVN', 'SK': 'SVK', 'UK': 'GBR', 'CH': 'CHE', 'NO': 'NOR',
    'IS': 'ISL', 'LI': 'LIE', 'ME': 'MNE', 'MK': 'MKD', 'AL': 'ALB',
    'RS': 'SRB', 'TR': 'TUR', 'BA': 'BIH'
}
df_prison['ISO3'] = df_prison['Country'].map(eu_iso2_to_iso3)
df_prison = df_prison.dropna(subset=['ISO3'])
df_prison = df_prison.sort_values(['Year', 'Country'])

print(f"✅ Prison ETL done — {len(df_prison)} country-year rows, "
      f"{int(df_prison['Year'].min())}–{int(df_prison['Year'].max())}")
print(df_prison[['Country', 'Year', 'FOR', 'NAT', 'TOTAL', 'Foreign_Share_Pct']].head(10).to_string(index=False))
"""

CHOROPLETH_SRC = """\
import plotly.express as px

# ─── Animated Choropleth: Foreign Share (%) across Europe 2008-2024 ─────────
# Cap colour scale at 95th percentile so Luxembourg doesn't crush the scale
max_share = df_prison['Foreign_Share_Pct'].quantile(0.95)

fig_map = px.choropleth(
    df_prison,
    locations='ISO3',
    color='Foreign_Share_Pct',
    hover_name='Country',
    animation_frame='Year',
    color_continuous_scale='OrRd',
    range_color=[0, max_share],
    scope='europe',
    title='Pillar 3 — Incarceration: Foreign Share of Prison Population (%) by Country (2008–2024)',
    labels={'Foreign_Share_Pct': 'Foreign Share (%)'}
)

fig_map.update_geos(
    fitbounds='locations',
    resolution=50,
    showcountries=True,
    countrycolor='LightGrey',
    showcoastlines=True,
    coastlinecolor='Black'
)
fig_map.update_layout(
    height=650,
    margin={'r': 0, 't': 50, 'l': 0, 'b': 0},
    coloraxis_colorbar=dict(
        title='Foreign<br>Share (%)',
        thicknessmode='pixels', thickness=20,
        lenmode='pixels', len=300,
        yanchor='top', y=1,
        ticks='outside'
    )
)

fig_map.show()
"""

TREND_SRC = """\
import plotly.express as px

# ─── Top-12 countries by avg Foreign Share — trend lines 2008-2024 ───────────
avg_share     = df_prison.groupby('Country')['Foreign_Share_Pct'].mean().nlargest(12)
top_countries = avg_share.index.tolist()

df_top = df_prison[df_prison['Country'].isin(top_countries)].copy()

fig_trend = px.line(
    df_top,
    x='Year',
    y='Foreign_Share_Pct',
    color='Country',
    markers=True,
    title='Pillar 3 — Incarceration: Foreign Prison Share Trends (Top 12 Countries, 2008–2024)',
    labels={
        'Foreign_Share_Pct': 'Foreign Share of Prison Population (%)',
        'Year': 'Year'
    }
)

fig_trend.add_hline(
    y=avg_share.mean(),
    line_dash='dash',
    line_color='gray',
    annotation_text=f'Avg across top countries ({avg_share.mean():.1f}%)',
    annotation_position='bottom right'
)

fig_trend.update_layout(
    height=550,
    hovermode='x unified',
    xaxis=dict(tickmode='linear', dtick=2),
    legend=dict(title='Country')
)

fig_trend.show()
"""

BAR_SRC = """\
import plotly.express as px

# ─── Snapshot Bar Chart: Most recent data point per country ──────────────────
df_latest = df_prison.sort_values('Year').groupby('Country').last().reset_index()
df_latest  = df_latest.sort_values('Foreign_Share_Pct', ascending=True)

eu_avg = df_latest['Foreign_Share_Pct'].mean()

fig_bar = px.bar(
    df_latest,
    x='Foreign_Share_Pct',
    y='Country',
    orientation='h',
    color='Foreign_Share_Pct',
    color_continuous_scale='OrRd',
    range_color=[0, df_latest['Foreign_Share_Pct'].max()],
    title='Pillar 3 — Incarceration: Foreign Share of Prison Population (Latest Year per Country)',
    labels={'Foreign_Share_Pct': 'Foreign Share (%)', 'Country': 'Country'}
)

fig_bar.add_vline(
    x=eu_avg,
    line_dash='dash',
    line_color='steelblue',
    annotation_text=f'EU Avg: {eu_avg:.1f}%',
    annotation_position='top right'
)

fig_bar.update_layout(
    height=700,
    coloraxis_showscale=False,
    xaxis_title='Foreign Share of Prison Population (%)',
    yaxis_title=''
)

fig_bar.show()
"""


def make_markdown_cell(source):
    return {
        "cell_type": "markdown",
        "id": cid(),
        "metadata": {},
        "source": source
    }


def make_code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cid(),
        "metadata": {},
        "outputs": [],
        "source": source
    }


# ── Read notebook as raw JSON ─────────────────────────────────────────────────
with open(NB_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Remove empty trailing code cells
def _src_empty(cell):
    src = cell["source"]
    if isinstance(src, list):
        return not "".join(src).strip()
    return not src.strip()

while nb["cells"] and nb["cells"][-1]["cell_type"] == "code" and _src_empty(nb["cells"][-1]):
    nb["cells"].pop()

# Append new cells
new_cells = [
    make_markdown_cell(MARKDOWN_SRC),
    make_code_cell(ETL_SRC),
    make_code_cell(CHOROPLETH_SRC),
    make_code_cell(TREND_SRC),
    make_code_cell(BAR_SRC),
]
nb["cells"].extend(new_cells)

# Write back
with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"✅ Added {len(new_cells)} Pillar 3 cells to {NB_PATH.name}")
print(f"   Total cells now: {len(nb['cells'])}")
