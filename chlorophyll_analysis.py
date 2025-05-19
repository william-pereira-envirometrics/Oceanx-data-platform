import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
from config import iron_release_date
import os
from PIL import Image
import plotly.graph_objects as go
import io
 
def aggregate_for_heatmap(df):    # AVG CHL + FHL PER LOCATION - TABLE
    query = """
    SELECT
        Latitude AS lat_bin,
        Longitude AS lon_bin,
        AVG(value) AS avg_value
    FROM df
    GROUP BY lat_bin, lon_bin
    """
    return duckdb.query(query).to_df()
 
def plotly_heatmap(df, title="Heatmap"):       # AVERAGE CHL+ FLH PER LOC - HEATMAP
    if df.empty:
        st.warning("No data available for this selection.")
        return
    px.set_mapbox_access_token("pk.eyJ1Ijoid2lsbHBlcmVpcmExMDgtIiwiYSI6ImNtYWRxeGloOTBhcWwybG9meWMybWQ0bG0ifQ.1PqKU69HpvY4u3LfqkthQw")  # User's real token
    fig = px.density_mapbox(
        df,
        lat='lat_bin',
        lon='lon_bin',
        z='avg_value',
        radius=10,
        center=dict(lat=df['lat_bin'].mean(), lon=df['lon_bin'].mean()),
        zoom=6,
        mapbox_style='carto-darkmatter',
        color_continuous_scale=[
            [0, "#B2EBF2"],
            [0.5, "#00bcd4"],
            [1, "#003366"]
        ],
        title=title,
        labels={'avg_value': 'Average Chlorophyll-a (mg/m³)'}
    )
    fig.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)
 
def render_chlorophyll_analysis(df):    
    # UI + TRANSAPRENCY
    st.markdown("""
    <style>
    /* Make everything transparent */
    .stApp {
        background-color: transparent !important;          
    }
    /* Make header/top bar transparent */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    /* Make sidebar transparent */
    section[data-testid="stSidebar"] {
        background-color: transparent !important;
    }
    /* Make all plot backgrounds transparent */
    .js-plotly-plot, .plot-container {
        background-color: transparent !important;
    }
    /* Make metrics transparent */
    .stMetric {
        background-color: transparent !important;
    }
    /* Make subheaders transparent */
    .stSubheader {
        background-color: transparent !important;
    }
    /* Make the tab bar background transparent */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
    }
    /* Make individual tab backgrounds transparent */
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
    }
    /* Existing slider styles */
    .stSlider {
        max-width: 300px !important;
        margin-left: 0 !important;
        padding: 0 !important;
    }
    .stSlider > div[data-baseweb="slider"] > div > div {
        background: #4FC3F7 !important;
    }
    .stSlider .rc-slider-track {
        background: #4FC3F7 !important;
    }
    .stSlider .rc-slider-handle {
        border-color: #4FC3F7 !important;
        background: #4FC3F7 !important;
    }
    .stSlider .rc-slider-mark-text {
        color: #4FC3F7 !important;
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
 
    chl_df = df[df['Measurement'].str.contains('CHL', case=False, na=False)].copy() # FITLERS DF WHERE = CHL
               
    chl_df['date'] = pd.to_datetime(chl_df['date'])                                           # CONVERT TO DATE
 
    before_data = chl_df[chl_df['date'] < pd.to_datetime(iron_release_date)]                   # CHL DF PRE INSTALL
 
    after_data = chl_df[chl_df['date'] >= pd.to_datetime(iron_release_date)]                   # CHL DF POST INSTALL
   
   
   
    # ----- TOTAL CHL OVER REGION OVER TIME -----
    st.subheader("Total Chlorophyll-a in Region Over Time")
    daily_totals = chl_df.groupby('date')['value'].sum().reset_index() # TOTAL CHL PER DATE - WHOLE REGION
    fig = go.Figure()
    fig.add_trace(go.Scatter(            
        x=daily_totals['date'],
        y=daily_totals['value'],
        mode='lines',
        line=dict(width=3, color='#4FC3F7'),
        fill='tozeroy',
        fillcolor='rgba(79, 195, 247, 0.3)',  
        hovertemplate="Date: %{x}<br>Total: %{y:.2f} mg/m³<extra></extra>"
    ))
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Total Chlorophyll-a (mg/m³)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)
   
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Average iron before release")
        agg_before = aggregate_for_heatmap(before_data)   #  HEATMAP BEFORE
        plotly_heatmap(agg_before, title="Average iron before release")
        st.metric(
            "Average Concentration",                    # AVERAGE CHL BEFORE
            f"{before_data['value'].mean():.2f} mg/m³"
        )
        st.metric(
            "Total Concentration",                       # TOTAL CHL BEFORE
            f"{before_data['value'].sum():.2f} mg/m³"
        )
    with col2:
        st.subheader("Average iron after release")
        agg_after = aggregate_for_heatmap(after_data)     # HEATMAP AFTER
        plotly_heatmap(agg_after, title="Average iron after release")
        st.metric(
            "Average Concentration",                   # AVERAGE CHL AFTER
            f"{after_data['value'].mean():.2f} mg/m³"
        )
        st.metric(
            "Total Concentration",                   # TOTAL CHL AFTER
            f"{after_data['value'].sum():.2f} mg/m³"
        )
    # GROWTH % (moved below heatmaps)
    st.metric("Growth Percentage", f"{((after_data['value'].mean() - before_data['value'].mean()) / before_data['value'].mean() * 100) if before_data['value'].mean() != 0 else 0:.1f}%")
    st.markdown("<br>", unsafe_allow_html=True)
   
   
   
    # ----- Single-Day Heatmap by Date Slider -----
    st.markdown("<br>", unsafe_allow_html=True)
 
 
 
    # SLIDER
    dates = sorted(chl_df['date'].unique()) # unique values for date in df
   
    selected_date = st.slider(                                        # SLIDER
        "Select Date",
        min_value=pd.to_datetime(min(dates)).to_pydatetime(),  # sets earlierst/ latest values for slider    
        max_value=pd.to_datetime(max(dates)).to_pydatetime(),
        value=pd.to_datetime(max(dates)).to_pydatetime(),      #set default value to latest date
        format="YYYY-MM-DD",
        key="chl_date_slider"
    )
 
    time_data = chl_df[chl_df['date'] == selected_date]    # When the user moves the slider, this line filters the chlorophyll data to only include rows for the selected date
   
 
 
   
    agg_time = aggregate_for_heatmap(time_data)    # ALLOWS SLIDER TO AFFECT CHL DF & AGGREGATE FOR HEATMAP
   
   
    plotly_heatmap(agg_time, title=f"{selected_date.strftime('%Y-%m-%d')}")  # HEATMAP ????????
 
   
    csv = df.to_csv(index=False)              # CSV DOWNLOAD
    st.download_button(
        label="Download raw data as CSV",
        data=csv,
        file_name='raw_data.csv',
        mime='text/csv',
        key='download_chl_csv'
    )
