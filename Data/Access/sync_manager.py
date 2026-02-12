# sync_manager.py: Orchestrates data synchronization to Supabase.
# Refactored for Clean Architecture (v2.7)

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(project_root)

from Scripts.sync_to_supabase import SupabaseSync
from Data.Access.db_helpers import (
    PREDICTIONS_CSV, SCHEDULES_CSV, TEAMS_CSV, 
    STANDINGS_CSV, REGION_LEAGUE_CSV
)

def run_predictions_sync():
    """
    Executes the synchronization of all core CSVs to Supabase.
    This should be called at the end of Chapter 1B (Analysis).
    """
    print("\n--- SYNCHRONIZATION: Pushing Database to Cloud ---")
    
    # Load env
    load_dotenv(os.path.join(project_root, ".env"))
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("   [Sync Error] Missing Supabase credentials in .env")
        return

    try:
        syncer = SupabaseSync(url, key)
        
        # Define syncing tasks: (CSV Path, Supabase Table Name, Unique Key)
        tasks = [
            (PREDICTIONS_CSV, "predictions", "fixture_id"),
            (SCHEDULES_CSV, "schedules", "fixture_id"),
            (TEAMS_CSV, "teams", "team_id"),
            (REGION_LEAGUE_CSV, "region_leagues", "rl_id"),
            (STANDINGS_CSV, "standings", "standings_key")
        ]
        
        for csv_path, table_name, unique_key in tasks:
            if not os.path.exists(csv_path):
                 print(f"   [Sync Warning] {os.path.basename(csv_path)} not found. Skipping.")
                 continue

            print(f"   [Sync] Syncing {table_name}...")
            
            # Using the generic upsert method from SupabaseSync (we need to expose it or reuse existing)
            # Since sync_predictions is specialized, we'll use a more generic approach here 
            # by reading rows and using the client directly, or extending SupabaseSync.
            
            # Re-using internal helper from SupabaseSync would be ideal, 
            # but let's just use the public generic method if available, or call internal logic.
            # NOTE: sync_to_supabase.py's SupabaseSync class currently has `sync_predictions` 
            # which is specialized (deduplication logic). 
            # We should probably extend SupabaseSync in `sync_to_supabase.py` first to support generic tables.
            
            # For now, let's use a simple direct generic sync here for the new tables
            # and use the specialized one for predictions.
            
            if table_name == "predictions":
                syncer.sync_predictions(Path(csv_path), dry_run=False)
            else:
                _generic_sync(syncer, csv_path, table_name, unique_key)

        print("   [Sync] Cloud synchronization complete.")
            
    except Exception as e:
        print(f"   [Sync Error] Failed to sync: {e}")

def _generic_sync(syncer, csv_path, table_name, unique_key):
    """Helper to sync standard CSVs without special logic."""
    rows = syncer.read_csv(Path(csv_path))
    if not rows: return

    # Basic cleanup (empty strings to None)
    cleaned_rows = [syncer.clean_row(row) for row in rows]
    
    # Robust Date Format Fix for Schedules/Standings
    if table_name in ['schedules', 'standings']:
        from datetime import datetime
        
        def parse_and_fix_date(date_str):
            """Convert various date formats to YYYY-MM-DD."""
            if not date_str or date_str == 'None':
                return None
                
            # Try YY-MM-DD (e.g., "26-02-07" -> "2026-02-07")
            if '-' in date_str and len(date_str.split('-')[0]) == 2:
                try:
                    dt = datetime.strptime(date_str, "%y-%m-%d")
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass
            
            # Try DD.MM.YY (e.g., "07.02.26" -> "2026-02-07")
            if '.' in date_str:
                try:
                    dt = datetime.strptime(date_str, "%d.%m.%y")
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    try:
                        # Try DD.MM.YYYY
                        dt = datetime.strptime(date_str, "%d.%m.%Y")
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        pass
            
            # Already in correct format or unparseable
            return date_str
        
        for row in cleaned_rows:
            if row.get('date'):
                row['date'] = parse_and_fix_date(row['date'])
    
    # Filter out invalid standings rows (NULL standings_key)
    if table_name == 'standings':
        original_count = len(cleaned_rows)
        cleaned_rows = [r for r in cleaned_rows if r.get('standings_key')]
        filtered_count = original_count - len(cleaned_rows)
        if filtered_count > 0:
            print(f"      [!] Filtered {filtered_count} rows with NULL standings_key")

    # Upsert in batches
    batch_size = 500
    total = len(cleaned_rows)
    
    for i in range(0, total, batch_size):
        batch = cleaned_rows[i:i + batch_size]
        try:
            syncer.client.table(table_name).upsert(
                batch, on_conflict=unique_key
            ).execute()
            print(f"      -> Batch {i//batch_size + 1}: {len(batch)} rows synced.")
        except Exception as e:
             print(f"      [x] Batch failed for {table_name}: {e}")
