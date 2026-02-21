import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

def check_recent_signups():
    print("Checking for recent signups (last 48 hours)...")
    
    # Since we can't easily query auth.users, let's check the 'users' profiles table or 'resumes' table
    # Most apps have a 'users' or 'profiles' table that syncs with auth.users
    
    try:
        # Check resumes table for any entries from new user IDs
        res = supabase.table('resumes').select('user_id, created_at').order('created_at', desc=True).limit(20).execute()
        if res.data:
            print(f"\nRecent activity in 'resumes' table:")
            for r in res.data:
                print(f"User: {r['user_id']} | Created: {r['created_at']}")
        else:
            print("\nNo entries found in 'resumes' table.")

        # Check for any users in the public 'users' table
        res_users = supabase.table('users').select('id, email, created_at').order('created_at', desc=True).limit(10).execute()
        if res_users.data:
            print(f"\nRecent signups in 'users' table:")
            for u in res_users.data:
                print(f"ID: {u['id']} | Email: {u['email']} | Created: {u['created_at']}")
        else:
            print("\nNo users found in public 'users' table.")
            
    except Exception as e:
        print(f"Error checking database: {e}")

    # --- CHECK GUEST SCANS ---
    print("\nChecking for anonymous guest scans...")
    try:
        guests = supabase.table('guest_scans').select('*').order('created_at', desc=True).limit(10).execute()
        if guests.data:
            print(f"Found {len(guests.data)} recent guest scans:")
            for g in guests.data:
                print(f" - {g['created_at']} | Score: {g['overall_score']} | Referral: {g['referral']}")
        else:
            print("No guest scans found yet.")
    except Exception as e:
        print(f"Could not read guest_scans table (it may not be created yet): {e}")

if __name__ == "__main__":
    check_recent_signups()
