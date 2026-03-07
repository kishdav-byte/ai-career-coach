from supabase import create_client, Client
import os

url = 'https://nvfjmqacxzlmfamiynuu.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52ZmptcWFjeHpsbWZhbWl5bnV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUxMzk3MzAsImV4cCI6MjA4MDcxNTczMH0.W3J-E2ldrc99btVeChF0SauTQxr_48uFwImVaoHfOXI'
supabase: Client = create_client(url, key)

try:
    response = supabase.table('error_logs').select('*').order('created_at', desc=True).limit(5).execute()
    print("Recent Errors:")
    for err in response.data:
        print(f"[{err.get('created_at')}] {err.get('error_message')} - {err.get('error_context')}")
except Exception as e:
    print(f"Failed to query: {e}")
