# fs_live_streamer.py: Continuous live score streaming from Flashscore LIVE tab.
# Runs in parallel with the main Leo cycle via asyncio.create_task().
# v2: Also scrapes FINISHED tab for terminal statuses (Pen, AET, Canc).
#     Purges stale entries from live_scores on every cycle.

"""
Live Score Streamer
Scrapes the Flashscore LIVE tab every 60 seconds using its own browser context.
Also scrapes the FINISHED tab to resolve terminal match statuses.
Saves results to live_scores.csv and upserts to Supabase.
Propagates live/finished status to schedules.csv and predictions.csv.
Purges matches no longer live from live_scores.csv and Supabase.
"""

import asyncio
import csv
import os
from datetime import datetime as dt, timedelta
from playwright.async_api import Playwright

from Data.Access.db_helpers import (
    save_live_score_entry, log_audit_event,
    SCHEDULES_CSV, PREDICTIONS_CSV, LIVE_SCORES_CSV,
    files_and_headers
)
from Data.Access.sync_manager import SyncManager
from Core.Browser.site_helpers import fs_universal_popup_dismissal
from Core.Utils.constants import NAVIGATION_TIMEOUT, WAIT_FOR_LOAD_STATE_TIMEOUT

STREAM_INTERVAL = 60  # seconds
FLASHSCORE_URL = "https://www.flashscore.com/football/"


# ---------------------------------------------------------------------------
# CSV helper: read all rows from a CSV
# ---------------------------------------------------------------------------
def _read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _write_csv(path, rows, fieldnames):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Status propagation: update schedules + predictions when matches go live/finish
# ---------------------------------------------------------------------------
def _compute_outcome_correct(prediction_str, home_score, away_score):
    """Check if a prediction was correct given the final score."""
    try:
        hs = int(home_score)
        aws = int(away_score)
    except (ValueError, TypeError):
        return ''
    p = (prediction_str or '').lower()
    if 'home win' in p:
        return 'True' if hs > aws else 'False'
    if 'away win' in p:
        return 'True' if aws > hs else 'False'
    if 'draw' in p:
        return 'True' if hs == aws else 'False'
    if 'over 2.5' in p:
        return 'True' if (hs + aws) > 2 else 'False'
    if 'under 2.5' in p:
        return 'True' if (hs + aws) < 3 else 'False'
    if 'btts' in p or 'both teams to score' in p:
        return 'True' if hs > 0 and aws > 0 else 'False'
    return ''


