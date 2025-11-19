# db_connection.py
from dotenv import load_dotenv
from supabase import create_client, Client

import os

# Load environment variables from .env
load_dotenv()
# Fetch variables
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Connect to the database
supabase: Client = create_client(url, key)
