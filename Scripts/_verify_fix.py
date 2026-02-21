"""Verify the fix: simulate what build_search_dict.py would count after the changes."""
import csv

def is_field_empty(value):
    v = (value or '').strip().lower()
    return v in ('', 'none', 'null', 'unknown', '[]')

TEAMS_CSV = "Data/Store/teams.csv"
REGION_LEAGUE_CSV = "Data/Store/region_league.csv"

# --- Teams ---
TEAM_CRITICAL_FIELDS = ['country', 'city']  # NEW (was: country, city, stadium, team_crest)
fully_enriched = 0
incomplete = 0
empty = 0
with open(TEAMS_CSV, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        st = row.get('search_terms', '').strip()
        tid = row.get('team_id', '').strip()
        if not tid: continue
        if st and st != '[]':
            missing = [fld for fld in TEAM_CRITICAL_FIELDS if is_field_empty(row.get(fld, ''))]
            if missing:
                incomplete += 1
            else:
                fully_enriched += 1
        else:
            empty += 1

total_teams = fully_enriched + incomplete + empty
print(f"=== TEAMS (new critical: {TEAM_CRITICAL_FIELDS}) ===")
print(f"[PASS 1] Empty (no search_terms): {empty}")
print(f"[PASS 2] Incomplete:              {incomplete}")
print(f"[SKIP]   Fully enriched:          {fully_enriched}")
print(f"Total:                            {total_teams}")

# --- Leagues ---
LEAGUE_CRITICAL_FIELDS = ['country']  # NEW (was: country, logo_url)
fully_enriched_l = 0
incomplete_l = 0
empty_l = 0
with open(REGION_LEAGUE_CSV, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        rl_id = row.get('rl_id', '').strip()
        if not rl_id: continue
        st = row.get('search_terms', '').strip()
        if st and st != '[]':
            missing = [fld for fld in LEAGUE_CRITICAL_FIELDS if is_field_empty(row.get(fld, ''))]
            if missing:
                incomplete_l += 1
            else:
                fully_enriched_l += 1
        else:
            empty_l += 1

total_l = fully_enriched_l + incomplete_l + empty_l
print(f"\n=== LEAGUES (new critical: {LEAGUE_CRITICAL_FIELDS}) ===")
print(f"[PASS 1] Empty (no search_terms): {empty_l}")
print(f"[PASS 2] Incomplete:              {incomplete_l}")
print(f"[SKIP]   Fully enriched:          {fully_enriched_l}")
print(f"Total:                            {total_l}")
