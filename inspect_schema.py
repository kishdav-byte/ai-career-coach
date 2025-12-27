
import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Missing Supabase credentials")
    exit(1)

supabase = create_client(url, key)

tables = ['users', 'user_jobs', 'interviews', 'error_logs', 'system_logs']

schema_info = {}

for table in tables:
    try:
        # Fetch one row to inspect keys
        res = supabase.table(table).select("*").limit(1).execute()
        if res.data:
            schema_info[table] = list(res.data[0].keys())
        else:
             # If empty, we can't easily get columns via API without metadata query usually
             # But let's try to infer or assume it exists
             schema_info[table] = "Empty Table (Columns unknown via simple select)"
    except Exception as e:
        schema_info[table] = f"Error: {str(e)}"

print(json.dumps(schema_info, indent=2))
