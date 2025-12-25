# pages/1_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from db_connection import supabase

st.set_page_config(page_title="Service Dashboard", page_icon="📊", layout="wide")

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .urgent-card {
        background-color: #ffebee;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #f44336;
        margin-bottom: 10px;
    }
    .warning-card {
        background-color: #ffe0b2;
        color: #e65100;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ff9800;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Service Management Dashboard")
st.markdown("---")

# ====================================
# --- OPTIMIZED DATA LOADING ---
# ====================================
@st.cache_data(ttl=300, show_spinner=False)
def load_all_service_logs(version=0):
    """Load all service logs with pagination - optimized with version param"""
    all_data = []
    page_size = 1000
    start = 0
    
    try:
        while True:
            end = start + page_size - 1
            response = supabase.table("Service_Log").select("*").range(start, end).execute()
            batch = response.data
            
            if not batch:
                break
                
            all_data.extend(batch)
            
            # Break if we got less than page_size (last page)
            if len(batch) < page_size:
                break
                
            start += page_size
            
        return pd.DataFrame(all_data) if all_data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading service logs: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def load_all_instruments(version=0):
    """Load all instruments with pagination - optimized with version param"""
    all_data = []
    page_size = 1000
    start = 0
    
    try:
        while True:
            end = start + page_size - 1
            response = supabase.table("Instruments").select("*").range(start, end).execute()
            batch = response.data
            
            if not batch:
                break
                
            all_data.extend(batch)
            
            if len(batch) < page_size:
                break
                
            start += page_size
            
        return pd.DataFrame(all_data) if all_data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading instruments: {str(e)}")
        return pd.DataFrame()

# ====================================
# --- SESSION STATE FOR VERSIONING ---
# ====================================
if "dashboard_version" not in st.session_state:
    st.session_state.dashboard_version = 0

# Add refresh button in top right
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("🔄 Refresh", type="primary"):
        st.session_state.dashboard_version += 1
        st.cache_data.clear()
        st.rerun()

# Load data with version control
with st.spinner("Loading dashboard data..."):
    df_logs = load_all_service_logs(st.session_state.dashboard_version)
    df_instruments = load_all_instruments(st.session_state.dashboard_version)

if df_logs.empty:
    st.warning("⚠️ No service log data available. Please add some service logs first.")
    st.stop()

# ====================================
# --- OPTIMIZED DATA PREPROCESSING ---
# ====================================
# Convert dates once, handle errors gracefully
df_logs['date_logged'] = pd.to_datetime(df_logs['date_logged'], errors='coerce')
df_logs['date_visited'] = pd.to_datetime(df_logs['date_visited'], errors='coerce')
df_logs['last_updated'] = pd.to_datetime(df_logs['last_updated'], errors='coerce')

# Calculate days open for each call
today = pd.Timestamp(datetime.now().date())
df_logs['days_open'] = (today - df_logs['date_logged']).dt.days.fillna(0).astype(int)

# ====================================
# --- KPI METRICS SECTION ---
# ====================================
st.subheader("📈 Key Performance Indicators")

# Calculate metrics efficiently
total_calls = len(df_logs)
status_counts = df_logs['status'].value_counts()
open_calls = status_counts.get('Open', 0)
on_hold_calls = status_counts.get('On_Hold', 0)
solved_calls = status_counts.get('Solved', 0)

# Calculate trends (compare to last 30 days)
last_30_days = today - timedelta(days=30)
prev_30_days = today - timedelta(days=60)

recent_calls = len(df_logs[df_logs['date_logged'] >= last_30_days])
previous_calls = len(df_logs[(df_logs['date_logged'] >= prev_30_days) & 
                             (df_logs['date_logged'] < last_30_days)])
trend = recent_calls - previous_calls

# Average resolution time (for solved calls only)
solved_df = df_logs[df_logs['status'] == 'Solved'].copy()
if not solved_df.empty:
    solved_df['resolution_days'] = (solved_df['last_updated'] - solved_df['date_logged']).dt.days
    # Remove negative values and outliers (> 365 days)
    solved_df = solved_df[(solved_df['resolution_days'] >= 0) & (solved_df['resolution_days'] <= 365)]
    avg_resolution = solved_df['resolution_days'].mean() if not solved_df.empty else 0
else:
    avg_resolution = 0

# Display metrics in columns
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="📞 Total Calls",
        value=f"{total_calls:,}",
        delta=f"{trend:+d} this month" if trend != 0 else "No change"
    )

with col2:
    st.metric(
        label="🔴 Open Calls",
        value=open_calls,
        delta=f"{(open_calls/total_calls*100):.1f}%" if total_calls > 0 else "0%"
    )

