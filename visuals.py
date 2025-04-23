# visualise.py
import streamlit as st
import pandas as pd
import pymysql
from config import db_config
import leafmap.foliumap as leafmap

# Function to load data from the database
def load_data():
    conn = pymysql.connect(**db_config)
    query = "SELECT * FROM satellite_metrics ORDER BY date DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Configure the Streamlit page
st.set_page_config(page_title="Chlorophyll Data Viewer", layout="wide")


# -------------------------------
# Raw data table
# -------------------------------
st.title("🛰️ Satellite Chlorophyll Data (Raw Table View)")

# Load and display the raw data
with st.spinner("Loading data..."):
    df = load_data()

if df.empty:
    st.warning("No data found in the database.")
else:
    st.dataframe(df, use_container_width=True)



# -------------------------------
# Split Panel NASA Image
# -------------------------------
st.title("🗺️ ESA WorldCover Split-panel Map")

m = leafmap.Map()
m.split_map(
    left_layer="ESA WorldCover 2020 S2 FCC", right_layer="ESA WorldCover 2020"
)
m.add_legend(title="ESA Land Cover", builtin_legend="ESA_WorldCover")
m.to_streamlit(height=700)




# -------------------------------
# Heatmap Visualisation
# -------------------------------

st.title("🔥 Chlorophyll Heatmap")

# Use real database data if it contains lat/lon and chlor_a fields
if {'latitude', 'longitude', 'mean'}.issubset(df.columns):
    heatmap = leafmap.Map(center=[df['latitude'].mean(), df['longitude'].mean()], zoom=4)
    heatmap.add_heatmap(
        df,
        latitude="latitude",
        longitude="longitude",
        value="mean",
        name="Chlorophyll-a Heatmap",
        radius=20,
    )
    heatmap.to_streamlit(height=700)
else:
    st.warning("Latitude, longitude, or chlorophyll value column not found in the dataset.")
