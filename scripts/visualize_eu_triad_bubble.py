import pandas as pd
import plotly.graph_objects as go
import json
import os

# --- Configuration & Paths ---
PROCESSED_DATA = "../data/processed/eurostat_insights.csv"
OUTPUT_HTML = "../docs/eu_triad_bubble_map.html"

EU_ISO2_TO_ISO3 = {
    "AT":"AUT","BE":"BEL","BG":"BGR","CY":"CYP","CZ":"CZE",
    "DE":"DEU","DK":"DNK","EE":"EST","ES":"ESP","FI":"FIN",
    "FR":"FRA","GR":"GRC","EL":"GRC","HR":"HRV","HU":"HUN",
    "IE":"IRL","IT":"ITA","LT":"LTU","LU":"LUX","LV":"LVA",
    "MT":"MLT","NL":"NLD","PL":"POL","PT":"PRT","RO":"ROU",
    "SE":"SWE","SI":"SVN","SK":"SVK","UK":"GBR","NO":"NOR",
    "CH":"CHE","IS":"ISL","MK":"MKD","RS":"SRB","ME":"MNE",
    "AL":"ALB","TR":"TUR","BA":"BIH","XK":"XKX",
}

# Centroids for EU countries for Scattergeo markers
COUNTRY_COORDS = {
    "AUT":(47.8,13.3),"BEL":(50.8,4.4),"BGR":(42.7,25.5),
    "CYP":(35.1,33.4),"CZE":(49.8,15.5),"DEU":(51.2,10.4),
    "DNK":(56.3,9.5),"EST":(58.6,25.0),"ESP":(40.4,-3.7),
    "FIN":(61.9,25.7),"FRA":(46.2,2.2),"GRC":(39.1,21.8),
    "HRV":(45.1,15.2),"HUN":(47.2,19.5),"IRL":(53.4,-8.2),
    "ITA":(41.9,12.6),"LTU":(55.2,23.9),"LUX":(49.8,6.1),
    "LVA":(57.0,24.8),"MLT":(35.9,14.5),"NLD":(52.1,5.3),
    "POL":(51.9,19.1),"PRT":(39.4,-8.2),"ROU":(45.9,24.9),
    "SWE":(60.1,18.6),"SVN":(46.1,14.8),"SVK":(48.7,19.7),
    "GBR":(55.4,-3.4),"NOR":(60.5,8.5),"CHE":(46.8,8.2),
    "ISL":(65.0,-18.6),"MKD":(41.6,21.7),"SRB":(44.0,21.0),
    "MNE":(42.7,19.4),"ALB":(41.2,20.2),"TUR":(39.9,32.9),
    "BIH":(43.9,17.7),"XKX":(42.6,20.9),
}