with col3:
    st.metric(
        label="⏸️ On Hold",
        value=on_hold_calls,
        delta=f"{(on_hold_calls/total_calls*100):.1f}%" if total_calls > 0 else "0%"
    )

with col4:
    st.metric(
        label="✅ Solved",
        value=solved_calls,
        delta=f"{(solved_calls/total_calls*100):.1f}%" if total_calls > 0 else "0%"
    )

with col5:
    st.metric(
        label="⏱️ Avg Resolution",
        value=f"{avg_resolution:.1f} days",
        delta="Target: <5 days" if avg_resolution <= 5 else "Above target",
        delta_color="normal" if avg_resolution <= 5 else "inverse"
    )

st.markdown("---")

# ====================================
# --- URGENT ATTENTION SECTION ---
# ====================================
st.subheader("🚨 Requires Immediate Attention")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🔴 Overdue Calls (Open >7 days)")
    overdue_calls = df_logs[(df_logs['status'] == 'Open') & 
                            (df_logs['days_open'] > 7)].sort_values('days_open', ascending=False)
    
    if not overdue_calls.empty:
        for idx, row in overdue_calls.head(5).iterrows():
            tech_name = row.get('technician_name', 'Unassigned')
            problem_preview = str(row.get('problem_description', ''))[:60]
            st.markdown(f"""
                <div class="urgent-card">
                    <strong>{row['customer_name']}</strong> - {row['instrument_name']}<br>
                    <small>Open for {row['days_open']} days | Technician: {tech_name}</small><br>
                    <small>Problem: {problem_preview}...</small>
                </div>
            """, unsafe_allow_html=True)
        if len(overdue_calls) > 5:
            st.info(f"➕ {len(overdue_calls) - 5} more overdue calls")
    else:
        st.success("✅ No overdue calls!")

with col2:
    st.markdown("#### ⏸️ On Hold - Follow Up Required")
    on_hold_df = df_logs[df_logs['status'] == 'On_Hold'].sort_values('last_updated')
    
    if not on_hold_df.empty:
        for idx, row in on_hold_df.head(5).iterrows():
            days_on_hold = (today - row['last_updated']).days
            tech_name = row.get('technician_name', 'Unassigned')
            remarks_preview = str(row.get('remarks', 'No remarks'))[:60]
            st.markdown(f"""
                <div class="warning-card">
                    <strong>{row['customer_name']}</strong> - {row['instrument_name']}<br>
                    <small>On hold for {days_on_hold} days | Technician: {tech_name}</small><br>
                    <small>Remarks: {remarks_preview}...</small>
                </div>
            """, unsafe_allow_html=True)
        if len(on_hold_df) > 5:
            st.info(f"➕ {len(on_hold_df) - 5} more on-hold calls")
    else:
        st.success("✅ No calls on hold!")

st.markdown("---")

# ====================================
# --- CHARTS & VISUALIZATIONS ---
# ====================================
st.subheader("📊 Analytics & Trends")

