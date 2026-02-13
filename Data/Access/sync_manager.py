import csv
import logging
import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from Data.Access.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "Data" / "Store"

TABLE_CONFIG = {
    'predictions': {'csv': 'predictions.csv', 'table': 'predictions', 'key': 'fixture_id'},
    'schedules': {'csv': 'schedules.csv', 'table': 'schedules', 'key': 'fixture_id'},
    'teams': {'csv': 'teams.csv', 'table': 'teams', 'key': 'team_id'},
    'region_league': {'csv': 'region_league.csv', 'table': 'region_league', 'key': 'rl_id'},
    'standings': {'csv': 'standings.csv', 'table': 'standings', 'key': 'standings_key'},
    'fb_matches': {'csv': 'fb_matches.csv', 'table': 'fb_matches', 'key': 'site_match_id'},
    'profiles': {'csv': 'profiles.csv', 'table': 'profiles', 'key': 'id'},
    'custom_rules': {'csv': 'custom_rules.csv', 'table': 'custom_rules', 'key': 'id'},
    'rule_executions': {'csv': 'rule_executions.csv', 'table': 'rule_executions', 'key': 'id'},
}

class SyncManager:
    """
    Manages bi-directional synchronization between local CSVs and Supabase.
    """
    def __init__(self):
        self.supabase = get_supabase_client()
        if not self.supabase:
            logger.warning("[!] SyncManager initialized without Supabase connection. Sync disabled.")

    async def sync_on_startup(self):
        """
        Pull remote changes and push local changes for all configured tables.
        Design:
          1. Fetch all remote keys + last_updated.
          2. Read local keys + last_updated.
          3. Compare and determine delta.
          4. Sync differences.
        """
        if not self.supabase:
            return

        logger.info("Starting bi-directional sync on startup...")

        for table_key, config in TABLE_CONFIG.items():
            await self._sync_table(table_key, config)

    async def _sync_table(self, table_key: str, config: Dict):
        """Sync a single table."""
        table_name = config['table']
        csv_file = config['csv']
        key_field = config['key']
        csv_path = DATA_DIR / csv_file
        
        if not csv_path.exists():
            logger.warning(f"  [SKIP] {csv_file} not found.")
            return

        logger.info(f"  Syncing {table_name} <-> {csv_file}...")

        # 1. Fetch Remote Keys/Timestamps (lightweight query)
        try:
            # Fetch minimal data: id, last_updated
            # Supabase API might paginate, so we need to handle that for large tables (22k)
            # For now, let's assume get() fetches enough or we implement paging.
            # Using a simplified approach: fetch all IDs and timestamps.
            # Note: 22k rows might be too much for one request. We should probably use a stored procedure or just page it.
            # Enhancing: Paging 1000 at a time.
            
            remote_map = await self._fetch_remote_metadata(table_name, key_field)
        except Exception as e:
            logger.error(f"    [x] Failed to fetch remote metadata for {table_name}: {e}")
            return

        # 2. Read Local Data
        local_rows = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                local_rows = list(reader)
        except Exception as e:
            logger.error(f"    [x] Failed to read {csv_file}: {e}")
            return

        local_map = {row[key_field]: row.get('last_updated', '') for row in local_rows if row.get(key_field)}
        local_data_map = {row[key_field]: row for row in local_rows if row.get(key_field)}

        # 3. Operations Lists
        to_push_ids = []   # Local > Remote (or new in Local)
        to_pull_ids = []   # Remote > Local (or new in Remote)

        # Compare Local vs Remote
        all_ids = set(local_map.keys()) | set(remote_map.keys())
        
        for uid in all_ids:
            local_ts_str = local_map.get(uid)
            remote_ts_str = remote_map.get(uid)

            if not remote_ts_str:
                # New locally (or remote has no timestamp), push to remote
                to_push_ids.append(uid)
            elif not local_ts_str:
                # New remotely, pull to local
                to_pull_ids.append(uid)
            else:
                # Compare timestamps
                # Handle ISO format. "2024-02-12T10:00:00"
                # If simplified comparison (string compare) works for ISO
                if local_ts_str > remote_ts_str:
                    to_push_ids.append(uid)
                elif remote_ts_str > local_ts_str:
                    to_pull_ids.append(uid)

        logger.info(f"    Analyzed {len(all_ids)} rows: {len(to_push_ids)} to push, {len(to_pull_ids)} to pull.")

        # 4. Execute Sync
        if to_pull_ids:
            await self._pull_updates(table_name, key_field, to_pull_ids, local_rows, csv_path, list(local_rows[0].keys()) if local_rows else [])

        if to_push_ids:
             # We push the FULL row data for these IDs
             rows_to_push = [local_data_map[uid] for uid in to_push_ids]
             await self.batch_upsert(table_key, rows_to_push)


    async def _fetch_remote_metadata(self, table_name: str, key_field: str) -> Dict[str, str]:
        """Fetch all ID:last_updated pairs from Supabase. Handles pagination."""
        remote_map = {}
        batch_size = 1000
        offset = 0
        
        while True:
            # We can't use async calling convention directly with the synchronous Supabase client wrapper 
            # unless we wrap it. But `sync_to_supabase.py` used .execute().
            # If `result` is returned synchronously, we don't need await.
            # But the calling context is async def.
            # Supabase Python client is synchronous by default (using httpx sync client).
            # So we don't await the client call.
            
            # Select only ID and last_updated
            try:
                # Using synchronous call in async function is blocking, but okay for this script logic 
                # or we run in executor if needed. For now, blocking is acceptable as it's startup sync.
                res = self.supabase.table(table_name).select(f"{key_field},last_updated").range(offset, offset + batch_size - 1).execute()
                
                rows = res.data
                if not rows:
                    break
                
                for r in rows:
                    k = r.get(key_field)
                    if k:
                        remote_map[str(k)] = r.get('last_updated', '')
                
                if len(rows) < batch_size:
                    break
                offset += batch_size

            except Exception as e:
                logger.error(f"      [x] Error fetching remote metadata (offset {offset}): {e}")
                break
        
        return remote_map

    async def _pull_updates(self, table_name: str, key_field: str, ids: List[str], current_local_rows: List[Dict], csv_path: Path, fieldnames: List[str]):
        """Fetch full rows from Supabase and update local CSV."""
        if not ids:
            return

        logger.info(f"    Pulling {len(ids)} updates from Supabase...")
        
        # Batch fetch
        batch_size = 200
        upserted_rows = {}
        
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            try:
                res = self.supabase.table(table_name).select("*").in_(key_field, batch_ids).execute()
                for r in res.data:
                    upserted_rows[str(r[key_field])] = r
            except Exception as e:
                logger.error(f"      [x] Failed to pull batch: {e}")

        # Merge into local rows
        local_map = {str(row[key_field]): row for row in current_local_rows if row.get(key_field)}
        
        updated_count = 0
        for uid, remote_row in upserted_rows.items():
            cleaned_remote = {}
            for k, v in remote_row.items():
                if v is None:
                    cleaned_remote[k] = ''
                elif isinstance(v, bool):
                     cleaned_remote[k] = str(v).lower()
                else:
                    val_str = str(v)
                    # NORMALIZE DATE BACK TO CSV FORMAT (DD.MM.YYYY)
                    if k in ['date', 'date_updated', 'last_extracted'] and re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
                         iso_date = val_str[:10]
                         y, m, d = iso_date.split('-')
                         cleaned_remote[k] = f"{d}.{m}.{y}"
                    else:
                        cleaned_remote[k] = val_str
            
            if uid in local_map:
                local_map[uid].update(cleaned_remote)
            else:
                local_map[uid] = cleaned_remote
            updated_count += 1
            
        # Write back to CSV
        # Use existing fieldnames if possible, else union
        all_keys = set(fieldnames)
        for r in local_map.values():
            all_keys.update(r.keys())
        
        final_fieldnames = list(all_keys)
        # Ensure ID is first, last_updated last
        if 'last_updated' in final_fieldnames:
             final_fieldnames.remove('last_updated')
             final_fieldnames.append('last_updated')
        
        if key_field in final_fieldnames:
             final_fieldnames.remove(key_field)
             final_fieldnames.insert(0, key_field)

        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=final_fieldnames)
                writer.writeheader()
                writer.writerows(local_map.values())
            logger.info(f"    [SUCCESS] Updated {csv_path.name} with {updated_count} rows from remote.")
        except Exception as e:
            logger.error(f"    [x] Failed to write local CSV: {e}")

    async def batch_upsert(self, table_key: str, data: List[Dict[str, Any]]):
        """
        Upsert a batch of data to Supabase.
        """
        if not self.supabase or not data:
            return

        conf = TABLE_CONFIG.get(table_key)
        if not conf:
            return
        
        table_name = conf['table']
        conflict_key = conf['key']

        # Clean data for Supabase (None handling)
        cleaned_data = []
        for row in data:
            clean = {}
            for k, v in row.items():
                if v == '' or v == 'N/A':
                    clean[k] = None
                else:
                    val = v
                    if k in ['date', 'date_updated', 'last_extracted'] and isinstance(val, str):
                        match = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', val)
                        if match:
                            d, m, y = match.groups()
                            val = f"{y}-{m}-{d}"
                    
                    if isinstance(val, str):
                        val = val.strip()
                        
                    clean[k] = val
            
            # Remove 'id' if it is null/empty so Supabase encounters no constraint violation (auto-increment)
            if 'id' in clean and (clean['id'] is None or clean['id'] == ''):
                del clean['id']

            # Sanitize timestamp columns: strict regex check with end of string anchor
            # ISO 8601 regex: YYYY-MM-DDTHH:MM:SS(.mmm)?(Z|+HH:MM)?
            ts_regex = re.compile(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:?\d{2}|Z)?$')
            
            for ts_col in ['last_updated', 'date_updated', 'last_extracted', 'created_at', 'updated_at']:
                if ts_col in clean:
                    val = str(clean[ts_col]).strip()
                    if not ts_regex.match(val):
                        # print(f"    [SYNC WARN] Invalid timestamp for {ts_col}: {val}. Using now().")
                        clean[ts_col] = datetime.utcnow().isoformat()
            
            # Ensure last_updated is present
            if 'last_updated' not in clean:
                clean['last_updated'] = datetime.utcnow().isoformat()
            
            cleaned_data.append(clean)

        # --- DATA QUALITY GATES ---
        # 1. Filter rows with null conflict key (Supabase rejects these)
        conflict_keys = [k.strip() for k in conflict_key.split(',')]
        cleaned_data = [
            row for row in cleaned_data
            if all(row.get(k) not in (None, '', 'null') for k in conflict_keys)
        ]

        # 2. Deduplicate by conflict key (Supabase rejects duplicate keys in same batch)
        seen = set()
        deduped = []
        for row in cleaned_data:
            key_val = tuple(row.get(k) for k in conflict_keys)
            if key_val not in seen:
                seen.add(key_val)
                deduped.append(row)
        cleaned_data = deduped

        # 3. Sanitize null Unicode escapes (\u0000) that PostgreSQL rejects
        for row in cleaned_data:
            for k, v in row.items():
                if isinstance(v, str) and '\x00' in v:
                    row[k] = v.replace('\x00', '')

        if not cleaned_data:
            return

        try:
            # Upsert
            self.supabase.table(table_name).upsert(cleaned_data, on_conflict=conflict_key).execute()
            logger.info(f"    [SYNC] Upserted {len(cleaned_data)} rows to {table_name}.")
        except Exception as e:
            logger.error(f"    [x] Upsert failed for {table_name}: {e}")

async def run_predictions_sync():
    """Wrapper to sync predictions table."""
    manager = SyncManager()
    await manager._sync_table('predictions', TABLE_CONFIG['predictions'])

