import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
from storage import DataStore
from analytics import resample_ohlcv, calculate_spread_and_zscore, calculate_rolling_correlation
from config import SYMBOLS, ROLLING_WINDOW_SHORT, ROLLING_WINDOW_LONG, Z_SCORE_THRESHOLD

# Page Config
st.set_page_config(
    page_title="Quant Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Data Store
# We don't cache this because we want fresh connections in the thread
store = DataStore()

# Sidebar Controls
st.sidebar.title("Controls")
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 0.5, 5.0, 1.0)
timeframe = st.sidebar.selectbox("Timeframe", ["1s", "1Min", "5Min"], index=0)
window_size = st.sidebar.number_input("Rolling Window", min_value=10, max_value=200, value=ROLLING_WINDOW_SHORT)
z_threshold = st.sidebar.number_input("Z-Score Threshold", min_value=1.0, max_value=5.0, value=Z_SCORE_THRESHOLD)

# Mapping timeframes to pandas alias
tf_map = {"1s": "1S", "1Min": "1min", "5Min": "5min"}
selected_tf = tf_map[timeframe]

# Main Title
st.title("Real-Time Crypto Arbitrage Monitor")

# Placeholders for live updates
# Placeholders for live updates
alert_placeholder = st.empty()
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
chart_col1, chart_col2 = st.columns(2)
spread_col, zscore_col = st.columns(2)

def load_data():
    # Load last 1 hour of data roughly (or more depending on analysis needs)
    # Using timestamp logic is better than fixed limit
    now = time.time()
    # Fetch enough data to cover the window
    data_map = {}
    for s in SYMBOLS:
        # Get data for the last N minutes to ensure safe resampling
        # 1 day = 86400s. Fetching last 1 hour for display speed
        df = store.get_data_since(s, now - 3600) 
        if not df.empty:
            resampled = resample_ohlcv(df, selected_tf)
            data_map[s] = resampled
    return data_map

# Main Loop Logic (simulation of auto-refresh using rerun)
if 'last_run' not in st.session_state:
    st.session_state.last_run = time.time()

# -----------------
# DATA PROCESSING
# -----------------
data_map = load_data()

if len(data_map) >= 2:
    s1, s2 = SYMBOLS[0], SYMBOLS[1]
    df1 = data_map.get(s1, pd.DataFrame())
    df2 = data_map.get(s2, pd.DataFrame())

    if not df1.empty and not df2.empty:
        # Align lengths roughly
        spread, zscore, beta = calculate_spread_and_zscore(df1, df2, window=window_size)
        corr = calculate_rolling_correlation(df1, df2, window=window_size)

        
        # -----------------
        # KPI DISPLAY
        # -----------------
        last_p1 = df1['close'].iloc[-1]
        last_p2 = df2['close'].iloc[-1]
        last_z = zscore.iloc[-1] if not zscore.empty else 0.0
        last_spread = spread.iloc[-1] if not spread.empty else 0.0
        
        with kpi_col1:
            st.metric(f"{s1} Price", f"{last_p1:.2f}")
        with kpi_col2:
            st.metric(f"{s2} Price", f"{last_p2:.2f}")
        with kpi_col3:
            st.metric("Hedge Ratio (Beta)", f"{beta:.4f}")
        with kpi_col4:
            delta_color = "normal"
            if abs(last_z) > z_threshold:
                delta_color = "inverse" # Highlight red if crossing threshold
            st.metric("Z-Score", f"{last_z:.2f}", delta_color=delta_color)

        # -----------------
        # ALERTS
        # -----------------
        if last_z > z_threshold:
            alert_placeholder.error(
                f"⚠️ **Action Required: SELL**\n\n"
                f"The price spread matches a statistical extreme (Z-Score: {last_z:.2f}). "
                f"This suggests {s1} is expensive relative to {s2}. \n"
                f"Consider selling the spread to capture mean reversion."
            )
        elif last_z < -z_threshold:
            alert_placeholder.success(
                f"✅ **Action Required: BUY**\n\n"
                f"The price spread matches a statistical extreme (Z-Score: {last_z:.2f}). "
                f"This suggests {s1} is cheap relative to {s2}. \n"
                f"Consider buying the spread to capture mean reversion."
            )
        else:
            alert_placeholder.info(
                f"ℹ️ **Market Neutral**\n\n"
                f"Z-Score ({last_z:.2f}) is within normal range (-{z_threshold} to {z_threshold}). "
                f"No immediate trading action required."
            )

        # -----------------
        # CHARTS
        # -----------------
        # Price Chart
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=df1.index, y=df1['close'], name=s1))
        # Plot s2 on secondary y since prices might differ vastly
        # fig_price.add_trace(go.Scatter(x=df2.index, y=df2['close'], name=s2, yaxis="y2"))
        # Actually simplest to normalize or just plot both if close
        fig_price.add_trace(go.Scatter(x=df2.index, y=df2['close'], name=s2))
        fig_price.update_layout(title="Price History", height=400, margin=dict(l=0,r=0,t=30,b=0))
        with chart_col1:
            st.plotly_chart(fig_price, use_container_width=True)
            
        # Correlation Chart
        fig_corr = px.line(x=corr.index, y=corr, title=f"Rolling Correlation ({window_size})")
        fig_corr.update_layout(height=400, margin=dict(l=0,r=0,t=30,b=0))
        with chart_col2:
            st.plotly_chart(fig_corr, use_container_width=True)

        # Spread Chart
        fig_spread = px.line(x=spread.index, y=spread, title="Spread")
        fig_spread.update_layout(height=350, margin=dict(l=0,r=0,t=30,b=0))
        with spread_col:
            st.plotly_chart(fig_spread, use_container_width=True)

        # Z-Score Chart
        fig_z = go.Figure()
        fig_z.add_trace(go.Scatter(x=zscore.index, y=zscore, name="Z-Score"))
        fig_z.add_hline(y=z_threshold, line_dash="dash", line_color="red")
        fig_z.add_hline(y=-z_threshold, line_dash="dash", line_color="green")
        fig_z.update_layout(title="Z-Score", height=350, margin=dict(l=0,r=0,t=30,b=0))
        with zscore_col:
            st.plotly_chart(fig_z, use_container_width=True)
            
        # -----------------
        # RAW DATA
        # -----------------
        with st.expander("Raw Data View"):
            st.dataframe(df1.tail(10))

else:
    st.info("Waiting for data... Ensure Ingestion is running.")

# Auto-Refresh
time.sleep(refresh_rate)
st.rerun()
