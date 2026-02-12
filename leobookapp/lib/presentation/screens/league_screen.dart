import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:leobookapp/core/constants/app_colors.dart';
import '../widgets/league_tabs/overview_tab.dart';
import '../widgets/league_tabs/fixtures_tab.dart';
import '../widgets/league_tabs/predictions_tab.dart';
import '../widgets/league_tabs/stats_tab.dart';

class LeagueScreen extends StatefulWidget {
  final String leagueId;
  final String leagueName;

  const LeagueScreen({
    super.key,
    required this.leagueId,
    required this.leagueName,
  });

  @override
  State<LeagueScreen> createState() => _LeagueScreenState();
}

class _LeagueScreenState extends State<LeagueScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark
          ? AppColors.backgroundDark
          : AppColors.backgroundLight,
      body: NestedScrollView(
        headerSliverBuilder: (context, innerBoxIsScrolled) {
          return [
            SliverAppBar(
              backgroundColor: isDark
                  ? AppColors.backgroundDark.withValues(alpha: 0.9)
                  : AppColors.backgroundLight.withValues(alpha: 0.9),
              surfaceTintColor: Colors.transparent, // Disable Material 3 tint
              pinned: true,
              floating: true,
              snap: true,
              elevation: 0,
              toolbarHeight: 64, // Increased from 56
              leading: IconButton(
                icon: Icon(
                  Icons.arrow_back_ios_new,
                  size: 20,
                  color: isDark ? Colors.white : AppColors.textDark,
                ),
                onPressed: () => Navigator.pop(context),
              ),
              titleSpacing: 0,
              title: Row(
                children: [
                  Container(
                    width: 32,
                    height: 32,
                    margin: const EdgeInsets.only(right: 10),
                    decoration: BoxDecoration(
                      color: isDark ? AppColors.cardDark : Colors.white,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: isDark
                            ? Colors.white.withValues(alpha: 0.1)
                            : Colors.black.withValues(alpha: 0.1),
                      ),
                    ),
                    child: Icon(
                      Icons.emoji_events_outlined,
                      size: 18,
                      color: AppColors.primary,
                    ),
                  ),
                  Column(
                    mainAxisSize: MainAxisSize.min, // Added
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.leagueName,
                        style: GoogleFonts.lexend(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: isDark ? Colors.white : AppColors.textDark,
                          height: 1.0, // Reduced from 1.1
                        ),
                      ),
                      Text(
                        "Season 2024/25".toUpperCase(),
                        style: GoogleFonts.lexend(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textGrey,
                          letterSpacing: 1.0,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              actions: [
                IconButton(
                  icon: const Icon(
                    Icons.star_border,
                    color: AppColors.textGrey,
                  ),
                  onPressed: () {},
                ),
                IconButton(
                  icon: const Icon(Icons.search, color: AppColors.textGrey),
                  onPressed: () {},
                ),
              ],
              bottom: PreferredSize(
                preferredSize: const Size.fromHeight(50), // Increased from 48
                child: Container(
                  decoration: BoxDecoration(
                    border: Border(
                      bottom: BorderSide(
                        color: isDark
                            ? Colors.white.withValues(alpha: 0.1)
                            : Colors.black.withValues(alpha: 0.05),
                      ),
                    ),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    isScrollable: true,
                    tabAlignment: TabAlignment.start,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    labelColor: AppColors.primary,
                    unselectedLabelColor: AppColors.textGrey,
                    indicatorColor: AppColors.primary,
                    indicatorSize: TabBarIndicatorSize.label,
                    indicatorWeight: 3,
                    labelStyle: GoogleFonts.lexend(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.5,
                    ),
                    unselectedLabelStyle: GoogleFonts.lexend(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                    dividerColor: Colors.transparent, // Remove default divider
                    tabs: const [
                      Tab(text: "OVERVIEW"),
                      Tab(text: "FIXTURES"),
                      Tab(text: "PREDICTIONS"),
                      Tab(text: "STATS"),
                    ],
                  ),
                ),
              ),
            ),
          ];
        },
        body: TabBarView(
          controller: _tabController,
          children: [
            LeagueOverviewTab(leagueName: widget.leagueName),
            LeagueFixturesTab(leagueName: widget.leagueName),
            LeaguePredictionsTab(leagueName: widget.leagueName),
            LeagueStatsTab(leagueName: widget.leagueName),
          ],
        ),
      ),
    );
  }
}
