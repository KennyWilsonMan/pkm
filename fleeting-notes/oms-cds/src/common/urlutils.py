from streamlit_javascript import st_javascript
import streamlit as st
import urllib.parse
import time


def get_base_url():
    return_value = st_javascript(""" window.location.href """)
    parsed_url = urllib.parse.urlparse(return_value)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Really horrible but the JS that extracts the URL seems to blow up
    # if we don't wait for a bit
    time.sleep(1)
    return base_url

