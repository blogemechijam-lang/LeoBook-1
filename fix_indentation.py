#!/usr/bin/env python3
"""Fix indentation error in matcher.py"""

# Read the current file
with open('Sites/football_com/matcher.py', 'r') as f:
    content = f.read()

# Fix the indentation error in the validation loop
content = content.replace(
    """    for m in site_matches:
            # Handle both DB format (home_team/away_team) and matcher format (home/away)
            h = m.get('home', '') or m.get('home_team', '')
            a = m.get('away', '') or m.get('away_team', '')
            h = h.strip() if h else ''
            a = a.strip() if a else ''
        if len(h) < 2 or len(a) < 2:
            continue""",
    """    for m in site_matches:
            # Handle both DB format (home_team/away_team) and matcher format (home/away)
            h = m.get('home', '') or m.get('home_team', '')
            a = m.get('away', '') or m.get('away_team', '')
            h = h.strip() if h else ''
            a = a.strip() if a else ''
            if len(h) < 2 or len(a) < 2:
                continue"""
)

# Remove duplicate line
content = content.replace(
    """            site_away = site_away.strip()
            site_away = site_match.get('away', '').strip()""",
    """            site_away = site_away.strip()"""
)

# Write back the file
with open('Sites/football_com/matcher.py', 'w') as f:
    f.write(content)

print("Fixed indentation error in matcher.py")
