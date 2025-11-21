# OMS CDS Streamlit App

[← Back to OMS CDS Notes](../README.md)

This directory contains a Streamlit application for analyzing OMS CDS data.

## Setup with Pegasus

### 1. Create Pegasus Environment

```bash
# Create a new pegasus environment (using 311-1 distribution)
pegasus create -d 311-1 oms-cds-app

# Activate the environment
pegasus activate oms-cds-app
```

### 2. Install Dependencies

```bash
# Navigate to the src directory
cd /turbo/kewilson/github/pkm/fleeting-notes/oms-cds/src

# Install required packages
pip install -r requirements.txt
```

### 3. Run the Streamlit App

```bash
streamlit run app.py
```

## App Features

- **CDS Position Selection**: Input Security ID and Book ID
- **Database Connection**: Connect to OMS database
- **Data Visualization**: Display CDS security details and key metrics
- **Interactive UI**: User-friendly interface built with Streamlit

## Configuration

### Database Connection

The app supports multiple environments via `db_connection.py`:

- **DEV**: D-DB-OMS-01,2001
- **UAT**: U-DB-OMS-01,2001 (default)
- **PROD**: P-DB-OMS-01,2001

All connections use:
- **Database**: OMS
- **Auth**: Windows Integrated Security
- **Driver**: ODBC Driver 17 for SQL Server

You can select the environment in the sidebar dropdown and test the connection before querying.

### Default Values

- **Security ID**: 24031746 (CDS WORLDLINE 500)
- **Book ID**: 137878

## Files

- `app.py` - Main Streamlit application
- `db_connection.py` - Database connection utilities (SQLAlchemy-based)
- `requirements.txt` - Python dependencies

## Dependencies

- **streamlit** - Web app framework
- **pandas** - Data manipulation
- **pyodbc** - Database connectivity
- **sqlalchemy** - SQL toolkit
- **plotly** - Interactive visualizations

## Usage

1. Start the app using `streamlit run app.py`
2. Enter Security ID and Book ID in the sidebar
3. Click "🔍 Query CDS Details" to retrieve data
4. View CDS details and metrics in the main panel

## Development

To add new features:
1. Activate your pegasus environment: `pegasus activate oms-cds-app`
2. Edit `app.py`
3. The app will auto-reload when you save changes

## Notes

- Ensure you have network access to U-DB-OMS-01
- The app uses Windows Integrated Authentication
- Query results are displayed in an interactive DataFrame
