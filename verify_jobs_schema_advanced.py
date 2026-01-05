
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or SUPABASE_KEY

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("\n--- CHECKING 'user_jobs' SCHEMA ---")
    
    # Introspect via PostgREST RPC if possible, or just try to insert a dummy row to see errors,
    # OR better: use a specialized RPC if available.
    # Since we can't easily query information_schema via standard client without raw SQL access (which we might have via psql but here we are python),
    # We will try to SELECT specific columns one by one.
    
    required_columns = ["id", "job_title", "company_name", "status", "job_description", "job_intel", "salary_target"]
    
    for col in required_columns:
        try:
            # Try to select just this column
            supabase.table('user_jobs').select(col).limit(1).execute()
            print(f"[OK] Column '{col}' exists.")
        except Exception as e:
            print(f"[FAILED] Column '{col}' MISSING or Error: {e}")

except Exception as e:
    print(f"Init Error: {e}")
