from collections import Counter
import streamlit as st
from fulcra_api.core import FulcraAPI
from utils import get_current_week_dates, get_current_year_window
from menu import menu_with_redirect

st.header("Sleep insights")
menu_with_redirect()

# Set authenticated fulcra access token
fulcra = FulcraAPI()
fulcra.fulcra_cached_access_token = st.secrets["fulcra_access_token"]

# Create a period widget for current week
start_of_week, end_of_week = get_current_week_dates()
start_of_year, end_of_year = get_current_year_window()

week_period = st.date_input(
    "Select the date range (defaults to current week)",
    (start_of_week, end_of_week),
    start_of_year,
    end_of_year,
    format="MM.DD.YYYY",
    key="daterange",
)
# st.write(fulcra.metrics_catalog())
df = fulcra.metric_time_series(
    start_time=start_of_week, end_time=end_of_week, sample_rate=1, metric="SleepStage"
)

st.write(df)
