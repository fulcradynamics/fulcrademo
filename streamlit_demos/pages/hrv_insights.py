from datetime import date, timedelta

import pandas as pd
import streamlit as st
from fulcra_api.core import FulcraAPI
from streamlit_demos.utils.menu import menu_with_redirect
from streamlit_demos.utils.utils import get_user_name

st.set_page_config(
    layout="wide",
    menu_items={"Get Help": "https://discord.com/invite/aunahVEnPU"},
)
fulcra = FulcraAPI()

st.header("HRV Insights")
menu_with_redirect()
# Set authenticated fulcra access token
fulcra = FulcraAPI()
fulcra.fulcra_cached_access_token = st.session_state["access_token"]

fulcra_user_id = None

try:
    datasets = fulcra.get_shared_datasets()
except Exception as exc:
    datasets = []
    st.write(exc)


def get_season_dates(year):
    return {
        "Spring": (date(year, 3, 20), date(year, 6, 20)),
        "Summer": (date(year, 6, 21), date(year, 9, 22)),
        "Fall": (date(year, 9, 23), date(year, 12, 20)),
        "Winter": (date(year, 12, 21), date(year + 1, 3, 19)),
    }


# Adding the year selector
year = st.selectbox(
    "Select Year",
    options=list(range(2020, 2030)),
    index=4,
)  # Select a year range as per your requirement

# Get the season dates for the selected year
season_dates = get_season_dates(year)

col1, col2 = st.columns([2, 2])

with col1:
    users = st.multiselect(
        "Choose Users",
        options=[get_user_name(dataset) for dataset in datasets],
    )

with col2:
    season = st.radio("Season", options=list(season_dates.keys()))


@st.cache_data
def get_hrv_data(fulcra_user_id, start_date, end_date) -> pd.DataFrame:
    df = fulcra.metric_time_series(
        start_time=start_date,
        end_time=end_date,
        sample_rate=86400,
        metric="HeartRateVariabilitySDNN",
        fulcra_userid=fulcra_user_id if fulcra_user_id else None,
        calculations=["max"],
    )
    return df


start_date, end_date = season_dates[season]
if users:
    cols = st.columns(len(users))

    if users:
        for index, user in enumerate(users):
            dataset_user = next(
                (item for item in datasets if get_user_name(item) == user), None
            )
            if dataset_user:
                fulcra_user_id = dataset_user["fulcra_userid"]
                df = get_hrv_data(fulcra_user_id, start_date, end_date)
                personal_best_day = (
                    df["max_heart_rate_variability_sdnn"].idxmax().date()
                )  # Gets the date with the max HRV
                personal_best_hrv = df[
                    "max_heart_rate_variability_sdnn"
                ].max()  # Gets the maximum step count

                # Display in a single card with Markdown
                cols[index].markdown(
                    f"""
                    <div style="background-color: #000000; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1); text-align: left; margin-bottom: 25px;">
                        <h2>Personal Best</h2>
                        <h3>{get_user_name(dataset_user)}</h3>
                        <p>Day: <strong>{personal_best_day}</strong></p>
                        <p>HRV: <strong style="color:green">{round(personal_best_hrv, 2)}</strong></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                cols[index].bar_chart(df)
