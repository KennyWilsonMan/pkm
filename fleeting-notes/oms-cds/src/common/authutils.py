import streamlit as st
import requests
import urllib.parse
import jwt  # Import the jwt library
import pandas as pd
from streamlit.web.server.server import Server
from urllib.parse import urlunparse

# Configuration


# Function to generate a URL we can use to obtain a code from keycloak. 
# This code can be exchanged for an access token.
# The request will automajically include user credentials so long as the 
# user is not running incognito mode.
def get_login_url(auth_url, client_id, redirect_url):
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_url,
        "response_type": "code",
        "scope": "openid",
    }
    return f"{auth_url}?{urllib.parse.urlencode(params)}"

def get_access_token_from_kc(token_url, auth_code, client_id, redirect_url):
    payload = {
        "client_id": client_id,
        "redirect_uri": redirect_url,
        "grant_type": "authorization_code",
        "code": auth_code,
    }
    
    response = requests.post(token_url, data=payload, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch token: {response.status_code}, {response.text}")
        return None

def get_access_token_response(auth_url,token_url, client_id, redirect_uri):
    # We have not been to KC and hence have not been redirected with a code in the query params 
    if "code" not in st.query_params:
        # Check if we have an access token in the session state
        if "access_token" not in st.session_state:
            # No access token so call KC
            login_url = get_login_url(auth_url, client_id, redirect_uri)
            
            # Ouch! We want to make a clicky like thing with nothing rendered
            st.markdown(f'<meta http-equiv="refresh" content="0; url={login_url}">', unsafe_allow_html=True)
            return None   
        else:
            # We have an access token in the session state so we can return it
            return st.session_state["access_token"]
    else:
        # KC has redirected us and we have an access code which we can swap for a JWT token
        auth_code = st.query_params["code"]
        # Swap the access token for the JWT token
        access_token = get_access_token_from_kc(token_url, auth_code, client_id, redirect_uri)

        # Save the access token in the session state
        st.session_state["access_token"] = access_token
        st.query_params.clear()  # Clear the URL parameters
        return access_token


