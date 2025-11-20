import streamlit as st
import uuid
import pandas as pd
from datetime import datetime, date
from db_connection import supabase

st.set_page_config(page_title="Mobile Service Log", layout="centered")

# -----------------------------------------------------------
# Load Paginated Data
# -----------------------------------------------------------
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

def get_technician_list():
    try:
        result = supabase.table("Technicians").select("technician_name").execute()
        return sorted([t.get("technician_name", "") for t in result.data if t.get("technician_name")])
    except Exception as e:
        st.error(f"Error loading technicians: {e}")
        return []

# -----------------------------------------------------------
# Load Required Tables
# -----------------------------------------------------------
with st.spinner("Loading service logs..."):
    df_logs = load_paginated_data("Service_Log")
    df_customers = load_paginated_data("Customers", "customer_name, contact_person, phone")
    df_instruments = load_paginated_data("Instruments", "instrument_name, customer_name, serial_number")
    technician_list = get_technician_list()

# -----------------------------------------------------------
# Lookup Dictionaries
# -----------------------------------------------------------
customer_contacts = {
    row.get('customer_name', ''): {
        'contact_person': row.get('contact_person', ''),
        'phone': row.get('phone', '')
    }
    for _, row in df_customers.fillna("").iterrows()
}

customer_list = sorted(df_customers['customer_name'].dropna().unique().tolist()) if not df_customers.empty else []
instrument_list = sorted(df_instruments['instrument_name'].dropna().unique().tolist()) if not df_instruments.empty else []

# -----------------------------------------------------------
# UI - New Service Log Form
# -----------------------------------------------------------
st.title("📱 New Service Log")
st.write("Simple mobile form – all entries go to admin for review.")

with st.form("mobile_service_log_form", clear_on_submit=True):

    customer_name = st.selectbox("Customer Name *", [""] + customer_list, key="new_customer")

    default_contact = customer_contacts.get(customer_name, {}).get("contact_person", "") if customer_name else ""
    default_phone = customer_contacts.get(customer_name, {}).get("phone", "") if customer_name else ""

    contact_person = st.text_input("Contact Person", value=default_contact, key="new_contact")
    

    phone = st.number_input("Contact Phone Number", value=default_phone)

    instrument_name = st.text_input("Instrument Name")

    warranty_status = st.selectbox(
        "Warranty Status",
        ["In Warranty", "AMC", "Out of Warranty/AMC"]
    )

    technician_name = st.text_input("Technician Name")
    date_visited = st.date_input("Date Visited", value=date.today())

    problem_description = st.text_area("Problem Description")

    call_type = st.selectbox(
        "Call Type",
        ["Installation", "Preventive Maintenance", "Breakdown", "Training", "Other"]
    )

    action_taken = st.text_area("Action Taken")
    status = st.selectbox("Status", ["Open", "On Hold", "Solved"])
    remarks = st.text_area("Remarks")

    submitted = st.form_submit_button("📥 Submit Service Log")


# -----------------------------------------------------------
# Handle Submission
# -----------------------------------------------------------
if submitted:

    if not customer_name:
        st.error("Customer name is required.")
        st.stop()

    now = datetime.now().isoformat(timespec="seconds")

    log_data = {
        "call_id": str(uuid.uuid4()),
        "date_logged": now,
        "last_updated": now,
        "customer_name": customer_name,
        "contact_person": contact_person,
        "phone": phone,
        "instrument_name": instrument_name,
        "warranty_status": warranty_status,
        "technician_name": technician_name,
        "date_visited": str(date_visited),
        "problem_description": problem_description,
        "call_type": call_type,
        "action_taken": action_taken,
        "status": status,
        "remarks": remarks,
        "approved": False,
        "submitted_at": now,
    }

    try:
        supabase.table("Service_Log_Pending").insert(log_data).execute()
        st.success("⏳ Submitted — waiting for admin approval.")
        st.balloons()
    except Exception as e:
        st.error(f"Error submitting service log: {e}")


