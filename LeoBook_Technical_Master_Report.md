# LeoBook Comprehensive Technical Master Report

This report provides an objective technical breakdown of the LeoBook ecosystem, detailing the Search Dictionary pipeline and the architectural "Chapters" of the application workflow.

---

## Part I: The Search Dictionary Infrastructure

The Search Dictionary is the "Brain" of LeoBook, enabling **Canonical Entity Resolution**—mapping messy web strings to consistent, high-fidelity IDs.

### 1. The Build Pipeline (`Scripts/build_search_dict.py`)
This script executes a resilient ETL (Extract, Transform, Load) process.

#### A. Extraction & Grouping
- **Source**: `Data/Store/schedules.csv` (contains ~22k+ raw records).
- **Logic**: Aggregates teams and leagues based on raw IDs and occurrences. It preserves "variant names" (e.g., "Man Utd" vs "Manchester United") to build a comprehensive alias map.

#### B. Enrichment with xAI Grok (Grok-4-1)
- **Batching**: Sends 10 items per API call to maximize throughput and maintain context.
- **JSON Salvage Logic**: 
    - Designed to combat malformed and truncated responses.
    - Uses regex to find JSON blocks and attempts to "patch" missing closing brackets or salvage partial objects if the response is cutoff mid-stream.
- **Retry Mechanism**: Implements 3 retries with exponential backoff (5s, 10s, 15s) to handle transient API instability.

#### C. ID Disambiguation & Slug Strategy
- **Compound Slugs**: Generates IDs like `fra-ligue-1` (Country + League) to prevent collisions across international borders.
- **Deterministic UUID Fallback**: Uses `uuid.uuid5` (DNS namespace) to generate consistent, unique IDs when context is missing or slugs collide.
- **Normalization**: Unicode NFKD decomposition strips diacritics (Sao -> São) ensures search parity.

#### D. Dual-Sync Synchronization (Resilience)
- **Local CSV Sync**: Updates `teams.csv` and `region_league.csv` **incrementally** after every batch. This prevents data loss if a process is interrupted.
- **Supabase Batching**: Upserts data in chunks of 1000 items to avoid payload limits and stabilize cloud sync.
- **Self-Healing Schema**: Automatically detects and handles missing table columns (e.g., `stadium`) by retrying without the offending field.

### 2. Runtime Interaction (`Core/System/search_dict.py`)
The search engine optimized for real-time mobile and web performance.

- **Lazy paginated Fetch**: Instead of a "Big Bang" load, it fetches Supabase data in 1000-row pages (to bypass API limits) upon the first search query.
- **Offline Fallback**: If Supabase connectivity fails (e.g., 502/Timeout), it immediately switches to the local CSV store (`Data/Store/`).
- **Hybrid Fuzzy Matching**:
    - **Leveshtein Ratio**: Standard fuzzy matching.
    - **Token Sort Ratio**: Order-independent matching (e.g., "United Manchester" matches "Manchester United" with 1.0 score).
- **Adaptive Thresholding**:
    - **Short Queries** (<4 chars): Strict threshold (0.9) to prevent noise for "FC" or "IFK".
    - **Long Queries** (>10 chars): Relaxed threshold (0.7) to favor partial matches in long names.

### 3. UI Integration (Flutter/Web)
- **The Service**: `SearchService.dart` consumes the search API.
- **The BLoC**: `SearchCubit` manages loading states and filters results into **Teams**, **Leagues**, and **Matches**.
- **The UI**: `SearchScreen.dart` provides an instant results overlay with categories and result highlighting.

---

## Part II: The LeoBook Workflow "Chapters"

The application is structured into distinct chapters, each serving a critical role in the user's prediction journey.

### Chapter 1: The Core Navigation (`MainScreen`)
- **NavigationSideBar**: A responsive left-aligned navigation hub.
    - Features: Static logo, dynamic NavItems (Home, Predictions, Odds, Account), and a collapse/expand toggle.
    - **Responsive Logic**: Uses `SingleChildScrollView` to prevent overflow on small viewports and `AnimatedContainer` for smooth width transitions.
- **PageController**: Orchestrates the top-level view switching without re-building the entire scaffold.

### Chapter 2: The Dashboard (`HomeScreen`)
The primary entry point, designed for maximum information density and "Wowed" aesthetics.
- **Header Section**:
    - **CategoryBar**: Horizontal chips for quick filtering (e.g., Live, Soccer, Basketball).
    - **Search Bubble**: Tappable search bar for instant navigation.
- **Value Section**:
    - **TopPredictionsGrid**: Highlights the "Best Value" picks of the day.
    - **FeaturedCarousel**: High-impact match previews and recommendations.
- **Engagement Section**:
    - **NewsFeed**: Real-time ticker of sports news.
- **The Match Console (Sticky Tabs)**:
    - **Tabs**: ALL (Alphabetical), FINISHED (Time-descending), SCHEDULED (Time-ascending).
    - **Match Cards**: Detailed units showing teams, odds, live status, and prediction reliability.
    - **Integrated Index (SideRuler)**: Spans from TabBar to Footer.
        - **All Tab**: A-Z jump points grouped by League.
        - **Finished/Scheduled**: Time jump points (HH:00) grouped by Match Hour.
- **The FootnoteSection**: Persistent footer with global stats and predictor credits.

### Chapter 3: Search & Discovery (`SearchScreen`)
- Full-screen search interface.
- Instant keyboard interaction.
- Result categories (Team, League, Match) each leading to their respective deep-dive screens.

### Chapter 4: Prediction Analytics
- **TopPredictionsScreen**: Deep list view of AI-vetted picks.
- **AllPredictionsScreen**: Complete searchable archive of current recommendations.
- **TopOddsScreen**: Focused view on outlier odds and arbitrage opportunities.

### Chapter 5: Entity Intelligence (Deep Dives)
- **MatchDetailsScreen**:
    - Section: Live Score / Status.
    - Section: H2H History (Head-to-Head).
    - Section: AI Analysis & Reliability Stats.
    - Section: Market Odds (1X2, Over/Under, etc.).
- **TeamScreen**: Canonical official names, crests, stadium info, and recent performance trends.
- **LeagueScreen**: Standings tables, official logos, and league-specific schedules.

### Chapter 6: Personalization & Account (`AccountScreen`)
- User profile management.
- Balance tracker and transaction history.
- Settings (Theme toggles, Notification preferences).

---

## Technical Summary Table
| Component | Objective Truth / Implementation |
| :--- | :--- |
| **State Management** | Flutter Bloc (Cubit) + Provider |
| **Data Layer** | Repository Pattern (Remote: GitHub/Supabase, Local: CSV) |
| **Search Algo** | Adaptive Hybrid Fuzzy (Token Sort + Levenshtein) |
| **Logic Layer** | Python Scripts (ETL) + Dart Logic Services |
| **Design System** | Custom Material 3 (Dark Slate/Primary Blue theme) |
| **Resilience** | Dual-Sync, Dynamic Schema Retries, CSV Fallback |
