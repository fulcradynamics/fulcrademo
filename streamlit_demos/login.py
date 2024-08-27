import streamlit as st
from fulcra_api.core import FulcraAPI


def on_login():
    fulcra = FulcraAPI()
    fulcra.authorize()
    st.session_state["access_token"] = fulcra.fulcra_cached_access_token
    st.switch_page("pages/fulcra_insights.py")


st.header("Login to access fulcra insights", divider=True)
st.button("Login", on_click=on_login, type="primary")
