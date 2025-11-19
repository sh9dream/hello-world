# db_connection.py
from supabase import create_client, Client

# Connect to the database
supabase: Client = create_client("https://dqxobamrnoeccpuxekyh.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRxeG9iYW1ybm9lY2NwdXhla3loIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDQ3ODEyNSwiZXhwIjoyMDc2MDU0MTI1fQ.D9-_AbzNZJe_9X5mqGRPfmdChX961FHDxgE67IL84do")




