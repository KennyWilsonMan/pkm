AUTH_URL = "https://keycloak-lon.prod/auth/realms/master/protocol/openid-connect/auth"
TOKEN_URL = "https://keycloak-lon.prod/auth/realms/master/protocol/openid-connect/token"
CLIENT_ID = "tpc-oms-tradeentrydashboard-{}"

def get_client_id(env):
    return f"""tpc-oms-tradeentrydashboard-{env}"""