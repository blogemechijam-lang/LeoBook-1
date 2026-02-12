import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import 'package:leobookapp/logic/cubit/home_cubit.dart';
import 'package:leobookapp/core/constants/app_colors.dart';
import '../widgets/match_card.dart';
import '../widgets/filter_modal.dart';

class AllPredictionsScreen extends StatelessWidget {
  final DateTime date;
  final String sport;

  const AllPredictionsScreen({
    super.key,
    required this.date,
    required this.sport,
  });

  @override
  Widget build(BuildContext context) {
    final dateStr = DateFormat('EEEE, d MMM yyyy').format(date).toUpperCase();

    return Scaffold(
      backgroundColor: Theme.of(context).brightness == Brightness.dark
          ? AppColors.backgroundDark
          : AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "ALL PREDICTIONS",
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            Text(
              "$dateStr • $sport",
              style: TextStyle(
                fontSize: 11,
                color: Colors.white.withValues(alpha: 0.2),
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.search, color: AppColors.textGrey),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text("Search triggered for $dateStr")),
              );
            },
          ),
          BlocBuilder<HomeCubit, HomeState>(
            builder: (context, state) {
              if (state is HomeLoaded) {
                return IconButton(
                  icon: const Icon(Icons.tune, color: AppColors.primary),
                  onPressed: () {
                    final cubit = context.read<HomeCubit>();
                    final availableLeagues =
                        state.allMatches
                            .map((m) => m.league)
                            .whereType<String>()
                            .toSet()
                            .toList()
                          ..sort();

                    showModalBottomSheet(
                      context: context,
                      isScrollControlled: true,
                      backgroundColor: Colors.transparent,
                      builder: (modalContext) => DraggableScrollableSheet(
                        initialChildSize: 0.92,
                        maxChildSize: 0.92,
                        minChildSize: 0.5,
                        builder: (_, controller) => FilterModal(
                          initialLeagues: state.selectedLeagues,
                          initialTypes: state.selectedPredictionTypes,
                          initialMinOdds: state.minOdds,
                          initialMaxOdds: state.maxOdds,
                          availableLeagues: availableLeagues,
                          onApply: (leagues, types, minO, maxO) {
                            cubit.applyFilters(
                              leagues: leagues,
                              types: types,
                              minOdds: minO,
                              maxOdds: maxO,
                            );
                          },
                        ),
                      ),
                    );
                  },
                );
              }
              return IconButton(
                icon: Icon(Icons.tune, color: AppColors.textGrey),
                onPressed: null,
              );
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: BlocBuilder<HomeCubit, HomeState>(
        builder: (context, state) {
          if (state is HomeLoaded) {
            final matches = state.filteredMatches;

            if (matches.isEmpty) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.event_busy,
                      size: 64,
                      color: AppColors.textGrey.withValues(alpha: 0.3),
                    ),
                    SizedBox(height: 16),
                    Text(
                      "No predictions found for this date.",
                      style: TextStyle(color: AppColors.textGrey),
                    ),
                  ],
                ),
              );
            }

            return ListView.builder(
              padding: EdgeInsets.symmetric(vertical: 8),
              itemCount: matches.length,
              itemBuilder: (context, index) {
                return MatchCard(match: matches[index], showLiveBadge: false);
              },
            );
          }
          return Center(child: CircularProgressIndicator());
        },
      ),
    );
  }
}
