import streamlit as st
import pandas as pd
import pymysql
from config import db_config
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go



# Function to load data from the database
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

# Configure the Streamlit page
st.set_page_config(page_title="Ocean Bloom Analysis", layout="wide")

# Title
st.title("🌊 Ocean Bloom Analysis Dashboard")

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
    # Filter for chlorophyll-a and FLH data
    chl_df = df[df['Measurement'].str.contains('CHL', case=False, na=False)].copy()
    flh_df = df[df['Measurement'].str.contains('FLH', case=False, na=False)].copy()
    
    # Convert date strings to datetime objects
    chl_df['date'] = pd.to_datetime(chl_df['date'])
    flh_df['date'] = pd.to_datetime(flh_df['date'])
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["Chlorophyll Analysis", "Bloom Growth", "FLH Analysis"])
    
    with tab1:
        st.header("Chlorophyll-a Concentration Analysis")
        
        # Get unique dates
        dates = sorted(chl_df['date'].unique())
        
        # Create two columns for before/after comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Before")
            before_date = st.selectbox(
                "Select 'Before' Date",
                dates,
                index=0,
                key="before"
            )
            
            # Filter data for selected date
            before_data = chl_df[chl_df['date'] == before_date]
            
            # Create heatmap
            m1 = folium.Map(
                location=[before_data['Latitude'].mean(), before_data['Longitude'].mean()],
                zoom_start=6
            )
            
            # Add heatmap layer
            heat_data = [[row['Latitude'], row['Longitude'], row['value']] 
                        for _, row in before_data.iterrows()]
            
            HeatMap(
                heat_data,
                radius=15,
                blur=10,
                max_zoom=1,
            ).add_to(m1)
            
            folium_static(m1, height=500)
            
            # Display statistics
            st.metric(
                "Average Concentration",
                f"{before_data['value'].mean():.2f} mg/m³"
            )
            st.metric(
                "Total Concentration",
                f"{before_data['value'].sum():.2f} mg/m³"
            )
        
        with col2:
            st.subheader("After")
            after_date = st.selectbox(
                "Select 'After' Date",
                dates,
                index=min(1, len(dates)-1),
                key="after"
            )
            
            # Filter data for selected date
            after_data = chl_df[chl_df['date'] == after_date]
            
            # Create heatmap
            m2 = folium.Map(
                location=[after_data['Latitude'].mean(), after_data['Longitude'].mean()],
                zoom_start=6
            )
            
            # Add heatmap layer
            heat_data = [[row['Latitude'], row['Longitude'], row['value']] 
                        for _, row in after_data.iterrows()]
            
            HeatMap(
                heat_data,
                radius=15,
                blur=10,
                max_zoom=1,
            ).add_to(m2)
            
            folium_static(m2, height=500)
            
            # Display statistics
            st.metric(
                "Average Concentration",
                f"{after_data['value'].mean():.2f} mg/m³"
            )
            st.metric(
                "Total Concentration",
                f"{after_data['value'].sum():.2f} mg/m³"
            )
        
        # Time series chart
        st.subheader("Chlorophyll-a Concentration Trend")
        date_range = st.slider(
            "Select Date Range",
            min_value=pd.to_datetime(min(dates)).to_pydatetime(),
            max_value=pd.to_datetime(max(dates)).to_pydatetime(),
            value=(pd.to_datetime(min(dates)).to_pydatetime(), pd.to_datetime(max(dates)).to_pydatetime()),
            format="YYYY-MM-DD"
        )
        
        time_series_data = chl_df[
            (chl_df['date'] >= date_range[0]) &
            (chl_df['date'] <= date_range[1])
        ]
        
        daily_means = time_series_data.groupby('date')['value'].mean().reset_index()
        
        fig = px.line(daily_means, x='date', y='value',
                     title='Chlorophyll-a Concentration Over Time',
                     labels={'value': 'Concentration (mg/m³)', 'date': 'Date'})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Bloom Growth Analysis")
        
        # Calculate growth percentage
        before_avg = before_data['value'].mean()
        after_avg = after_data['value'].mean()
        growth_pct = ((after_avg - before_avg) / before_avg) * 100 if before_avg != 0 else 0
        
        # Display growth metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Growth Percentage", f"{growth_pct:.1f}%")
        with col2:
            st.metric("Before Average", f"{before_avg:.2f} mg/m³")
        with col3:
            st.metric("After Average", f"{after_avg:.2f} mg/m³")
        
        # Create comparison slider
        st.subheader("Chlorophyll Concentration Comparison")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=before_data['Longitude'], y=before_data['Latitude'],
                                mode='markers', name='Before',
                                marker=dict(color=before_data['value'], colorscale='Viridis')))
        fig.add_trace(go.Scatter(x=after_data['Longitude'], y=after_data['Latitude'],
                                mode='markers', name='After',
                                marker=dict(color=after_data['value'], colorscale='Viridis')))
        fig.update_layout(title='Before/After Comparison',
                         xaxis_title='Longitude',
                         yaxis_title='Latitude')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("Fluorescence Line Height (FLH) Analysis")
        
        # FLH metrics
        flh_before = flh_df[flh_df['date'] == before_date]['value'].mean()
        flh_after = flh_df[flh_df['date'] == after_date]['value'].mean()
        flh_change = flh_after - flh_before
        
        # Calculate FLH/Chlorophyll ratio
        flh_chl_ratio_before = flh_before / before_avg if before_avg != 0 else 0
        flh_chl_ratio_after = flh_after / after_avg if after_avg != 0 else 0
        
        # Display FLH metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average FLH", f"{flh_df['value'].mean():.2f}")
        with col2:
            st.metric("Max FLH", f"{flh_df['value'].max():.2f}")
        with col3:
            st.metric("ΔFLH", f"{flh_change:.2f}")
        with col4:
            st.metric("FLH/Chl Ratio", f"{flh_chl_ratio_after:.2f}")
        
        # FLH Time Series
        st.subheader("FLH Time Trend")
        flh_time_series = flh_df[
            (flh_df['date'] >= date_range[0]) &
            (flh_df['date'] <= date_range[1])
        ]
        daily_flh_means = flh_time_series.groupby('date')['value'].mean().reset_index()
        
        fig = px.line(daily_flh_means, x='date', y='value',
                     title='FLH Trend Over Time',
                     labels={'value': 'FLH', 'date': 'Date'})
        st.plotly_chart(fig, use_container_width=True)
        
        # FLH vs Chlorophyll Scatter Plot
        st.subheader("FLH vs Chlorophyll-a Relationship")
        combined_data = pd.merge(chl_df, flh_df, on=['date', 'Latitude', 'Longitude'], suffixes=('_chl', '_flh'))
        fig = px.scatter(combined_data, x='value_chl', y='value_flh',
                        title='FLH vs Chlorophyll-a',
                        labels={'value_chl': 'Chlorophyll-a (mg/m³)', 'value_flh': 'FLH'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Add download button for CSV
    st.download_button(
        label="📥 Download CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='satellite_data.csv',
        mime='text/csv',
    )
    
    # Display raw data
    st.header("Raw Data")
    st.dataframe(df, use_container_width=True)
