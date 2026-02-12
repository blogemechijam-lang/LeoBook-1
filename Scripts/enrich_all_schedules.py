#!/usr/bin/env python3
"""
Match Enrichment Pipeline: Process ALL schedules to extract missing data
Author: LeoBook Team
Date: 2026-02-12

Purpose:
  - Visit ALL match URLs in schedules.csv (22k+)
  - Extract team IDs, league IDs, final scores
  - Upsert teams.csv and region_league.csv
  - Fix "Unknown" or "N/A" entries
  - Smart date/time parsing for merged datetime strings

Usage:
  python Scripts/enrich_all_schedules.py [--limit N] [--dry-run]
"""

import asyncio
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import Playwright, async_playwright
from Data.Access.db_helpers import (
    SCHEDULES_CSV, TEAMS_CSV, REGION_LEAGUE_CSV,
    save_team_entry, save_region_league_entry, save_schedule_entry
)
from Data.Access.outcome_reviewer import smart_parse_datetime

# Configuration
CONCURRENCY = 10  # Process 10 matches concurrently
BATCH_SIZE = 100  # Report progress every 100 matches


async def extract_match_enrichment(page, match_url: str) -> Optional[Dict]:
    """
    Extract team IDs, league ID, final score, and datetime from match page.
    
    Args:
        page: Playwright page instance
        match_url: Full match URL
        
    Returns:
        Dictionary with enriched data or None if failed
    """
    try:
        await page.goto(match_url, wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(500)  # Brief wait for JS
        
        enriched = {}
        
        # Extract team IDs from team links
        try:
            home_link = await page.query_selector('a.participant__participantName--home')
            if home_link:
                href = await home_link.get_attribute('href')
                if href:
                    # Extract team ID from URL: /team/name/ABC123/
                    parts = href.strip('/').split('/')
                    if len(parts) >= 3:
                        enriched['home_team_id'] = parts[-1]
        except:
            pass
        
        try:
            away_link = await page.query_selector('a.participant__participantName--away')
            if away_link:
                href = await away_link.get_attribute('href')
                if href:
                    parts = href.strip('/').split('/')
                    if len(parts) >= 3:
                        enriched['away_team_id'] = parts[-1]
        except:
            pass
        
        # Extract league ID and info
        try:
            league_link = await page.query_selector('a.tournamentHeader__country')
            if league_link:
                href = await league_link.get_attribute('href')
                if href:
                    # Extract league ID from URL
                    enriched['rl_id'] = href.strip('/').split('/')[-1]
                    
                text = await league_link.inner_text()
                if ':' in text:
                    region, league = text.split(':', 1)
                    enriched['region'] = region.strip()
                    enriched['league'] = league.strip()
        except:
            pass
        
        # Extract final score
        try:
            home_score_el = await page.query_selector('.detailScore__wrapper span:first-child')
            away_score_el = await page.query_selector('.detailScore__wrapper span:last-child')
            
            if home_score_el and away_score_el:
                home_score = await home_score_el.inner_text()
                away_score = await away_score_el.inner_text()
                enriched['home_score'] = home_score.strip()
                enriched['away_score'] = away_score.strip()
        except:
            pass
        
        # Extract match datetime
        try:
            datetime_el = await page.query_selector('.duelParticipant__startTime')
            if datetime_el:
                dt_text = await datetime_el.inner_text()
                date_part, time_part = smart_parse_datetime(dt_text)
                if date_part:
                    enriched['date'] = date_part
                if time_part:
                    enriched['match_time'] = time_part
        except:
            pass
        
        return enriched if enriched else None
        
    except Exception as e:
        print(f"      [ERROR] Failed to enrich {match_url}: {e}")
        return None


async def enrich_batch(playwright: Playwright, matches: List[Dict], batch_num: int) -> List[Dict]:
    """
    Process a batch of matches concurrently.
    
    Args:
        playwright: Playwright instance
        matches: List of match dictionaries from schedules.csv
        batch_num: Current batch number for logging
        
    Returns:
        List of enriched match dictionaries
    """
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        viewport={'width': 1280, 'height': 720},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    
    results = []
    
    # Process matches in smaller concurrent chunks
    for i in range(0, len(matches), CONCURRENCY):
        chunk = matches[i:i + CONCURRENCY]
        tasks = []
        
        for match in chunk:
            page = await context.new_page()
            task = extract_match_enrichment(page, match['match_link'])
            tasks.append((page, task))
        
        # Wait for all tasks
        chunk_results = await asyncio.gather(*[t for _, t in tasks], return_exceptions=True)
        
        # Close pages
        for page, _ in tasks:
            await page.close()
        
        # Merge results with original match data
        for match, enriched in zip(chunk, chunk_results):
            if isinstance(enriched, dict):
                match.update(enriched)
            results.append(match)
    
    await context.close()
    await browser.close()
    
    return results


async def enrich_all_schedules(limit: Optional[int] = None, dry_run: bool = False):
    """
    Main enrichment pipeline.
    
    Args:
        limit: Process only first N matches (for testing)
        dry_run: If True, don't write to CSV files
    """
    print("=" * 80)
    print("  MATCH ENRICHMENT PIPELINE")
    print("=" * 80)
    
    # Load schedules
    if not os.path.exists(SCHEDULES_CSV):
        print(f"[ERROR] {SCHEDULES_CSV} not found!")
        return
    
    with open(SCHEDULES_CSV, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        all_matches = list(reader)
    
    # Filter matches that need enrichment
    to_enrich = [
        m for m in all_matches
        if m.get('match_link') and (
            not m.get('home_team_id') or
            not m.get('away_team_id') or
            m.get('region_league') == 'Unknown'
        )
    ]
    
    if limit:
        to_enrich = to_enrich[:limit]
    
    print(f"[INFO] Total matches: {len(all_matches)}")
    print(f"[INFO] Matches to enrich: {len(to_enrich)}")
    
    if dry_run:
        print("[DRY-RUN] Simulating enrichment...")
    
    # Process in batches
    total_batches = (len(to_enrich) + BATCH_SIZE - 1) // BATCH_SIZE
    enriched_count = 0
    teams_added = set()
    leagues_added = set()
    
    async with async_playwright() as playwright:
        for batch_idx in range(0, len(to_enrich), BATCH_SIZE):
            batch = to_enrich[batch_idx:batch_idx + BATCH_SIZE]
            batch_num = (batch_idx // BATCH_SIZE) + 1
            
            print(f"\n[BATCH {batch_num}/{total_batches}] Processing {len(batch)} matches...")
            
            enriched_batch = await enrich_batch(playwright, batch, batch_num)
            
            if not dry_run:
                # Save enriched data
                for match in enriched_batch:
                    # Update schedule
                    save_schedule_entry(match)
                    
                    # Upsert teams
                    if match.get('home_team_id'):
                        save_team_entry({
                            'team_id': match['home_team_id'],
                            'team_name': match.get('home_team', 'Unknown')
                        })
                        teams_added.add(match['home_team_id'])
                    
                    if match.get('away_team_id'):
                        save_team_entry({
                            'team_id': match['away_team_id'],
                            'team_name': match.get('away_team', 'Unknown')
                        })
                        teams_added.add(match['away_team_id'])
                    
                    # Upsert league
                    if match.get('rl_id'):
                        save_region_league_entry({
                            'rl_id': match['rl_id'],
                            'region': match.get('region', 'Unknown'),
                            'league': match.get('league', 'Unknown')
                        })
                        leagues_added.add(match['rl_id'])
                    
                    enriched_count += 1
            
            print(f"   [+] Enriched {len(enriched_batch)} matches")
            print(f"   [+] Teams: {len(teams_added)}, Leagues: {len(leagues_added)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("  ENRICHMENT COMPLETE")
    print("=" * 80)
    print(f"  Total enriched:  {enriched_count}")
    print(f"  Teams updated:   {len(teams_added)}")
    print(f"  Leagues updated: {len(leagues_added)}")
    
    if dry_run:
        print("\n[DRY-RUN] No files were modified")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich all match schedules')
    parser.add_argument('--limit', type=int, help='Process only first N matches (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without writing files')
    args = parser.parse_args()
    
    asyncio.run(enrich_all_schedules(limit=args.limit, dry_run=args.dry_run))
