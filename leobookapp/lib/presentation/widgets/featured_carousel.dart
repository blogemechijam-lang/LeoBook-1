import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:leobookapp/core/constants/app_colors.dart';
import 'package:leobookapp/core/constants/responsive_constants.dart';
import 'package:leobookapp/data/models/match_model.dart';
import 'package:leobookapp/data/models/recommendation_model.dart';
import '../screens/top_predictions_screen.dart';
import '../screens/match_details_screen.dart';
import 'package:leobookapp/core/widgets/glass_container.dart';

class FeaturedCarousel extends StatelessWidget {
  final List<MatchModel> matches;
  final List<RecommendationModel> recommendations;
  final List<MatchModel> allMatches;
  final VoidCallback? onViewAll;

  const FeaturedCarousel({
    super.key,
    required this.matches,
    required this.recommendations,
    required this.allMatches,
    this.onViewAll,
  });

  /// Sort: live first (by minute), then scheduled (by time asc), then finished (by time desc)
  List<MatchModel> get _sortedMatches {
    final sorted = List<MatchModel>.from(matches);
    sorted.sort((a, b) {
      int groupA = a.isLive ? 0 : (a.isFinished ? 2 : 1);
      int groupB = b.isLive ? 0 : (b.isFinished ? 2 : 1);
      if (groupA != groupB) return groupA.compareTo(groupB);
      // Within same group, sort by time
      if (groupA == 2) {
        return b.time.compareTo(a.time); // finished: latest first
      }
      return a.time.compareTo(b.time); // live/scheduled: earliest first
    });
    return sorted;
  }

  @override
  Widget build(BuildContext context) {
    if (matches.isEmpty) return const SizedBox.shrink();

    final displayMatches = _sortedMatches;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: EdgeInsets.symmetric(
            horizontal: Responsive.sp(context, 10),
            vertical: Responsive.sp(context, 6),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(
                    Icons.auto_awesome,
                    color: AppColors.primary,
                    size: Responsive.sp(context, 14),
                  ),
                  SizedBox(width: Responsive.sp(context, 5)),
                  Text(
                    "TOP PREDICTIONS",
                    style: TextStyle(
                      fontSize: Responsive.sp(context, 10),
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1.0,
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.white
                          : AppColors.textDark,
                    ),
                  ),
                ],
              ),
              GestureDetector(
                onTap: onViewAll ??
                    () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const TopPredictionsScreen(),
                        ),
                      );
                    },
                child: Text(
                  "VIEW ALL",
                  style: TextStyle(
                    color: AppColors.primary,
                    fontSize: Responsive.sp(context, 8),
                    fontWeight: FontWeight.w900,
                    letterSpacing: 0.8,
                  ),
                ),
              ),
            ],
          ),
        ),
        SizedBox(
          height: Responsive.sp(context, 140),
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding:
                EdgeInsets.symmetric(horizontal: Responsive.sp(context, 10)),
            itemCount: displayMatches.length,
            itemBuilder: (context, index) {
              return _FeaturedCard(match: displayMatches[index]);
            },
          ),
        ),
      ],
    );
  }
}

class _FeaturedCard extends StatefulWidget {
  final MatchModel match;
  const _FeaturedCard({required this.match});

  @override
  State<_FeaturedCard> createState() => _FeaturedCardState();
}

