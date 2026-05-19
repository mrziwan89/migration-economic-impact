import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="IPUMS Brain Waste Map", layout="wide")

st.title("🧠 Brain Waste Ratio by State")
st.markdown(
    """
    This choropleth map compares the **brain-waste ratio** between immigrants and native-born residents across U.S. states.

    - **Red** = immigrants experience more brain waste
    - **Blue** = native-born residents experience more brain waste
    - Stronger colors indicate larger differences
    """
)

# ------------------------------------------------------------
# Expected CSV structure:
#
# state,immigrant_brain_waste,native_brain_waste
# CA,0.42,0.18
# TX,0.39,0.22
# NY,0.37,0.20
#
# state must use 2-letter USPS abbreviations.
# ------------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload your state-level brain waste CSV",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    required_cols = [
        "state",
        "immigrant_brain_waste",
        "native_brain_waste"
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}")
        st.stop()

    # Calculate the difference
    # Positive = immigrants have more brain waste
    # Negative = native-born have more brain waste
    df["brain_waste_diff"] = (
        df["immigrant_brain_waste"]
        - df["native_brain_waste"]
    )

    # Determine symmetric color range
    max_abs = max(abs(df["brain_waste_diff"].min()), abs(df["brain_waste_diff"].max()))

    fig = px.choropleth(
        df,
        locations="state",
        locationmode="USA-states",
        color="brain_waste_diff",
        scope="usa",
        color_continuous_scale=[
            [0.0, "darkblue"],
            [0.25, "royalblue"],
            [0.5, "white"],
            [0.75, "lightcoral"],
            [1.0, "darkred"],
        ],
        range_color=(-max_abs, max_abs),
        hover_name="state",
        hover_data={
            "immigrant_brain_waste": ":.2%",
            "native_brain_waste": ":.2%",
            "brain_waste_diff": ":+.2%",
        },
        labels={
            "brain_waste_diff": "Immigrant − Native Difference"
        },
    )

    fig.update_layout(
        height=700,
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(
            title="Brain Waste Difference"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Underlying Data")
    st.dataframe(df, use_container_width=True)

else:
    st.info(
        "Upload a CSV file containing state-level brain waste rates "
        "for immigrants and native-born residents."
    )

    example_df = pd.DataFrame({
        "state": ["CA", "TX", "NY", "FL"],
        "immigrant_brain_waste": [0.42, 0.39, 0.37, 0.33],
        "native_brain_waste": [0.18, 0.22, 0.20, 0.25]
    })

    st.subheader("Example Format")
    st.dataframe(example_df, use_container_width=True)
