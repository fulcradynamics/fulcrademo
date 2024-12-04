from datetime import datetime, time
import streamlit as st
from fulcra_api.core import FulcraAPI
from collections import Counter
import pandas as pd
import altair as alt
import pydeck as pdk
from streamlit_demos.utils.utils import get_user_name
import folium
from streamlit_folium import st_folium
from utils.utils import create_ics

from streamlit_demos.utils.utils import (
    get_current_year_window,
    get_current_week_dates,
    filter_and_rank_locations,
)
from streamlit_demos.utils.menu import menu_with_redirect


@st.cache
def apple_workouts(start_time, end_time, fulcra_user_id):
    return fulcra.apple_workouts(start_time, end_time, fulcra_user_id)


fulcra_user_id = None

st.set_page_config(
    layout="wide",
    menu_items={"Get Help": "https://discord.com/invite/aunahVEnPU"},
)
st.header("Fulcra Location Insights")
menu_with_redirect()

# Set authenticated fulcra access token
fulcra = FulcraAPI()
fulcra.fulcra_cached_access_token = st.session_state["access_token"]

try:
    datasets = fulcra.get_shared_datasets()
except Exception as exc:
    datasets = []
    st.write(exc)

users = st.selectbox(
    "Choose Users",
    options=[get_user_name(dataset) for dataset in datasets],
)

chosen_date = st.date_input("Choose a day for map", None)

st.sidebar.title("Location Analyzer")
change_meters = st.sidebar.slider(
    "Change Meters (Subsequent samples lower than this won't be included)",
    min_value=0,
    max_value=1000,
    value=50,
    step=1,
)
sample_rate = st.sidebar.slider(
    "Sample Rate (The length (in seconds) of each sample)",
    min_value=1,
    max_value=3400,
    value=1,
    step=1,
)

drop_nas = st.sidebar.radio(
    "Drop Nones",
    ["Yes", "No"],
)


def fulcra_location_insights():
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
        # Get location updates from apple for chosen period
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


def choose_day_for_map(users, chosen_date, change_meters, sample_rate, drop_nas):
    fulcra_user_id = None
    # User inputs for minimum distance change and speed thresholds

    if chosen_date:
        start_of_day = datetime.combine(chosen_date, time.min)
        end_of_day = datetime.combine(chosen_date, time.max)

        col1, col2 = st.columns(2)

        dataset_user = next(
            (item for item in datasets if get_user_name(item) == users), None
        )
        if dataset_user:
            fulcra_user_id = dataset_user["fulcra_userid"]

        # with col1:
        #     st.title("Apple Location Updates")
        #     apple_location_updates = fulcra.apple_location_updates(
        #         start_of_day,
        #         end_of_day,
        #         fulcra_user_id,
        #     )
        #     df_location_updates = pd.DataFrame(apple_location_updates)
        #     st.write(df_location_updates)
        #
        # with col2:
        #     st.title("Apple Location Visits")
        #     apple_location_visits = fulcra.apple_location_visits(
        #         start_of_day, end_of_day, fulcra_user_id
        #     )
        #     df_location_visits = pd.DataFrame(apple_location_visits)
        #     st.write(df_location_visits)

        if change_meters == 0:
            map_location_data = fulcra.location_time_series(
                start_time=start_of_day,
                end_time=end_of_day,
                sample_rate=sample_rate,
                reverse_geocode=False,
                fulcra_userid=fulcra_user_id,
            )
        else:
            map_location_data = fulcra.location_time_series(
                start_time=start_of_day,
                end_time=end_of_day,
                sample_rate=sample_rate,
                change_meters=change_meters,
                reverse_geocode=False,
                fulcra_userid=fulcra_user_id,
            )
        map_loc_dataframe = pd.DataFrame(map_location_data)
        map_loc_dataframe = map_loc_dataframe.rename(columns={"long": "lon"})
        if drop_nas == "Yes":
            map_loc_dataframe.dropna(subset=["lat", "lon"], inplace=True)

        # Create a list of [longitude, latitude] pairs
        path = map_loc_dataframe[["lon", "lat"]].values.tolist()
        with col1:
            col1.title("Apple workouts")
            df_workouts = apple_workouts(start_of_day, end_of_day, fulcra_user_id)
            col1.write(df_workouts)

        # with col2:
        # col2.title("Sleep Data")
        # df_sleep_data = fulcra.metric_time_series(
        #     start_time=start_of_day,
        #     end_time=end_of_day,
        #     sample_rate=300,
        #     metric="SleepStage",
        # )
        # col2.write(df_sleep_data)

        df_sorted = calculate_movements(map_loc_dataframe)
        # display_movements_map(map_loc_dataframe, df_sorted)

        if drop_nas == "Yes":
            # Create a DataFrame with the path
            path_data = pd.DataFrame({"path": [path]})
            view_state = pdk.ViewState(
                latitude=map_loc_dataframe["lat"].iloc[0],
                longitude=map_loc_dataframe["lon"].iloc[0],
                zoom=15,
                pitch=0,
            )

            layer = pdk.Layer(
                type="PathLayer",
                data=path_data,
                pickable=True,
                width_scale=20,
                width_min_pixels=1,
                get_color=[255, 0, 0],
                get_path="path",
                get_width=2,
            )
            r = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                map_style="mapbox://styles/mapbox/streets-v11",
            )
            st.pydeck_chart(r)


