import streamlit as st
import pandas as pd
import pymysql
from config import db_config
from st_aggrid import AgGrid, GridOptionsBuilder

# Function to load data from the database
def load_data():
    conn = pymysql.connect(**db_config)
    query = "SELECT * FROM satellite_metrics_simple ORDER BY date DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Configure the Streamlit page
st.set_page_config(page_title="Satellite Data Viewer", layout="wide")

# Title
st.title("🛰️ Satellite Data Viewer")

# Load and display the raw data
with st.spinner("Loading data..."):
    df = load_data()

    # Rename only if columns exist
    rename_dict = {}
    if "variable" in df.columns:
        rename_dict["variable"] = "Measurement"
    if "latitude" in df.columns:
        rename_dict["latitude"] = "Latitude"
    if "longitude" in df.columns:
        rename_dict["longitude"] = "Longitude"
    df.rename(columns=rename_dict, inplace=True)

if df.empty:
    st.warning("No data found in the database.")
else:
    gb = GridOptionsBuilder.from_dataframe(df)
    for col in df.columns:
        gb.configure_column(col, filter="agSetColumnFilter", sortable=True)

    grid_options = gb.build()

    AgGrid(
        df,
        gridOptions=grid_options,
        enable_enterprise_modules=False,
        fit_columns_on_grid_load=True,
        height=700,
    )
