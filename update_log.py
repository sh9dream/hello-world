"""
SERVICE LOG MANAGER
--------------------
Allows user to:
✔ View all service logs
✔ Filter logs by technician/engineer
✔ Edit/update a selected log
✔ Sort logs by engineer or date

DEPENDENCIES:
    pip install supabase
    pip install pandas
    pip install python-dotenv
"""

import os
import pandas as pd
from datetime import datetime, date
from db_connection import supabase
# Load .env (SUPABASE_URL and SUPABASE_KEY)
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ===================== FETCH ALL SERVICE LOGS ======================
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

def get_all_logs():
    return load_paginated_data("Service_Log")

# ===================== FILTER BY TECHNICIAN ======================

def filter_by_engineer(engineer_name: str):
    response = supabase.table("Service_Log").select("*").eq("technician_name", engineer_name).execute()
    return pd.DataFrame(response.data)

# ===================== UPDATE A SERVICE LOG ENTRY ======================

def update_service_log(entry_id: int, updated_data: dict):
    try:
        response = supabase.table("Service_log").update(updated_data).eq("id", entry_id).execute()
        return response.data
    except Exception as e:
        return str(e)

# ===================== SORTING FACILITY ======================

def sort_logs(by_field: str = "technician_name"):
    if by_field not in ["technician_name", "date_logged", "customer_name", "instrument_name"]:
        raise ValueError("Unsupported sort field")

    logs = get_all_logs()
    return logs.sort_values(by=by_field)

# ===================== INTERACTIVE MENU (OPTIONAL) ======================

def interactive_menu():
    while True:
        print("\n====== SERVICE LOG MANAGER ======")
        print("1. View All Logs")
        print("2. Filter by Service Engineer")
        print("3. Sort Logs")
        print("4. Update a Log")
        print("5. Exit")

        choice = input("\nEnter option (1-5): ")

        if choice == "1":
            print("\n--- ALL SERVICE LOGS ---")
            print(get_all_logs())

        elif choice == "2":
            name = input("Enter Engineer Name: ")
            logs = filter_by_engineer(name)
            print(f"\n--- LOGS for Engineer: {name} ---")
            print(logs)

        elif choice == "3":
            print("Sort by: technician_name | date_logged | customer_name | instrument_name")
            field = input("Enter sort field: ")
            try:
                print(sort_logs(field))
            except ValueError as e:
                print(e)

        elif choice == "4":
            entry_id = input("Enter Service Log ID to Update: ")
            key = input("Enter field name to update (e.g., status, remarks, action_taken): ")
            value = input("Enter new value: ")

            update_result = update_service_log(int(entry_id), {key: value})
            print("Update Result:", update_result)

        elif choice == "5":
            print("Exiting Service Log Manager...")
            break

        else:
            print("Invalid Option!")

# ===================== RUN IF FILE EXECUTED DIRECTLY ======================
if __name__ == "__main__":
    interactive_menu()
