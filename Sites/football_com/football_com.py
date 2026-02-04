"""
Football.com Main Orchestrator
Coordinates all sub-modules to execute the complete booking workflow.
"""

import asyncio
import os
import subprocess
import sys
from datetime import datetime as dt, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import Browser, Playwright

from Helpers.constants import WAIT_FOR_LOAD_STATE_TIMEOUT

from .navigator import load_or_create_session, navigate_to_schedule, select_target_date, extract_balance, log_page_title
from .extractor import extract_league_matches
from .matcher import match_predictions_with_site, filter_pending_predictions
from .booker.booking_code import harvest_single_match_code
from .booker.placement import place_multi_bet_from_codes
from .booker.slip import force_clear_slip

from Helpers.DB_Helpers.db_helpers import (
    PREDICTIONS_CSV, 
    update_prediction_status, 
    load_site_matches, 
    load_harvested_site_matches,
    save_site_matches, 
    update_site_match_status,
    get_site_match_id
)
from Helpers.utils import log_error_state
from Helpers.monitor import PageMonitor


async def cleanup_chrome_processes():
    """Automatically terminate conflicting Chrome processes before launch."""
    try:
        if os.name == 'nt':
            # Windows
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
            print("  [Cleanup] Cleaned up Chrome processes.")
        else:
            # Unix-like systems
            subprocess.run(["pkill", "-f", "chrome"], capture_output=True)
            print("  [Cleanup] Cleaned up Chrome processes.")
    except Exception as e:
        print(f"  [Cleanup] Warning: Could not cleanup Chrome processes: {e}")


async def launch_browser_with_retry(playwright: Playwright, user_data_dir: Path, max_retries: int = 3):
    """Launch browser with retry logic and exponential backoff."""
    base_timeout = 60000  # 60 seconds starting timeout
    backoff_multiplier = 1.2

    for attempt in range(max_retries):
        timeout = int(base_timeout * (backoff_multiplier ** attempt))
        print(f"  [Launch] Attempt {attempt + 1}/{max_retries} with {timeout}ms timeout...")

        try:
            # Simplified, faster arguments
            chrome_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-infobars",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-service-autorun",
                "--password-store=basic"
            ]

            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=False,
                args=chrome_args,
                ignore_default_args=["--enable-automation"],
                viewport={'width': 375, 'height': 612}, # iPhone X
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                timeout=timeout
            )

            print(f"  [Launch] Browser launched successfully on attempt {attempt + 1}!")
            return context

        except Exception as e:
            print(f"  [Launch] Attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                # Cleanup before next attempt
                #await cleanup_chrome_processes()

                # Remove lock files
                lock_file = user_data_dir / "SingletonLock"
                if lock_file.exists():
                    try:
                        lock_file.unlink()
                        print(f"  [Launch] Removed SingletonLock before retry.")
                    except Exception as lock_e:
                        print(f"  [Launch] Could not remove lock file: {lock_e}")

                # Wait before retry with exponential backoff
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"  [Launch] Waiting {wait_time}s before next attempt...")
                await asyncio.sleep(wait_time)
            else:
                print(f"  [Launch] All {max_retries} attempts failed.")
                raise e

def _ensure_ai_server_if_needed(predictions_missing_urls: bool):
    """Checks if AI server is needed (cache miss) and starts it."""
    try:
        from Leo import is_server_running, start_ai_server
        if predictions_missing_urls:
            if not is_server_running():
                 print("  [System] AI Server needed for Phase 2 matching. Starting...")
                 start_ai_server()
            else:
                 print("  [System] AI Server already active for Phase 2.")
    except ImportError:
        print("  [System Warning] Could not import Leo server controls. AI features may fail.")

