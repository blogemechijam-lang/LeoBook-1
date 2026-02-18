import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:leobookapp/core/constants/app_colors.dart';
import 'package:leobookapp/core/constants/responsive_constants.dart';
import 'package:leobookapp/data/models/match_model.dart';
import 'package:leobookapp/data/models/recommendation_model.dart';
import 'package:leobookapp/data/repositories/data_repository.dart';
import '../screens/top_predictions_screen.dart';
import '../screens/match_details_screen.dart';
import '../screens/team_screen.dart';
import '../screens/league_screen.dart';
import 'package:leobookapp/core/widgets/glass_container.dart';

class FeaturedCarousel extends StatelessWidget {
  final List<MatchModel> matches;
  final List<RecommendationModel> recommendations;
  final List<MatchModel> allMatches;

  const FeaturedCarousel({
    super.key,
    required this.matches,
    required this.recommendations,
    required this.allMatches,
  });

  @override
  Widget build(BuildContext context) {
    if (matches.isEmpty) return const SizedBox.shrink();

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
                onTap: () {
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
            itemCount: matches.length,
            itemBuilder: (context, index) {
              return _buildFeaturedCard(context, matches[index]);
            },
          ),
        ),
      ],
    );
  }

  Widget _buildFeaturedCard(BuildContext context, MatchModel match) {
    return GlassContainer(
      margin: EdgeInsets.only(right: Responsive.sp(context, 8)),
      borderRadius: Responsive.sp(context, 14),
      padding: EdgeInsets.zero,
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => MatchDetailsScreen(match: match),
          ),
        );
      },
      child: SizedBox(
        width: Responsive.sp(context, 200),
        child: AspectRatio(
          aspectRatio: 16 / 10,
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
                      Colors.transparent,
                      Colors.black.withValues(alpha: 0.2),
                      Colors.black.withValues(alpha: 0.85),
                    ],
                  ),
                ),
              ),
              Padding(
                padding: EdgeInsets.all(Responsive.sp(context, 10)),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Top: League & Time
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Flexible(
                          child: GestureDetector(
                            onTap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => LeagueScreen(
                                    leagueId: match.league ?? "LEAGUE",
                                    leagueName: match.league ?? "LEAGUE",
                                  ),
                                ),
                              );
                            },
                            child: Container(
                              padding: EdgeInsets.symmetric(
                                horizontal: Responsive.sp(context, 6),
                                vertical: Responsive.sp(context, 2),
                              ),
                              decoration: BoxDecoration(
                                color: AppColors.primary.withValues(alpha: 0.8),
                                borderRadius: BorderRadius.circular(
                                    Responsive.sp(context, 12)),
                                border: Border.all(
                                  color: Colors.white.withValues(alpha: 0.15),
                                  width: 0.5,
                                ),
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
                        ),
                        SizedBox(width: Responsive.sp(context, 4)),
                        Flexible(
                          child: Text(
                            "${match.date} • ${match.time}",
                            maxLines: 1,
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: Responsive.sp(context, 7),
                              fontWeight: FontWeight.w900,
                              shadows: const [
                                Shadow(color: Colors.black87, blurRadius: 4),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),

                    // Middle: Teams
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _buildFeaturedTeam(context, match.homeTeam, true),
                        Padding(
                          padding: EdgeInsets.symmetric(
                              horizontal: Responsive.sp(context, 8)),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                match.displayStatus == "FINISHED" ||
                                        match.isLive
                                    ? "${match.homeScore} : ${match.awayScore}"
                                    : "VS",
                                style: TextStyle(
                                  fontSize: Responsive.sp(context, 14),
                                  fontWeight: FontWeight.w900,
                                  color: Colors.white,
                                  fontStyle: FontStyle.italic,
                                  shadows: const [
                                    Shadow(color: Colors.black, blurRadius: 6),
                                  ],
                                ),
                              ),
                              if (match.displayStatus.isNotEmpty)
                                Text(
                                  match.displayStatus,
                                  style: TextStyle(
                                    fontSize: Responsive.sp(context, 7),
                                    fontWeight: FontWeight.w900,
                                    color: AppColors.primary,
                                    letterSpacing: 0.3,
                                  ),
                                ),
                            ],
                          ),
                        ),
                        _buildFeaturedTeam(context, match.awayTeam, false),
                      ],
                    ),

                    // Bottom: Prediction
                    ClipRRect(
                      borderRadius:
                          BorderRadius.circular(Responsive.sp(context, 10)),
                      child: Container(
                        padding: EdgeInsets.symmetric(
                          horizontal: Responsive.sp(context, 10),
                          vertical: Responsive.sp(context, 6),
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.1),
                          borderRadius:
                              BorderRadius.circular(Responsive.sp(context, 10)),
                          border: Border.all(
                            color: Colors.white.withValues(alpha: 0.15),
                            width: 0.5,
                          ),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    "LEO PREDICTION",
                                    style: TextStyle(
                                      fontSize: Responsive.sp(context, 6),
                                      color:
                                          Colors.white.withValues(alpha: 0.7),
                                      fontWeight: FontWeight.w900,
                                      letterSpacing: 0.8,
                                    ),
                                  ),
                                  Text(
                                    match.prediction ?? "N/A",
                                    style: TextStyle(
                                      fontSize: Responsive.sp(context, 10),
                                      color: Colors.white,
                                      fontWeight: FontWeight.w700,
                                    ),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),
                            Container(
                              padding: EdgeInsets.symmetric(
                                horizontal: Responsive.sp(context, 8),
                                vertical: Responsive.sp(context, 3),
                              ),
                              decoration: BoxDecoration(
                                color: AppColors.primary,
                                borderRadius: BorderRadius.circular(
                                    Responsive.sp(context, 6)),
                                border: Border.all(
                                    color: Colors.white24, width: 0.5),
                              ),
                              child: Text(
                                match.odds ?? "1.00",
                                style: TextStyle(
                                  fontSize: Responsive.sp(context, 10),
                                  fontWeight: FontWeight.w900,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              if (match.status.toLowerCase().contains('finish') &&
                  match.isPredictionAccurate)
                Positioned(
                  top: 0,
                  right: 0,
                  child: Container(
                    padding: EdgeInsets.symmetric(
                      horizontal: Responsive.sp(context, 6),
                      vertical: Responsive.sp(context, 2),
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.success,
                      borderRadius: BorderRadius.only(
                        topRight: Radius.circular(Responsive.sp(context, 14)),
                        bottomLeft: Radius.circular(Responsive.sp(context, 6)),
                      ),
                    ),
                    child: Text(
                      "ACCURATE",
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: Responsive.sp(context, 6),
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeaturedTeam(
      BuildContext context, String teamName, bool isHome) {
    final logoSize = Responsive.sp(context, 32);
    return Expanded(
      child: GestureDetector(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => TeamScreen(
                teamName: teamName,
                repository: context.read<DataRepository>(),
              ),
            ),
          );
        },
        child: Column(
          children: [
            Container(
              width: logoSize,
              height: logoSize,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.1),
                shape: BoxShape.circle,
                border: Border.all(
                  color: Colors.white.withValues(alpha: 0.2),
                  width: 0.5,
                ),
              ),
              child: Center(
                child: Text(
                  teamName.substring(0, 1).toUpperCase(),
                  style: TextStyle(
                    fontSize: Responsive.sp(context, 14),
                    fontWeight: FontWeight.w900,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
            SizedBox(height: Responsive.sp(context, 3)),
            Text(
              teamName.toUpperCase(),
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: Responsive.sp(context, 7),
                fontWeight: FontWeight.w900,
                color: Colors.white,
                letterSpacing: 0.3,
                shadows: const [
                  Shadow(color: Colors.black87, blurRadius: 4),
                ],
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}
