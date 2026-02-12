import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:leobookapp/core/constants/app_colors.dart';

class FilterModal extends StatefulWidget {
  final List<String> initialLeagues;
  final List<String> initialTypes;
  final double initialMinOdds;
  final double initialMaxOdds;
  final List<String> availableLeagues;
  final Function(
    List<String> leagues,
    List<String> types,
    double minO,
    double maxO,
  )
  onApply;

  const FilterModal({
    super.key,
    required this.initialLeagues,
    required this.initialTypes,
    required this.initialMinOdds,
    required this.initialMaxOdds,
    required this.availableLeagues,
    required this.onApply,
  });

  @override
  State<FilterModal> createState() => _FilterModalState();
}

class _FilterModalState extends State<FilterModal> {
  late List<String> selectedLeagues;
  late List<String> selectedTypes;
  late double minOdds;
  late double maxOdds;

  final List<String> predictionTypes = [
    "Home Win",
    "Away Win",
    "Draw",
    "BTTS",
    "Over/Under",
    "Goals",
  ];

  @override
  void initState() {
    super.initState();
    selectedLeagues = List.from(widget.initialLeagues);
    selectedTypes = List.from(widget.initialTypes);
    minOdds = widget.initialMinOdds;
    maxOdds = widget.initialMaxOdds;
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      decoration: BoxDecoration(
        color: isDark ? AppColors.backgroundDark : Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(40)),
        border: Border.all(
          color: isDark ? Colors.white10 : Colors.black.withValues(alpha: 0.05),
        ),
      ),
      child: Stack(
        children: [
          Column(
            children: [
              // Drag Handle
              Center(
                child: Container(
                  width: 48,
                  height: 6,
                  margin: const EdgeInsets.symmetric(vertical: 12),
                  decoration: BoxDecoration(
                    color: isDark ? Colors.white24 : Colors.grey[300],
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
              ),

              // Header
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 8,
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      "Filters",
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                        color: isDark ? Colors.white : AppColors.textDark,
                      ),
                    ),
                    GestureDetector(
                      onTap: () => Navigator.pop(context),
                      child: Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: isDark
                              ? Colors.white.withValues(alpha: 0.05)
                              : Colors.grey[100],
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.close,
                          size: 20,
                          color: isDark ? Colors.white54 : Colors.grey[600],
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Filter Content
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(24, 16, 24, 100),
                  children: [
                    _buildSectionHeader("Leagues"),
                    const SizedBox(height: 16),
                    ...widget.availableLeagues.map(
                      (league) => _buildLeagueItem(league, isDark),
                    ),

                    const SizedBox(height: 32),
                    _buildSectionHeader("Prediction Type"),
                    const SizedBox(height: 16),
                    Wrap(
                      spacing: 8,
                      runSpacing: 10,
                      children: predictionTypes
                          .map((type) => _buildTypeChip(type))
                          .toList(),
                    ),

                    const SizedBox(height: 32),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _buildSectionHeader("Odds Range"),
                        Text(
                          "${minOdds.toStringAsFixed(1)} — ${maxOdds.toStringAsFixed(1)}",
                          style: const TextStyle(
                            color: AppColors.primary,
                            fontSize: 14,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    RangeSlider(
                      values: RangeValues(minOdds, maxOdds),
                      min: 1.0,
                      max: 5.0,
                      divisions: 40,
                      activeColor: AppColors.primary,
                      inactiveColor: isDark ? Colors.white10 : Colors.grey[200],
                      onChanged: (values) {
                        setState(() {
                          minOdds = values.start;
                          maxOdds = values.end;
                        });
                      },
                    ),
                    _buildOddsLabels(),
                  ],
                ),
              ),
            ],
          ),

          // Footer with glassmorphism
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: ClipRRect(
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                child: Container(
                  padding: const EdgeInsets.fromLTRB(24, 20, 24, 32),
                  decoration: BoxDecoration(
                    color: isDark
                        ? AppColors.backgroundDark.withValues(alpha: 0.8)
                        : Colors.white.withValues(alpha: 0.8),
                    border: Border(
                      top: BorderSide(
                        color: isDark
                            ? Colors.white10
                            : Colors.black.withValues(alpha: 0.05),
                      ),
                    ),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        flex: 1,
                        child: TextButton(
                          onPressed: () {
                            setState(() {
                              selectedLeagues = [];
                              selectedTypes = [];
                              minOdds = 1.0;
                              maxOdds = 5.0;
                            });
                          },
                          child: Text(
                            "RESET",
                            style: TextStyle(
                              color: isDark ? Colors.white54 : Colors.grey[600],
                              fontWeight: FontWeight.w900,
                              letterSpacing: 1.2,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        flex: 2,
                        child: ElevatedButton(
                          onPressed: () {
                            widget.onApply(
                              selectedLeagues,
                              selectedTypes,
                              minOdds,
                              maxOdds,
                            );
                            Navigator.pop(context);
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                            elevation: 8,
                            shadowColor: AppColors.primary.withValues(
                              alpha: 0.4,
                            ),
                          ),
                          child: const Text(
                            "APPLY FILTERS",
                            style: TextStyle(
                              fontWeight: FontWeight.w900,
                              letterSpacing: 1.2,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Text(
      title.toUpperCase(),
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w900,
        color: AppColors.textGrey,
        letterSpacing: 1.5,
      ),
    );
  }

  Widget _buildLeagueItem(String league, bool isDark) {
    bool isSelected = selectedLeagues.contains(league);
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: () {
          setState(() {
            if (isSelected) {
              selectedLeagues.remove(league);
            } else {
              selectedLeagues.add(league);
            }
          });
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isDark
                ? AppColors.cardDark.withValues(alpha: 0.4)
                : Colors.grey[50],
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isSelected
                  ? AppColors.primary
                  : (isDark
                        ? Colors.white.withValues(alpha: 0.05)
                        : Colors.black.withValues(alpha: 0.05)),
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                league,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              Container(
                width: 20,
                height: 20,
                decoration: BoxDecoration(
                  color: isSelected ? AppColors.primary : Colors.transparent,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                    color: isSelected
                        ? AppColors.primary
                        : (isDark ? Colors.white24 : Colors.grey[400]!),
                    width: 2,
                  ),
                ),
                child: isSelected
                    ? const Icon(Icons.check, size: 14, color: Colors.white)
                    : null,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTypeChip(String type) {
    bool isSelected = selectedTypes.contains(type);
    return InkWell(
      onTap: () {
        setState(() {
          if (isSelected) {
            selectedTypes.remove(type);
          } else {
            selectedTypes.add(type);
          }
        });
      },
      borderRadius: BorderRadius.circular(100),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected
              ? AppColors.primary.withValues(alpha: 0.1)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(100),
          border: Border.all(
            color: isSelected
                ? AppColors.primary
                : AppColors.textGrey.withValues(alpha: 0.3),
          ),
        ),
        child: Text(
          type,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w800,
            color: isSelected ? AppColors.primary : AppColors.textGrey,
          ),
        ),
      ),
    );
  }

  Widget _buildOddsLabels() {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            "1.0",
            style: TextStyle(
              fontSize: 10,
              color: AppColors.textGrey,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            "2.0",
            style: TextStyle(
              fontSize: 10,
              color: AppColors.textGrey,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            "3.0",
            style: TextStyle(
              fontSize: 10,
              color: AppColors.textGrey,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            "4.0",
            style: TextStyle(
              fontSize: 10,
              color: AppColors.textGrey,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            "5.0+",
            style: TextStyle(
              fontSize: 10,
              color: AppColors.textGrey,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
