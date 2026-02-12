import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:leobookapp/logic/cubit/home_cubit.dart';
import 'package:leobookapp/logic/cubit/search_cubit.dart';
import '../screens/search_screen.dart';
import 'package:intl/intl.dart';
import 'package:leobookapp/core/constants/app_colors.dart';

class HeaderSection extends StatefulWidget {
  final DateTime selectedDate;
  final String selectedSport;
  final List<String> availableSports;
  final Function(DateTime) onDateChanged;
  final Function(String) onSportChanged;

  const HeaderSection({
    super.key,
    required this.selectedDate,
    required this.selectedSport,
    required this.availableSports,
    required this.onDateChanged,
    required this.onSportChanged,
  });

  @override
  State<HeaderSection> createState() => _HeaderSectionState();
}

class _HeaderSectionState extends State<HeaderSection> {
  late ScrollController _scrollController;
  final double itemWidth = 83.0; // 75px + 8px horizontal margin total

  @override
  void initState() {
    super.initState();
    // Calculate initial offset to center 'Today' (index 3)
    // Formula: (index * itemWidth) - (viewportWidth / 2) + (itemWidth / 2)
    // We'll estimate viewport width as 428 for now, but better to do it in build
    _scrollController = ScrollController();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Use LayoutBuilder to get exact width for centering
    return LayoutBuilder(
      builder: (context, constraints) {
        final viewportWidth = constraints.maxWidth;
        final initialOffset =
            (3 * itemWidth) - (viewportWidth / 2) + (itemWidth / 2);

        // We only set the offset if the controller is newly created
        if (!_scrollController.hasClients) {
          Future.microtask(() {
            if (_scrollController.hasClients) {
              _scrollController.jumpTo(initialOffset);
            }
          });
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Bar
            Container(
              padding: const EdgeInsets.fromLTRB(16, 8, 8, 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.sports_soccer,
                        color: AppColors.primary,
                        size: 30,
                      ),
                      const SizedBox(width: 10),
                      Text(
                        "LeoBook",
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          color: isDark ? Colors.white : AppColors.textDark,
                          letterSpacing: -0.5,
                        ),
                      ),
                    ],
                  ),
                  Row(
                    children: [
                      IconButton(
                        icon: Icon(
                          Icons.search,
                          color: AppColors.textGrey,
                          size: 24,
                        ),
                        onPressed: () {
                          final homeState = context.read<HomeCubit>().state;
                          if (homeState is HomeLoaded) {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => BlocProvider(
                                  create: (context) => SearchCubit(
                                    allMatches: homeState.allMatches,
                                    allRecommendations:
                                        homeState.allRecommendations,
                                  ),
                                  child: const SearchScreen(),
                                ),
                              ),
                            );
                          }
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Navigation Tabs (Active Sport)
            SizedBox(
              height: 48,
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  children: widget.availableSports.map((sport) {
                    return _buildNavTab(
                      sport[0].toUpperCase() + sport.substring(1).toLowerCase(),
                      widget.selectedSport == sport,
                    );
                  }).toList(),
                ),
              ),
            ),

            Divider(
              height: 1,
              color: isDark ? AppColors.cardDark : Colors.grey.withAlpha(50),
            ),

            // Date Strip - Centered on Today
            Container(
              height: 85,
              margin: const EdgeInsets.only(top: 4),
              child: ListView.builder(
                controller: _scrollController,
                scrollDirection: Axis.horizontal,
                itemCount: 7,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                itemBuilder: (context, index) {
                  final dayOffset = index - 3;
                  final date = DateTime(
                    now.year,
                    now.month,
                    now.day,
                  ).add(Duration(days: dayOffset));

                  final isSelected =
                      date.year == widget.selectedDate.year &&
                      date.month == widget.selectedDate.month &&
                      date.day == widget.selectedDate.day;

                  return _buildDateItem(date, isSelected);
                },
              ),
            ),
            const SizedBox(height: 12),
          ],
        );
      },
    );
  }

  Widget _buildNavTab(String title, bool isSelected) {
    return GestureDetector(
      onTap: () => widget.onSportChanged(title.toUpperCase()),
      child: Container(
        margin: const EdgeInsets.only(right: 28),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          border: isSelected
              ? const Border(
                  bottom: BorderSide(color: AppColors.primary, width: 2.5),
                )
              : null,
        ),
        child: Text(
          title.toUpperCase(),
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: isSelected ? AppColors.primary : AppColors.textGrey,
            letterSpacing: 1.2,
          ),
        ),
      ),
    );
  }

  Widget _buildDateItem(DateTime date, bool isSelected) {
    final now = DateTime.now();
    final isToday =
        date.year == now.year && date.month == now.month && date.day == now.day;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final dayName = DateFormat('EEE').format(date).toUpperCase();
    final dayNum = DateFormat('d MMM').format(date).toUpperCase();

    return GestureDetector(
      onTap: () => widget.onDateChanged(date),
      child: Container(
        width: 75,
        margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
        padding: const EdgeInsets.symmetric(vertical: 4),
        decoration: BoxDecoration(
          color: isSelected
              ? AppColors.primary.withValues(alpha: 0.1)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
          border: isSelected
              ? Border.all(
                  color: AppColors.primary.withValues(alpha: 0.2),
                  width: 1,
                )
              : null,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              isToday ? "TODAY" : dayName,
              style: TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.w900,
                color: isSelected
                    ? AppColors.primary
                    : (isDark ? Colors.white38 : Colors.black38),
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              dayNum,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: isSelected
                    ? AppColors.primary
                    : (isDark ? Colors.white70 : Colors.black87),
              ),
            ),
            if (isSelected) ...[
              const SizedBox(height: 4),
              Container(
                width: 4,
                height: 4,
                decoration: const BoxDecoration(
                  color: AppColors.primary,
                  shape: BoxShape.circle,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
