import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:leobookapp/core/constants/app_colors.dart';
import 'package:leobookapp/logic/cubit/home_cubit.dart';
import '../widgets/match_card.dart';
import '../widgets/footnote_section.dart';

class TopOddsScreen extends StatefulWidget {
  const TopOddsScreen({super.key});

  @override
  State<TopOddsScreen> createState() => _TopOddsScreenState();
}

class _TopOddsScreenState extends State<TopOddsScreen> {
  String _sortBy = 'odds_desc'; // odds_desc, odds_asc
  String? _filterLeague;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDark,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "TOP ODDS",
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.5,
              ),
            ),
            Text(
              "BEST VALUE PICKS",
              style: TextStyle(
                fontSize: 10,
                color: AppColors.textGrey,
                fontWeight: FontWeight.w600,
                letterSpacing: 1.2,
              ),
            ),
          ],
        ),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.sort, color: AppColors.primary),
            onSelected: (value) => setState(() => _sortBy = value),
            itemBuilder: (_) => [
              const PopupMenuItem(
                value: 'odds_desc',
                child: Text('Highest Odds First'),
              ),
              const PopupMenuItem(
                value: 'odds_asc',
                child: Text('Lowest Odds First'),
              ),
            ],
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: BlocBuilder<HomeCubit, HomeState>(
        builder: (context, state) {
          if (state is! HomeLoaded) {
            return const Center(child: CircularProgressIndicator());
          }

          var matches = state.filteredMatches
              .where((m) => m.odds != null && m.odds!.isNotEmpty)
              .toList();

          // Filter by league
          if (_filterLeague != null) {
            matches = matches.where((m) => m.league == _filterLeague).toList();
          }

          // Sort by odds
          matches.sort((a, b) {
            final oddsA = double.tryParse(a.odds ?? '0') ?? 0;
            final oddsB = double.tryParse(b.odds ?? '0') ?? 0;
            return _sortBy == 'odds_desc'
                ? oddsB.compareTo(oddsA)
                : oddsA.compareTo(oddsB);
          });

          // League filter chips
          final allLeagues = state.filteredMatches
              .map((m) => m.league)
              .whereType<String>()
              .toSet()
              .toList()
            ..sort();

          if (matches.isEmpty) {
            return const Center(
              child: Text(
                "No odds data available.",
                style: TextStyle(color: AppColors.textGrey),
              ),
            );
          }

          return CustomScrollView(
            slivers: [
              // League filter chips
              SliverToBoxAdapter(
                child: SizedBox(
                  height: 44,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    children: [
                      _buildFilterChip("ALL", _filterLeague == null, () {
                        setState(() => _filterLeague = null);
                      }),
                      ...allLeagues.map((league) => _buildFilterChip(
                            league.split(':').last.trim().toUpperCase(),
                            _filterLeague == league,
                            () => setState(() => _filterLeague = league),
                          )),
                    ],
                  ),
                ),
              ),
              const SliverToBoxAdapter(child: SizedBox(height: 16)),
              // Match list
              SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: MatchCard(match: matches[index]),
                    ),
                    childCount: matches.length,
                  ),
                ),
              ),
              // Footer
              const SliverToBoxAdapter(
                child: FootnoteSection(),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildFilterChip(String label, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : AppColors.desktopSearchFill,
          borderRadius: BorderRadius.circular(20),
          border: isSelected
              ? null
              : Border.all(color: Colors.white.withValues(alpha: 0.05)),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w900,
              color: isSelected ? Colors.white : AppColors.textGrey,
              letterSpacing: 1.0,
            ),
          ),
        ),
      ),
    );
  }
}
