import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page config
st.set_page_config(
    page_title="ETF Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📊 AUS & USA ETF Portfolio Dashboard")
st.markdown("Real-time tracking with automatic updates")

# ============================================================================
# ETF Configuration - EDIT THIS SECTION WITH YOUR HOLDINGS
# ============================================================================

ETF_DATA = {
    'VAS': {
        'ticker': 'VAS.AX',
        'name': 'Vanguard Australian Shares',
        'region': '🇦🇺 AUS',
        'units': 50,
        'purchase_price': 110.00
    },
    'VGS': {
        'ticker': 'VGS.AX',
        'name': 'Vanguard Global Shares',
        'region': '🌍 Global',
        'units': 30,
        'purchase_price': 260.00
    },
    'SPY': {
        'ticker': 'SPY',
        'name': 'S&P 500',
        'region': '🇺🇸 USA',
        'units': 20,
        'purchase_price': 420.00
    },
    'QQQ': {
        'ticker': 'QQQ',
        'name': 'Nasdaq-100',
        'region': '🇺🇸 USA',
        'units': 15,
        'purchase_price': 380.00
    },
    'VTI': {
        'ticker': 'VTI',
        'name': 'Vanguard Total US Market',
        'region': '🇺🇸 USA',
        'units': 25,
        'purchase_price': 225.00
    }
}

# ============================================================================
# FETCH DATA FUNCTION
# ============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes, auto-refresh every 5 min
def fetch_etf_data():
    """Fetch current price and historical data from Yahoo Finance"""
    portfolio_data = []
    historical_data = {}
    
    for code, info in ETF_DATA.items():
        try:
            ticker = yf.Ticker(info['ticker'])
            
            # Current data
            history = ticker.history(period='1d')
            current_price = history['Close'].iloc[-1]
            
            # Historical data (1 year)
            hist_1y = ticker.history(period='1y')
            
            portfolio_data.append({
                'Code': code,
                'Ticker': info['ticker'],
                'Name': info['name'],
                'Region': info['region'],
                'Current Price': current_price,
                'Units': info['units'],
                'Purchase Price': info['purchase_price'],
                'Total Value': current_price * info['units'],
                'Cost Basis': info['purchase_price'] * info['units'],
                'Gain/Loss $': (current_price - info['purchase_price']) * info['units'],
                'Gain/Loss %': ((current_price - info['purchase_price']) / info['purchase_price'] * 100),
                '1M Return %': ((current_price / history['Close'].iloc[0] - 1) * 100) if len(history) > 0 else 0
            })
            
            historical_data[code] = hist_1y['Close']
            
        except Exception as e:
            st.warning(f"⚠️ Error fetching {code}: {e}")
    
    return pd.DataFrame(portfolio_data), historical_data

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def calculate_portfolio_metrics(df):
    """Calculate key portfolio metrics"""
    total_value = df['Total Value'].sum()
    total_cost = df['Cost Basis'].sum()
    total_gain_loss = df['Gain/Loss $'].sum()
    total_return_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
    
    return {
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain_loss': total_gain_loss,
        'total_return_pct': total_return_pct
    }

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

st.markdown("---")

# Fetch data with loading message
with st.spinner('📡 Fetching latest data from Yahoo Finance...'):
    df, hist_data = fetch_etf_data()

# Calculate metrics
metrics = calculate_portfolio_metrics(df)

# ============================================================================
# KEY METRICS (TOP ROW)
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💰 Total Portfolio Value",
        f"${metrics['total_value']:,.2f}",
        f"${metrics['total_gain_loss']:,.2f}",
        delta_color="normal"
    )

with col2:
    st.metric(
        "📈 Total Return",
        f"{metrics['total_return_pct']:.2f}%",
        f"${metrics['total_gain_loss']:,.2f}",
        delta_color="normal"
    )

with col3:
    st.metric(
        "💵 Cost Basis",
        f"${metrics['total_cost']:,.2f}"
    )

