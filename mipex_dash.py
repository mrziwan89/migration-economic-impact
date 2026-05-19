import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc

COUNTRY_TO_ISO3 = {
    "Albania": "ALB",
    "Argentina": "ARG",
    "Australia": "AUS",
    "Austria": "AUT",
    "Belgium": "BEL",
    "Brazil": "BRA",
    "Bulgaria": "BGR",
    "Canada": "CAN",
    "Chile": "CHL",
    "China": "CHN",
    "Croatia": "HRV",
    "Cyprus": "CYP",
    "Czechia": "CZE",
    "Denmark": "DNK",
    "Estonia": "EST",
    "Finland": "FIN",
    "France": "FRA",
    "Germany": "DEU",
    "Greece": "GRC",
    "Hungary": "HUN",
    "Iceland": "ISL",
    "India": "IND",
    "Indonesia": "IDN",
    "Ireland": "IRL",
    "Israel": "ISR",
    "Italy": "ITA",
    "Japan": "JPN",
    "Jordan": "JOR",
    "Korea": "KOR",
    "Latvia": "LVA",
    "Lithuania": "LTU",
    "Luxembourg": "LUX",
    "Malta": "MLT",
    "Mexico": "MEX",
    "Moldova": "MDA",
    "Netherlands": "NLD",
    "New Zealand": "NZL",
    "North Macedonia": "MKD",
    "Norway": "NOR",
    "Poland": "POL",
    "Portugal": "PRT",
    "Romania": "ROU",
    "Russia": "RUS",
    "Saudi Arabia": "SAU",
    "Serbia": "SRB",
    "Slovakia": "SVK",
    "Slovenia": "SVN",
    "South Africa": "ZAF",
    "Spain": "ESP",
    "Sweden": "SWE",
    "Switzerland": "CHE",
    "Turkey": "TUR",
    "Ukraine": "UKR",
    "United Arab Emirates": "ARE",
    "United Kingdom": "GBR",
    "USA": "USA",
}

def load_data():
    df = pd.read_csv("data/raw/mipex/MIPEX2019.csv", sep=";")
    df.columns = df.columns.str.strip()
    metric_columns = [col for col in df.columns if col != "COUNTRY"]
    for col in metric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["iso_alpha"] = df["COUNTRY"].map(COUNTRY_TO_ISO3)
    return df

df = load_data()
metric_columns = [col for col in df.columns if col != "COUNTRY" and col != "iso_alpha"]

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("MIPEX 2019 World Map"),
    dbc.Row([
        dbc.Col([
            html.Label("Indicator"),
            dcc.Dropdown(
                id="metric-dropdown",
                options=[{"label": col, "value": col} for col in metric_columns],
                value=metric_columns[0],
                clearable=False
            ),
        ], width=4),
        dbc.Col([
            html.Label("Chart type"),
            dcc.RadioItems(
                id="chart-type-radio",
                options=[{"label": "World map", "value": "World map"}, {"label": "Bar chart", "value": "Bar chart"}],
                value="World map",
                inline=True
            ),
        ], width=4),
    ]),
    dbc.Row([
        dbc.Col([
            html.Label("Select up to 5 countries for radar plot"),
            dcc.Dropdown(
                id="country-multiselect",
                options=[{"label": c, "value": c} for c in df["COUNTRY"].tolist()],
                multi=True,
                value=[],
                maxHeight=200
            ),
        ], width=8),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="main-graph", config={"displayModeBar": False}),
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="radar-plot", config={"displayModeBar": False}),
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.Details([
                html.Summary("Show underlying data"),
                html.Div(id="data-table")
            ])
        ])
    ])
], fluid=True)

@app.callback(
    Output("main-graph", "figure"),
    Output("country-multiselect", "value"),
    Input("metric-dropdown", "value"),
    Input("chart-type-radio", "value"),
    Input("main-graph", "clickData"),
    State("country-multiselect", "value"),
)
def update_main_graph(selected_metric, chart_type, clickData, selected_countries):
    clicked_country = None
    if clickData and "points" in clickData and clickData["points"]:
        idx = clickData["points"][0]["pointIndex"]
        if chart_type == "World map":
            clicked_country = df.iloc[idx]["COUNTRY"]
        else:
            bar_df = df[["COUNTRY", selected_metric]].dropna().sort_values(selected_metric, ascending=False)
            clicked_country = bar_df.iloc[idx]["COUNTRY"]
    # Update selected countries
    if clicked_country:
        if clicked_country in selected_countries:
            selected_countries.remove(clicked_country)
        elif len(selected_countries) < 5:
            selected_countries.append(clicked_country)
    if chart_type == "World map":
        fig = px.choropleth(
            df,
            locations="iso_alpha",
            locationmode="ISO-3",
            color=selected_metric,
            hover_name="COUNTRY",
            color_continuous_scale=["lightcoral", "cornflowerblue"],
            title=f"MIPEX 2019 - {selected_metric}",
        )
        fig.update_layout(margin={"r": 0, "t": 60, "l": 0, "b": 0})
    else:
        bar_df = df[["COUNTRY", selected_metric]].dropna().sort_values(selected_metric, ascending=False)
        fig = px.bar(
            bar_df,
            x="COUNTRY",
            y=selected_metric,
            color=selected_metric,
            color_continuous_scale=["lightcoral", "cornflowerblue"],
            title=f"MIPEX 2019 - {selected_metric} (Bar chart)",
        )
        fig.update_layout(
            xaxis_title="Country",
            yaxis_title=selected_metric,
            xaxis_tickangle=-45,
            margin={"r": 0, "t": 60, "l": 0, "b": 0},
        )
    return fig, selected_countries

@app.callback(
    Output("radar-plot", "figure"),
    Input("country-multiselect", "value"),
    Input("metric-dropdown", "value"),
)
def update_radar(selected_countries, selected_metric):
    if not selected_countries:
        return {}
    radar_df = df[df["COUNTRY"].isin(selected_countries)][["COUNTRY"] + metric_columns].set_index("COUNTRY")
    radar_fig = px.line_polar(
        radar_df.reset_index().melt(id_vars="COUNTRY", value_vars=metric_columns),
        r="value",
        theta="variable",
        color="COUNTRY",
        line_close=True,
        title="Comparison of Selected Countries (Radar Plot)",
    )
    radar_fig.update_traces(fill="toself")
    radar_fig.update_layout(margin={"r": 0, "t": 60, "l": 0, "b": 0})
    return radar_fig

@app.callback(
    Output("data-table", "children"),
    Input("metric-dropdown", "value"),
)
def update_table(selected_metrics):
    table_df = df[["COUNTRY", selected_metric]].sort_values(selected_metric, ascending=False)
    return dbc.Table.from_dataframe(table_df, striped=True, bordered=True, hover=True)

if __name__ == "__main__":
    app.run(debug=True)
