
import os
from supabase import create_client, Client

# CONFIGURATION
# You must export these in your terminal before running:
# export SUPABASE_URL="https://nvfjmqacxzlmfamiynuu.supabase.co"
# export SUPABASE_SERVICE_ROLE_KEY="<YOUR_SERVICE_ROLE_KEY>" 

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("❌ ERROR: Missing Environment Variables.")
    print("Please run:")
    print('export SUPABASE_URL="https://nvfjmqacxzlmfamiynuu.supabase.co"')
    print('export SUPABASE_SERVICE_ROLE_KEY="<YOUR_SECRET_KEY>"')
    exit(1)

print(f"Connecting to Supabase at {url}...")
try:
    supabase: Client = create_client(url, key)
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    exit(1)

# TARGET USER (From your logs/screenshot)
TARGET_USER_ID = "0510d2c8-53e2-4449-9f56-f8ebf7947031" # kishdav@gmail.com
CREDIT_TYPE = "interview_credits"

print(f"Attempting to update {CREDIT_TYPE} for User {TARGET_USER_ID}...")

try:
    # 1. READ CURRENT VALUE
    print("Step 1: Reading current balance...")
    res = supabase.table('users').select(CREDIT_TYPE).eq('id', TARGET_USER_ID).single().execute()
    
    if not res.data:
        print(f"❌ Error: User not found or Read Access Denied.")
        exit(1)
        
    current_credits = res.data.get(CREDIT_TYPE, 0)
    print(f"✅ Current {CREDIT_TYPE}: {current_credits}")

    # 2. WRITE UPDATE
    print(f"Step 2: Incrementing to {current_credits + 1}...")
    update_res = supabase.table('users').update({CREDIT_TYPE: current_credits + 1}).eq('id', TARGET_USER_ID).execute()
    
    if update_res.data:
        print(f"✅ SUCCESS! New {CREDIT_TYPE}: {update_res.data[0].get(CREDIT_TYPE)}")
        print("Note: Since this was a test, you may want to manually decrement it back if needed.")
    else:
        print("❌ Write Failed! (No data returned, possible RLS block)")

except Exception as e:
    print(f"❌ OPERATION FAILED: {e}")
    print("\nDIAGNOSIS:")
    print("1. If Authorization Error -> Your Service Role Key is invalid.")
    print("2. If RLS Error -> You need to run 'fix_rls_policies.sql'.")
