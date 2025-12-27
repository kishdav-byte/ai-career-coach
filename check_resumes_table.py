
from supabase import create_client, Client

url = 'https://nvfjmqacxzlmfamiynuu.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52ZmptcWFjeHpsbWZhbWl5bnV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUxMzk3MzAsImV4cCI6MjA4MDcxNTczMH0.W3J-E2ldrc99btVeChF0SauTQxr_48uFwImVaoHfOXI'

supabase: Client = create_client(url, key)

try:
    # Fetch one row to inspect keys
    response = supabase.table('resumes').select("*").limit(1).execute()
    if response.data:
        print("Columns found:", response.data[0].keys())
    else:
        print("Table 'resumes' exists but is empty. Cannot verify columns from data.")
        # Try to insert a dummy to see errors? No, safer to just list data.
        # If empty, I will assume user is correct about 'overall_score'
except Exception as e:
    print(f"Error accessing table: {e}")
