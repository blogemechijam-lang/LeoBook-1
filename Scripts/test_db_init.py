import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Data.Access.db_helpers import init_csvs, REGION_LEAGUE_CSV, TEAMS_CSV

print(f"Testing CSV paths:")
print(f"REGION_LEAGUE_CSV: {REGION_LEAGUE_CSV}")
print(f"TEAMS_CSV: {TEAMS_CSV}")

init_csvs()

if os.path.exists(REGION_LEAGUE_CSV):
    print(f"SUCCESS: {os.path.basename(REGION_LEAGUE_CSV)} created.")
else:
    print(f"FAILURE: {os.path.basename(REGION_LEAGUE_CSV)} NOT created.")

if os.path.exists(TEAMS_CSV):
    print(f"SUCCESS: {os.path.basename(TEAMS_CSV)} created.")
else:
    print(f"FAILURE: {os.path.basename(TEAMS_CSV)} NOT created.")