def _propagate_status_updates(live_matches: list, finished_matches: list = None):
    """
    Propagate live scores and finished results into schedules.csv and predictions.csv.
    1. Mark matching fixtures as 'live' with current score.
    2. Mark finished matches with their terminal status.
    3. Detect fixtures past 2.5hrs with no live/finish signal → mark 'finished'.
    """
    finished_matches = finished_matches or []
    live_ids = {m['fixture_id'] for m in live_matches}
    live_map = {m['fixture_id']: m for m in live_matches}
    finished_ids = {m['fixture_id'] for m in finished_matches}
    finished_map = {m['fixture_id']: m for m in finished_matches}
    now = dt.now()

    # --- Update schedules.csv ---
    sched_headers = files_and_headers.get(SCHEDULES_CSV, [])
    sched_rows = _read_csv(SCHEDULES_CSV)
    sched_changed = False
    for row in sched_rows:
        fid = row.get('fixture_id', '')

        # Live match
        if fid in live_ids:
            lm = live_map[fid]
            if row.get('status', '').lower() != 'live':
                row['status'] = 'live'
                sched_changed = True
            if lm.get('home_score'):
                row['home_score'] = lm['home_score']
                row['away_score'] = lm['away_score']
                sched_changed = True

        # Finished match (from FINISHED tab)
        elif fid in finished_ids:
            fm = finished_map[fid]
            terminal_status = fm.get('status', 'finished')
            if row.get('status', '').lower() != terminal_status:
                row['status'] = terminal_status
                row['home_score'] = fm.get('home_score', row.get('home_score', ''))
                row['away_score'] = fm.get('away_score', row.get('away_score', ''))
                if fm.get('stage_detail'):
                    row['stage_detail'] = fm['stage_detail']
                sched_changed = True

        # Was live but now gone — time-based fallback
        elif row.get('status', '').lower() == 'live' and fid not in live_ids:
            try:
                match_time_str = f"{row.get('date','2000-01-01')}T{row.get('match_time','00:00')}:00"
                match_start = dt.fromisoformat(match_time_str)
                if now > match_start + timedelta(minutes=150):
                    row['status'] = 'finished'
                    sched_changed = True
            except Exception:
                pass

    sched_updates = []
    if sched_changed:
        _write_csv(SCHEDULES_CSV, sched_rows, sched_headers)
        sched_updates = [r for r in sched_rows if r.get('fixture_id') in (live_ids | finished_ids)]

    # --- Update predictions.csv ---
    pred_headers = files_and_headers.get(PREDICTIONS_CSV, [])
    pred_rows = _read_csv(PREDICTIONS_CSV)
    pred_changed = False
    pred_updates = []
    
    for row in pred_rows:
        fid = row.get('fixture_id', '')
        cur_status = row.get('status', row.get('match_status', '')).lower()

        # Live match
        if fid in live_ids:
            lm = live_map[fid]
            row_changed = False
            if cur_status != 'live':
                row['status'] = 'live'
                row_changed = True
            
            new_hs = lm.get('home_score', '')
            new_as = lm.get('away_score', '')
            if row.get('home_score') != new_hs or row.get('away_score') != new_as:
                row['home_score'] = new_hs
                row['away_score'] = new_as
                row['actual_score'] = f"{new_hs}-{new_as}"
                row_changed = True
            
            if row_changed:
                pred_changed = True
                pred_updates.append(row)

        # Finished match (from FINISHED tab)
        elif fid in finished_ids:
            fm = finished_map[fid]
            terminal_status = fm.get('status', 'finished')
            if cur_status != terminal_status:
                row['status'] = terminal_status
                row['home_score'] = fm.get('home_score', row.get('home_score', ''))
                row['away_score'] = fm.get('away_score', row.get('away_score', ''))
                row['actual_score'] = f"{fm.get('home_score', '')}-{fm.get('away_score', '')}"
                if fm.get('stage_detail'):
                    row['stage_detail'] = fm['stage_detail']
                # Compute outcome_correct for finished matches
                oc = _compute_outcome_correct(
                    row.get('prediction', ''),
                    row.get('home_score', ''),
                    row.get('away_score', '')
                )
                if oc:
                    row['outcome_correct'] = oc
                pred_changed = True
                pred_updates.append(row)

        # Was live but gone — time-based fallback
        elif cur_status == 'live' and fid not in live_ids:
            try:
                date_val = row.get('date', '2000-01-01')
                time_val = row.get('match_time', '00:00')
                match_start = dt.fromisoformat(f"{date_val}T{time_val}:00")
                if now > match_start + timedelta(minutes=150):
                    row['status'] = 'finished'
                    oc = _compute_outcome_correct(
                        row.get('prediction', ''),
                        row.get('home_score', ''),
                        row.get('away_score', '')
                    )
                    if oc:
                        row['outcome_correct'] = oc
                    pred_changed = True
                    pred_updates.append(row)
            except Exception:
                pass
    if pred_changed:
        _write_csv(PREDICTIONS_CSV, pred_rows, pred_headers)
        
    return sched_updates, pred_updates


# ---------------------------------------------------------------------------
# Purge stale live_scores: remove matches no longer in the LIVE tab
# ---------------------------------------------------------------------------
def _purge_stale_live_scores(current_live_ids: set):
    """
    Remove any fixture from live_scores.csv that is NOT in the current LIVE set.
    Returns the set of stale fixture_ids that were removed.
    """
    live_headers = files_and_headers.get(LIVE_SCORES_CSV, [])
    existing_rows = _read_csv(LIVE_SCORES_CSV)
    if not existing_rows:
        return set()
    
    existing_ids = {r.get('fixture_id', '') for r in existing_rows}
    stale_ids = existing_ids - current_live_ids
    
    if stale_ids:
        kept_rows = [r for r in existing_rows if r.get('fixture_id', '') not in stale_ids]
        _write_csv(LIVE_SCORES_CSV, kept_rows, live_headers)
    
    return stale_ids


# ---------------------------------------------------------------------------
# JS: Expand all collapsed league headers
# ---------------------------------------------------------------------------
EXPAND_COLLAPSED_JS = """() => {
    const buttons = document.querySelectorAll('.wcl-accordion_7Fi80');
    let clicked = 0;
    buttons.forEach(btn => {
        const parent = btn.closest('.wcl-trigger_CGiIV');
        if (parent && parent.getAttribute('data-state') === 'delayed-open') {
            btn.click();
            clicked++;
        }
    });
    return clicked;
}"""


