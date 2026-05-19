import pandas as pd

import plotly.express as px
import streamlit as st
from streamlit_plotly_events import plotly_events

st.set_page_config(page_title="MIPEX 2019 World Map", layout="wide")
st.title("MIPEX 2019 World Map")

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



@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("data/raw/mipex/MIPEX2019.csv", sep=";")
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    metric_columns = [col for col in df.columns if col != "COUNTRY"]
    for col in metric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["iso_alpha"] = df["COUNTRY"].map(COUNTRY_TO_ISO3)
    return df


df = load_data()
metric_columns = [col for col in df.columns if col != "COUNTRY" and col != "iso_alpha"]

selected_metric = st.selectbox(
    "Indicator",
    metric_columns,
    index=0,
)


# Use session state to store selected countries
if "selected_countries" not in st.session_state:
    st.session_state.selected_countries = []

def update_selected_countries(country):
    if country in st.session_state.selected_countries:
        st.session_state.selected_countries.remove(country)
    elif len(st.session_state.selected_countries) < 5:
        st.session_state.selected_countries.append(country)

selected_countries = st.multiselect(
    "Select up to 5 countries for radar plot",
    options=df["COUNTRY"].tolist(),
    default=st.session_state.selected_countries,
    max_selections=5,
    key="country_multiselect",
)

st.session_state.selected_countries = selected_countries

chart_type = st.radio(
    "Chart type",
    ("World map", "Bar chart"),
    horizontal=True,
)



# Show the main chart (no click selection, just display)
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
    st.plotly_chart(fig, use_container_width=True)
elif chart_type == "Bar chart":
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
    st.plotly_chart(fig, use_container_width=True)

# Radar plot for selected countries
if selected_countries:
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
    st.plotly_chart(radar_fig, use_container_width=True)

with st.expander("Show underlying data"):
    st.dataframe(df[["COUNTRY", selected_metric]].sort_values(selected_metric, ascending=False))
