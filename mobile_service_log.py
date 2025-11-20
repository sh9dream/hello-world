import streamlit as st
import uuid
from datetime import datetime, date
from db_connection import supabase

st.set_page_config(page_title="Mobile Service Log", layout="centered")

st.title("📱 New Service Log")
st.write("Simple mobile form – all entries go to admin for review.")

# ------------------------------------------
# MAIN MOBILE FORM (No validation)
# ------------------------------------------
with st.form("mobile_service_log_form", clear_on_submit=True):

    customer_name = st.text_input("Customer Name")
    contact_person = st.text_input("Contact Person")
    instrument_name = st.text_input("Instrument Name")

    warranty_status = st.selectbox(
        "Warranty Status",
        ["In Warranty", "AMC", "Out of Warranty/AMC"]
    )

    technician_name = st.text_input("Engineer's Name")
    date_visited = st.date_input("Date Visited", value=date.today())

    problem_description = st.text_area("Customer's Complaint:")
    call_type = st.selectbox(
        "Call Type",
        ["Installation", "Preventive Maintenance", "Breakdown", "Training", "Other"]
    )

    action_taken = st.text_area("Description of Work Done:")
    status = st.selectbox(
        "Status",
        ["Open", "On Hold", "Solved"]
    )
    remarks = st.text_area("Remarks")

    submitted = st.form_submit_button("📥 Submit Service Log")


# ------------------------------------------
# HANDLE SUBMISSION → Insert to pending table
# ------------------------------------------
if submitted:

    now = datetime.now().isoformat(timespec="seconds")
    call_id = str(uuid.uuid4())

    log_data = {
        "call_id": call_id,
        "date_logged": now,
        "last_updated": now,
        "customer_name": customer_name,
        "contact_person": contact_person,
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

    supabase.table("Service_Log_Pending").insert(log_data).execute()

    st.success("⏳ Submitted — waiting for admin approval.")
    st.balloons()

