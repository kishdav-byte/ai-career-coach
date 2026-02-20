import os
import json
from supabase import create_client, Client

SUPABASE_URL = 'https://nvfjmqacxzlmfamiynuu.supabase.co'
# Using service role key from env if available, else hardcoded (not ideal but I see it in files)
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52ZmptcWFjeHpsbWZhbWl5bnV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUxMzk3MzAsImV4cCI6MjA4MDcxNTczMH0.W3J-E2ldrc99btVeChF0SauTQxr_48uFwImVaoHfOXI'

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def toggle_feature(feature_key, enabled):
    key = 'feature_flags'
    
    # Try to get existing flags
    res = supabase.table('admin_settings').select('value').eq('key', key).execute()
    
    flags = {}
    if res.data:
        flags = res.data[0]['value']
    
    flags[feature_key] = enabled
    
    # Update or Insert
    res = supabase.table('admin_settings').upsert({
        'key': key,
        'value': flags
    }).execute()
    
    print(f"Feature '{feature_key}' set to {enabled}")
    print(f"Current Flags: {flags}")

if __name__ == "__main__":
    # Enable the guest resume scan hook
    toggle_feature('guest_resume_scan_enabled', True)