async def run_football_com_booking(playwright: Playwright):
    """
    Main Phase 2 Orchestrator.
    """
    print("\n--- Running Football.com Booking (Phase 2) ---")
    
    # 1. Filter Predictions
    pending_predictions = await filter_pending_predictions()
    if not pending_predictions:
        print("  [Info] No pending predictions to book.")
        return

    # Group by Date
    predictions_by_date = {}
    today = dt.now().date()
    for pred in pending_predictions:
        d_str = pred.get('date')
        if d_str:
            try:
                if dt.strptime(d_str, "%d.%m.%Y").date() >= today:
                    predictions_by_date.setdefault(d_str, []).append(pred)
            except: continue
            
    if not predictions_by_date:
        print("  [Info] No future predictions found.")
        return
    
    user_data_dir = Path("DB/ChromeData_v3").absolute()
    user_data_dir.mkdir(parents=True, exist_ok=True)

    max_restarts = 1
    restarts = 0
    
    while restarts <= max_restarts:
        context = None
        page = None
        try:
            # Browser Launch
            print(f"  [System] Launching Session (Restart {restarts}/{max_restarts})...")
            context = await launch_browser_with_retry(playwright, user_data_dir)
            
            # Session & Validation
            _, page = await load_or_create_session(context)
            PageMonitor.attach_listeners(page)
            
            # 1. Balance Check
            current_balance = await extract_balance(page)
            print(f"  [Balance] Current: ₦{current_balance:.2f}")

            # 2. Process Dates
            for target_date, day_preds in sorted(predictions_by_date.items()):
                print(f"\n--- Date: {target_date} ({len(day_preds)} matches) ---")
                
                # --- STEP 1: URL RESOLUTION ---
                cached_site_matches = load_site_matches(target_date)
                matched_urls = {}
                unmatched_predictions = []

                for pred in day_preds:
                    fid = str(pred.get('fixture_id'))
                    cached_match = next((m for m in cached_site_matches if m.get('fixture_id') == fid), None)
                    if cached_match and cached_match.get('url'):
                        if cached_match.get('booking_status') != 'booked':
                             matched_urls[fid] = cached_match.get('url')
                    else:
                        unmatched_predictions.append(pred)

                if unmatched_predictions:
                    print(f"  [Registry] Resolving {len(unmatched_predictions)} unmatched URLs...")
                    _ensure_ai_server_if_needed(predictions_missing_urls=True) 
                    await navigate_to_schedule(page)
                    if await select_target_date(page, target_date):
                        site_matches = await extract_league_matches(page, target_date)
                        if site_matches:
                            save_site_matches(site_matches)
                            cached_site_matches = load_site_matches(target_date)
                            new_mappings = await match_predictions_with_site(unmatched_predictions, cached_site_matches)
                            for fid, url in new_mappings.items():
                                matched_urls[fid] = url
                                site_match = next((m for m in cached_site_matches if m.get('url') == url), None)
                                if site_match:
                                    update_site_match_status(site_match['site_match_id'], 'pending', fixture_id=fid)

                if not matched_urls:
                    continue

                # --- STEP 2: HARVEST PHASE ---
                print(f"  [Phase 2a] Entering Harvest for {len(matched_urls)} matches...")
                
                for match_id, match_url in matched_urls.items():
                    pred = next((p for p in day_preds if str(p['fixture_id']) == str(match_id)), None)
                    if not pred: continue

                    match_dict = {
                        'url': match_url, 
                        'site_match_id': get_site_match_id(target_date, pred['home_team'], pred['away_team']),
                        'home_team': pred['home_team'], 'away_team': pred['away_team']
                    }
                    
                    # Check if already harvested
                    matches_now = load_site_matches(target_date)
                    existing_m = next((m for m in matches_now if m['site_match_id'] == match_dict['site_match_id']), None)
                    if existing_m and existing_m.get('booking_status') == 'harvested':
                         continue

                    # Execute Harvest
                    await harvest_single_match_code(page, match_dict, pred)
                
                # --- STEP 3: EXECUTE PHASE ---
                harvested_matches = load_harvested_site_matches(target_date)
                if harvested_matches:
                    print(f"  [Phase 2b] Entering Execution for {len(harvested_matches)} selections...")
                    success = await place_multi_bet_from_codes(page, harvested_matches, current_balance)
                    if success:
                        print(f"  [Execute] Multi-bet placed successfully for {target_date}!")
                else:
                    print("  [Execute] No harvested matches available to place multi-bet for this date.")

            # If we reached here without raising FatalSessionError, we are done
            break

        except Exception as e:
            # Check for our specific fatal error
            is_fatal = "FatalSessionError" in str(type(e)) or "dirty" in str(e).lower()
            
            if is_fatal and restarts < max_restarts:
                print(f"\n[!!!] FATAL SESSION ERROR: {e}")
                print(f"[!!!] Resetting session and restarting browser (Attempt {restarts+1}/{max_restarts})...")
                restarts += 1
                if context: await context.close()
                await asyncio.sleep(5)
                continue # Retry while loop
            else:
                await log_error_state(page, "phase2_fatal", e)
                print(f"  [CRITICAL] Phase 2 failed: {e}")
                break # Exit while loop
        
        finally:
            if context: await context.close()