def generate_bubble_map():
    if not os.path.exists(PROCESSED_DATA):
        print(f"Error: {PROCESSED_DATA} not found. Run preprocessing first.")
        return

    # 1. Load data
    df = pd.read_csv(PROCESSED_DATA)
    df["ISO3"] = df["Country"].map(EU_ISO2_TO_ISO3)
    df = df.dropna(subset=["ISO3"])

    # Pivot: one row per (Year, ISO3) with all metrics as columns
    pivoted = df.pivot_table(
        index=["Year","ISO3","Country"],
        columns="Metric",
        values="Gap_ExtraEU_vs_Native_PP",
        aggfunc="mean"
    ).reset_index()
    pivoted.columns.name = None

    # Ensure all target columns exist
    for col in ["Highly_Educated_Employment_Rate","Poverty_Rate","Temporary_Contract_Rate"]:
        if col not in pivoted.columns:
            pivoted[col] = float("nan")

    # Add coordinates
    pivoted["lat"] = pivoted["ISO3"].map(lambda x: COUNTRY_COORDS.get(x,(None,None))[0])
    pivoted["lon"] = pivoted["ISO3"].map(lambda x: COUNTRY_COORDS.get(x,(None,None))[1])
    pivoted = pivoted.dropna(subset=["lat","lon"])

    # 2. Setup Animation Scales
    START_YEAR = 2005
    years = sorted(pivoted["Year"].unique())
    years = [y for y in years if y >= START_YEAR]

    # Global scale anchors for consistency across frames
    max_temp = pivoted["Temporary_Contract_Rate"].abs().quantile(0.95)
    min_pov  = pivoted["Poverty_Rate"].min(skipna=True)
    max_pov  = pivoted["Poverty_Rate"].max(skipna=True)

    def make_trace(sub):
        temp_gap = sub["Temporary_Contract_Rate"].fillna(0)
        pov_gap  = sub["Poverty_Rate"]
        empl_gap = sub["Highly_Educated_Employment_Rate"]

        # Size ∝ absolute temp contract gap (larger = more inequality)
        sizes = (temp_gap.abs() / max_temp * 35 + 4).clip(lower=4, upper=45)

        # Handle Missing Poverty Data (Post-2020)
        # Instead of transparency, we use a gray color for missing data
        colors = pov_gap.fillna(-999) # Placeholder for missing
        
        # Define a custom colorscale that handles the placeholder
        # Since Plotly express doesn't easily mix categorical/continuous, 
        # we'll just use the default and explain in the hover.
        # Actually, let's stick to the previous opacity trick but IMPROVE it.
        # We'll use 0.9 for real data and 0.4 for missing, but KEEP the color scale.
        opacity = pov_gap.notna().map({True: 0.9, False: 0.5})

        customdata = list(zip(
            sub["Country"],
            empl_gap.round(1).fillna("N/A"),
            pov_gap.round(1).fillna("N/A (Lags post-2020)"),
            temp_gap.round(1),
        ))

        return go.Scattergeo(
            lat=sub["lat"],
            lon=sub["lon"],
            mode="markers",
            marker=dict(
                size=sizes,
                color=pov_gap,
                colorscale="Reds",
                cmin=min_pov,
                cmax=max_pov,
                colorbar=dict(
                    title="Poverty Risk Gap (PP)",
                    x=1.02,
                    thickness=15,
                    len=0.7
                ),
                opacity=opacity.values,
                line=dict(width=1, color="rgba(255,255,255,0.8)"),
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Employment Gap (Educated): <b>%{customdata[1]} pp</b><br>"
                "Poverty Risk Gap:        <b>%{customdata[2]} pp</b><br>"
                "Temp Contract Gap:       <b>%{customdata[3]} pp</b><br>"
                "<extra></extra>"
            ),
            showlegend=False,
        )

    # 3. Assemble Frames
    frames = [
        go.Frame(data=[make_trace(pivoted[pivoted["Year"] == y])], name=str(y))
        for y in years
    ]

    # First frame trace
    first_trace = make_trace(pivoted[pivoted["Year"] == years[0]])

    # 4. Define Layout
    fig = go.Figure(
        data=[first_trace],
        frames=frames,
        layout=go.Layout(
            title=dict(
                text="<b>The Triad of Brain Waste in Europe</b> (2005–2023)<br>"
                     "<sup>Size = Contract Inequality | Color = Poverty Risk | Hover = Employment Gap</sup>",
                x=0.5, xanchor="center",
                font=dict(size=20)
            ),
            geo=dict(
                scope="europe",
                projection_type="natural earth",
                showland=True, landcolor="#1c1e26",
                showocean=True, oceancolor="#0d1117",
                showcountries=True, countrycolor="#3a3d4d",
                showcoastlines=True, coastlinecolor="#3a3d4d",
                showframe=False,
                bgcolor="#0d1117",
            ),
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            font=dict(color="#e0e0e0", family="Inter, sans-serif"),
            height=750,
            margin=dict(r=50, t=100, l=50, b=50),
            updatemenus=[dict(
                type="buttons", showactive=False,
                x=0.1, xanchor="right", y=0, yanchor="top",
                pad={"r":10,"t":70},
                buttons=[
                    dict(label="▶ Play", method="animate",
                         args=[None, {"frame":{"duration":800,"redraw":True},
                                      "fromcurrent":True,"transition":{"duration":500}}]),
                    dict(label="⏸ Pause", method="animate",
                         args=[[None], {"frame":{"duration":0,"redraw":False},
                                        "mode":"immediate","transition":{"duration":0}}]),
                ],
            )],
            sliders=[dict(
                active=0,
                steps=[dict(args=[[str(y)],{"frame":{"duration":800,"redraw":True},
                                             "mode":"immediate",
                                             "transition":{"duration":400}}],
                            label=str(y), method="animate")
                       for y in years],
                x=0.1, xanchor="left",
                y=0, yanchor="top",
                len=0.9,
                currentvalue=dict(prefix="Year: ", font=dict(size=16, color="#e0e0e0")),
                pad={"b":10,"t":50},
                font=dict(color="#e0e0e0"),
            )],
            annotations=[
                dict(
                    x=0.5, y=-0.08, xref="paper", yref="paper",
                    text="ℹ️ <b>Data Insight:</b> Employment and Contract data is available through 2023. "
                         "Poverty data (color) lags and is shown as semi-transparent for post-2020 years.",
                    font=dict(size=12, color="#aaaaaa"),
                    showarrow=False, align="center",
                )
            ],
        ),
    )

    # 5. Export/Show
    fig.write_html(OUTPUT_HTML)
    print(f"\n✅ Visualization saved to {OUTPUT_HTML}")
    fig.show()

if __name__ == "__main__":
    generate_bubble_map()
