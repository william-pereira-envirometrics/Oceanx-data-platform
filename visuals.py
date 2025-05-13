import streamlit as st
import pandas as pd
import pymysql
from config import db_config
from PIL import Image
import os
import plotly.express as px
from chlorophyll_analysis import render_chlorophyll_analysis
from flh_analysis import render_flh_analysis


st.set_page_config(
    page_title="OceanX Analysis",      # TITLE 
    layout="wide",
    initial_sidebar_state="collapsed"  # Collapse sidebar by default
)

@st.cache_data(show_spinner="Loading data from database...")
def load_data():
    conn = pymysql.connect(**db_config)                       
    query = "SELECT * FROM satellite_metrics_simple ORDER BY date DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Export to CSV
    csv_filename = 'satellite_data_export.csv'
    df.to_csv(csv_filename, index=False)
    print(f"💾 Data exported to {csv_filename}")
    
    return df

# Inject custom CSS for tabs
st.markdown('''
    <style>
    /* Custom tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: #111111;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        background-color: #111111;
        border-radius: 0.5rem;
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #222831 !important;
        color: #ffffff !important;
    }
    </style>
''', unsafe_allow_html=True)

# OceanX logo at the very top
logo_path = r"C:/Users/Will_/OneDrive/Clients/Oceanx/Project/LOGO.png"
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo = Image.open(f)
        st.markdown('<div style="display: flex; justify-content: center; align-items: center; margin-bottom: 1rem;">', unsafe_allow_html=True)
        st.image(logo, width=300)
        st.markdown('</div>', unsafe_allow_html=True)

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

    # Convert numeric columns
    numeric_columns = ['Latitude', 'Longitude', 'value']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

if df.empty:
    st.warning("No data found in the database.")
else:
    # Create tabs for navigation
    tab1, tab2 = st.tabs(["Chlorophyll Analysis", "Fluorescence Analysis"])
    
    with tab1:
        st.markdown(
            '<div style="color:#fff;font-size:3.5rem;font-weight:700;line-height:1;margin-bottom:1.5rem;">Chlorophyll Analysis</div>',
            unsafe_allow_html=True
        )
        render_chlorophyll_analysis(df)
    with tab2:
        st.markdown(
            '<div style="color:#fff;font-size:3.5rem;font-weight:700;line-height:1;margin-bottom:1.5rem;">Fluorescence Analysis</div>',
            unsafe_allow_html=True
        )
        render_flh_analysis(df)
