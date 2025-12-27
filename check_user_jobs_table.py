import os
from supabase import create_client

# Initialize Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Missing Supabase credentials in environment variables")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("CHECKING USER_JOBS TABLE")
print("=" * 60)

try:
    # Try to query the user_jobs table
    result = supabase.table('user_jobs').select('*').limit(5).execute()
    
    print(f"\n✅ Table 'user_jobs' exists!")
    print(f"📊 Found {len(result.data)} jobs (showing max 5)")
    
    if result.data:
        print("\n📋 Sample Data:")
        for job in result.data:
            print(f"\n  - ID: {job.get('id')}")
            print(f"    Title: {job.get('job_title')}")
            print(f"    Company: {job.get('company_name')}")
            print(f"    Status: {job.get('status')}")
            print(f"    User ID: {job.get('user_id')}")
    else:
        print("\n⚠️  Table is empty - no jobs found")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\n💡 The 'user_jobs' table might not exist in Supabase.")
    print("   You need to run the schema creation SQL first.")

print("\n" + "=" * 60)
