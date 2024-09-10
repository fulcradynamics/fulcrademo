import streamlit as st
import pandas as pd
from fulcra_api.core import FulcraAPI
from datetime import date, datetime, time, timedelta

from utils.utils import get_user_name
from utils.menu import menu_with_redirect


st.set_page_config(layout="wide")
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

season_dates = {
    "Spring": (date(2024, 3, 20), date(2024, 6, 20)),
    "Summer": (date(2024, 6, 21), date(2024, 9, 22)),
    "Fall": (date(2024, 9, 23), date(2024, 12, 20)),
    "Winter": (date(2024, 12, 21), date(2025, 3, 19)),
}

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
        end_time=start_date + timedelta(days=60),
        sample_rate=1,
        metric="HeartRateVariabilitySDNN",
        fulcra_userid=fulcra_user_id if fulcra_user_id else None,
        calculations=["max"],
    )
    daily_hrv = df.resample("D").max()
    daily_hrv = daily_hrv[["max_heart_rate_variability_sdnn"]]
    return daily_hrv


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
                        <p>HRV: <strong style="color:green">{personal_best_hrv}</strong></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                cols[index].bar_chart(df)
