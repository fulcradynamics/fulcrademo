import streamlit as st
import pandas as pd
from fulcra_api.core import FulcraAPI
from datetime import date, datetime, time

from utils.utils import get_user_name
from utils.menu import menu_with_redirect


st.set_page_config(layout="wide")
fulcra = FulcraAPI()

st.header("Walk/Stepcount insights")
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
def get_walking_data(fulcra_user_id, start_date, end_date) -> pd.DataFrame:
    df = fulcra.metric_time_series(
        start_time=start_date,
        end_time=end_date,
        sample_rate=1,
        metric="StepCount",
        fulcra_userid=fulcra_user_id if fulcra_user_id else None,
    )
    daily_sum = df["step_count"].resample("D").sum()
    daily_sum = daily_sum.round(0).astype(int)
    return daily_sum


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
                df = get_walking_data(fulcra_user_id, start_date, end_date)
                personal_best_day = df.idxmax()  # Gets the date with the max step count
                personal_best_steps = df.max()  # Gets the maximum step count

                start_of_day = datetime.combine(personal_best_day, time.min)
                end_of_day = datetime.combine(personal_best_day, time.max)
                location_time_series = fulcra.location_time_series(
                    start_of_day, end_of_day, change_meters=100, reverse_geocode=True
                )

                # Display in a single card with Markdown
                cols[index].markdown(
                    f"""
                    <div style="background-color: #000000; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1); text-align: left; margin-bottom: 25px;">
                        <h2>Personal Best</h2>
                        <h3>{get_user_name(dataset_user)}</h3>
                        <p>Day: <strong>{personal_best_day.strftime('%B %d, %Y')}</strong></p>
                        <p>Step Count: <strong style="color:green">{personal_best_steps}</strong></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                cols[index].bar_chart(df)
