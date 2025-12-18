
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
# Use Service key if available, else Anon
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY')

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("\n--- CHECKING 'user_jobs' TABLE ---")
    try:
        res = supabase.table('user_jobs').select('*').limit(1).execute()
        print("Success! user_jobs exists.")
        if res.data:
            print("Columns:", list(res.data[0].keys()))
        else:
            print("Table empty but accessible.")
    except Exception as e:
        print(f"FAILED to access 'user_jobs': {e}")

except Exception as e:
    print(f"Init Error: {e}")