# ---------------------------------------------------------------------------
# Flashscore LIVE tab extraction
# ---------------------------------------------------------------------------
async def _extract_live_matches(page) -> list:
    """
    Extracts all live matches from the currently visible LIVE tab.
    Expands collapsed league headers first.
    """
    # Expand collapsed headers
    try:
        expanded = await page.evaluate(EXPAND_COLLAPSED_JS)
        if expanded:
            print(f"   [Streamer] Expanded {expanded} collapsed league headers (LIVE)")
            await asyncio.sleep(1)
    except Exception:
        pass

    matches = await page.evaluate(r"""() => {
        const matches = [];
        const container = document.querySelector('.sportName.soccer') || document.body;
        if (!container) return [];

        const allElements = container.querySelectorAll(
            '.headerLeague__wrapper, .event__match--live'
        );

        let currentRegion = '';
        let currentLeague = '';

        allElements.forEach((el) => {
            if (el.classList.contains('headerLeague__wrapper')) {
                const catEl = el.querySelector('.headerLeague__category-text');
                const titleEl = el.querySelector('.headerLeague__title-text');
                currentRegion = catEl ? catEl.innerText.trim() : '';
                currentLeague = titleEl ? titleEl.innerText.trim() : '';
                return;
            }

            if (el.classList.contains('event__match--live')) {
                const rowId = el.getAttribute('id');
                const cleanId = rowId ? rowId.replace('g_1_', '') : null;
                if (!cleanId) return;

                const homeNameEl = el.querySelector('.event__homeParticipant .wcl-name_jjfMf');
                const awayNameEl = el.querySelector('.event__awayParticipant .wcl-name_jjfMf');
                const homeScoreEl = el.querySelector('span.event__score--home');
                const awayScoreEl = el.querySelector('span.event__score--away');
                const stageEl = el.querySelector('.event__stage--block');
                const linkEl = el.querySelector('a.eventRowLink');

                if (homeNameEl && awayNameEl) {
                    let minute = stageEl ? stageEl.innerText.trim().replace(/\s+/g, '') : '';

                    let status = 'live';
                    const minuteLower = minute.toLowerCase();
                    if (minuteLower.includes('half')) status = 'halftime';
                    else if (minuteLower.includes('break')) status = 'break';
                    else if (minuteLower.includes('pen')) status = 'penalties';
                    else if (minuteLower.includes('et')) status = 'extra_time';

                    const regionLeague = currentRegion
                        ? currentRegion + ' - ' + currentLeague
                        : currentLeague || 'Unknown';

                    matches.push({
                        fixture_id: cleanId,
                        home_team: homeNameEl.innerText.trim(),
                        away_team: awayNameEl.innerText.trim(),
                        home_score: homeScoreEl ? homeScoreEl.innerText.trim() : '0',
                        away_score: awayScoreEl ? awayScoreEl.innerText.trim() : '0',
                        minute: minute,
                        status: status,
                        region_league: regionLeague,
                        match_link: linkEl ? linkEl.getAttribute('href') : '',
                        timestamp: new Date().toISOString()
                    });
                }
            }
        });
        return matches;
    }""")
    return matches or []


