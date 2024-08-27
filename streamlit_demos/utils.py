from datetime import datetime, timedelta
from collections import Counter


def get_current_week_dates():
    today = datetime.today()
    start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    end_of_week = start_of_week + timedelta(days=6)
    end_of_week = end_of_week.replace(hour=23, minute=59, second=59, microsecond=0)

    return (start_of_week, end_of_week)


def get_current_year_window():
    current_year = datetime.now().year
    start_of_year = datetime(current_year, 1, 1)
    end_of_year = datetime(current_year, 12, 31, 23, 59, 59)

    return (start_of_year, end_of_year)


def filter_and_rank_locations(data, location_type=None, top_n=50):
    # Filter locations optionally by type
    filtered_locations = [
        loc["address"]
        for loc in data
        if location_type is None
        or loc["location_details"]["components"].get("_type") in location_type
    ]

    # Count occurrences of each location
    location_counts = Counter(filtered_locations)

    # Get the top N locations
    top_locations = location_counts.most_common(top_n)

    return top_locations
