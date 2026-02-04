"""
Booking Code Extractor
Handles the specific logic for Phase 2a: Harvest.
Visits a match, books a single bet, extracts the code, and saves it.
"""

import asyncio
import re
from typing import Dict, Optional, Tuple
from playwright.async_api import Page
from Neo.selector_manager import SelectorManager
from .ui import robust_click
from .slip import force_clear_slip
from Helpers.DB_Helpers.db_helpers import update_site_match_status

async def harvest_single_match_code(page: Page, match: Dict, prediction: Dict) -> bool:
    """
    Main Phase 2a (Harvest) orchestrator.
    1. Force clears slip.
    2. Navigates to match URL.
    3. Selects outcome (Market selection + Odds >= 1.20 check).
    4. Clicks "Book Bet".
    5. Extracts booking code & URL from modal.
    6. Saves to football_com_matches.csv.
    7. Force clears slip again.
    """
    url = match.get('url')
    site_match_id = match.get('site_match_id')

    print(f"\n   [Harvest] Starting harvest for: {match.get('home_team')} vs {match.get('away_team')}")
    
    # 1. Force Clear Slip (Critical start)
    await force_clear_slip(page)

    # 2. Navigate
    try:
        if page.url != url:
            await page.goto(url, timeout=60000, wait_until='domcontentloaded')
        # Wait for meaningful content
        await page.wait_for_selector(SelectorManager.get_selector_strict("fb_match_page", "market_group_header"), timeout=20000)
        await asyncio.sleep(1)
    except Exception as e:
        print(f"    [Harvest Error] Navigation failed: {e}")
        return False

    # 3. Select Outcome (with Odds check)
    outcome_found = await select_outcome(page, prediction)
    if not outcome_found:
        print(f"    [Harvest Skip] Outcome selection failed or odds < 1.20.")
        update_site_match_status(site_match_id, status="failed", details="Outcome selection failed or odds < 1.20")
        return False

    # 4. Verify Slip container visible
    slip_trigger = SelectorManager.get_selector_strict("fb_match_page", "slip_trigger_button")
    try:
        await page.wait_for_selector(slip_trigger, state="visible", timeout=5000)
    except:
        print(f"    [Harvest Warning] Slip trigger not visible after selection. Attempting booking anyway...")

    # --- BOT EVASION DELAY ---
    await asyncio.sleep(1.2)

    # 5. Book Bet & Extract
    book_btn_sel = SelectorManager.get_selector_strict("fb_match_page", "book_bet_button")
    try:
        btn = page.locator(book_btn_sel).first
        await robust_click(btn, page)
        
        # 6. Extract Code & URL
        code, booking_url = await extract_booking_info(page)
        
        if not code:
            print(f"    [Harvest Error] Failed to extract booking code.")
            update_site_match_status(site_match_id, status="failed", details="Modal code extraction failed")
            return False

        print(f"    [Harvest Success] Code Found: {code}")
        
        # Save results
        update_site_match_status(
            site_match_id, 
            status="harvested", 
            booking_code=code, 
            booking_url=booking_url
        )
        
        # 7. Dismiss and Clean
        close_sel = SelectorManager.get_selector_strict("fb_match_page", "modal_close_button")
        try:
             await page.locator(close_sel).first.click()
        except:
             await page.keyboard.press("Escape")
             
        await force_clear_slip(page)
        return True

    except Exception as e:
        print(f"    [Harvest Error] Booking stage failed: {e}")
        return False


from .mapping import find_market_and_outcome

async def expand_collapsed_market(page: Page, market_name: str):
    """If a market is found but collapsed, expand it."""
    try:
        header_sel = SelectorManager.get_selector("fb_match_page", "market_header")
        if header_sel:
             target_header = page.locator(header_sel).filter(has_text=market_name).first
             if await target_header.count() > 0:
                 print(f"    [Market] Clicking market header for '{market_name}' to ensure expansion...")
                 await robust_click(target_header, page)
                 await asyncio.sleep(1)
    except Exception as e:
        print(f"    [Market] Expansion failed: {e}")

async def select_outcome(page: Page, prediction: Dict) -> bool:
    """
    Safe outcome selection with odds check (v2.7).
    1. Maps prediction -> generic names.
    2. Searches/Locates market (expands if collapsed).
    3. Finds outcome button.
    4. Extracts odds -> skips if < 1.20.
    5. Clicks and verifies.
    """
    from .mapping import find_market_and_outcome
    
    # 1. Map Prediction
    m_name, o_name = await find_market_and_outcome(prediction)
    if not m_name:
        print(f"    [Selection Error] No mapping for pred: {prediction.get('prediction')}")
        return False

    try:
        # 2. Expand Market if needed
        # We look for the market header and click if it's not 'open'
        header_sel = SelectorManager.get_selector_strict("fb_match_page", "market_group_header")
        market_container = page.locator(header_sel).filter(has_text=m_name).first
        
        if await market_container.count() > 0:
            # Check if collapsed (often has a specific class or child icon)
            is_collapsed = await market_container.locator(".collapsed").count() > 0 or \
                           await market_container.locator(".icon-arrow-down").count() > 0
            
            if is_collapsed:
                print(f"    [Selection] Market '{m_name}' is collapsed. Expanding...")
                await robust_click(market_container, page)
                await asyncio.sleep(1)

        # 3. Locate Outcome Button & Check Odds
        # We look for a button that contains the outcome name and also extract the odds from it or near it
        btn_sel = f"button:has-text('{o_name}'), div[role='button']:has-text('{o_name}')"
        outcome_btn = page.locator(btn_sel).filter(has_text=o_name).first
        
        if await outcome_btn.count() == 0:
            print(f"    [Selection Error] Outcome button '{o_name}' not found.")
            return False

        # Extract Odds
        odds_text = await outcome_btn.inner_text()
        # regex for float numbers
        odds_match = re.search(r'(\d+\.\d+)', odds_text)
        if odds_match:
            odds_val = float(odds_match.group(1))
            if odds_val < 1.20:
                print(f"    [Selection Skip] Odds {odds_val} for '{o_name}' are < 1.20 limit.")
                return False
            print(f"    [Selection] Found odds: {odds_val} for '{o_name}'.")
        else:
             print(f"    [Selection Warning] Could not parse odds from '{odds_text}'. Proceeding with caution.")

        # 4. Click
        await robust_click(outcome_btn, page)
        await asyncio.sleep(0.5)
        
        # Simple verification: button usually changes color or gets a specific class when selected
        # But we'll rely on the slip counter verification in the main harvester
        return True

    except Exception as e:
        print(f"    [Selection Error] Logic failed: {e}")
        return False


async def extract_booking_info(page: Page) -> Tuple[str, str]:
    """
    Pulls code & URL from the Book Bet modal (v2.7).
    Returns (code, url) or ("", "") if failed.
    """
    modal_sel = SelectorManager.get_selector_strict("fb_match_page", "booking_code_modal")
    code_sel = SelectorManager.get_selector_strict("fb_match_page", "booking_code_text")
    
    try:
        # Wait for modal
        await page.wait_for_selector(modal_sel, state="visible", timeout=15000)
        
        # Extract code with retries
        code_text = ""
        for _ in range(5):
             code_text = (await page.locator(code_sel).first.inner_text(timeout=2000)).strip()
             if code_text and len(code_text) >= 5:
                 break
             await asyncio.sleep(1)
        
        if not code_text:
            return "", ""
            
        booking_url = f"https://www.football.com/ng/m?shareCode={code_text}"
        return code_text, booking_url

    except Exception as e:
        print(f"    [Extraction Error] Modal extraction failed: {e}")
        return "", ""


    return False
