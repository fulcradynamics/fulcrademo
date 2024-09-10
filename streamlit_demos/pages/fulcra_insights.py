import streamlit as st
from fulcra_api.core import FulcraAPI
from collections import Counter
import pandas as pd
import altair as alt
from utils.utils import (
    get_current_year_window,
    get_current_week_dates,
    filter_and_rank_locations,
)
from utils.menu import menu_with_redirect

st.header("Fulcra Location Insights")
menu_with_redirect()

# Set authenticated fulcra access token
fulcra = FulcraAPI()
fulcra.fulcra_cached_access_token = st.session_state["access_token"]

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

location_visits = []
if len(week_period) > 1:
    # Get location updates from apple for the day
    location_visits = fulcra.location_time_series(
        start_time=week_period[0],
        end_time=week_period[1],
        reverse_geocode=True,
        sample_rate=5 * 60,
        change_meters=50,
    )

col1, col2 = st.columns(2)
location_counts = Counter()

with col1:
    if location_visits:
        location_counts = Counter([f"{loc['address']}" for loc in location_visits])
        # st.write(dict(location_counts.most_common()))
        st.slider(
            "Select Top No of locations",
            min_value=1,
            max_value=50,
            key="top_n_locations",
            value=25,
        )

top_locations = filter_and_rank_locations(
    location_visits, top_n=st.session_state["top_n_locations"]
)

# Extract unique location types from the top N locations
location_types = list(
    {
        loc["location_details"]["components"].get("_type", None)
        for loc in location_visits
        if all([loc["address"] in dict(top_locations), loc["location_details"]])
    }
)

with col2:
    # Multiselect to filter by location types
    selected_types = st.multiselect(
        "Filter by Location Type", options=location_types, default=location_types
    )

# st.bar_chart(
#     dict(
#         filter_and_rank_locations(
#             location_visits,
#             location_type=selected_types,
#             top_n=st.session_state["top_n_locations"],
#         )
#     ),
#     horizontal=True,
#     x_label="No of times visited",
#     y_label="Location name",
# )
filtered_top_locations = filter_and_rank_locations(
    location_visits,
    location_type=selected_types,
    top_n=st.session_state["top_n_locations"],
)

df = pd.DataFrame(filtered_top_locations, columns=["Location", "Visits"])
bar_chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("Visits:Q", title="Number of Visits"),
        y=alt.Y("Location:N", sort="-x", title="Location"),
        tooltip=["Location", "Visits"],
    )
    .properties(
        width=700,
        height=400,
        title=f"Top {st.session_state['top_n_locations']} Locations by Number of Visits",
    )
    .interactive()
)  # This makes the chart interactive

# Display the chart in Streamlit
st.altair_chart(bar_chart, use_container_width=True)
