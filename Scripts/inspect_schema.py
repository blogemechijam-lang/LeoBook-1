
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

# Load environment variables
load_dotenv(os.path.join(project_root, ".env"))

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("Error: Missing Supabase credentials in .env")
    sys.exit(1)

supabase: Client = create_client(url, key)

def get_columns(table_name):
    print(f"\n--- Columns in '{table_name}' ---")
    try:
        # Use RPC if available, or just query information_schema via SQL if enabled?
        # Actually simplest way is usually selecting limits 1 and inspecting keys if row exists.
        # But we want schema even if empty.
        # Let's try querying information_schema via helper stored function if exists, 
        # otherwise we might need to rely on `rpc` if direct SQL isn't exposed.
        # Ah, supabase-py doesn't expose direct SQL execution easily without an RPC.
        #
        # Better Idea: Just try to select 1 row.
        res = supabase.table(table_name).select("*").limit(1).execute()
        if res.data:
            print(f"Columns found in data: {list(res.data[0].keys())}")
        else:
             print("Table is empty, cannot inspect columns easily via SELECT *.")
             # Fallback: We can try inserting a dummy row with just ID and catch error? No...
             pass

    except Exception as e:
        print(f"Error inspecting {table_name}: {e}")

get_columns("predictions")
get_columns("schedules")
get_columns("region_leagues")
