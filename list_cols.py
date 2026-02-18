import os
import json
from supabase import create_client, Client

SUPABASE_URL = "https://nvfjmqacxzlmfamiynuu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52ZmptcWFjeHpsbWZhbWl5bnV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUxMzk3MzAsImV4cCI6MjA4MDcxNTczMH0.W3J-E2ldrc99btVeChF0SauTQxr_48uFwImVaoHfOXI"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = supabase.table('users').select('*').limit(1).execute()
    
    if response.data:
        print("COLUMNS_START")
        print(json.dumps(list(response.data[0].keys())))
        print("COLUMNS_END")
    else:
        print("Table empty or no access.")
except Exception as e:
    print(f"Error: {e}")
