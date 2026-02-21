"""Quick analysis of region_league.csv to find what's missing."""
import csv

REGION_LEAGUE_CSV = "Data/Store/region_league.csv"
LEAGUE_CRITICAL_FIELDS = ['country', 'logo_url']

rows = list(csv.DictReader(open(REGION_LEAGUE_CSV, 'r', encoding='utf-8')))
print(f"Total rows in region_league.csv: {len(rows)}")

# Rows with search_terms
st_rows = [r for r in rows if r.get('search_terms', '').strip() and r.get('search_terms', '').strip() != '[]']
no_st_rows = [r for r in rows if not r.get('search_terms', '').strip() or r.get('search_terms', '').strip() == '[]']
print(f"Rows WITH search_terms: {len(st_rows)}")
print(f"Rows WITHOUT search_terms: {len(no_st_rows)}")

# What's missing in st_rows?
missing_country = [r for r in st_rows if not r.get('country', '').strip()]
missing_logo = [r for r in st_rows if not r.get('logo_url', '').strip() or r.get('logo_url', '').strip() == 'None']
missing_both = [r for r in st_rows if (not r.get('country', '').strip()) and (not r.get('logo_url', '').strip() or r.get('logo_url', '').strip() == 'None')]

print(f"\n--- Breakdown of 'incomplete' (has search_terms) ---")
print(f"Missing country: {len(missing_country)}")
print(f"Missing logo_url: {len(missing_logo)}")
print(f"Missing BOTH: {len(missing_both)}")
print(f"Missing country ONLY (has logo): {len(missing_country) - len(missing_both)}")
print(f"Missing logo_url ONLY (has country): {len(missing_logo) - len(missing_both)}")

# Fully enriched = has search_terms AND has country AND has logo_url
fully = [r for r in st_rows if r.get('country', '').strip() and r.get('logo_url', '').strip() and r.get('logo_url', '').strip() != 'None']
print(f"\nFully enriched (search_terms + country + logo_url): {len(fully)}")

# Show some examples of logo_url values that ARE None-string vs empty
print("\n--- First 15 missing logo_url (has country) ---")
logo_only_missing = [r for r in st_rows if r.get('country', '').strip() and (not r.get('logo_url', '').strip() or r.get('logo_url', '').strip() == 'None')]
for r in logo_only_missing[:15]:
    print(f"  league={r.get('league', '?'):<40} country={r.get('country', '?'):<15} logo_url={repr(r.get('logo_url', ''))}")

print("\n--- First 5 missing country ---")
for r in missing_country[:5]:
    print(f"  league={r.get('league', '?'):<40} country={repr(r.get('country', '')):<15} logo_url={repr(r.get('logo_url', ''))}")

# Check what Grok returns as 'None' vs null vs empty
print(f"\n--- logo_url value distribution (enriched rows) ---")
from collections import Counter
logo_vals = Counter()
for r in st_rows:
    v = r.get('logo_url', '')
    if not v or v.strip() == '':
        logo_vals['<empty>'] += 1
    elif v.strip() == 'None':
        logo_vals['None-string'] += 1
    elif v.strip() == 'null':
        logo_vals['null-string'] += 1
    elif v.strip().startswith('http'):
        logo_vals['valid-url'] += 1
    else:
        logo_vals[f'other: {v[:30]}'] += 1
for k, v in logo_vals.most_common():
    print(f"  {k}: {v}")
