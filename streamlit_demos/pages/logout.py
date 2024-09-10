import streamlit as st
from utils.menu import menu_with_redirect


def on_logout():
    if "access_token" in st.session_state:
        del st.session_state.access_token


st.header("Logout from Fulcra Insights")
st.button("Logout", on_click=on_logout)
menu_with_redirect()
