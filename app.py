import streamlit as st
import pandas as pd
import pymysql
from config import db_config
from PIL import Image
import os
import plotly.express as px
from chlorophyll_analysis import render_chlorophyll_analysis
from flh_analysis import render_flh_analysis
from login import check_login

# Set page config
st.set_page_config(
    page_title="OceanX Analysis",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Check login before showing any content
username = check_login()

# Add logout button in the top right
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# Show welcome message
st.markdown(f"<div style='text-align: right; color: #4FC3F7;'>Welcome, {username}!</div>", unsafe_allow_html=True)

@st.cache_data(show_spinner="Loading data from database...")
def load_data():
    try:
        conn = pymysql.connect(**db_config)                       
        query = "SELECT * FROM satellite_metrics_simple ORDER BY date DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Custom CSS for tabs
st.markdown('''
    <style>
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

# Try to load logo - works both locally and in cloud
try:
    # First try relative path (for cloud)
    if os.path.exists("LOGO.png"):
        logo = Image.open("LOGO.png")
    else:
        # Fallback to absolute path (for local)
        logo = Image.open(os.path.join(os.path.dirname(__file__), "LOGO.png"))
    
    st.markdown('<div style="display: flex; justify-content: center; align-items: center; margin-bottom: 1rem;">', 
                unsafe_allow_html=True)
    st.image(logo, width=300)
    st.markdown('</div>', unsafe_allow_html=True)
except Exception as e:
    st.title("OceanX Analysis")

# Load and display the data
with st.spinner("Loading data..."):
    df = load_data()

    if not df.empty:
        # Rename columns if they exist
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
    else:
        st.warning("No data found in the database.") 
