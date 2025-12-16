# pages/Mobile_Service_Log.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from db_connection import supabase

st.set_page_config(page_title="Mobile Service Log", layout="centered", page_icon="📱")

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
    .required-label {
        color: #d32f2f;
        font-size: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# Load Paginated Data
# -----------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def load_paginated_data(table_name, columns="*"):
    all_data = []
    page_size = 1000
    start = 0

    while True:
        try:
            response = supabase.table(table_name).select(columns).range(start, start + page_size - 1).execute()
        except Exception as e:
            st.error(f"Error loading {table_name}: {e}")
            break

        batch = response.data
        if not batch:
            break

        all_data.extend(batch)
        start += page_size

    return pd.DataFrame(all_data) if all_data else pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def get_technician_list():
    try:
        result = supabase.table("Technicians").select("technician_name").execute()
        return sorted([t.get("technician_name", "") for t in result.data if t.get("technician_name")])
    except Exception as e:
        return []

# -----------------------------------------------------------
# Load Required Tables
# -----------------------------------------------------------
with st.spinner("Loading data..."):
    df_customers = load_paginated_data("Customers", "customer_name, contact_person, phone")
    df_instruments = load_paginated_data("Instruments", "instrument_name, customer_name, serial_number")
    technician_list = get_technician_list()

# Create validation sets
existing_customers = set(df_customers['customer_name'].dropna().tolist()) if not df_customers.empty else set()
existing_instruments = set(df_instruments['instrument_name'].dropna().tolist()) if not df_instruments.empty else set()

# -----------------------------------------------------------
# Lookup Dictionaries
# -----------------------------------------------------------
customer_contacts = {}
if not df_customers.empty:
    for _, row in df_customers.fillna("").iterrows():
        customer_contacts[row.get('customer_name', '')] = {
            'contact_person': row.get('contact_person', ''),
            'phone': row.get('phone', '')
        }

customer_list = sorted(df_customers['customer_name'].dropna().unique().tolist()) if not df_customers.empty else []
instrument_list = sorted(df_instruments['instrument_name'].dropna().unique().tolist()) if not df_instruments.empty else []

# Get instruments by customer
def get_instruments_for_customer(customer_name):
    if df_instruments.empty or not customer_name:
        return []
    filtered = df_instruments[df_instruments['customer_name'] == customer_name]
    return sorted(filtered['instrument_name'].dropna().unique().tolist())

def get_serial_numbers(customer_name, instrument_name):
    if df_instruments.empty or not customer_name or not instrument_name:
        return []
    filtered = df_instruments[
        (df_instruments['customer_name'] == customer_name) & 
        (df_instruments['instrument_name'] == instrument_name)
    ]
    serials = filtered['serial_number'].dropna().unique().tolist()
    return sorted([s for s in serials if s])

# -----------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------
if "selected_customer" not in st.session_state:
    st.session_state.selected_customer = ""
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "serial_lookup_mode" not in st.session_state:
    st.session_state.serial_lookup_mode = False
if "looked_up_data" not in st.session_state:
    st.session_state.looked_up_data = None

# -----------------------------------------------------------
# UI - Header
# -----------------------------------------------------------
st.title("📱 Mobile Service Log")
st.caption("Quick entry form for field engineers")

# Show success message if just submitted
if st.session_state.form_submitted:
    st.markdown("""
        <div class="success-box">
            <h3>✅ Service Log Submitted!</h3>
            <p>Your log has been sent for admin approval.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ Add Another Log", type="primary"):
        st.session_state.form_submitted = False
        st.rerun()
    
    st.stop()

st.markdown("---")

# -----------------------------------------------------------
# Quick Serial Number Lookup
# -----------------------------------------------------------
st.markdown("### 🔍 Quick Serial Number Lookup")
st.caption("Know the serial number? Enter it below to auto-fill all details!")

col1, col2 = st.columns([3, 1])

with col1:
    serial_lookup = st.text_input(
        "Enter Serial Number",
        key="serial_lookup_input",
        placeholder="e.g., SN123456",
        help="Type serial number and click lookup to auto-fill customer and instrument details"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Spacing
    if st.button("🔎 Lookup", use_container_width=True, type="primary"):
        if serial_lookup and serial_lookup.strip():
            # Search for serial number in instruments
            matching = df_instruments[df_instruments['serial_number'].str.strip().str.lower() == serial_lookup.strip().lower()]
            
            if not matching.empty:
                # Found - use first match
                instrument_data = matching.iloc[0]
                st.session_state.looked_up_data = {
                    'customer_name': instrument_data['customer_name'],
                    'instrument_name': instrument_data['instrument_name'],
                    'serial_number': instrument_data['serial_number']
                }
                st.session_state.serial_lookup_mode = True
                st.success(f"✅ Found: {instrument_data['instrument_name']} for {instrument_data['customer_name']}")
                st.rerun()
            else:
                st.error(f"❌ Serial number '{serial_lookup}' not found in database")
                st.info("💡 You can still fill the form manually below")
        else:
            st.warning("Please enter a serial number")

# Display looked up data if available
if st.session_state.serial_lookup_mode and st.session_state.looked_up_data:
    st.markdown("---")
    st.success("✅ Serial Number Found - Details Auto-filled Below")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Customer:** {st.session_state.looked_up_data['customer_name']}")
    with col2:
        st.info(f"**Instrument:** {st.session_state.looked_up_data['instrument_name']}")
    with col3:
        st.info(f"**Serial:** {st.session_state.looked_up_data['serial_number']}")
    
    if st.button("🔄 Clear and Enter Manually"):
        st.session_state.serial_lookup_mode = False
        st.session_state.looked_up_data = None
        st.rerun()

st.markdown("---")

# -----------------------------------------------------------
# Customer Selection (Outside Form for Dynamic Updates)
# -----------------------------------------------------------
st.markdown("### Customer Details")
st.markdown('<span class="required-label">* Required fields</span>', unsafe_allow_html=True)

# Use looked up data if available, otherwise use dropdown
if st.session_state.serial_lookup_mode and st.session_state.looked_up_data:
    # Show as text (read-only) when using serial lookup
    customer_name = st.session_state.looked_up_data['customer_name']
    st.text_input("Customer Name *", value=customer_name, disabled=True, key="customer_readonly")
else:
    customer_name = st.selectbox(
        "Customer Name *", 
        ["Select Customer..."] + customer_list, 
        key="customer_select"
    )
    
    # Show validation warning if customer not in database
    if customer_name and customer_name != "Select Customer...":
        if customer_name not in existing_customers:
            st.warning(f"⚠️ '{customer_name}' is not in the customer database. Admin will need to add it before approval.", icon="⚠️")

# Auto-fill contact details when customer changes
if customer_name and customer_name != "Select Customer...":
    contact_info = customer_contacts.get(customer_name, {})
    default_contact = contact_info.get('contact_person', '')
    default_phone = contact_info.get('phone', '')
    
    # Get instruments for this customer
    customer_instruments = get_instruments_for_customer(customer_name)
else:
    default_contact = ""
    default_phone = ""
    customer_instruments = []

# -----------------------------------------------------------
# Main Form
# -----------------------------------------------------------
with st.form("mobile_service_log_form", clear_on_submit=False):
    
    # Contact Info
    col1, col2 = st.columns(2)
    with col1:
        contact_person = st.text_input("Contact Person", value=default_contact)
    with col2:
        phone = st.text_input("Phone", value=default_phone)
    
    st.markdown("---")
    st.markdown("### Instrument Details")
    
    # Use looked up data if available
    if st.session_state.serial_lookup_mode and st.session_state.looked_up_data:
        # Show as text (read-only) when using serial lookup
        instrument_name = st.session_state.looked_up_data['instrument_name']
        serial_number = st.session_state.looked_up_data['serial_number']
        
        st.text_input("Instrument Name *", value=instrument_name, disabled=True, key="instrument_readonly")
        st.text_input("Serial Number", value=serial_number, disabled=True, key="serial_readonly")
    else:
        # Normal instrument selection flow
        if customer_instruments:
            instrument_options = ["Select Instrument..."] + customer_instruments + ["Other (Enter manually)"]
            instrument_selection = st.selectbox("Instrument Name *", instrument_options)
            
            if instrument_selection == "Other (Enter manually)":
                instrument_name = st.text_input("Enter Instrument Name *")
                if instrument_name and instrument_name not in existing_instruments:
                    st.warning(f"⚠️ '{instrument_name}' is not in the instruments database. Admin will need to add it before approval.", icon="⚠️")
                serial_number = st.text_input("Serial Number")
            elif instrument_selection and instrument_selection != "Select Instrument...":
                instrument_name = instrument_selection
                # Get serial numbers for this instrument
                serial_options = get_serial_numbers(customer_name, instrument_name)
                if serial_options:
                    serial_number = st.selectbox("Serial Number", ["Select..."] + serial_options + ["Other"])
                    if serial_number == "Other":
                        serial_number = st.text_input("Enter Serial Number")
                else:
                    serial_number = st.text_input("Serial Number")
            else:
                instrument_name = ""
                serial_number = ""
        else:
            instrument_name = st.text_input("Instrument Name *")
            if instrument_name and instrument_name not in existing_instruments:
                st.warning(f"⚠️ '{instrument_name}' is not in the instruments database. Admin will need to add it before approval.", icon="⚠️")
            serial_number = st.text_input("Serial Number")
    
    warranty_status = st.selectbox(
        "Warranty Status *",
        ["In Warranty", "AMC", "Free Service", "Charged Service"]
    )
    
    st.markdown("---")
    st.markdown("### Service Details")
    
    # Technician - Dropdown with option for manual entry
    if technician_list:
        tech_options = ["Select Technician..."] + technician_list + ["Other (Enter manually)"]
        tech_selection = st.selectbox("Technician Name *", tech_options)
        
        if tech_selection == "Other (Enter manually)":
            technician_name = st.text_input("Enter Technician Name *")
        elif tech_selection and tech_selection != "Select Technician...":
            technician_name = tech_selection
        else:
            technician_name = ""
    else:
        technician_name = st.text_input("Technician Name *")
    
    date_visited = st.date_input("Date Visited *", value=date.today())
    
    call_type = st.selectbox(
        "Call Type *",
        ["Installation", "Preventive Maintenance", "Breakdown", "Application", "Training", "Other"]
    )
    
    problem_description = st.text_area("Customer Complaints *", height=100)
    action_taken = st.text_area("Description of the Work Done: ", height=100)
    
    # Spare Parts Field
    spare_parts = st.text_area(
        "Spare Parts Replaced",
        height=80,
        help="Separate multiple parts with semicolons. Example: Filter; Sensor; O-ring"
    )
    
    status = st.selectbox("Status *", ["Open", "On_Hold", "Waiting for Parts", "Solved"])
    remarks = st.text_area("Remarks/Notes", height=80)
    
    st.markdown("---")
    
    # Submit Button
    submitted = st.form_submit_button("📥 Submit Service Log", type="primary", use_container_width=True)

# -----------------------------------------------------------
# Handle Submission
# -----------------------------------------------------------
if submitted:
    # Validation
    errors = []
    
    if not customer_name or customer_name == "Select Customer...":
        errors.append("Customer Name is required")
    if not instrument_name or instrument_name == "Select Instrument...":
        errors.append("Instrument Name is required")
    if not technician_name or technician_name == "Select Technician...":
        errors.append("Technician Name is required")
    if not problem_description:
        errors.append("Problem Description is required")
    
    if errors:
        for error in errors:
            st.error(f"⚠️ {error}")
        st.stop()
    
    # Prepare data
    now = datetime.now().isoformat(timespec="seconds")
    
    log_data = {
        "date_logged": str(date.today()),
        "last_updated": now,
        "customer_name": customer_name,
        "contact_person": contact_person.strip() if contact_person else None,
        "instrument_name": instrument_name,
        "serial_number": serial_number if serial_number and serial_number != "Select..." else None,
        "warranty_status": warranty_status,
        "technician_name": technician_name,
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
    
    try:
        # Submit to pending table for approval
        supabase.table("Service_Log_Pending").insert(log_data).execute()
        
        # Reset serial lookup mode after successful submission
        st.session_state.serial_lookup_mode = False
        st.session_state.looked_up_data = None
        
        st.session_state.form_submitted = True
        st.balloons()
        st.rerun()
        
    except Exception as e:
        st.error(f"Error submitting service log: {str(e)}")
        st.info("Please try again or contact admin if the problem persists.")

# -----------------------------------------------------------
# Footer
# -----------------------------------------------------------
st.markdown("---")
st.caption("📱 Mobile Service Log v2.0")
st.caption("Submissions require admin approval before appearing in main system.")
