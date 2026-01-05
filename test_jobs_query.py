
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# Mock a user ID that we know exists (or use one from seed logic)
# I will use a dummy one or try to find one.
# For now, I'll bypass the 'get_user' check and just try to run the query part 
# using a Service Key client to simulate "authorized" access if I can't get a real token.
# BUT, the failure point is likely the "Client Handshake" or the Query itself.

print(f"URL: {SUPABASE_URL}")
print(f"KEY: {SUPABASE_KEY[:5]}..." if SUPABASE_KEY else "KEY: None")

try:
    print("1. Creating Client...")
    user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Mocking a token? 
    # If I don't have a valid user token, I can't test RLS auth fully.
    # However, I can test if `postgrest.auth()` crashes on random string.
    print("2. Auth handshake with dummy token...")
    user_client.postgrest.auth("dummy.token.part")
    print("   Handshake Success.")

    print("3. Executing Query (Expect 401/400 if token invalid, but NOT CRASH)...")
    # This might fail with 401, but we want to see if Python CRASHES (which causes 500).
    try:
        user_id = "test_user_id" 
        response = user_client.table('user_jobs').select(
            "id, job_title, company_name, status, job_description, job_intel, salary_target"
        ).eq('user_id', user_id).execute()
        print("   Query Executed (Response received).")
    except Exception as e:
        print(f"   Query Output Error: {e}")

except Exception as e:
    print(f"CRASHED: {e}")
