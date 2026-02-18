import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/responsive_constants.dart';
import '../../../core/theme/liquid_glass_theme.dart';
import '../../../logic/cubit/home_cubit.dart';
import 'leo_date_picker.dart';

class CategoryBar extends StatefulWidget {
  const CategoryBar({super.key});

  @override
  State<CategoryBar> createState() => _CategoryBarState();
}

class _CategoryBarState extends State<CategoryBar> {
  final ScrollController _scrollController = ScrollController();

  // 4 past + TODAY + 4 future = 9 date items + 1 "More Dates" = 10 total
  static const int _pastDays = 4;
  static const int _futureDays = 4;
  static const int _todayIndex = _pastDays; // index 4
  static const int _totalDates = _pastDays + 1 + _futureDays; // 9
  static const int _totalItems = _totalDates + 1; // 10 (includes More Dates)

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToIndex(_todayIndex);
    });
  }

  void _scrollToIndex(int index) {
    if (!_scrollController.hasClients) return;
    final screenWidth = MediaQuery.sizeOf(context).width;
    final itemExtent = Responsive.sp(context, 56);
    final offset = (index * itemExtent) - (screenWidth / 2) + (itemExtent / 2);
    _scrollController.animateTo(
      offset.clamp(0.0, _scrollController.position.maxScrollExtent),
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeOut,
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<HomeCubit, HomeState>(
      listener: (context, state) {
        if (state is HomeLoaded) {
          final now = DateTime.now();
          final start = DateTime(now.year, now.month, now.day)
              .subtract(Duration(days: _pastDays));
          final diff = DateTime(
            state.selectedDate.year,
            state.selectedDate.month,
            state.selectedDate.day,
          ).difference(start).inDays;
          if (diff >= 0 && diff < _totalDates) {
            _scrollToIndex(diff);
          }
        }
      },
      builder: (context, state) {
        final selectedDate =
            state is HomeLoaded ? state.selectedDate : DateTime.now();
        final now = DateTime.now();

        return Container(
          height: Responsive.sp(context, 28),
          margin: EdgeInsets.symmetric(vertical: Responsive.sp(context, 6)),
          child: ListView.separated(
            controller: _scrollController,
            scrollDirection: Axis.horizontal,
            itemCount: _totalItems,
            separatorBuilder: (_, __) =>
                SizedBox(width: Responsive.sp(context, 4)),
            itemBuilder: (context, index) {
              if (index == _totalDates) {
                return _buildMoreDates(context, selectedDate);
              }

              final date = now.add(Duration(days: index - _pastDays));
              final isYesterday =
                  _isSameDay(date, now.subtract(const Duration(days: 1)));
              final isToday = _isSameDay(date, now);
              final isTomorrow =
                  _isSameDay(date, now.add(const Duration(days: 1)));

              String label;
              if (isYesterday) {
                label = "YESTERDAY";
              } else if (isToday) {
                label = "TODAY";
              } else if (isTomorrow) {
                label = "TOMORROW";
              } else {
                label =
                    "${DateFormat('EEE').format(date).toUpperCase()} ${date.day}";
              }

              return _buildChip(
                context,
                label,
                _isSameDay(selectedDate, date),
                () => context.read<HomeCubit>().updateDate(date),
              );
            },
          ),
        );
      },
    );
  }

  bool _isSameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;

  Widget _buildChip(
      BuildContext context, String label, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        constraints: BoxConstraints(minWidth: Responsive.sp(context, 52)),
        padding: EdgeInsets.symmetric(horizontal: Responsive.sp(context, 8)),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : AppColors.desktopSearchFill,
          borderRadius: BorderRadius.circular(Responsive.sp(context, 8)),
          border: isSelected
              ? null
              : Border.all(color: LiquidGlassTheme.glassBorderDark, width: 0.5),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              fontSize: Responsive.sp(context, 7),
              fontWeight: FontWeight.w900,
              color: isSelected ? Colors.white : AppColors.textGrey,
              letterSpacing: 0.8,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMoreDates(BuildContext context, DateTime current) {
    return GestureDetector(
      onTap: () async {
        final maxDate = DateTime.now().add(const Duration(days: 7));
        final date = await LeoDatePicker.show(
          context,
          current,
          lastDate: maxDate,
        );
        if (date != null && context.mounted) {
          context.read<HomeCubit>().updateDate(date);
        }
      },
      child: Container(
        constraints: BoxConstraints(minWidth: Responsive.sp(context, 52)),
        padding: EdgeInsets.symmetric(horizontal: Responsive.sp(context, 8)),
        decoration: BoxDecoration(
          color: AppColors.desktopSearchFill,
          borderRadius: BorderRadius.circular(Responsive.sp(context, 8)),
          border:
              Border.all(color: LiquidGlassTheme.glassBorderDark, width: 0.5),
        ),
        child: Center(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.calendar_today_rounded,
                  color: AppColors.textGrey, size: Responsive.sp(context, 10)),
              SizedBox(width: Responsive.sp(context, 4)),
              Text(
                "MORE DATES",
                style: TextStyle(
                  fontSize: Responsive.sp(context, 7),
                  fontWeight: FontWeight.w900,
                  color: AppColors.textGrey,
                  letterSpacing: 0.8,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
