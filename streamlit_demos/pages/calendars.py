from collections import Counter
import streamlit as st
from fulcra_api.core import FulcraAPI
from utils import get_current_week_dates, get_current_year_window
import pandas as pd
import altair as alt


def get_top_participants(calendar_data):
    participants = []

    for event in calendar_data:
        if event["participants"]:
            for participant in event["participants"]:
                # Exclude the current user if needed
                if not participant.get("is_current_user", False):
                    participants.append(participant["name"] or participant["url"])

    # Count occurrences of each participant
    participant_counts = Counter(participants)

    # Convert to a sorted list of tuples (participant, count)
    top_participants = participant_counts.most_common()

    return top_participants


st.header("Calendar insights")

# Set authenticated fulcra access token
fulcra = FulcraAPI()
fulcra.fulcra_cached_access_token = st.session_state["access_token"]

calendars = fulcra.calendars()
calendar_select = [calendar["calendar_name"] for calendar in calendars]
selected_option = st.selectbox("Choose calendar", calendar_select)
calendar_id = next(
    (
        calendar["calendar_id"]
        for calendar in calendars
        if calendar["calendar_name"] == selected_option
    ),
    None,
)

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

calendar_data = fulcra.calendar_events(
    start_time=week_period[0], end_time=week_period[1], calendar_ids=[calendar_id]
)

# Get top participants
if calendar_data:
    top_participants = get_top_participants(calendar_data)
    df = pd.DataFrame(top_participants, columns=["Participant", "Meetings"])
    bar_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Meetings:Q", title="Number of Meetings"),
            y=alt.Y("Participant:N", sort="-x", title="Participant"),
            tooltip=["Participant", "Meetings"],
        )
        .properties(
            width=700, height=400, title="Top Participants by Number of Meetings"
        )
        .interactive()
    )
    st.altair_chart(bar_chart, use_container_width=True)
    st.write("Top Participants:")
    st.dataframe(df)
