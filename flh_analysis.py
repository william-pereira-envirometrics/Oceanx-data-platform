import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
from config import iron_release_date
import plotly.graph_objects as go
 
def aggregate_for_heatmap(df):     # TABLE - AVG CHL/FHL PER LONG/ LAT   ?????????
    query = """
    SELECT
        Latitude AS lat_bin,
        Longitude AS lon_bin,
        AVG(value) AS avg_value
    FROM df
    GROUP BY lat_bin, lon_bin
    """
    return duckdb.query(query).to_df()
 
 
 
 
def plotly_heatmap(df, title="Heatmap"):    # PLOTS AVERAGE FHL PER SPECIFIC LONG/LAT ON HEATMAP ????
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
        labels={'avg_value': ' Average Fluorescence (W·m⁻²·µm⁻¹·sr⁻¹) '}
    )
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)
 
 
 
 
 
def render_flh_analysis(df):     # ????
    st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
 
    flh_df = df[df['Measurement'].str.contains('FLH', case=False, na=False)].copy() # FITLERS FOR FHL???
    flh_df['date'] = pd.to_datetime(flh_df['date'])                                 # CHANGE TO DATE ???
    before_data = flh_df[flh_df['date'] < pd.to_datetime(iron_release_date)]       # BEFORE IRON RELEASE???
    after_data = flh_df[flh_df['date'] >= pd.to_datetime(iron_release_date)]     # AFTER IRON RELEASE???
 
    flh_before = before_data['value'].mean()              #GROWTH %
    flh_after = after_data['value'].mean()    
    flh_change = flh_after - flh_before
    flh_change_pct = ((flh_after - flh_before) / flh_before) * 100 if flh_before != 0 else 0
 
    # ----- FLH OVER TIME LINE CHART (moved to top) -----
    st.subheader("Total FLH in Region Over Time")
    daily_flh_totals = flh_df.groupby('date')['value'].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_flh_totals['date'],
        y=daily_flh_totals['value'],
        mode='lines',
        line=dict(width=3, color='#4FC3F7'),
        fill='tozeroy',
        fillcolor='rgba(79, 195, 247, 0.3)',
        hovertemplate="Date: %{x}<br>Total FLH: %{y:.2f}<extra></extra>"
    ))
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Total FLH',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)
 
    col1, col2, col3, col4 = st.columns(4)
   
    with col1:
        st.metric("Average FLH", f"{flh_df['value'].mean():.2f}")     # AVG FLH
   
   
    with col2:
        st.metric("Max FLH", f"{flh_df['value'].max():.2f}")         # MAX FLH
   
    with col3:
        st.metric("ΔFLH", f"{flh_change:.2f}")                     # ??? ABSOUTLE CHANGE IN AVERAGE FLH AFTER RELEASE COMAPRED TO BEFORE
   
    with col4:
        st.metric("FLH Change", f"{flh_change_pct:.1f}%")      # GROWTH %
 
    st.markdown("<br>", unsafe_allow_html=True)
   
   
   
    # ----- BEFORE/AFTER HEATMAPS -----
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Before Iron Release")                 # HEATMAP AVERAGE FHL EACH LOCATION - BEFORE
        agg_before = aggregate_for_heatmap(before_data)
        plotly_heatmap(agg_before)
   
   
    with col2:
        st.subheader("After Iron Release")
        agg_after = aggregate_for_heatmap(after_data)   # HEATMAP AFTER FLH EACH LOCATION - AFTER
        plotly_heatmap(agg_after)
 
    st.markdown("<br>", unsafe_allow_html=True)
   
   
   
    # ----- SINGLE-DAY HEATMAP BY DATE SLIDER -----
 
    dates = sorted(flh_df['date'].unique())    # unique values for date in df
   
    selected_date = st.slider(                                # SLIDER
        "Select Date",
        min_value=pd.to_datetime(min(dates)).to_pydatetime(), # sets earlierst/ latest values for slider
        max_value=pd.to_datetime(max(dates)).to_pydatetime(),
        value=pd.to_datetime(max(dates)).to_pydatetime(),    # set default value to latest date
        format="YYYY-MM-DD",
        key="flh_date_slider"
    )
   
   
    time_data = flh_df[flh_df['date'] == selected_date]    #????
   
    agg_time = aggregate_for_heatmap(time_data)           #????
   
    plotly_heatmap(agg_time, title=f"{selected_date.strftime('%Y-%m-%d')}")  #????
 
    st.markdown("<br>", unsafe_allow_html=True)
   
   
    # ----- CHLOROPHYLL VS FLH SCATTER PLOT -----
    chl_df = df[df['Measurement'].str.contains('CHL', case=False, na=False)].copy()      #???????
    chl_df['date'] = pd.to_datetime(chl_df['date'])
    flh_df['date'] = pd.to_datetime(flh_df['date'])
    combined_data = pd.merge(chl_df, flh_df, on=['date', 'Latitude', 'Longitude'], suffixes=('_chl', '_flh'))
    st.subheader("Chlorophyll vs FLH Scatter Plot")
    fig = px.scatter(combined_data, x='value_chl', y='value_flh',
                    labels={'value_chl': 'Chlorophyll-a (mg/m³)', 'value_flh': 'FLH'},
                    color_discrete_sequence=['#4FC3F7'])
    st.plotly_chart(fig, use_container_width=True)
 
    st.markdown("""
    <style>
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
 
    # Download button for raw data (at the bottom)
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download raw data as CSV",
        data=csv,
        file_name='raw_data.csv',
        mime='text/csv',
        key='download_fhl_csv'
    )
