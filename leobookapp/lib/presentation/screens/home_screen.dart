import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:leobookapp/logic/cubit/home_cubit.dart';
import 'package:leobookapp/core/constants/app_colors.dart';
import '../widgets/match_card.dart';
import '../widgets/header_section.dart';
import '../widgets/featured_carousel.dart';
import '../widgets/news_feed.dart';
import '../widgets/footnote_section.dart';
import 'all_predictions_screen.dart';
import 'rule_engine/backtest_dashboard.dart';
import 'package:leobookapp/logic/cubit/user_cubit.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: BlocBuilder<HomeCubit, HomeState>(
          builder: (context, state) {
            final isDark = Theme.of(context).brightness == Brightness.dark;
            if (state is HomeLoading) {
              return Center(child: CircularProgressIndicator());
            } else if (state is HomeLoaded) {
              return RefreshIndicator(
                onRefresh: () async {
                  context.read<HomeCubit>().loadDashboard();
                },
                child: CustomScrollView(
                  slivers: [
                    SliverToBoxAdapter(
                      child: HeaderSection(
                        selectedDate: state.selectedDate,
                        selectedSport: state.selectedSport,
                        availableSports: state.availableSports,
                        onDateChanged: (date) =>
                            context.read<HomeCubit>().updateDate(date),
                        onSportChanged: (sport) =>
                            context.read<HomeCubit>().updateSport(sport),
                      ),
                    ),
                    SliverToBoxAdapter(
                      child: FeaturedCarousel(
                        matches: state.featuredMatches,
                        recommendations: state.filteredRecommendations,
                        allMatches: state.allMatches,
                      ),
                    ),
                    const SliverToBoxAdapter(child: SizedBox(height: 16)),
                    SliverToBoxAdapter(child: NewsFeed(news: state.news)),
                    SliverPadding(
                      padding: const EdgeInsets.fromLTRB(16, 32, 16, 16),
                      sliver: SliverToBoxAdapter(
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  Icons.list_alt,
                                  color: AppColors.primary,
                                  size: 20,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  "ALL PREDICTIONS",
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w900,
                                    color: isDark
                                        ? Colors.white
                                        : AppColors.textDark,
                                    letterSpacing: 1.2,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                    SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (context, index) {
                          return MatchCard(match: state.filteredMatches[index]);
                        },
                        childCount: state.isAllMatchesExpanded
                            ? state.filteredMatches.length
                            : (state.filteredMatches.length > 12
                                  ? 12
                                  : state.filteredMatches.length),
                      ),
                    ),
                    if (!state.isAllMatchesExpanded &&
                        state.filteredMatches.length > 12)
                      SliverPadding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16.0,
                          vertical: 16.0,
                        ),
                        sliver: SliverToBoxAdapter(
                          child: InkWell(
                            onTap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => AllPredictionsScreen(
                                    date: state.selectedDate,
                                    sport: state.selectedSport,
                                  ),
                                ),
                              );
                            },
                            child: Container(
                              height: 50,
                              decoration: BoxDecoration(
                                color: AppColors.primary.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                  color: AppColors.primary.withValues(
                                    alpha: 0.3,
                                  ),
                                ),
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(
                                    "LOAD MORE (${state.filteredMatches.length - 12} MATCHES)",
                                    style: TextStyle(
                                      color: AppColors.primary,
                                      fontWeight: FontWeight.bold,
                                      letterSpacing: 1.1,
                                    ),
                                  ),
                                  SizedBox(width: 8),
                                  Icon(
                                    Icons.keyboard_arrow_down,
                                    color: AppColors.primary,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    SliverToBoxAdapter(child: FootnoteSection()),
                  ],
                ),
              );
            } else if (state is HomeError) {
              return Center(child: Text(state.message));
            }
            return Container();
          },
        ),
      ),
      floatingActionButton: BlocBuilder<UserCubit, UserState>(
        builder: (context, state) {
          if (state.user.canCreateCustomRules) {
            return FloatingActionButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const BacktestDashboard(),
                  ),
                );
              },
              tooltip: "Rule Engine (Lite/Pro)",
              child: const Icon(Icons.science),
            );
          }
          return const SizedBox.shrink(); // Hide for unregistered
        },
      ),
    );
  }
}
