import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load env variables
load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

try:
    print(f"Connecting to Supabase: {SUPABASE_URL}")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Try to select the new columns from one user
    print("Attempting to select 'analysis_count' and 'last_analysis_date' from 'users' table...")
    
    # We limit to 1 row just to check schema validity
    response = supabase.table('users').select('analysis_count, last_analysis_date').limit(1).execute()
    
    print("SUCCESS! Columns found.")
    print(f"Data sample (one row): {response.data}")
    
except Exception as e:
    print("\nFAILED. The columns likely do not exist or there is a permission issue.")
    print(f"Error details: {e}")
