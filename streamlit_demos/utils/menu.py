import streamlit as st


def authenticated_menu():
    # Show a navigation menu for authenticated users
    st.sidebar.page_link(
        "pages/calendars.py",
        label="Calendar Insights",
        icon=":material/calendar_month:",
    )

    st.sidebar.page_link(
        "pages/fulcra_insights.py",
        label="Location Insights",
        icon=":material/location_on:",
    )

    st.sidebar.page_link(
        "pages/walk_insights.py",
        label="Walk/Step Count Insights",
        icon=":material/footprint:",
    )

    st.sidebar.page_link(
        "pages/hrv_insights.py",
        label="HRV Insights",
        icon=":material/monitor_heart:",
    )

    st.sidebar.page_link(
        "pages/logout.py",
        label="Logout",
        icon=":material/logout:",
    )


def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    st.sidebar.page_link("login.py", label="Log in")


def menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    if "access_token" not in st.session_state:
        unauthenticated_menu()
        return
    authenticated_menu()


def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if "access_token" not in st.session_state:
        st.switch_page("login.py")
    menu()
