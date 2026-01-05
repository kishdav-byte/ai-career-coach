
import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Missing Env Var")
    exit()

supabase = create_client(url, key)

try:
    # Try to insert a dummy row to check columns
    # We use a fake user_id (or a real one if we knew it, but auth might block if RLS is on)
    # Actually RLS might block this if we don't have a user token. 
    # But we have the service key usually in env? No, usually anon.
    # If using Service Role Key, we bypass RLS.
    # Let's hope the env has SERVICE_ROLE_KEY or we can sign in?
    # Retrying with just checking if we can select (even if empty) to see if it errors on column selection?
    # No, select * works. Select specific columns verifies existence.
    
    print("Testing Select...")
    # Try selecting specific potential columns
    res = supabase.table("job_tracker").select("role_title, job_description, notes, salary_target, status").limit(1).execute()
    print("Select Success:", res)
    
except Exception as e:
    print("Error:", e)
