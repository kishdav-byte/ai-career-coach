import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from api.app import supabase_admin as supabase
from dotenv import load_dotenv

load_dotenv()

def check_columns():
    print("Checking 'users' table schema...")
    try:
        # Try to select the specific column. If it fails, it doesn't exist.
        # We limit to 1 row to be fast.
        res = supabase.table('users').select('star_drill_count').limit(1).execute()
        print("SUCCESS: Column 'star_drill_count' found.")
        print(f"Sample Data: {res.data}")
    except Exception as e:
        print("\nCRITICAL FAILURE: Could not select 'star_drill_count'.")
        print(f"Error Details: {e}")
        print("\nDIAGNOSIS: The SQL migration script was likely NOT run.")

if __name__ == "__main__":
    if not supabase:
        print("Error: Could not init Supabase client.")
    else:
        check_columns()
