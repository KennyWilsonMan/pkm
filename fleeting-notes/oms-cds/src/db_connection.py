"""
Database connection module for OMS SQL Server.
This module provides functions to connect to OMS SQL Server databases
and execute queries.
"""

import pandas as pd
from sqlalchemy.engine import URL
from sqlalchemy import create_engine, text

# Configuration
SQL_CONNECTIONS = {
    "dev": {
        "server": "D-DB-OMS-01",
        "port": 2001,
        "database": "OMS",
        "trusted_connection": True,
    },
    "uat": {
        "server": "U-DB-OMS-01",
        "port": 2001,
        "database": "OMS",
        "trusted_connection": True,
    },
    "prod": {
        "server": "P-DB-OMS-01",
        "port": 2001,
        "database": "OMS",
        "trusted_connection": True,
    }
}

DEFAULT_DRIVER = '{ODBC Driver 17 for SQL Server}'
APPLICATION_NAME = 'OMS-CDS-Streamlit-App'


def get_connection_string(env):
    """
    Generate a connection string for the specified environment.

    Args:
        env (str): The environment key from SQL_CONNECTIONS

    Returns:
        str: Connection string for SQL Server
    """
    if env not in SQL_CONNECTIONS:
        raise ValueError(f"Environment '{env}' not found in configuration")

    conn_config = SQL_CONNECTIONS[env]
    driver = DEFAULT_DRIVER
    server = conn_config["server"]
    port = conn_config.get("port", 1433)
    database = conn_config["database"]

    # Build the connection string
    connection_parts = [
        f"DRIVER={driver}",
        f"Server={server},{port}",
        f"Database={database}",
        f"Application Name={APPLICATION_NAME}"
    ]

    # Add authentication details
    if conn_config.get("trusted_connection", False):
        connection_parts.append("Trusted_Connection=yes")
        connection_parts.append("Integrated Security=true")
    else:
        username = conn_config.get("username")
        password = conn_config.get("password")
        if username and password:
            connection_parts.append(f"UID={username}")
            connection_parts.append(f"PWD={password}")
        else:
            raise ValueError(f"Username and password required for environment '{env}'")

    return ";".join(connection_parts)


def get_connection(env):
    """
    Create a SQLAlchemy engine for the specified environment.

    Args:
        env (str): The environment key from SQL_CONNECTIONS

    Returns:
        Engine: SQLAlchemy engine object
    """
    connection_string = get_connection_string(env)
    connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
    engine = create_engine(connection_url)

    return engine


def execute_query(env, query, params=None):
    """
    Execute a SQL query and return the results as a pandas DataFrame.

    Args:
        env (str): The environment key from SQL_CONNECTIONS
        query (str): SQL query to execute
        params (dict, optional): Parameters for the SQL query

    Returns:
        DataFrame: Results of the query
    """
    engine = get_connection(env)

    try:
        if params:
            df = pd.read_sql(text(query), engine, params=params)
        else:
            df = pd.read_sql(text(query), engine)
        return df
    except Exception as e:
        # Log the error and re-raise
        print(f"Error executing query: {str(e)}")
        raise


def test_connection(env):
    """
    Test the connection to the specified environment.

    Args:
        env (str): The environment key from SQL_CONNECTIONS

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        engine = get_connection(env)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Connection test failed: {str(e)}")
        return False
