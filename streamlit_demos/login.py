import streamlit as st
from streamlit.components.v1 import html
from utils.menu import menu
import datetime
import time

from fulcra_api.core import (
    FULCRA_AUTH0_AUDIENCE,
    FULCRA_AUTH0_CLIENT_ID,
    FULCRA_AUTH0_DOMAIN,
    FULCRA_AUTH0_SCOPE,
    FulcraAPI,
)


def open_page(url, fulcra, device_code):
    open_script = """
        <script type="text/javascript">
            window.open('%s', '_blank').focus();
        </script>
    """ % (url)
    html(open_script)
    stop_at = datetime.datetime.now() + datetime.timedelta(seconds=120)
    while datetime.datetime.now() < stop_at:
        time.sleep(0.5)
        token, expiration_date = fulcra.get_token(device_code)
        if token is not None:
            st.toast("Login successful", icon=":material/thumb_up:")
            st.session_state["access_token"] = token
            return
    fulcra.fulcra_cached_access_token = None
    fulcra.fulcra_cached_access_token_expiration = None


st.header("Login to access fulcra insights", divider=True)
fulcra = FulcraAPI()
device_code, uri, _ = fulcra._request_device_code(
    FULCRA_AUTH0_DOMAIN,
    FULCRA_AUTH0_CLIENT_ID,
    FULCRA_AUTH0_SCOPE,
    FULCRA_AUTH0_AUDIENCE,
)
st.button("Login to fulcra", on_click=open_page, args=(uri, fulcra, device_code))
menu()
if "access_token" in st.session_state:
    st.switch_page("pages/fulcra_insights.py")
