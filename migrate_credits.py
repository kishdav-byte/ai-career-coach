
import os
import json
from supabase import create_client

# -- CONFIG --
SUPABASE_URL = "https://nvfjmqacxzlmfamiynuu.supabase.co"
# Using the Service Role Key found in previous view (assuming it works or I'll prompt)
# Since I can't see the full key in the logs always, I will try to read it from the environment or ask.
# Actually, I'll write it to take it from the environment.

def migrate():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Missing SUPABASE_URL or SUPABASE_KEY environment variables.")
        return

    supabase = create_client(url, key)
    
    print("--- 🚀 Starting Credit Consolidation Migration ---")
    
    # Fetch all users
    res = supabase.table('users').select('*').execute()
    users = res.data
    print(f"Found {len(users)} users.")

    for user in users:
        uid = user['id']
        email = user.get('email', 'Unknown')
        
        updates = {}
        
        # 1. Interviews
        old_int_1 = user.get('interview_credits', 0) or 0
        old_int_2 = user.get('credits_interview_sim', 0) or 0
        current_int = user.get('credits_interview', 0) or 0
        new_int = current_int + old_int_1 + old_int_2
        if old_int_1 != 0 or old_int_2 != 0:
            updates['credits_interview'] = new_int
            updates['interview_credits'] = 0
            updates['credits_interview_sim'] = 0

        # 2. Rewrite/Resume
        old_res_1 = user.get('rewrite_credits', 0) or 0
        old_res_2 = user.get('resume_credits', 0) or 0
        current_res = user.get('credits_resume', 0) or 0
        new_res = current_res + old_res_1 + old_res_2
        if old_res_1 != 0 or old_res_2 != 0:
            updates['credits_resume'] = new_res
            updates['rewrite_credits'] = 0
            updates['resume_credits'] = 0

        # 3. Cover Letter
        old_cov_1 = user.get('credits_cover_letter', 0) or 0
        old_cov_2 = user.get('strategy_cover_credits', 0) or 0
        old_cov_3 = user.get('credits_cover', 0) or 0 # Note: credits_cover is our target, but we check if it was used as legacy
        current_cov = user.get('credits_cover', 0) or 0
        # If we are migrating TO credits_cover, we sum the others into it.
        new_cov = current_cov + old_cov_1 + old_cov_2
        if old_cov_1 != 0 or old_cov_2 != 0:
            updates['credits_cover'] = new_cov
            updates['credits_cover_letter'] = 0
            updates['strategy_cover_credits'] = 0

        # 4. Follow-up
        old_fol_1 = user.get('strategy_followup_credits', 0) or 0
        current_fol = user.get('credits_followup', 0) or 0
        new_fol = current_fol + old_fol_1
        if old_fol_1 != 0:
            updates['credits_followup'] = new_fol
            updates['strategy_followup_credits'] = 0

        if updates:
            print(f"Migrating {email}: {updates}")
            try:
                supabase.table('users').update(updates).eq('id', uid).execute()
            except Exception as e:
                print(f"Failed to update {email}: {e}")

    print("--- ✅ Migration Complete ---")

if __name__ == "__main__":
    migrate()
