import streamlit as st
import requests
import urllib.parse
import jwt  # Import the jwt library

# Configuration
AUTH_URL = "https://keycloak-lon.prod.m/auth/realms/master/protocol/openid-connect/auth"
TOKEN_URL = "https://keycloak-lon.prod.m/auth/realms/master/protocol/openid-connect/token"
CLIENT_ID = "tpc-oms-tradeentrydashboard-uat"
# REDIRECT_URI = "https://basics.d.res.m"
REDIRECT_URI = "http://localhost:8501"
# CLIENT_SECRET = "your-client-secret"  # Replace with the actual client secret
SCOPE = "openid"

# Function to generate the login URL
def get_login_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

# Function to exchange authorization code for access token
def get_access_token(auth_code):
    payload = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": auth_code,
    }

    response = requests.post(TOKEN_URL, data=payload, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch token: {response.status_code}, {response.text}")
        return None

# Function to fetch user credentials
def get_user_info(access_token):
    userinfo_url = "https://keycloak-lon.prod.m/auth/realms/master/protocol/openid-connect/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(userinfo_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch user info: {response.status_code}, {response.text}")
        return None

# Function to decode JWT token
def decode_jwt(token):
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    return decoded_token

# Streamlit app logic
st.title("Keycloak Authentication Demo")

st.write(st.query_params)

# Step 1: Redirect user to Keycloak login
if "code" not in st.query_params:
    login_url = get_login_url()
    st.markdown(f'<meta http-equiv="refresh" content="0; url={login_url}">', unsafe_allow_html=True)
else:
    # Step 2: Handle the Keycloak redirect with auth code
    query_params = st.query_params
    auth_code = query_params["code"]  # Extract the authorization code from URL
    st.success("Authorization code received!")

#     # Step 3: Exchange auth code for access token
    token_response = get_access_token(auth_code)
    if token_response:
        access_token = token_response["access_token"]
        st.success("JWT code received!")
        st.write(access_token)

        st.query_params.clear()  # Clear the URL parameters

        # Decode the JWT token
        decoded_token = decode_jwt(access_token)
        st.success("Decoded JWT token:")
        st.json(decoded_token)
