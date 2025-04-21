import streamlit as st
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go
from pinotdb import connect
from typing import Dict, List, Any, Tuple

# Set page config
st.set_page_config(
    page_title="Real-time Racing Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dashboard title
st.title("🏎️ Real-time Racing Telemetry Dashboard")

def fetch_data() -> Dict[str, List[Any]]:
    try:
        conn = connect(host='localhost', port=8099, path='/query/sql', scheme='http')
        query = """
        SELECT DriverNo, SessionKey, drs, n_gear, Utc, 'timestamp' as ts, rpm, speed, throttle, brake 
        FROM carData
        ORDER BY DriverNo ASC 
        LIMIT 20
        """
        cursor = conn.cursor()
        cursor.execute(query)
        
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()

        result_dict = {col: [] for col in columns}
        for row in data:
            for i, col in enumerate(columns):
                result_dict[col].append(row[i])
        
        numeric_cols = ['drs', 'n_gear', 'rpm', 'speed', 'throttle', 'brake']
        for col in numeric_cols:
            if col in result_dict:
                result_dict[col] = [float(val) if val is not None else None for val in result_dict[col]]
            
        return result_dict
    except Exception as e:
        st.error(f"Error connecting to Pinot: {e}")
        return {col: [] for col in ['DriverNo', 'SessionKey', 'drs', 'n_gear', 'Utc', 'ts', 'rpm', 'speed', 'throttle', 'brake']}


def get_driver_data(data: Dict[str, List[Any]], driver_no: str) -> Dict[str, List[Any]]:
    indices = [i for i, d in enumerate(data['DriverNo']) if d == driver_no]
    if not indices:
        return {key: None for key in data.keys()}
    
    # Get the most recent data point for this driver
    latest_idx = indices[-1]
    return {key: value[latest_idx] for key, value in data.items()}

def get_unique_drivers(data: Dict[str, List[Any]]) -> List[str]:
    unique_drivers = list(set(data['DriverNo']))
    return sorted(unique_drivers, key=lambda x: int(x))

def create_gauge(value: float, title: str, max_value: float, color_threshold: List[float] = None) -> go.Figure:
    """Create a gauge chart for telemetry data"""
    if color_threshold is None:
        color_threshold = [0.33, 0.66, 1]
    
    # Modern color palette
    colors = {
        "low": "#4CAF50",     # Green
        "medium": "#FFC107",  # Amber
        "high": "#F44336",    # Red
        "bar": "#2196F3"      # Blue
    }
        
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'color': '#424242', 'size': 16}},
        gauge={
            'axis': {'range': [None, max_value], 'tickcolor': '#757575'},
            'bar': {'color': colors["bar"]},
            'steps': [
                {'range': [0, max_value * color_threshold[0]], 'color': colors["low"]},
                {'range': [max_value * color_threshold[0], max_value * color_threshold[1]], 'color': colors["medium"]},
                {'range': [max_value * color_threshold[1], max_value], 'color': colors["high"]},
            ],
            'borderwidth': 2,
            'bordercolor': "#E0E0E0"
        },
        number={'font': {'color': '#212121'}}
    ))
    fig.update_layout(
        height=250, 
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

with st.sidebar:
    st.header("Dashboard Settings")
    auto_refresh = st.checkbox("Auto-refresh data", value=True)
    refresh_interval = st.slider("Refresh interval (seconds)", 1, 10, 3)

# Main dashboard area
data = fetch_data()
unique_drivers = get_unique_drivers(data)

if not unique_drivers:
    st.warning("No driver data available. Please check your connection to Pinot.")
else:
    with st.sidebar:
        selected_driver = st.selectbox("Select Driver", unique_drivers)

    if selected_driver:
        # Create a placeholder for the dashboard
        dashboard_placeholder = st.empty()
        
        # Auto-refresh loop
        while True:
            data = fetch_data()
            driver_data = get_driver_data(data, selected_driver)
            
            # Generate a unique timestamp for this iteration's keys
            timestamp = int(time.time() * 1000)
            
            with dashboard_placeholder.container():
                # Driver info header
                st.subheader(f"Driver #{selected_driver} Telemetry")
                
                # Create two rows of metrics
                col1, col2= st.columns(2)
                
                # DRS Status
                with col1:
                    drs_value = driver_data.get('drs')
                    drs_status = "ACTIVE" if drs_value == 12 else "INACTIVE"
                    drs_color = "#4CAF50" if drs_status == "ACTIVE" else "#9E9E9E"  # Green when active, gray when inactive
                    st.markdown(f"""
                    <div style="border:2px solid {drs_color}; border-radius:10px; padding:10px; text-align:center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h3 style="color:#424242; margin-bottom:5px;">DRS</h3>
                        <h2 style="color:{drs_color}; margin-top:0;">{drs_status}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Current Gear
                with col2:
                    current_gear = int(driver_data.get('n_gear', 0))
                    gear_color = "#2196F3"  # Blue color for gear display
                    st.markdown(f"""
                    <div style="border:2px solid {gear_color}; border-radius:10px; padding:10px; text-align:center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h3 style="color:#424242; margin-bottom:5px;">Current Gear</h3>
                        <h2 style="color:{gear_color}; margin-top:0;">{current_gear}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Second row
                col3, col4, col5, col6 = st.columns(4)
                
                # RPM
                with col3:
                    rpm_value = driver_data.get('rpm', 0)
                    rpm_fig = create_gauge(rpm_value, "RPM", 15000)
                    st.plotly_chart(rpm_fig, use_container_width=True, key=f"rpm_chart_{timestamp}")

                # Speed
                with col4:
                    speed_value = driver_data.get('speed', 0)
                    speed_fig = create_gauge(speed_value, "Speed (km/h)", 350)
                    st.plotly_chart(speed_fig, use_container_width=True, key=f"speed_chart_{timestamp}")
                
                # Throttle
                with col5:
                    throttle_value = driver_data.get('throttle', 0)
                    throttle_fig = create_gauge(throttle_value, "Throttle %", 100, [0.5, 0.8, 1])
                    st.plotly_chart(throttle_fig, use_container_width=True, key=f"throttle_chart_{timestamp}")
                
                # Brake
                with col6:
                    brake_value = driver_data.get('brake', 0)
                    brake_fig = create_gauge(brake_value, "Brake %", 100, [0.3, 0.6, 1])
                    st.plotly_chart(brake_fig, use_container_width=True, key=f"brake_chart_{timestamp}")
                
                # Raw data in expandable section
                with st.expander("Raw Telemetry Data"):
                    st.write(driver_data)
            
            if not auto_refresh:
                break
                
            time.sleep(refresh_interval)

    