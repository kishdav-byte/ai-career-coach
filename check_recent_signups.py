from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") # We need this to list users

if not url or not key:
    print("Error: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(url, key)

try:
    # Check the auth.users count (via public.users table)
    response = supabase.table('users').select("id, email, created_at").order('created_at', desc=True).limit(5).execute()
    users = response.data
    print(f"\n--- RECENT SIGNUPS (Last 5) ---")
    if not users:
        print("No users found in public.users table.")
    for u in users:
        print(f"ID: {u['id']} | Email: {u['email']} | Created: {u['created_at']}")
    
except Exception as e:
    print(f"Error checking users: {e}")
