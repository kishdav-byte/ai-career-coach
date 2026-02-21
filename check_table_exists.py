import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Missing Supabase credentials in .env")
    exit(1)

supabase = create_client(url, key)

try:
    res = supabase.table('guest_scans').select('*', count='exact').execute()
    print(f"Table 'guest_scans' exists. Rows: {res.count}")
    if res.data:
        print("Latest guest scan data:")
        for row in res.data[:5]:
            print(row)
except Exception as e:
    print(f"Error: {e}")
