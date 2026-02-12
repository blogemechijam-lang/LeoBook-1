#!/usr/bin/env python3
"""
Migration Script: Add 'status' Column to schedules.csv
Author: LeoBook Team
Date: 2026-02-12

Purpose:
  Adds a new 'status' column to schedules.csv based on existing 'match_status' values.
  Maps: finished -> finished, scheduled -> scheduled, postponed -> postponed, canceled -> canceled

Usage:
  python Scripts/migrate_add_status_column.py [--dry-run]
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

SCHEDULES_CSV = "Data/Store/schedules.csv"
BACKUP_PATH = f"Data/Store/schedules_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# New headers with 'status' added
NEW_HEADERS = [
    'fixture_id', 'date', 'match_time', 'region_league', 'rl_id',
    'home_team', 'away_team', 'home_team_id', 'away_team_id',
    'home_score', 'away_score', 'match_status', 'status', 'match_link'
]

def map_status(match_status: str) -> str:
    """Map match_status to new status column."""
    status_map = {
        'finished': 'finished',
        'scheduled': 'scheduled',
        'postponed': 'postponed',
        'canceled': 'canceled',
        'cancelled': 'canceled',  # Handle alternate spelling
    }
    return status_map.get(match_status.lower(), 'scheduled')  # Default to scheduled


def migrate(dry_run=False):
    """
    Migrate schedules.csv by adding 'status' column.
    
    Args:
        dry_run: If True, only print what would happen without modifying files
    """
    
    if not os.path.exists(SCHEDULES_CSV):
        print(f"[ERROR] {SCHEDULES_CSV} not found!")
        return False
    
    # Step 1: Read existing data
    print(f"[INFO] Reading {SCHEDULES_CSV}...")
    rows = []
    with open(SCHEDULES_CSV, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        existing_headers = reader.fieldnames
        rows = list(reader)
    
    print(f"   Found {len(rows)} rows")
    print(f"   Existing headers: {existing_headers}")
    
    # Step 2: Check if 'status' already exists
    if 'status' in existing_headers:
        print("[SUCCESS] 'status' column already exists. No migration needed.")
        return True
    
    # Step 3: Add 'status' column to each row
    print(f"\n[PROCESSING] Adding status column...")
    updated_rows = []
    status_counts = {'finished': 0, 'scheduled': 0, 'postponed': 0, 'canceled': 0}
    
    for row in rows:
        match_status = row.get('match_status', '')
        new_status = map_status(match_status)
        row['status'] = new_status
        status_counts[new_status] += 1
        updated_rows.append(row)
    
    print(f"\n[STATS] Status Distribution:")
    for status, count in status_counts.items():
        print(f"   {status:12}: {count:6} ({count/len(rows)*100:.1f}%)")
    
    if dry_run:
        print("\n[DRY-RUN] No files will be modified")
        print(f"   Would create backup: {BACKUP_PATH}")
        print(f"   Would write {len(updated_rows)} rows with new 'status' column")
        return True
    
    # Step 4: Create backup
    print(f"\n[BACKUP] Creating backup: {BACKUP_PATH}")
    # Write original data (without the new status column)
    with open(BACKUP_PATH, 'w', encoding='utf-8', newline='') as f:
        # Use a standard writer for the backup to preserve original format
        writer = csv.writer(f)
        writer.writerow(existing_headers)
        for original_row in rows:
            # Write only the original fields (without 'status')
            row_values = [original_row.get(h, '') for h in existing_headers]
            writer.writerow(row_values)
    
    # Step 5: Write updated data with new column
    print(f"\n[WRITING] Updating schedules.csv...")
    with open(SCHEDULES_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=NEW_HEADERS)
        writer.writeheader()
        writer.writerows(updated_rows)
    
    print(f"[SUCCESS] Migration complete! {len(updated_rows)} rows updated.")
    print(f"   Backup saved to: {BACKUP_PATH}")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Add status column to schedules.csv')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Simulate migration without modifying files')
    args = parser.parse_args()
    
    print("=" * 60)
    print("  SCHEDULES.CSV MIGRATION: Add 'status' Column")
    print("=" * 60)
    
    success = migrate(dry_run=args.dry_run)
    
    if success:
        print("\n[SUCCESS] Migration script completed successfully!")
        if args.dry_run:
            print("   Run without --dry-run to apply changes")
    else:
        print("\n[ERROR] Migration failed!")
        sys.exit(1)
