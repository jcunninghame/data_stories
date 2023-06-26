import streamlit as st
from st_pages import show_pages_from_config, add_page_title
import util
import components as comp
import data
from palette import ORDINAL, PALETTE
import time
import pandas as pd

## --------------------------------- ##
## --- Page Setup
## --------------------------------- ##
st.set_page_config(
    layout="wide",
    page_icon=comp.favicon(),
    page_title="Tuva Health - Patient Summary",
    initial_sidebar_state="expanded",
)

comp.add_logo()
st.image(comp.tuva_logo())
add_page_title()
show_pages_from_config()

st.markdown(
    """
The charts below take a look at the demographics of patients in the 2020 Medicare LDS dataset as well as some key
patient indicators.
"""
)

patient_race = data.patient_race_data()
patient_gender = data.patient_gender_data()
patient_age = data.patient_age_data()
patient_state = data.patient_state_data()

demo_col1, demo_col2 = st.columns([1, 2])
with demo_col1:
    comp.donut_chart(
        df=patient_gender,
        quant="count",
        category="gender",
        title="Patient Counts by Sex",
        colors=[PALETTE["melon"], PALETTE["1-alice-blue"]],
    )
with demo_col2:
    comp.generic_simple_v_bar(
        df=patient_age,
        x="count",
        y="age_group",
        title="Patient Count by Age Group",
        color=PALETTE["2-light-sky-blue"],
        sort_col="age_group",
    )

comp.generic_simple_h_bar(
    patient_race,
    x="race",
    y="count",
    title="Patient Counts by Race",
    color=PALETTE["3-air-blue"],
    height="500px",
)

comp.state_map_chart(
    patient_state, "state", "count", "Patient Count by State", height="500px"
)
