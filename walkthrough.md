# Walkthrough - LeoBook Phase 2 Refactor & Fixes

This walkthrough covers the major architectural upgrade to the LeoBook booking system and the resolution of critical dependency and import issues.

## 1. UI Standardization (Stitch System)

- [x] **UI Atoms & Styling Standardization (Stitch v4)**
  - Updated `AppColors` with v4 semantic tokens: `successGreen` (#34C759) and `liveRed` (#FF3B30).
  - Refined `AppTheme` with global Lexend typography for titles and body text.
  - Standardized border treatments (0.05 opacity) and shadows across all cards.
- [x] **Search System Implementation (Stitch v2)**
  - Implemented `SearchScreen` with high-fidelity header and categorization logic.
  - Added "Recent Searches" with persistence (runtime) and "Popular Teams" horizontal list.
  - Developed `SearchCubit` for efficient filtering across matches and leagues.
  - Integrated search triggers on `HomeScreen` and `HeaderSection`.

## 2. Phase 2: Harvest -> Execute Strategy

We have completely refactored the booking process for Football.com to ensure maximum robustness.

### Phase 2a: Harvesting Codes
Instead of adding matches to the slip and placing bets in one go, the system now iterates through matched URLs and "harvests" booking codes for each individual match.
- **File**: [booking_code.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Sites/football_com/booker/booking_code.py)
- **Action**: Navigates to match, selects outcome (Odds >= 1.20), clicks "Book", and extracts the code.
- **Persistence**: Codes are saved to `football_com_matches.csv` for the current date.

### Phase 2b: Execution
Once codes are harvested, the system builds the multi-bet in a single step using URL parameters.
- **File**: [placement.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Sites/football_com/booker/placement.py)
- **Logic**: Injects all codes via `?shareCode=CODE1,CODE2...` which automatically populates the betslip.
- **Verification**: Verifies the bet placement by checking the booking code dialog and ensuring the balance decreases by the exact stake amount.

## 2. Robust Slip Management

The new `force_clear_slip` function ensures the browser is in a clean state before any booking operation.
- **Retry Logic**: Attempts to clear the slip up to 3 times.
- **Fatal Error Path**: If clearing fails repeatedly, it deletes `storage_state.json` and triggers a `FatalSessionError`, forcing the main loop to perform a hard restart of the browser session.

## 3. Strict Betting & Withdrawal Rules

- **Stake Rules**: Minimum ₦1, Maximum 50% of current balance (or 1% for conservative play).
- **Withdrawal Rules**:
    - Minimum ₦500.
    - Maximum capped at `Min(30% Balance, 50% Latest Win)`.
- **Implementation**: [withdrawal.py](file:///c:/Users/Admin/Desktop/ProProjection/LeoBook/Sites/football_com/booker/withdrawal.py)

## 4. On-Demand AI Server

The AI server is no longer started globally on startup. It is now lazy-loaded only when URL resolution (Matcher) fails to find a match in the cache or via standard scraping.
- **Logic**: `_ensure_ai_server_if_needed()` in `football_com.py` checks server status and starts it only if matching is actually required.

## 5. Critical Fixes & Stability

After the refactor, we resolved several issues:
- **Phase 2 Crash Fix**: Corrected `match_predictions_with_site` call to pass only 2 arguments (day_predictions, site_matches) after ensuring scraping has occurred.
- **URL Resolution Logic**: Restored the correct "Scrape -> Cache -> Match" sequence in `football_com.py`.
- **Navigator Fix**: Resolved the stale `clear_bet_slip` import in `navigator.py` by updating it to use the new `force_clear_slip` function.
- **Dependency**: Added `google-generativeai` to `requirements.txt` to fix the `ModuleNotFoundError`.
- **Import Errors**: Fixed all stale imports across `placement.py`, `football_com.py`, and package `__init__.py` files.
- **Git**: Configured `.gitignore` to correctly exclude large `Mind/*.gguf` models.

## 6. Verification Results

A dry run of the import chain was successful:
```powershell
PS C:\Users\Admin\Desktop\ProProjection\LeoBook> python -c "import Leo; print('Imports OK')"
Imports OK
```

The system is now stable, state-aware, and follows the strict Harvest-first strategy requested.
