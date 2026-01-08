import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing env vars")
    exit(1)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = supabase.table('users').select('*').limit(1).execute()
    
    if response.data:
        print("Columns found:")
        print(json.dumps(list(response.data[0].keys()), indent=2))
    else:
        print("Table empty or no access.")
except Exception as e:
    print(f"Error: {e}")
