# pages/Mobile_Service_App.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from db_connection import supabase

st.set_page_config(page_title="Mobile Service App", layout="centered", page_icon="📱")

# Custom CSS for mobile-friendly styling
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 18px;
        margin-top: 10px;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .stSelectbox > div > div {
        font-size: 16px;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .call-info-box {
        background-color: #f8f9fa;
        border-left: 4px solid #2196F3;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .status-open {
        background-color: #ffebee;
        color: #c62828;
        padding: 5px 12px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 14px;
    }
    .status-on-hold {
        background-color: #fff3e0;
        color: #e65100;
        padding: 5px 12px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 14px;
    }
    .info-banner {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .nav-button {
        background-color: #2196F3;
        color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin: 5px 0;
        cursor: pointer;
        font-size: 16px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------
if "mobile_mode" not in st.session_state:
    st.session_state.mobile_mode = "home"  # home, new_log, update_log
if "mobile_version" not in st.session_state:
    st.session_state.mobile_version = 0
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "update_success" not in st.session_state:
    st.session_state.update_success = False
if "serial_lookup_mode" not in st.session_state:
    st.session_state.serial_lookup_mode = False
if "looked_up_data" not in st.session_state:
    st.session_state.looked_up_data = None
if "selected_call_for_update" not in st.session_state:
    st.session_state.selected_call_for_update = None
if "search_mode" not in st.session_state:
    st.session_state.search_mode = "customer"

# -----------------------------------------------------------
# OPTIMIZED Data Loading Functions
# -----------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def load_paginated_data(table_name, columns="*", version=0):
    """Optimized pagination loader with early break"""
    all_data = []
    page_size = 1000
    start = 0

    try:
        while True:
            response = supabase.table(table_name).select(columns).range(start, start + page_size - 1).execute()
            batch = response.data
            
            if not batch:
                break

            all_data.extend(batch)
            
            if len(batch) < page_size:
                break
            
            start += page_size
            
        return pd.DataFrame(all_data) if all_data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading {table_name}: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def get_technician_list(version=0):
    """Get technician list with error handling"""
    try:
        result = supabase.table("Technicians").select("technician_name").execute()
        if result.data:
            techs = [t.get("technician_name", "") for t in result.data if t.get("technician_name")]
            return sorted([t.strip() for t in techs if t.strip()])
        return []
    except Exception:
        return []

def parse_date_safely(date_value):
    """Safely parse a date from string or datetime object"""
    if pd.isna(date_value) or date_value == "" or date_value is None:
        return None
    
    try:
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, datetime):
            return date_value.date()
        if hasattr(date_value, 'date'):
            return date_value.date()
        date_str = str(date_value).strip()
        if date_str and date_str not in ['NaT', 'None', 'nan']:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        pass
    
    return None

def display_calls(calls_df):
    """Display call cards with update buttons"""
    st.success(f"Found {len(calls_df)} unsolved call(s)")
    
    for idx, row in calls_df.iterrows():
        status_class = "status-open" if row['status'] == 'Open' else "status-on-hold"
        
        st.markdown(f"""
        <div class="call-info-box">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{row['customer_name']} - {row['instrument_name']}</strong><br>
                    <small>Call ID: {row['call_id'][:16]}...</small><br>
                    <small>Logged: {row['date_logged'].strftime('%Y-%m-%d') if pd.notna(row['date_logged']) else 'N/A'} 
                    | Days: {row['days_open']}</small><br>
                    <small>Tech: {row['technician_name']}</small>
                </div>
                <div>
                    <span class="{status_class}">{row['status']}</span>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <small><strong>Problem:</strong> {str(row['problem_description'])[:80]}...</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"📝 Update", key=f"update_{row['call_id']}", use_container_width=True):
            st.session_state.selected_call_for_update = row['call_id']
            st.rerun()

# -----------------------------------------------------------
# Navigation Helper Functions
# -----------------------------------------------------------
def go_to_home():
    st.session_state.mobile_mode = "home"
    st.session_state.form_submitted = False
    st.session_state.update_success = False
    st.session_state.selected_call_for_update = None
    st.session_state.serial_lookup_mode = False
    st.session_state.looked_up_data = None

def go_to_new_log():
    st.session_state.mobile_mode = "new_log"
    st.session_state.form_submitted = False
    st.session_state.serial_lookup_mode = False
    st.session_state.looked_up_data = None

def go_to_update_log():
    st.session_state.mobile_mode = "update_log"
    st.session_state.update_success = False
    st.session_state.selected_call_for_update = None

# -----------------------------------------------------------
# HOME SCREEN
# -----------------------------------------------------------
if st.session_state.mobile_mode == "home":
    st.title("📱 Mobile Service App")
    st.caption("Complete service management on the go")
    
    st.markdown("---")
    st.markdown("### 🚀 What would you like to do?")
    
    # Large action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 New Service Log", use_container_width=True, type="primary", key="btn_new"):
            go_to_new_log()
            st.rerun()
        st.caption("Create a new service call entry")
    
    with col2:
        if st.button("🔄 Update Existing", use_container_width=True, type="primary", key="btn_update"):
            go_to_update_log()
            st.rerun()
        st.caption("Update unsolved service calls")
    
    st.markdown("---")
    
    # Quick stats
    with st.spinner("Loading statistics..."):
        df_logs = load_paginated_data("Service_Log", "status", st.session_state.mobile_version)
        
        if not df_logs.empty:
            st.markdown("### 📊 Quick Stats")
            
            total_calls = len(df_logs)
            unsolved = len(df_logs[df_logs['status'].isin(['Open', 'On_Hold', 'Waiting for Parts'])])
            solved = len(df_logs[df_logs['status'] == 'Solved'])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Calls", f"{total_calls:,}")
            
            with col2:
                st.metric("Unsolved", unsolved, delta=f"{unsolved/total_calls*100:.0f}%" if total_calls > 0 else "0%")
            
            with col3:
                st.metric("Solved", solved, delta=f"{solved/total_calls*100:.0f}%" if total_calls > 0 else "0%")
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.mobile_version += 1
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption("📱 Mobile Service App v3.0")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# -----------------------------------------------------------
# NEW SERVICE LOG SCREEN
# -----------------------------------------------------------
elif st.session_state.mobile_mode == "new_log":
    
    # Back button
    if st.button("⬅️ Back to Home", key="back_from_new"):
        go_to_home()
        st.rerun()
    
    st.title("📝 New Service Log")
    st.caption("Create a new service call entry")
    
    # Show success message if just submitted
    if st.session_state.form_submitted:
        st.markdown("""
            <div class="success-box">
                <h3>✅ Service Log Submitted!</h3>
                <p>Your log has been sent for admin approval.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add Another Log", type="primary", use_container_width=True):
                st.session_state.form_submitted = False
                st.session_state.serial_lookup_mode = False
                st.session_state.looked_up_data = None
                st.rerun()
        
        with col2:
            if st.button("🏠 Back to Home", use_container_width=True):
                go_to_home()
                st.rerun()
        
        st.stop()
    
    # Load data for new log
    with st.spinner("Loading data..."):
        df_customers = load_paginated_data("Customers", "customer_name, contact_person, phone", 
                                           st.session_state.mobile_version)
        df_instruments = load_paginated_data("Instruments", "instrument_name, customer_name, serial_number", 
                                             st.session_state.mobile_version)
        technician_list = get_technician_list(st.session_state.mobile_version)
    
    # Create validation sets
    existing_customers = set(df_customers['customer_name'].dropna().tolist()) if not df_customers.empty else set()
    existing_instruments = set(df_instruments['instrument_name'].dropna().tolist()) if not df_instruments.empty else set()
    
    # Lookup dictionaries
    customer_contacts = {}
    if not df_customers.empty:
        customer_contacts = {
            row['customer_name']: {
                'contact_person': str(row.get('contact_person', '')),
                'phone': str(row.get('phone', ''))
            }
            for _, row in df_customers.fillna("").iterrows()
            if row.get('customer_name')
        }
    
    customer_list = sorted(df_customers['customer_name'].dropna().unique().tolist()) if not df_customers.empty else []
    
    # Pre-build instruments by customer dict
    instruments_by_customer = {}
    if not df_instruments.empty:
        for customer in df_instruments['customer_name'].dropna().unique():
            instruments_by_customer[customer] = sorted(
                df_instruments[df_instruments['customer_name'] == customer]['instrument_name'].dropna().unique().tolist()
            )
    
    def get_instruments_for_customer(customer_name):
        if not customer_name or customer_name not in instruments_by_customer:
            return []
        return instruments_by_customer[customer_name]
    
    def get_serial_numbers(customer_name, instrument_name):
        if df_instruments.empty or not customer_name or not instrument_name:
            return []
        
        filtered = df_instruments[
            (df_instruments['customer_name'] == customer_name) & 
            (df_instruments['instrument_name'] == instrument_name)
        ]
        serials = filtered['serial_number'].dropna().unique().tolist()
        return sorted([str(s).strip() for s in serials if str(s).strip()])
    
    st.markdown("---")
    
    # Serial Number Lookup
    st.markdown("### 🔍 Quick Serial Number Lookup")
    st.caption("Know the serial number? Enter it to auto-fill!")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        serial_lookup = st.text_input(
            "Serial Number",
            key="serial_lookup_input",
            placeholder="e.g., SN123456"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔎", use_container_width=True, type="primary"):
            if serial_lookup and serial_lookup.strip():
                matching = df_instruments[
                    df_instruments['serial_number'].astype(str).str.strip().str.lower() == 
                    serial_lookup.strip().lower()
                ]
                
                if not matching.empty:
                    instrument_data = matching.iloc[0]
                    st.session_state.looked_up_data = {
                        'customer_name': str(instrument_data['customer_name']),
                        'instrument_name': str(instrument_data['instrument_name']),
                        'serial_number': str(instrument_data['serial_number'])
                    }
                    st.session_state.serial_lookup_mode = True
                    st.success(f"✅ Found: {instrument_data['instrument_name']}")
                    st.rerun()
                else:
                    st.error(f"❌ Not found")
    
    # Display looked up data
    if st.session_state.serial_lookup_mode and st.session_state.looked_up_data:
        st.success("✅ Serial Number Found - Details Auto-filled")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Customer:** {st.session_state.looked_up_data['customer_name']}")
        with col2:
            st.info(f"**Instrument:** {st.session_state.looked_up_data['instrument_name']}")
        with col3:
            st.info(f"**Serial:** {st.session_state.looked_up_data['serial_number']}")
        
        if st.button("🔄 Clear"):
            st.session_state.serial_lookup_mode = False
            st.session_state.looked_up_data = None
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 👤 Customer Details")
    
    # Customer selection
    if st.session_state.serial_lookup_mode and st.session_state.looked_up_data:
        customer_name = st.session_state.looked_up_data['customer_name']
        st.text_input("Customer Name *", value=customer_name, disabled=True, key="customer_readonly")
    else:
        customer_name = st.selectbox(
            "Customer Name *", 
            ["Select Customer..."] + customer_list, 
            key="customer_select"
        )
        
        if customer_name and customer_name != "Select Customer..." and customer_name not in existing_customers:
            st.markdown("""
                <div class="info-banner">
                    ⚠️ Not in database. Admin will add it.
                </div>
            """, unsafe_allow_html=True)
    
    # Auto-fill contact details
    if customer_name and customer_name != "Select Customer...":
        contact_info = customer_contacts.get(customer_name, {})
        default_contact = contact_info.get('contact_person', '')
        default_phone = contact_info.get('phone', '')
        customer_instruments = get_instruments_for_customer(customer_name)
    else:
        default_contact = ""
        default_phone = ""
        customer_instruments = []
    
    # Main form
    with st.form("mobile_service_log_form"):
        
        # Contact Info
        col1, col2 = st.columns(2)
        with col1:
            contact_person = st.text_input("Contact Person", value=default_contact)
        with col2:
            phone = st.text_input("Phone", value=default_phone)
        
        st.markdown("---")
        st.markdown("### 🧪 Instrument")
        
        # Instrument selection
        if st.session_state.serial_lookup_mode and st.session_state.looked_up_data:
            instrument_name = st.session_state.looked_up_data['instrument_name']
            serial_number = st.session_state.looked_up_data['serial_number']
            
            st.text_input("Instrument *", value=instrument_name, disabled=True, key="instrument_readonly")
            st.text_input("Serial Number", value=serial_number, disabled=True, key="serial_readonly")
        else:
            if customer_instruments:
                instrument_options = ["Select..."] + customer_instruments + ["Other"]
                instrument_selection = st.selectbox("Instrument *", instrument_options)
                
                if instrument_selection == "Other":
                    instrument_name = st.text_input("Enter Instrument *")
                    serial_number = st.text_input("Serial Number")
                elif instrument_selection != "Select...":
                    instrument_name = instrument_selection
                    serial_options = get_serial_numbers(customer_name, instrument_name)
                    if serial_options:
                        serial_selection = st.selectbox("Serial Number", ["Select..."] + serial_options + ["Other"])
                        serial_number = st.text_input("Enter Serial") if serial_selection == "Other" else (serial_selection if serial_selection != "Select..." else "")
                    else:
                        serial_number = st.text_input("Serial Number")
                else:
                    instrument_name = ""
                    serial_number = ""
            else:
                instrument_name = st.text_input("Instrument *")
                serial_number = st.text_input("Serial Number")
        
        warranty_status = st.selectbox("Warranty *", ["In Warranty", "AMC", "Free Service", "Charged Service"])
        
        st.markdown("---")
        st.markdown("### 🔧 Service")
        
        # Technician
        if technician_list:
            tech_options = ["Select..."] + technician_list + ["Other"]
            tech_selection = st.selectbox("Technician *", tech_options)
            technician_name = st.text_input("Enter Name *") if tech_selection == "Other" else (tech_selection if tech_selection != "Select..." else "")
        else:
            technician_name = st.text_input("Technician *")
        
        date_visited = st.date_input("Date Visited *", value=date.today())
        call_type = st.selectbox("Call Type *", ["Installation", "Preventive Maintenance", "Breakdown", "Application", "Training", "Other"])
        
        problem_description = st.text_area("Customer Complaints *", height=100, placeholder="Describe the issue...")
        action_taken = st.text_area("Work Done", height=100, placeholder="Describe work performed...")
        spare_parts = st.text_area("Spare Parts", height=80, placeholder="Filter; Sensor; O-ring")
        status = st.selectbox("Status *", ["Open", "On_Hold", "Waiting for Parts", "Solved"])
        remarks = st.text_area("Remarks", height=80)
        
        st.markdown("---")
        
        submitted = st.form_submit_button("📥 Submit", type="primary", use_container_width=True)
    
    # Handle submission
    if submitted:
        errors = []
        
        if not customer_name or customer_name == "Select Customer...":
            errors.append("Customer Name required")
        if not instrument_name or instrument_name == "Select...":
            errors.append("Instrument required")
        if not technician_name or technician_name == "Select...":
            errors.append("Technician required")
        if not problem_description or not problem_description.strip():
            errors.append("Problem Description required")
        
        if errors:
            for error in errors:
                st.error(f"⚠️ {error}")
        else:
            try:
                now = datetime.now().isoformat(timespec="seconds")
                
                log_data = {
                    "date_logged": str(date.today()),
                    "last_updated": now,
                    "customer_name": str(customer_name).strip(),
                    "contact_person": contact_person.strip() if contact_person else None,
                    "instrument_name": str(instrument_name).strip(),
                    "serial_number": serial_number.strip() if serial_number and serial_number != "Select..." else None,
                    "warranty_status": warranty_status,
                    "technician_name": str(technician_name).strip(),
                    "date_visited": str(date_visited),
                    "problem_description": problem_description.strip(),
                    "call_type": call_type,
                    "action_taken": action_taken.strip() if action_taken else None,
                    "spare_parts": spare_parts.strip() if spare_parts else None,
                    "status": status,
                    "remarks": remarks.strip() if remarks else None,
                    "submitted_via": "mobile",
                    "submitted_at": now,
                }
                
                supabase.table("Service_Log_Pending").insert(log_data).execute()
                
                st.session_state.serial_lookup_mode = False
                st.session_state.looked_up_data = None
                st.session_state.form_submitted = True
                st.balloons()
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# -----------------------------------------------------------
# UPDATE SERVICE LOG SCREEN
# -----------------------------------------------------------
elif st.session_state.mobile_mode == "update_log":
    
    # Back button
    if st.button("⬅️ Back to Home", key="back_from_update"):
        go_to_home()
        st.rerun()
    
    st.title("🔄 Update Service Log")
    st.caption("Update unsolved service calls")
    
    # Show success message
    if st.session_state.update_success:
        st.markdown("""
            <div class="success-box">
                <h3>✅ Service Log Updated!</h3>
                <p>Changes saved successfully.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Update Another", type="primary", use_container_width=True):
                st.session_state.update_success = False
                st.session_state.selected_call_for_update = None
                st.rerun()
        
        with col2:
            if st.button("🏠 Back to Home", use_container_width=True):
                go_to_home()
                st.rerun()
        
        st.stop()
    
    # Load service logs
    with st.spinner("Loading calls..."):
        df_logs = load_paginated_data("Service_Log", "*", st.session_state.mobile_version)
        technician_list = get_technician_list(st.session_state.mobile_version)
    
    # Filter unsolved
    if not df_logs.empty:
        df_logs['date_logged'] = pd.to_datetime(df_logs['date_logged'], errors='coerce')
        df_logs['date_visited'] = pd.to_datetime(df_logs['date_visited'], errors='coerce')
        
        today = pd.Timestamp(datetime.now().date())
        df_logs['days_open'] = (today - df_logs['date_logged']).dt.days.fillna(0).astype(int)
        
        unsolved_df = df_logs[df_logs['status'].isin(['Open', 'On_Hold', 'Waiting for Parts'])].copy()
        unsolved_df = unsolved_df.sort_values('date_logged', ascending=False)
    else:
        unsolved_df = pd.DataFrame()
    
    if st.session_state.selected_call_for_update:
        # SHOW UPDATE FORM
        st.markdown("---")
        
        selected_call = df_logs[df_logs['call_id'] == st.session_state.selected_call_for_update]
        
        if selected_call.empty:
            st.error("⚠️ Call not found")
            st.session_state.selected_call_for_update = None
            if st.button("⬅️ Back"):
                st.rerun()
            st.stop()
        
        call = selected_call.iloc[0]
        
        st.markdown(f"""
        <div class="call-info-box">
            <strong>{call['customer_name']} - {call['instrument_name']}</strong><br>
            <small>Call ID: {call['call_id'][:16]}...</small><br>
            <small>Days Open: {call['days_open']}</small><br>
            <small><strong>Problem:</strong> {call['problem_description'][:80]}...</small>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("update_call_form"):
            current_date_visited = parse_date_safely(call.get('date_visited'))
            if current_date_visited is None:
                current_date_visited = date.today()
            
            date_visited = st.date_input("Date Visited *", value=current_date_visited)
            
            if technician_list:
                current_tech = str(call.get('technician_name', ''))
                tech_options = technician_list if current_tech in technician_list else [current_tech] + technician_list
                tech_index = tech_options.index(current_tech) if current_tech in tech_options else 0
                technician_name = st.selectbox("Technician *", tech_options, index=tech_index)
            else:
                technician_name = st.text_input("Technician *", value=str(call.get('technician_name', '')))
            
            action_taken = st.text_area("Work Done *", value=str(call.get('action_taken', '')), height=120, 
                                       placeholder="Describe work performed...")
            
            spare_parts = st.text_area("Spare Parts", value=str(call.get('spare_parts', '')), height=80)
            
            current_status = call['status']
            status_options = ["Open", "On_Hold", "Waiting for Parts", "Solved"]
            status_index = status_options.index(current_status) if current_status in status_options else 0
            status = st.selectbox("Status *", status_options, index=status_index)
            
            remarks = st.text_area("Remarks", value=str(call.get('remarks', '')), height=80)
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit_update = st.form_submit_button("💾 Save", type="primary", use_container_width=True)
            
            with col2:
                cancel_update = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if submit_update:
                if not action_taken or not action_taken.strip():
                    st.error("⚠️ Work description required")
                else:
                    try:
                        update_data = {
                            "date_visited": str(date_visited),
                            "technician_name": str(technician_name).strip(),
                            "action_taken": action_taken.strip(),
                            "spare_parts": spare_parts.strip() if spare_parts else None,
                            "status": status,
                            "remarks": remarks.strip() if remarks else None,
                            "last_updated": datetime.now().isoformat(timespec="seconds"),
                        }
                        
                        supabase.table("Service_Log").update(update_data).eq(
                            "call_id", st.session_state.selected_call_for_update
                        ).execute()
                        
                        st.session_state.update_success = True
                        st.session_state.selected_call_for_update = None
                        st.session_state.mobile_version += 1
                        st.cache_data.clear()
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            if cancel_update:
                st.session_state.selected_call_for_update = None
                st.rerun()
    
    else:
        # SHOW SEARCH OPTIONS
        st.markdown("---")
        st.markdown("### 🔍 Find Call to Update")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏢 Customer", use_container_width=True, 
                        type="primary" if st.session_state.search_mode == "customer" else "secondary"):
                st.session_state.search_mode = "customer"
                st.rerun()
        
        with col2:
            if st.button("🆔 Call ID", use_container_width=True,
                        type="primary" if st.session_state.search_mode == "call_id" else "secondary"):
                st.session_state.search_mode = "call_id"
                st.rerun()
        
        with col3:
            if st.button("👨‍🔧 Technician", use_container_width=True,
                        type="primary" if st.session_state.search_mode == "technician" else "secondary"):
                st.session_state.search_mode = "technician"
                st.rerun()
        
        st.markdown("---")
        
        if unsolved_df.empty:
            st.info("🎉 No unsolved calls!")
            st.stop()
        
        # Search by selected mode
        if st.session_state.search_mode == "customer":
            unique_customers = sorted(unsolved_df['customer_name'].dropna().unique().tolist())
            selected_customer = st.selectbox("Select Customer", ["Select..."] + unique_customers)
            
            if selected_customer and selected_customer != "Select...":
                customer_calls = unsolved_df[unsolved_df['customer_name'] == selected_customer]
                display_calls(customer_calls)
        
        elif st.session_state.search_mode == "call_id":
            call_id_search = st.text_input("Enter Call ID", placeholder="First 8-16 characters")
            
            if call_id_search:
                matching_calls = unsolved_df[unsolved_df['call_id'].str.contains(call_id_search, case=False, na=False)]
                if not matching_calls.empty:
                    display_calls(matching_calls)
                else:
                    st.warning(f"No calls found matching '{call_id_search}'")
        
        elif st.session_state.search_mode == "technician":
            unique_technicians = sorted(unsolved_df['technician_name'].dropna().unique().tolist())
            selected_technician = st.selectbox("Select Technician", ["Select..."] + unique_technicians)
            
            if selected_technician and selected_technician != "Select...":
                tech_calls = unsolved_df[unsolved_df['technician_name'] == selected_technician]
                display_calls(tech_calls)

# Helper function to display calls
def display_calls(calls_df):
    """Display call cards with update buttons"""
    st.success(f"Found {len(calls_df)} unsolved call(s)")
    
    for idx, row in calls_df.iterrows():
        status_class = "status-open" if row['status'] == 'Open' else "status-on-hold"
        
        st.markdown(f"""
        <div class="call-info-box">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{row['customer_name']} - {row['instrument_name']}</strong><br>
                    <small>Call ID: {row['call_id'][:16]}...</small><br>
                    <small>Logged: {row['date_logged'].strftime('%Y-%m-%d') if pd.notna(row['date_logged']) else 'N/A'} 
                    | Days: {row['days_open']}</small><br>
                    <small>Tech: {row['technician_name']}</small>
                </div>
                <div>
                    <span class="{status_class}">{row['status']}</span>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <small><strong>Problem:</strong> {str(row['problem_description'])[:80]}...</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"📝 Update", key=f"update_{row['call_id']}", use_container_width=True):
            st.session_state.selected_call_for_update = row['call_id']
            st.rerun()

# Call display function at the end if needed
if st.session_state.mobile_mode == "update_log" and not st.session_state.selected_call_for_update:
    if st.session_state.search_mode in ["customer", "call_id", "technician"]:
        # The display logic is already handled above
        pass

# -----------------------------------------------------------
# Footer (shown on all screens except home)
# -----------------------------------------------------------
if st.session_state.mobile_mode != "home":
    st.markdown("---")
    st.caption(f"📱 Mobile Service App v3.0 | {len(unsolved_df) if st.session_state.mobile_mode == 'update_log' and not unsolved_df.empty else ''}")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    if st.button("Open Dashboard"):
        st.markdown(
            '<meta http-equiv="refresh" content="0; url=https://hello-world-dashboard9841470867.streamlit.app/">',
            unsafe_allow_html=True
        )


