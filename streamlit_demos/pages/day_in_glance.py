import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from geopy.distance import geodesic
from streamlit_demos.utils.menu import menu_with_redirect


# Load JSON data
@st.cache_data
def load_data():
    with open("location_data.json", "r") as f:
        data = json.load(f)
    df = pd.json_normalize(data)
    return df


st.set_page_config(
    layout="wide",
    menu_items={"Get Help": "https://discord.com/invite/aunahVEnPU"},
)
st.header("Day in a Glance")
menu_with_redirect()

chosen_date = st.date_input("Choose a day for map", None)
if chosen_date:
    data = {
        "Task": ["Meeting", "Workout", "Rest", "Meeting", "Workout"],
        "Start": [
            "2023-10-07 09:00",
            "2023-10-07 12:30",
            "2023-10-07 23:00",
            "2023-10-07 14:00",
            "2023-10-07 18:00",
        ],
        "Finish": [
            "2023-10-07 10:30",
            "2023-10-07 13:30",
            "2023-10-08 07:00",
            "2023-10-07 15:00",
            "2023-10-07 19:00",
        ],
        "Description": [
            "Team Sync",
            "Gym Session",
            "Sleep",
            "Client Call",
            "Evening Run",
        ],
    }

    # Create DataFrame
    df = pd.DataFrame(data)
    df["Start"] = pd.to_datetime(df["Start"])
    df["Finish"] = pd.to_datetime(df["Finish"])

    # Create timeline chart
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Task",
        hover_data=["Description"],
    )

    # Update X-axis for 30-minute intervals
    fig.update_xaxes(
        type="date",
        tickformat="%H:%M",
        dtick=1800000,  # 30 minutes in milliseconds
        range=[df["Start"].min().floor("D"), df["Finish"].max().ceil("D")],
    )

    # Add annotations
    for idx, row in df.iterrows():
        fig.add_annotation(
            x=row["Start"] + (row["Finish"] - row["Start"]) / 2,
            y=idx,
            text=row["Description"],
            showarrow=False,
            yshift=1,
        )

    # Adjust layout
    fig.update_layout(
        title="Events",
        xaxis_title="Time",
        yaxis_title="",
        legend_title="Event Type",
        yaxis=dict(autorange="reversed"),
        height=600,
        margin=dict(l=50, r=50, t=50, b=50),
    )

    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    df = load_data()

    # Convert times to datetime and adjust to IST
    df["time"] = pd.to_datetime(df["time"]).dt.tz_convert("Asia/Kolkata")
    df = df.sort_values("time").reset_index(drop=True)

    # Calculate distance changes and time differences between consecutive points
    def calculate_distance_and_speed(df):
        distances = [0]
        time_deltas = [pd.Timedelta(seconds=0)]
        speeds = [0]
        for i in range(1, len(df)):
            prev_point = (df.loc[i - 1, "lat"], df.loc[i - 1, "long"])
            curr_point = (df.loc[i, "lat"], df.loc[i, "long"])
            distance = geodesic(prev_point, curr_point).meters
            time_delta = (df.loc[i, "time"] - df.loc[i - 1, "time"]).total_seconds()
            speed = distance / time_delta if time_delta > 0 else 0
            distances.append(distance)
            time_deltas.append(pd.Timedelta(seconds=time_delta))
            speeds.append(speed)
        df["distance_change_m"] = distances
        df["time_diff_s"] = [td.total_seconds() for td in time_deltas]
        df["speed_m_s"] = speeds
        return df

    df = calculate_distance_and_speed(df)

    # User inputs for minimum distance change and speed thresholds
    st.sidebar.title("Commute Analyzer")
    min_distance = st.sidebar.slider(
        "Minimum Distance Change (meters) to Define Movement",
        min_value=10,
        max_value=5000,
        value=500,
        step=10,
    )
    min_speed = st.sidebar.slider(
        "Minimum Speed (m/s) to Define Commute",
        min_value=0.0,
        max_value=30.0,
        value=2.0,
        step=0.1,
    )

    # Identify commute periods based on distance and speed thresholds
    df["is_commute"] = (df["distance_change_m"] >= min_distance) & (
        df["speed_m_s"] >= min_speed
    )

    # Function to identify commute periods with from and to locations
    def get_commute_periods(df):
        commute_periods = []
        for i in range(1, len(df)):
            if df.loc[i, "is_commute"]:
                start_time = df.loc[i - 1, "time"]
                end_time = df.loc[i, "time"]
                start_location = df.loc[i - 1, "address"]
                end_location = df.loc[i, "address"]
                distance = df.loc[i, "distance_change_m"]
                speed = df.loc[i, "speed_m_s"]
                date = start_time.date()
                commute_periods.append(
                    {
                        "Date": date,
                        "Start Time": start_time.strftime("%H:%M:%S"),
                        "End Time": end_time.strftime("%H:%M:%S"),
                        "From": start_location,
                        "To": end_location,
                        "Distance (m)": round(distance, 2),
                        "Speed (m/s)": round(speed, 2),
                    }
                )
        commute_df = pd.DataFrame(commute_periods)
        return commute_df

    commute_df = get_commute_periods(df)

    # Display commute periods
    st.title("Commute Periods")
    st.write(f"Minimum Distance Change: **{min_distance} meters**")
    st.write(f"Minimum Speed: **{min_speed} m/s**")

    if not commute_df.empty:
        # Group commutes by date
        for date, group in commute_df.groupby("Date"):
            st.subheader(f"Date: {date}")
            st.table(group.drop(columns=["Date"]).reset_index(drop=True))
    else:
        st.write("No commute periods found with the specified thresholds.")
