"""
Production-grade Supabase sync script for LeoBook.
Syncs Data/Store CSV files to Supabase with UPSERT logic.

Usage:
    python Scripts/sync_to_supabase.py [--dry-run] [--force] [--tables TABLE1,TABLE2]

Supported Tables:
    predictions, schedules, teams, region_league (default: all)

Environment Variables (required):
    SUPABASE_URL: Your Supabase project URL
    SUPABASE_SERVICE_KEY: Service role key (NOT anon key!)

Author: LeoBook Team
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/supabase_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Table configuration: CSV filename -> (Supabase table name, conflict key)
TABLE_CONFIG = {
    'predictions': {'csv': 'predictions.csv', 'table': 'predictions', 'key': 'fixture_id'},
    'schedules': {'csv': 'schedules.csv', 'table': 'schedules', 'key': 'fixture_id'},
    'teams': {'csv': 'teams.csv', 'table': 'teams', 'key': 'team_id'},
    'region_league': {'csv': 'region_league.csv', 'table': 'region_league', 'key': 'rl_id'},
}

class SupabaseSync:
    """Handles syncing CSV data to Supabase with production-grade error handling."""
    
    def __init__(self, supabase_url: str, service_key: str):
        """
        Initialize Supabase client.
        
        Args:
            supabase_url: Supabase project URL
            service_key: Service role key for admin operations
        """
        try:
            from supabase import create_client, Client
            self.client: Client = create_client(supabase_url, service_key)
            self.url = supabase_url
            logger.info(f"[+] Connected to Supabase: {supabase_url}")
        except ImportError:
            logger.error("[x] supabase-py not installed. Run: pip install supabase")
            sys.exit(1)
        except Exception as e:
            logger.error(f"[x] Failed to connect to Supabase: {e}")
            sys.exit(1)
    
    def read_csv(self, filepath: Path) -> List[Dict[str, Any]]:
        """
        Read CSV file and return list of dictionaries.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            List of row dictionaries
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                logger.info(f"    Read {len(rows)} rows from {filepath.name}")
                return rows
        except FileNotFoundError:
            logger.error(f"[x] File not found: {filepath}")
            return []
        except Exception as e:
            logger.error(f"[x] Error reading {filepath}: {e}")
            return []
    
    def clean_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and normalize row data for Supabase.
        
        Args:
            row: Raw CSV row dictionary
            
        Returns:
            Cleaned row dictionary
        """
        cleaned = {}
        
        for key, value in row.items():
            # Convert empty strings to None
            if value == '' or value == 'N/A':
                cleaned[key] = None
            # Convert string booleans
            elif value.lower() == 'true':
                cleaned[key] = True
            elif value.lower() == 'false':
                cleaned[key] = False
            # Convert numeric strings
            elif key in ['home_form_n', 'away_form_n', 'h2h_count', 'form_count']:
                try:
                    cleaned[key] = int(value) if value else None
                except (ValueError, TypeError):
                    cleaned[key] = None
            elif key in ['xg_home', 'xg_away']:
                try:
                    cleaned[key] = float(value) if value else None
                except (ValueError, TypeError):
                    cleaned[key] = None
            else:
                cleaned[key] = value
        
        # Renaissance fix: Rename over_2.5 -> over_2_5
        if 'over_2.5' in cleaned:
            cleaned['over_2_5'] = cleaned.pop('over_2.5')

        # Fix date format: DD.MM.YYYY -> YYYY-MM-DD
        if 'date' in cleaned and cleaned['date']:
            try:
                # Assuming input is DD.MM.YYYY
                parts = cleaned['date'].split('.')
                if len(parts) == 3:
                    cleaned['date'] = f"{parts[2]}-{parts[1]}-{parts[0]}"
            except Exception:
                pass # Keep original if parse fails
        
        return cleaned
    
    def upsert_table(
        self,
        table_name: str,
        conflict_key: str,
        rows: List[Dict[str, Any]],
        batch_size: int = 500,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Upsert data to any Supabase table (insert new, update existing).
        
        Args:
            table_name: Name of Supabase table
            conflict_key: Column name for conflict resolution
            rows: List of row dictionaries
            batch_size: Number of rows per batch
            dry_run: If True, don't actually write to database
            
        Returns:
            Dictionary with sync statistics
        """
        stats = {'total': len(rows), 'inserted': 0, 'failed': 0}
        
        # Deduplicate rows by conflict_key (keep latest)
        unique_rows = {}
        for row in rows:
            if conflict_key in row and row[conflict_key]:
                unique_rows[row[conflict_key]] = row
        
        deduped_rows = list(unique_rows.values())
        if len(deduped_rows) < len(rows):
            logger.info(f"    Deduplicated {len(rows)} -> {len(deduped_rows)} rows (removed {len(rows) - len(deduped_rows)} duplicates)")
            
        if dry_run:
            logger.info("[?] DRY RUN MODE - No data will be written")
        
        # Process in batches
        total_batches = (len(deduped_rows) + batch_size - 1) // batch_size
        
        for i in range(0, len(deduped_rows), batch_size):
            batch = deduped_rows[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} rows)")
            
            # Clean each row
            cleaned_batch = [self.clean_row(row) for row in batch]
            
            if dry_run:
                logger.info(f"   Would upsert {len(cleaned_batch)} rows")
                stats['inserted'] += len(cleaned_batch)
                continue
            
            try:
                # Upsert with conflict resolution
                response = self.client.table(table_name).upsert(
                    cleaned_batch,
                    on_conflict=conflict_key,
                    returning='minimal'  # Don't return data (faster)
                ).execute()
                
                stats['inserted'] += len(cleaned_batch)
                logger.info(f"   [+] Upserted {len(cleaned_batch)} rows successfully")
                
            except Exception as e:
                stats['failed'] += len(cleaned_batch)
                logger.error(f"   [x] Batch {batch_num} failed: {e}")
                
                # Try to log first row for debugging
                if cleaned_batch:
                    logger.error(f"   First row in failed batch: {cleaned_batch[0]}")
        
        return stats
    
    def sync_table(self, table_key: str, csv_path: Path, dry_run: bool = False) -> bool:
        """
        Sync a single table to Supabase.
        
        Args:
            table_key: Key from TABLE_CONFIG (e.g., 'predictions', 'schedules')
            csv_path: Path to CSV file
            dry_run: If True, simulate sync without writing
            
        Returns:
            True if successful, False otherwise
        """
        config = TABLE_CONFIG[table_key]
        logger.info("=" * 80)
        logger.info(f">> Syncing {table_key}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        # Read CSV
        rows = self.read_csv(csv_path)
        if not rows:
            logger.warning(f"(!) No data to sync for {table_key}")
            return True  # Not a failure, just empty
        
        # Upsert to Supabase
        stats = self.upsert_table(
            table_name=config['table'],
            conflict_key=config['key'],
            rows=rows,
            dry_run=dry_run
        )
        
        # Log results
        logger.info("=" * 80)
        logger.info(f"  SYNC RESULTS: {table_key}")
        logger.info("=" * 80)
        logger.info(f"  Total rows:    {stats['total']}")
        logger.info(f"  [+] Upserted:   {stats['inserted']}")
        logger.info(f"  [x] Failed:     {stats['failed']}")
        
        if stats['failed'] > 0:
            logger.warning(f"(!)  {stats['failed']} rows failed to sync")
            return False
        
        logger.info(f">> {table_key} sync completed successfully!\n")
        return True


def prompt_user_sync() -> bool:
    """
    Prompt user whether to sync to Supabase.
    
    Returns:
        True if user wants to sync, False otherwise
    """
    while True:
        response = input("\n🔄 Update Supabase with Data/Store changes? (Y/N): ").strip().upper()
        if response in ['Y', 'YES']:
            return True
        elif response in ['N', 'NO']:
            return False
        else:
            print("   Please enter Y or N")



def main():
    """Main entry point for Supabase sync script."""
    import argparse
    from dotenv import load_dotenv
    
    # Force UTF-8 output for Windows consoles
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description='Sync LeoBook CSV files to Supabase database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate sync without writing to database'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip user confirmation prompt'
    )
    parser.add_argument(
        '--tables',
        type=str,
        default='all',
        help='Comma-separated list of tables to sync (predictions,schedules,teams,region_league) or "all"'
    )
    args = parser.parse_args()
    
    # Get credentials from environment
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not service_key:
        logger.error("[x] Missing environment variables!")
        logger.error("   Required: SUPABASE_URL, SUPABASE_SERVICE_KEY")
        logger.error("   Set them in .env or export them")
        sys.exit(1)
    
    # Prompt user (unless --force)
    if not args.force and not prompt_user_sync():
        logger.info("⏭️  Sync cancelled by user")
        return
    
    # Initialize sync client
    sync = SupabaseSync(supabase_url, service_key)
    
    # Determine which tables to sync
    if args.tables == 'all':
        tables_to_sync = list(TABLE_CONFIG.keys())
    else:
        tables_to_sync = [t.strip() for t in args.tables.split(',')]
        # Validate table names
        invalid = [t for t in tables_to_sync if t not in TABLE_CONFIG]
        if invalid:
            logger.error(f"[x] Invalid table names: {invalid}")
            logger.error(f"   Valid options: {list(TABLE_CONFIG.keys())}")
            sys.exit(1)
    
    logger.info(f"[INFO] Tables to sync: {', '.join(tables_to_sync)}\n")
    
    # Sync each table
    project_root = Path(__file__).parent.parent
    all_success = True
    
    for table_key in tables_to_sync:
        config = TABLE_CONFIG[table_key]
        csv_path = project_root / 'Data' / 'Store' / config['csv']
        
        if not csv_path.exists():
            logger.warning(f"[!] {config['csv']} not found, skipping {table_key}")
            continue
        
        success = sync.sync_table(table_key, csv_path, dry_run=args.dry_run)
        if not success:
            all_success = False
    
    if all_success:
        logger.info("\n" + "=" * 80)
        logger.info("[SUCCESS] All tables synced successfully!")
        logger.info("=" * 80)
    
    sys.exit(0 if all_success else 1)


if __name__ == '__main__':
    main()