with col4:
    st.metric(
        "🕐 Last Updated",
        datetime.now().strftime("%H:%M:%S"),
        datetime.now().strftime("%Y-%m-%d")
    )

st.markdown("---")

# ============================================================================
# VISUALIZATIONS (2 COLUMNS)
# ============================================================================

col_chart1, col_chart2 = st.columns(2)

# Chart 1: Portfolio Allocation (Pie Chart)
with col_chart1:
    st.subheader("Portfolio Allocation by ETF")
    fig_allocation = px.pie(
        df,
        values='Total Value',
        names='Name',
        color='Region',
        hover_data=['Units', 'Current Price'],
        title="Distribution of Holdings"
    )
    fig_allocation.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_allocation, use_container_width=True)

# Chart 2: Regional Allocation
with col_chart2:
    st.subheader("Regional Allocation")
    region_df = df.groupby('Region')['Total Value'].sum().reset_index()
    fig_region = px.bar(
        region_df,
        x='Region',
        y='Total Value',
        color='Region',
        title="Value by Region",
        labels={'Total Value': 'Portfolio Value ($)'}
    )
    st.plotly_chart(fig_region, use_container_width=True)

st.markdown("---")

# ============================================================================
# PERFORMANCE TABLE
# ============================================================================

st.subheader("📊 Detailed Holdings")

# Format dataframe for display
display_df = df[[
    'Code', 'Name', 'Region', 'Current Price', 'Units',
    'Total Value', 'Gain/Loss $', 'Gain/Loss %'
]].copy()

display_df['Current Price'] = display_df['Current Price'].apply(lambda x: f"${x:.2f}")
display_df['Total Value'] = display_df['Total Value'].apply(lambda x: f"${x:,.2f}")
display_df['Gain/Loss $'] = display_df['Gain/Loss $'].apply(lambda x: f"${x:,.2f}")
display_df['Gain/Loss %'] = display_df['Gain/Loss %'].apply(lambda x: f"{x:.2f}%")

st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ============================================================================
# HISTORICAL PERFORMANCE CHART
# ============================================================================

st.subheader("📈 1-Year Performance Comparison")

# Create historical chart
if hist_data:
    fig_history = go.Figure()
    
    for code, series in hist_data.items():
        # Normalize to 100 for easy comparison
        normalized = (series / series.iloc[0]) * 100
        fig_history.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized.values,
            mode='lines',
            name=f"{code} ({ETF_DATA[code]['name']})",
            line=dict(width=2)
        ))
    
    fig_history.update_layout(
        title="Normalized Performance (Base = 100)",
        xaxis_title="Date",
        yaxis_title="Indexed Value",
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig_history, use_container_width=True)

st.markdown("---")

# ============================================================================
# SIDEBAR - CONTROLS & INFO
# ============================================================================

with st.sidebar:
    st.subheader("⚙️ Dashboard Settings")
    
    st.markdown("### 🔄 Auto-Refresh")
    st.info("""
    ✅ This dashboard **auto-updates every 5 minutes**
    
    Data is fetched from Yahoo Finance automatically.
    """)
    
    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📱 Portfolio Summary")
    st.metric("Total Holdings", len(df))
    st.metric("AUS Exposure", f"{(df[df['Region'].str.contains('AUS')]['Total Value'].sum() / metrics['total_value'] * 100):.1f}%")
    st.metric("USA Exposure", f"{(df[df['Region'].str.contains('USA')]['Total Value'].sum() / metrics['total_value'] * 100):.1f}%")
    st.metric("Global Exposure", f"{(df[df['Region'].str.contains('Global')]['Total Value'].sum() / metrics['total_value'] * 100):.1f}%")
    
    st.markdown("---")
    
    st.markdown("### ℹ️ About")
    st.info("""
    **ETF Portfolio Tracker**
    
    Real-time data from Yahoo Finance
    
    Updates every 5 minutes
    
    🔗 [Yahoo Finance](https://finance.yahoo.com)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    ⏱️ Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
    <br>
    📊 Real-time data from Yahoo Finance
</div>
""", unsafe_allow_html=True)