# Create tabs for different charts
tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🎯 Distribution", "👨‍🔧 Technicians", "🏢 Customers"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Calls over time (last 60 days)
        st.markdown("#### Service Calls Trend (Last 60 Days)")
        last_60_days = today - timedelta(days=60)
        last_60 = df_logs[df_logs['date_logged'] >= last_60_days].copy()
        
        if not last_60.empty:
            daily_calls = last_60.groupby(last_60['date_logged'].dt.date).size().reset_index()
            daily_calls.columns = ['Date', 'Count']
            
            fig = px.line(daily_calls, x='Date', y='Count', 
                         title='Daily Service Calls',
                         markers=True)
            fig.update_traces(line_color='#1f77b4', line_width=3)
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for the last 60 days")
    
    with col2:
        # Call status over time
        st.markdown("#### Call Status Over Time")
        if not last_60.empty:
            status_by_week = last_60.groupby([pd.Grouper(key='date_logged', freq='W'), 
                                              'status']).size().reset_index()
            status_by_week.columns = ['Week', 'Status', 'Count']
            
            fig = px.bar(status_by_week, x='Week', y='Count', color='Status',
                        title='Weekly Calls by Status',
                        color_discrete_map={'Open': '#f44336', 'On_Hold': '#ff9800', 'Solved': '#4caf50'})
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for the last 60 days")

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        # Call type distribution
        st.markdown("#### Calls by Type")
        call_type_dist = df_logs['call_type'].value_counts().reset_index()
        call_type_dist.columns = ['Call Type', 'Count']
        
        fig = px.pie(call_type_dist, values='Count', names='Call Type',
                    title='Call Type Distribution',
                    color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Warranty status
        st.markdown("#### Warranty Status")
        warranty_dist = df_logs['warranty_status'].value_counts().reset_index()
        warranty_dist.columns = ['Warranty Status', 'Count']
        
        fig = px.pie(warranty_dist, values='Count', names='Warranty Status',
                    title='Warranty Status Distribution',
                    color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    # Technician performance
    st.markdown("#### Technician Performance")
    
    tech_stats = df_logs.groupby('technician_name', dropna=False).agg({
        'call_id': 'count',
        'status': lambda x: (x == 'Solved').sum(),
        'days_open': 'mean'
    }).reset_index()
    tech_stats.columns = ['Technician', 'Total Calls', 'Solved Calls', 'Avg Days']
    tech_stats = tech_stats.sort_values('Total Calls', ascending=False).head(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(tech_stats, x='Technician', y='Total Calls',
                    title='Total Calls by Technician (Top 10)',
                    color='Total Calls',
                    color_continuous_scale='Blues')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(tech_stats, x='Technician', y='Solved Calls',
                    title='Solved Calls by Technician (Top 10)',
                    color='Solved Calls',
                    color_continuous_scale='Greens')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Display table
    st.dataframe(tech_stats.style.format({'Avg Days': '{:.1f}'}), 
                use_container_width=True, hide_index=True)

with tab4:
    # Customer analysis
    st.markdown("#### Top Customers by Service Calls")
    
    customer_stats = df_logs.groupby('customer_name', dropna=False).agg({
        'call_id': 'count',
        'status': lambda x: (x == 'Solved').sum()
    }).reset_index()
    customer_stats.columns = ['Customer', 'Total Calls', 'Solved']
    customer_stats['Pending'] = customer_stats['Total Calls'] - customer_stats['Solved']
    customer_stats = customer_stats.sort_values('Total Calls', ascending=False).head(10)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Solved', x=customer_stats['Customer'], y=customer_stats['Solved'],
                        marker_color='lightgreen'))
    fig.add_trace(go.Bar(name='Pending', x=customer_stats['Customer'], y=customer_stats['Pending'],
                        marker_color='lightcoral'))
    
    fig.update_layout(
        title='Top 10 Customers by Service Calls',
        barmode='stack',
        height=400,
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Display table
    st.dataframe(customer_stats, use_container_width=True, hide_index=True)

st.markdown("---")

# ====================================
# --- RECENT ACTIVITY ---
# ====================================
st.subheader("🕒 Recent Activity")

recent_logs = df_logs.sort_values('last_updated', ascending=False).head(10)
display_cols = ['date_logged', 'customer_name', 'instrument_name', 'technician_name', 
                'status', 'call_type', 'days_open']

if not recent_logs.empty and all(col in recent_logs.columns for col in display_cols):
    recent_display = recent_logs[display_cols].copy()
    recent_display['date_logged'] = recent_display['date_logged'].dt.strftime('%Y-%m-%d')
    recent_display.columns = ['Date', 'Customer', 'Instrument', 'Technician', 
                              'Status', 'Type', 'Days Open']
    
    # Color code status
    def highlight_status(row):
        if row['Status'] == 'Open' and row['Days Open'] > 7:
            return ['background-color: #ffcdd2; color: #b71c1c'] * len(row)
        elif row['Status'] == 'On_Hold':
            return ['background-color: #ffe0b2; color: #e65100'] * len(row)
        elif row['Status'] == 'Solved':
            return ['background-color: #c8e6c9; color: #1b5e20'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        recent_display.style.apply(highlight_status, axis=1),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No recent activity")

# ====================================
# --- INSTRUMENT INSIGHTS ---
# ====================================
if not df_instruments.empty:
    st.markdown("---")
    st.subheader("🧪 Instrument Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Instruments", len(df_instruments))
    
    with col2:
        # Instruments with expiring warranty (next 30 days)
        df_instruments['warranty_expiry'] = pd.to_datetime(df_instruments['warranty_expiry'], 
                                                           errors='coerce')
        expiring_soon = df_instruments[
            (df_instruments['warranty_expiry'] >= today) & 
            (df_instruments['warranty_expiry'] <= today + timedelta(days=30))
        ]
        st.metric("Warranty Expiring Soon", len(expiring_soon))
    
    with col3:
        # Most serviced instruments
        if 'instrument_name' in df_logs.columns:
            instrument_calls = df_logs['instrument_name'].value_counts()
            if not instrument_calls.empty:
                st.metric("Most Serviced", instrument_calls.index[0], 
                         delta=f"{instrument_calls.iloc[0]} calls")
            else:
                st.metric("Most Serviced", "N/A")
        else:
            st.metric("Most Serviced", "N/A")

st.markdown("---")
st.caption("Dashboard auto-refreshes every 5 minutes. Click 🔄 Refresh to update manually.")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