def calculate_movements(df):
    # Convert 'time' column to datetime
    df["time"] = pd.to_datetime(df["time"], format="ISO8601", utc=True)

    # Create 'start_time' and 'end_time' columns
    df["start_time"] = df["time"].shift(1)
    df["end_time"] = df["time"]

    # Calculate 'time_diff' between movements
    df["time_diff"] = (df["end_time"] - df["start_time"]).dt.total_seconds()

    # Remove rows with non-positive time differences
    df = df[df["time_diff"] > 0]

    # Calculate speed (meters per second)
    df["speed_mps"] = df["distance_change_m"] / df["time_diff"]

    # Define thresholds
    speed_threshold = 1.0  # Speed in m/s to be considered as moving
    time_gap_threshold = 6 * 60  # 6 minutes in seconds

    # Label movements based on speed
    df["status"] = df["speed_mps"].apply(
        lambda x: "In Commute" if x >= speed_threshold else "Stationary"
    )

    # Calculate time gaps between periods
    df["gap_duration"] = (
        (df["start_time"] - df["end_time"].shift(1)).dt.total_seconds().fillna(0)
    )

    # Identify where a new cluster starts
    df["new_cluster"] = (
        (df["gap_duration"] > time_gap_threshold)  # Time gap exceeds threshold
        | (df["status"] != df["status"].shift(1))  # Status changes
    ).astype(int)

    df["cluster_id"] = df["new_cluster"].cumsum()

    grouped = (
        df.groupby(["cluster_id", "status"])
        .agg(
            {
                "start_time": "first",
                "end_time": "last",
                "distance_change_m": "sum",
                "time_diff": "sum",
                "speed_mps": "mean",
            }
        )
        .reset_index()
    )

    # Display the results in Streamlit
    st.write("### Movement and Stationary Periods")
    st.dataframe(
        grouped[
            [
                "start_time",
                "end_time",
                "status",
                "distance_change_m",
                "time_diff",
                "speed_mps",
            ]
        ]
    )

    # Button to export to ICS
    if st.button("Export to ICS"):
        ics_data = create_ics(
            grouped[
                [
                    "start_time",
                    "end_time",
                    "status",
                    "distance_change_m",
                    "time_diff",
                    "speed_mps",
                ]
            ]
        )

        # Provide a download button
        st.download_button(
            label="Download ICS",
            data=ics_data,
            file_name="calendar_events.ics",
            mime="text/calendar",
        )


def display_movements_map(df, df_sorted):
    # Create a map centered at the average location
    avg_lat = df["lat"].mean()
    avg_lon = df["lon"].mean()
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

    # Add movement paths
    for _, row in df_sorted.iterrows():
        if pd.notnull(row["start_lat"]) and pd.notnull(row["start_lon"]):
            folium.PolyLine(
                locations=[
                    (row["start_lat"], row["start_lon"]),
                    (row["end_lat"], row["end_lon"]),
                ],
                color="blue",
                weight=2.5,
                opacity=0.8,
            ).add_to(m)

    # Display the map in Streamlit
    st.write("### Movement Paths")
    st_folium(m, width=700, height=500)


# fulcra_location_insights()
choose_day_for_map(users, chosen_date, change_meters, sample_rate, drop_nas)