class _FeaturedCardState extends State<_FeaturedCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final match = widget.match;
    final cardWidth = Responsive.isDesktop(context)
        ? Responsive.dp(context, 240)
        : Responsive.sp(context, 200);

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedScale(
        scale: _isHovered ? 1.02 : 1.0,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOutCubic,
        child: GlassContainer(
          margin: EdgeInsets.only(right: Responsive.sp(context, 8)),
          borderRadius: Responsive.sp(context, 14),
          padding: EdgeInsets.zero,
          borderColor: _isHovered
              ? AppColors.primary.withValues(alpha: 0.6)
              : Colors.transparent,
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => MatchDetailsScreen(match: match),
              ),
            );
          },
          child: SizedBox(
            width: cardWidth,
            child: AspectRatio(
              aspectRatio: 16 / 10,
              child: Stack(
                children: [
                  Positioned.fill(
                    child: ClipRRect(
                      borderRadius:
                          BorderRadius.circular(Responsive.sp(context, 14)),
                      child: Stack(
                        children: [
                          Image.network(
                            "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070&auto=format&fit=crop",
                            fit: BoxFit.cover,
                            width: double.infinity,
                            height: double.infinity,
                            errorBuilder: (context, error, stackTrace) =>
                                Container(color: AppColors.backgroundDark),
                          ),
                          Container(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.topCenter,
                                end: Alignment.bottomCenter,
                                colors: [
                                  Colors.black.withValues(alpha: 0.1),
                                  Colors.black.withValues(alpha: 0.4),
                                  Colors.black.withValues(alpha: 0.95),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  Padding(
                    padding: EdgeInsets.all(Responsive.sp(context, 10)),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Flexible(
                              child: Container(
                                padding: EdgeInsets.symmetric(
                                  horizontal: Responsive.sp(context, 6),
                                  vertical: Responsive.sp(context, 2),
                                ),
                                decoration: BoxDecoration(
                                  color:
                                      AppColors.primary.withValues(alpha: 0.9),
                                  borderRadius: BorderRadius.circular(
                                      Responsive.sp(context, 4)),
                                ),
                                child: Text(
                                  (match.league ?? "LEO LEAGUE").toUpperCase(),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: Responsive.sp(context, 6),
                                    fontWeight: FontWeight.w900,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                              ),
                            ),
                            if (match.isLive)
                              Container(
                                padding: EdgeInsets.symmetric(
                                  horizontal: Responsive.sp(context, 6),
                                  vertical: Responsive.sp(context, 2),
                                ),
                                decoration: BoxDecoration(
                                  color:
                                      AppColors.liveRed.withValues(alpha: 0.9),
                                  borderRadius: BorderRadius.circular(
                                      Responsive.sp(context, 4)),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Container(
                                      width: 4,
                                      height: 4,
                                      decoration: const BoxDecoration(
                                        color: Colors.white,
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                    SizedBox(width: Responsive.sp(context, 3)),
                                    Text(
                                      "LIVE ${match.liveMinute}'",
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: Responsive.sp(context, 6),
                                        fontWeight: FontWeight.w900,
                                      ),
                                    ),
                                  ],
                                ),
                              )
                            else
                              Text(
                                match.time.toUpperCase(),
                                style: TextStyle(
                                  color: Colors.white70,
                                  fontSize: Responsive.sp(context, 7),
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                          ],
                        ),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            _buildTeam(context, match.homeTeam),
                            Padding(
                              padding: EdgeInsets.symmetric(
                                  horizontal: Responsive.sp(context, 10)),
                              child: Text(
                                match.isLive ||
                                        match.status
                                            .toLowerCase()
                                            .contains('finish')
                                    ? "${match.homeScore}:${match.awayScore}"
                                    : "VS",
                                style: TextStyle(
                                  fontSize: Responsive.sp(context, 16),
                                  fontWeight: FontWeight.w900,
                                  color: Colors.white,
                                  fontStyle: FontStyle.italic,
                                  letterSpacing: -0.5,
                                ),
                              ),
                            ),
                            _buildTeam(context, match.awayTeam),
                          ],
                        ),
                        ClipRRect(
                          borderRadius:
                              BorderRadius.circular(Responsive.sp(context, 8)),
                          child: BackdropFilter(
                            filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
                            child: Container(
                              padding: EdgeInsets.symmetric(
                                horizontal: Responsive.sp(context, 8),
                                vertical: Responsive.sp(context, 5),
                              ),
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(
                                    Responsive.sp(context, 8)),
                                border: Border.all(
                                  color: Colors.white.withValues(alpha: 0.1),
                                  width: 0.5,
                                ),
                              ),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Text(
                                          "LEO PREDICTION",
                                          style: TextStyle(
                                            fontSize:
                                                Responsive.sp(context, 5.5),
                                            color: Colors.white70,
                                            fontWeight: FontWeight.w900,
                                            letterSpacing: 0.5,
                                          ),
                                        ),
                                        Text(
                                          match.prediction?.toUpperCase() ??
                                              "N/A",
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style: TextStyle(
                                            fontSize: Responsive.sp(context, 9),
                                            color: Colors.white,
                                            fontWeight: FontWeight.w900,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  Container(
                                    padding: EdgeInsets.symmetric(
                                      horizontal: Responsive.sp(context, 6),
                                      vertical: Responsive.sp(context, 2),
                                    ),
                                    decoration: BoxDecoration(
                                      color: AppColors.primary,
                                      borderRadius: BorderRadius.circular(
                                          Responsive.sp(context, 4)),
                                    ),
                                    child: Text(
                                      match.odds ?? "1.00",
                                      style: TextStyle(
                                        fontSize: Responsive.sp(context, 9),
                                        fontWeight: FontWeight.w900,
                                        color: Colors.white,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (match.status.toLowerCase().contains('finish') &&
                      match.isPredictionAccurate)
                    Positioned(
                      top: Responsive.sp(context, 8),
                      right: Responsive.sp(context, 8),
                      child: Container(
                        padding: EdgeInsets.all(Responsive.sp(context, 3)),
                        decoration: const BoxDecoration(
                          color: AppColors.success,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.check_rounded,
                          color: Colors.white,
                          size: Responsive.sp(context, 8),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTeam(BuildContext context, String teamName) {
    final logoSize = Responsive.sp(context, 30);
    return Expanded(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: logoSize,
            height: logoSize,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.1),
              shape: BoxShape.circle,
              border: Border.all(
                color: Colors.white.withValues(alpha: 0.1),
                width: 0.5,
              ),
            ),
            child: Center(
              child: Text(
                teamName.substring(0, 1).toUpperCase(),
                style: TextStyle(
                  fontSize: Responsive.sp(context, 12),
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          SizedBox(height: Responsive.sp(context, 4)),
          Text(
            teamName.toUpperCase(),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: Responsive.sp(context, 6.5),
              fontWeight: FontWeight.w900,
              color: Colors.white,
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );
  }
}