# ---------------------------------------------------------------------------
# Flashscore FINISHED tab extraction
# ---------------------------------------------------------------------------
async def _extract_finished_matches(page) -> list:
    """
    Extracts all finished matches from the FINISHED tab.
    Captures terminal statuses: Pen (penalties), AET (after extra time),
    Canc (cancelled), or normal FT.
    Expands collapsed league headers first.
    """
    # Expand collapsed headers
    try:
        expanded = await page.evaluate(EXPAND_COLLAPSED_JS)
        if expanded:
            print(f"   [Streamer] Expanded {expanded} collapsed league headers (FINISHED)")
            await asyncio.sleep(1)
    except Exception:
        pass

    matches = await page.evaluate(r"""() => {
        const matches = [];
        const container = document.querySelector('.sportName.soccer') || document.body;
        if (!container) return [];

        // Finished matches don't have --live, they use generic event__match rows
        // We look for rows that have a final score (wcl-isFinal)
        const allElements = container.querySelectorAll(
            '.headerLeague__wrapper, .event__match'
        );

        let currentRegion = '';
        let currentLeague = '';

        allElements.forEach((el) => {
            if (el.classList.contains('headerLeague__wrapper')) {
                const catEl = el.querySelector('.headerLeague__category-text');
                const titleEl = el.querySelector('.headerLeague__title-text');
                currentRegion = catEl ? catEl.innerText.trim() : '';
                currentLeague = titleEl ? titleEl.innerText.trim() : '';
                return;
            }

            // Skip live matches (they belong to the LIVE tab)
            if (el.classList.contains('event__match--live')) return;

            const rowId = el.getAttribute('id');
            const cleanId = rowId ? rowId.replace('g_1_', '') : null;
            if (!cleanId) return;

            // Check for final scores
            const homeScoreEl = el.querySelector('span.event__score--home');
            const awayScoreEl = el.querySelector('span.event__score--away');
            if (!homeScoreEl || !awayScoreEl) return;

            // Only process if score state is "final"
            const scoreState = homeScoreEl.getAttribute('data-state');
            if (scoreState !== 'final') return;

            const homeNameEl = el.querySelector('.event__homeParticipant .wcl-name_jjfMf');
            const awayNameEl = el.querySelector('.event__awayParticipant .wcl-name_jjfMf');
            if (!homeNameEl || !awayNameEl) return;

            // Stage detail: "Pen", "AET", "Canc", etc.
            const stageEl = el.querySelector('.event__stage--block');
            const stageText = stageEl ? stageEl.innerText.trim() : '';
            const stageLower = stageText.toLowerCase();

            let status = 'finished';
            let stageDetail = '';
            if (stageLower.includes('pen')) { status = 'finished'; stageDetail = 'Pen'; }
            else if (stageLower.includes('aet') || stageLower.includes('et')) { status = 'finished'; stageDetail = 'AET'; }
            else if (stageLower.includes('canc')) { status = 'cancelled'; stageDetail = 'Canc'; }
            else if (stageLower.includes('abn') || stageLower.includes('abd')) { status = 'cancelled'; stageDetail = 'Abn'; }
            else if (stageLower.includes('wo') || stageLower.includes('w.o')) { status = 'finished'; stageDetail = 'WO'; }

            const linkEl = el.querySelector('a.eventRowLink');
            const regionLeague = currentRegion
                ? currentRegion + ' - ' + currentLeague
                : currentLeague || 'Unknown';

            // Regulation scores (part elements)
            const regHomeEl = el.querySelector('.event__part--home.event__part--regulation');
            const regAwayEl = el.querySelector('.event__part--away.event__part--regulation');

            matches.push({
                fixture_id: cleanId,
                home_team: homeNameEl.innerText.trim(),
                away_team: awayNameEl.innerText.trim(),
                home_score: homeScoreEl.innerText.trim(),
                away_score: awayScoreEl.innerText.trim(),
                home_score_reg: regHomeEl ? regHomeEl.innerText.trim() : '',
                away_score_reg: regAwayEl ? regAwayEl.innerText.trim() : '',
                status: status,
                stage_detail: stageDetail,
                region_league: regionLeague,
                match_link: linkEl ? linkEl.getAttribute('href') : '',
                timestamp: new Date().toISOString()
            });
        });
        return matches;
    }""")
    return matches or []


# ---------------------------------------------------------------------------
# Tab clicking helpers
# ---------------------------------------------------------------------------
async def _click_live_tab(page) -> bool:
    """Clicks the LIVE tab on the Flashscore football page."""
    try:
        tab = page.locator('.filters__tab[data-analytics-alias="live"]')
        if await tab.count() > 0:
            await tab.first.click()
            await asyncio.sleep(2)
            return True
    except Exception:
        pass
    try:
        await page.get_by_text("LIVE", exact=False).first.click()
        await asyncio.sleep(2)
        return True
    except Exception:
        return False


async def _click_finished_tab(page) -> bool:
    """Clicks the FINISHED tab on the Flashscore football page."""
    try:
        tab = page.locator('.filters__tab[data-analytics-alias="finished"]')
        if await tab.count() > 0:
            await tab.first.click()
            await asyncio.sleep(2)
            return True
    except Exception:
        pass
    try:
        await page.get_by_text("FINISHED", exact=False).first.click()
        await asyncio.sleep(2)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Main streaming loop
