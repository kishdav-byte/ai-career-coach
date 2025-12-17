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
    
    # Columns to check
    columns = [
        'credits_negotiation', 
        'credits_inquisitor', 
        'credits_followup', 
        'credits_30_60_90', 
        'credits_cover_letter', 
        'credits_interview_sim'
    ]
    
    print(f"Attempting to select strategy columns: {columns} from 'users' table...")
    
    # Construct select string
    select_str = ", ".join(columns)
    
    # We limit to 1 row just to check schema validity
    response = supabase.table('users').select(select_str).limit(1).execute()
    
    print("SUCCESS! All strategy columns found.")
    print(f"Data sample (one row): {response.data}")
    
except Exception as e:
    print("\nFAILED. One or more columns likely do not exist.")
    print(f"Error details: {e}")
