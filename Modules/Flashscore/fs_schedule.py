# fs_schedule.py: Daily match list extraction for Flashscore.
# Part of LeoBook Modules — Flashscore
#
# Delegates to fs_extractor for ALL-tab extraction. Handles DB save + cloud sync.

from datetime import datetime as dt
from playwright.async_api import Page
from Data.Access.db_helpers import (
    batch_upsert, SCHEDULES_CSV, TEAMS_CSV, files_and_headers
)
from Data.Access.sync_manager import SyncManager
from Modules.Flashscore.fs_extractor import expand_all_leagues, extract_all_matches


async def extract_matches_from_page(page: Page) -> list:
    """
    Extracts ALL matches from the ALL tab, expands collapsed leagues first.
    Saves schedule entries + teams locally via batch upsert (single read/write).
    """
    print("    [Extractor] Extracting match data from ALL tab...")

    expanded = await expand_all_leagues(page)
    if expanded:
        print(f"    [Extractor] Bulk-expanded {expanded} collapsed leagues.")

    matches = await extract_all_matches(page, label="Extractor")

    if matches:
        print(f"    [Extractor] Pairings complete. Saving {len(matches)} fixtures and teams...")

        # Build schedule rows for batch upsert
        now = dt.now().isoformat()
        schedule_rows = []
        team_rows = []
        seen_teams = set()

        for m in matches:
            schedule_rows.append({
                'fixture_id': m.get('fixture_id'),
                'date': m.get('date', ''),
                'match_time': m.get('match_time', ''),
                'region_league': m.get('region_league', ''),
                'league_id': m.get('league_id', ''),
                'home_team': m.get('home_team', ''),
                'away_team': m.get('away_team', ''),
                'home_team_id': m.get('home_team_id', ''),
                'away_team_id': m.get('away_team_id', ''),
                'home_score': m.get('home_score', ''),
                'away_score': m.get('away_score', ''),
                'match_status': m.get('status', 'scheduled'),
                'match_link': m.get('match_link', ''),
                'last_updated': now
            })

            region = m['region_league'].split(' - ')[0] if ' - ' in m['region_league'] else 'Unknown'
            for prefix, name_key in [('home', 'home_team'), ('away', 'away_team')]:
                tid = m.get(f'{prefix}_team_id') or f"t_{hash(m[name_key]) & 0xfffffff}"
                if tid not in seen_teams:
                    seen_teams.add(tid)
                    team_rows.append({
                        'team_id': tid,
                        'team_name': m[name_key],
                        'rl_ids': region,
                        'team_crest': '',
                        'team_url': '',
                        'last_updated': now
                    })

        # Single read + write per file (instead of 1900 individual upserts)
        batch_upsert(SCHEDULES_CSV, schedule_rows, files_and_headers[SCHEDULES_CSV], 'fixture_id')
        batch_upsert(TEAMS_CSV, team_rows, files_and_headers[TEAMS_CSV], 'team_id')
        print(f"    [Extractor] Saved {len(schedule_rows)} schedules + {len(team_rows)} teams.")

        # Cloud sync
        sync = SyncManager()
        if sync.supabase:
            print(f"    [Cloud] Upserting {len(schedule_rows)} schedules and {len(team_rows)} teams...")
            await sync.batch_upsert('schedules', schedule_rows)
            await sync.batch_upsert('teams', team_rows)
            print(f"    [SUCCESS] Multi-table synchronization complete.")

    return matches
