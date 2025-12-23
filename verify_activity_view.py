import os
import sys

# Ensure we can import from 'api' folder
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from api.app import supabase_admin
from dotenv import load_dotenv

load_dotenv()

# Use the admin client directly
supabase = supabase_admin

if not supabase:
    print("Error: supabase_admin could not be initialized from api.app (missing env vars?)")
    # Fallback to manual creation if app.py init failed but we have keys in env now
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    if url and key:
        print("Fallback: Creating manual client.")
        supabase = create_client(url, key)
    else:
        exit(1)

def run_test():
    print("--- 1. Creating Test View ---")
    # Read the SQL file
    with open('test_activity_view.sql', 'r') as f:
        sql_content = f.read()
    
    # Execute SQL (Raw RPC call usually required for DDL, or we use the dashboard. 
    # Since we can't run raw SQL easily via client-js methods without an RPC wrapper, 
    # checking if we can just simulate the query first.
    # Actually, we can't run CREATE VIEW via standard client unless we have a specific RPC.
    # PLAN B: We will SIMULATE the result by running the SELECT queries individually in Python
    # and printing the combined result to prove the logic works.
    pass

def simulate_view_logic(target_email):
    print(f"\n--- Simulating View Logic for {target_email} ---")
    
    # 1. Get User ID
    user_res = supabase.table('users').select('id').eq('email', target_email).execute()
    if not user_res.data:
        print("User not found")
        return
    user_id = user_res.data[0]['id']
    print(f"User ID: {user_id}")

    # 2. Resumes
    resumes = supabase.table('resumes').select('created_at, overall_score').eq('user_id', user_id).limit(2).execute()
    print(f"\n[Resumes Found]: {len(resumes.data)}")
    for r in resumes.data:
        print(f" - Resume: Score {r['overall_score']} at {r['created_at']}")

    # 3. Interviews
    interviews = supabase.table('interviews').select('created_at, overall_score').eq('user_id', user_id).limit(2).execute()
    print(f"\n[Interviews Found]: {len(interviews.data)}")
    for i in interviews.data:
        print(f" - Interview: Score {i['overall_score']} at {i['created_at']}")

    # 4. LinkedIn (The New Logic)
    logs = supabase.table('activity_logs').select('*').eq('user_email', target_email).eq('feature', 'linkedin_optimize').execute()
    print(f"\n[LinkedIn Logs Found]: {len(logs.data)}")
    for l in logs.data:
        status = l['metadata'].get('status', 'unknown') if l['metadata'] else 'unknown'
        print(f" - LinkedIn: Status '{status}' at {l['created_at']} (Would map to Project: 'LinkedIn Optimization')")

    if len(logs.data) > 0:
        print("\nSUCCESS: The data exists in activity_logs and CAN be unioned into the view.")
    else:
        print("\nWARNING: No LinkedIn logs found. Did you run the optimizer after the fix?")

if __name__ == "__main__":
    print("--- DEBUG: Fetching Last 10 Activity Logs ---")
    recent_logs = supabase.table('activity_logs').select('*').limit(10).order('created_at', desc=True).execute()
    
    if recent_logs.data:
        for log in recent_logs.data:
            print(f"[{log['created_at']}] Feature: {log['feature']} | Email: {log['user_email']} | Metadata: {log['metadata']}")
            
        # Check if we see our target
        found = [l for l in recent_logs.data if l['feature'] == 'linkedin_optimize']
        if found:
            print("\nSUCCESS: Found 'linkedin_optimize' log!")
            simulate_view_logic(found[0]['user_email'])
        else:
            print("\nFAIL: 'linkedin_optimize' NOT found in the last 10 logs.")
    else:
        print("No logs found at all in activity_logs table.")
