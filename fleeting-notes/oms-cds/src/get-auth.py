import streamlit as st
from common.authutils import get_access_token_response
from common.urlutils import get_base_url
import time  # Import the time module

# Configuration
AUTH_URL = "https://keycloak-lon.prod.m/auth/realms/master/protocol/openid-connect/auth"
TOKEN_URL = "https://keycloak-lon.prod.m/auth/realms/master/protocol/openid-connect/token"
CLIENT_ID = "tpc-oms-tradeentrydashboard-uat"

# AUTH_URL = "https://devkeycloak.maninvestments.com/auth/realms/rosacore-dev/protocol/openid-connect/auth"
# TOKEN_URL = "https://devkeycloak.maninvestments.com/auth/realms/rosacore-dev/protocol/openid-connect/auth/token"
# CLIENT_ID = "rosa-openapi-client"

base_url = get_base_url()

# Really horrible but the JS that extracts the URL seems to blow up
# if we don't wait for a bit
time.sleep(1)  

access_token = get_access_token_response(AUTH_URL, TOKEN_URL, CLIENT_ID, base_url)

if access_token is not None:
    st.write(access_token)

