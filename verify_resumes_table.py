
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load env variables
load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_URL or Key not found in .env")
    exit(1)

try:
    print(f"Connecting to Supabase Admin: {SUPABASE_URL}")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Try to insert a dummy record (rollback or catch error)
    # OR better: Just try to select from the table to see columns if possible
    
    print("\n--- CHECKING 'resumes' TABLE SCHEMA ---")
    try:
        # Valid query to get one item
        res = supabase.table('resumes').select('*').limit(1).execute()
        if res.data:
            print("Columns found in data:", list(res.data[0].keys()))
        else:
            print("Table empty. Trying to insert a dummy to see if it fails on column names...")
            # If empty, we can't easily see columns via select * on client usually, 
            # unless we query information_schema or just try to insert.
            
            # Introspection Attempt
            # Does not work via Client usually.
            pass
            
    except Exception as e:
        print(f"Select Failed: {e}")

    # OPTIONAL: Test Insert
    # print("\n--- TESTING INSERT ---")
    # try:
    #     # We need a valid user_id to test insert if foreign key exists
    #     user_res = supabase.table('users').select('id').limit(1).execute()
    #     if user_res.data:
    #         uid = user_res.data[0]['id']
    #         test_data = {
    #             "user_id": uid,
    #             "overall_score": 99,
    #             "job_title": "TEST_DEBUGGER",
    #             "content": {"test": "true"}
    #         }
    #         print(f"Attempting to insert: {test_data}")
    #         # supabase.table('resumes').insert(test_data).execute()
    #         # print("Insert Successful!")
    #     else:
    #         print("No users found to test insert.")
    # except Exception as e:
    #     print(f"Insert Test Failed: {e}")

except Exception as e:
    print(f"Connection Failed: {e}")
