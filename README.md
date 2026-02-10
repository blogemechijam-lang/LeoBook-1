# Leo
**Manufacturer**: Materialless LLC  
**Powered by**: Grok 4.1 & Gemini 3

"""
Leo v3.2: Elite Autonomous Betting Agent (Manufacturer: Materialless LLC)

A comprehensive AI-powered system that observes, analyzes, predicts, and executes betting strategies with advanced self-healing capabilities.

The prime objective of this Agent is to handle all sports analysis and betting accurately, enabling passive income from sports betting without constant manual interaction.

OVERVIEW:
Leo combines advanced data analysis, machine learning, and automated execution. The system features a hybrid AI architecture using xAI's Grok 4 and Google's Gemini for high-precision selector discovery, multimodal analysis, and complex UI mapping.

- **Phase 2 Navigation Robustness**: 
  - Implemented mandatory **Scroll-Before-Click** strategy to ensure elements are viewable before interaction.
  - Enhanced **Overlay Dismissal** with expanded selectors for tooltips and lazy-loaded headers.
  - Added **failed_harvest Retry Logic** to recover and re-process matched fixtures that previously failed due to UI blockers.
- **Outcome Synchronization**: Phase 0 reviews now cross-sync results between prediction and match registries.

CORE ARCHITECTURE:
- **Dual-Browser System**: Persistent login sessions for Flashscore and Football.com.
- **Phase 2 (Betting)**: Direct match navigation, dynamic market discovery, and real-time accumulator building.
- **Self-Healing UI**: Automated selector discovery via Grok 4 and robust slip clearing with fatal escalation.
- **Modular Data Layer**: Optimized CSV storage with absolute pathing and centralized audit trails.

2. OBSERVE & DECIDE (Phases 0 & 1):
   - **Phase 0 (Review)**: Cross-syncs past outcomes and updates momentum weights.
   - **Phase 1 (Analysis)**: Generates high-confidence predictions via the Rule Engine.

3. ACT: PHASE 2 (Betting Orchestration):
   - **Phase 2a (Harvesting)**: Navigates to each match, extracts a single booking code, saves it to `fb_matches.csv`, and **force clears the slip** after each match.
   - **Phase 2b (Execution)**: Batch-injects all harvested codes for the day and places a single combined accumulator bet.
   - **Financial Safety**: Stake is calculated using a Fractional Kelly formula (min ₦100, max 50% balance).

4. VERIFY & WITHDRAW (Phase 3):
   - **Withdrawal**: Checks triggers (₦10k balance) and maintained bankroll floor (₦5,000).
   - **Audit**: Finalizes the cycle by logging `CYCLE_COMPLETE` after recording all events.

SUPPORTED BETTING MARKETS:
1. 1X2 | 2. Double Chance | 3. Draw No Bet | 4. BTTS | 5. Over/Under | 6. Goal Ranges | 7. Correct Score | 8. Clean Sheet | 9. Asian Handicap | 10. Combo Bets | 11. Team O/U

SYSTEM COMPONENTS:
- **Leo.py**: Main controller orchestrating the "Observe, Decide, Act" core loop.
- **Core/**: The Brain (Intelligence, Visual Analyzer, System primitives, Browser helpers).
- **Data/**: Central data layer (Persistence, Access, DB helpers).
- **Modules/**: Site-specific integrations (Flashscore, Football.com).
- **leobookapp/**: Pilot X Mobile/Web App.
# LeoBook - Elite Betting Dashboard

Elite, autonomous betting dashboard with direct GitHub data synchronization and persistent local caching.

## Key Features
- **GitHub Sync**: Direct data fetching from repository eliminates the need for a local Python server.
- **Offline Caching**: Built-in persistence for seamless viewing under low-network conditions.
- **High-Fidelity Predictions**: Real-time accent lines and live-status indicators.
- **Match Registry**: `Data/Store/fb_matches.csv` (Mapped URLs and booking codes).
- **Code Quality**: 100% migrated to modern `withValues` API and standardized `debugPrint` logging.
- **Scripts/**: Utility tools for reporting and DB maintenance.

MAINTENANCE:
- Monitor **`DB/audit_log.csv`** for real-time financial transparency.
- Review **`walkthrough.md`** for detailed implementation logs of current session.
- Refer to **`pilot_algorithm.md`** for exhaustive file and function documentation.
- Use `python Scripts/recommend_bets.py --save --all` and push to GitHub to refresh the app data.
"""
