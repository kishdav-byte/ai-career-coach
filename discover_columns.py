
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

candidates = ['id', 'email', 'name', 'full_name', 'credits', 'role', 'created_at', 'updated_at']
results = []
for c in candidates:
    try:
        supabase.table('users').select(c).limit(1).execute()
        results.append(c)
    except Exception:
        pass

print("Existing columns in 'users':", results)
