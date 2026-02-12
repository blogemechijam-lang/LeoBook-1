import 'package:flutter_bloc/flutter_bloc.dart';
import 'search_state.dart';
import 'package:leobookapp/data/models/match_model.dart';
import 'package:leobookapp/data/models/recommendation_model.dart';

class SearchCubit extends Cubit<SearchState> {
  final List<MatchModel> allMatches;
  final List<RecommendationModel> allRecommendations;
  List<String> _recentSearches = [];

  SearchCubit({required this.allMatches, required this.allRecommendations})
    : super(
        SearchInitial(
          recentSearches: [],
          popularTeams: _getPopularTeams(allMatches),
        ),
      );

  void search(String query) {
    if (query.isEmpty) {
      emit(
        SearchInitial(
          recentSearches: _recentSearches,
          popularTeams: _getPopularTeams(allMatches),
        ),
      );
      return;
    }

    emit(SearchLoading());

    final matchedMatches = allMatches.where((m) {
      final q = query.toLowerCase();
      return m.homeTeam.toLowerCase().contains(q) ||
          m.awayTeam.toLowerCase().contains(q) ||
          (m.league?.toLowerCase().contains(q) ?? false);
    }).toList();

    final matchedLeagues = allMatches
        .where(
          (m) => m.league?.toLowerCase().contains(query.toLowerCase()) ?? false,
        )
        .map((m) => m.league!)
        .toSet()
        .toList();

    emit(
      SearchResults(
        query: query,
        matchedMatches: matchedMatches,
        matchedLeagues: matchedLeagues,
        recentSearches: _recentSearches,
      ),
    );
  }

  void addRecentSearch(String query) {
    if (query.trim().isEmpty) return;
    if (!_recentSearches.contains(query)) {
      _recentSearches.insert(0, query);
      if (_recentSearches.length > 5) {
        _recentSearches.removeLast();
      }
    }
  }

  void clearRecentSearches() {
    _recentSearches = [];
    if (state is SearchInitial) {
      emit(
        SearchInitial(
          recentSearches: [],
          popularTeams: (state as SearchInitial).popularTeams,
        ),
      );
    } else if (state is SearchResults) {
      final s = state as SearchResults;
      emit(
        SearchResults(
          query: s.query,
          matchedMatches: s.matchedMatches,
          matchedLeagues: s.matchedLeagues,
          recentSearches: [],
        ),
      );
    }
  }

  void removeRecentSearch(String term) {
    _recentSearches.remove(term);
    if (state is SearchInitial) {
      emit(
        SearchInitial(
          recentSearches: List.from(_recentSearches),
          popularTeams: (state as SearchInitial).popularTeams,
        ),
      );
    } else if (state is SearchResults) {
      final s = state as SearchResults;
      emit(
        SearchResults(
          query: s.query,
          matchedMatches: s.matchedMatches,
          matchedLeagues: s.matchedLeagues,
          recentSearches: List.from(_recentSearches),
        ),
      );
    }
  }

  static List<MatchModel> _getPopularTeams(List<MatchModel> matches) {
    // Logic: Return first 6 matches to represent "Popular Teams" for demo/reference
    // In real app, this could be based on search frequency
    return matches.take(6).toList();
  }
}
