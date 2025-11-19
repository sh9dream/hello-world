# db_connection.py
from supabase import create_client, Client

import os

# Fetch variables
url: str = os.environ.get("https://dqxobamrnoeccpuxekyh.supabase.co")
key: str = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRxeG9iYW1ybm9lY2NwdXhla3loIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDQ3ODEyNSwiZXhwIjoyMDc2MDU0MTI1fQ.D9-_AbzNZJe_9X5mqGRPfmdChX961FHDxgE67IL84do")

# Connect to the database
supabase: Client = create_client(url, key)


