# fs_schedule.py: Daily match list extraction for Flashscore.
# Part of LeoBook Modules — Flashscore
#
# Delegates to fs_extractor for ALL-tab extraction. Handles DB save + cloud sync.

from playwright.async_api import Page
from Data.Access.db_helpers import save_schedule_entry, save_team_entry
from Data.Access.sync_manager import SyncManager
from Modules.Flashscore.fs_extractor import expand_all_leagues, extract_all_matches


async def extract_matches_from_page(page: Page) -> list:
    """
    Extracts ALL matches from the ALL tab, expands collapsed leagues first.
    Saves schedule entries + teams locally and syncs to cloud.
    """
    print("    [Extractor] Extracting match data from ALL tab...")

    expanded = await expand_all_leagues(page)
    if expanded:
        print(f"    [Extractor] Bulk-expanded {expanded} collapsed leagues.")

    matches = await extract_all_matches(page, label="Extractor")

    # Local Save + Supabase Upsert
    if matches:
        print(f"    [Extractor] Pairings complete. Saving {len(matches)} fixtures and teams...")
        sync = SyncManager()

        teams_to_sync = []
        for m in matches:
            save_schedule_entry(m)

            home_team = {
                'team_id': m.get('home_team_id') or f"t_{hash(m['home_team']) & 0xfffffff}",
                'team_name': m['home_team'],
                'region': m['region_league'].split(' - ')[0] if ' - ' in m['region_league'] else 'Unknown'
            }
            away_team = {
                'team_id': m.get('away_team_id') or f"t_{hash(m['away_team']) & 0xfffffff}",
                'team_name': m['away_team'],
                'region': m['region_league'].split(' - ')[0] if ' - ' in m['region_league'] else 'Unknown'
            }

            save_team_entry(home_team)
            save_team_entry(away_team)
            teams_to_sync.extend([home_team, away_team])

        if sync.supabase:
            print(f"    [Cloud] Upserting {len(matches)} schedules and {len(teams_to_sync)} teams...")
            await sync.batch_upsert('schedules', matches)
            unique_teams = list({t['team_id']: t for t in teams_to_sync}.values())
            await sync.batch_upsert('teams', unique_teams)
            print(f"    [SUCCESS] Multi-table synchronization complete.")

    return matches
