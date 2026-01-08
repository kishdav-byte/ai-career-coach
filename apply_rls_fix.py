import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Try common env var names for the connection string
DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")

if not DB_URL:
    print("Error: DATABASE_URL not found in .env")
    exit(1)

SQL_FILE = "fix_missing_credits.sql"

if not os.path.exists(SQL_FILE):
    print(f"Error: {SQL_FILE} not found")
    exit(1)

try:
    with open('fix_column_names.sql', 'r') as f:
        sql = f.read()
    
    print(f"Connecting to DB...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    print(f"Executing {SQL_FILE}...")
    cur.execute(sql)
    conn.commit()
    
    print("Success! SQL executed.")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Execution Failed: {e}")
    exit(1)
