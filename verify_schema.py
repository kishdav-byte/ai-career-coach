import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY')

if not url or not key:
    print("Cannot run verification: No Supabase Credentials in .env")
    exit(1)

print(f"Connecting to {url}...")
try:
    client = create_client(url, key)
    print("Client created.")
    
    print("Attempting to select new columns from user_jobs...")
    # Try selecting the specific columns
    try:
        res = client.table('user_jobs').select('job_description,notes,salary_target').limit(1).execute()
        print("SUCCESS: Columns job_description, notes, salary_target EXIST.")
    except Exception as e:
        print(f"FAILURE: Could not select columns. Error: {e}")
        
except Exception as e:
    print(f"Connection Error: {e}")