# ---------------------------------------------------------------------------
async def live_score_streamer(playwright: Playwright):
    """
    Main streaming loop. Runs independently in its own browser context.
    Scrapes LIVE + FINISHED tabs every 60 seconds and saves results.
    Purges stale entries from live_scores every cycle.
    Never crashes — errors are logged and retried.
    """
    print("\n   [Streamer] 🔴 Live Score Streamer starting...")
    log_audit_event("STREAMER_START", "Live score streamer initialized (v2: LIVE+FINISHED).")

    browser = None
    try:
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu"]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timezone_id="Africa/Lagos"
        )
        page = await context.new_page()

        # Initial navigation
        print("   [Streamer] Navigating to Flashscore...")
        await page.goto(FLASHSCORE_URL, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        await fs_universal_popup_dismissal(page, "fs_home_page")

        # Click LIVE tab
        if not await _click_live_tab(page):
            print("   [Streamer] ⚠ Could not find LIVE tab. Will retry on next cycle.")

        sync = SyncManager()
        cycle = 0

        while True:
            cycle += 1
            try:
                # Refresh the page periodically (every 10 cycles = ~10 min)
                if cycle % 10 == 0:
                    await page.reload(wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT)
                    await asyncio.sleep(3)
                    await fs_universal_popup_dismissal(page, "fs_home_page")
                    await _click_live_tab(page)

                # ── PHASE 1: LIVE TAB ──
                await _click_live_tab(page)
                live_matches = await _extract_live_matches(page)
                now = dt.now().strftime("%H:%M:%S")
                current_live_ids = {m['fixture_id'] for m in live_matches}

                # ── PHASE 2: FINISHED TAB ──
                finished_matches = []
                if await _click_finished_tab(page):
                    await asyncio.sleep(1)
                    finished_matches = await _extract_finished_matches(page)
                    # Switch back to LIVE for next cycle
                    await _click_live_tab(page)

                # ── PHASE 3: PURGE STALE LIVE SCORES ──
                stale_ids = _purge_stale_live_scores(current_live_ids)
                if stale_ids:
                    print(f"   [Streamer] 🧹 Purged {len(stale_ids)} stale entries from live_scores")

                # ── PHASE 4: PROCESS & SYNC ──
                if live_matches or finished_matches:
                    parts = []
                    if live_matches:
                        parts.append(f"{len(live_matches)} live")
                    if finished_matches:
                        parts.append(f"{len(finished_matches)} finished")
                    print(f"   [Streamer] {now} — {', '.join(parts)} (cycle {cycle})")

                    # Save live matches locally
                    for m in live_matches:
                        save_live_score_entry(m)

                    # Propagate status to schedules + predictions
                    sched_upd, pred_upd = _propagate_status_updates(live_matches, finished_matches)

                    # Sync everything to Supabase
                    if sync.supabase:
                        try:
                            # 1. Push raw live scores
                            if live_matches:
                                await sync.batch_upsert('live_scores', live_matches)
                            # 2. Purge stale live scores from Supabase
                            if stale_ids:
                                try:
                                    sync.supabase.table('live_scores').delete().in_(
                                        'fixture_id', list(stale_ids)
                                    ).execute()
                                except Exception as e:
                                    print(f"   [Streamer] Stale purge sync error: {e}")
                            # 3. Push modified predictions (for Realtime listeners)
                            if pred_upd:
                                await sync.batch_upsert('predictions', pred_upd)
                            # 4. Push modified schedules
                            if sched_upd:
                                await sync.batch_upsert('schedules', sched_upd)
                        except Exception as e:
                            print(f"   [Streamer] Cloud sync error: {e}")
                else:
                    # Even with no live/finished, check time-based transitions
                    sched_upd, pred_upd = _propagate_status_updates([], [])
                    
                    if sync.supabase and (pred_upd or sched_upd):
                        try:
                            if pred_upd:
                                await sync.batch_upsert('predictions', pred_upd)
                            if sched_upd:
                                await sync.batch_upsert('schedules', sched_upd)
                        except Exception as e:
                            print(f"   [Streamer] Cloud sync error (empty): {e}")

                    # Purge stale even when no live matches
                    if stale_ids and sync.supabase:
                        try:
                            sync.supabase.table('live_scores').delete().in_(
                                'fixture_id', list(stale_ids)
                            ).execute()
                        except Exception:
                            pass

                    if cycle % 5 == 1:
                        print(f"   [Streamer] {now} — No live matches (cycle {cycle})")

            except Exception as e:
                print(f"   [Streamer] ⚠ Extraction error (cycle {cycle}): {e}")
                try:
                    await page.goto(FLASHSCORE_URL, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
                    await asyncio.sleep(3)
                    await fs_universal_popup_dismissal(page, "fs_home_page")
                    await _click_live_tab(page)
                except Exception:
                    pass

            await asyncio.sleep(STREAM_INTERVAL)

    except asyncio.CancelledError:
        print("   [Streamer] Streamer cancelled.")
    except Exception as e:
        print(f"   [Streamer] Fatal error: {e}")
        log_audit_event("STREAMER_ERROR", f"Fatal: {e}", status="failed")
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        print("   [Streamer] 🔴 Streamer stopped.")
