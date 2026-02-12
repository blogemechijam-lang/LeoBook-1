import 'package:flutter/material.dart';

class AppColors {
  static const Color primary = Color(0xFF137FEC);
  static const Color electricBlue = primary; // Brand Identity v4

  static const Color backgroundLight = Color(0xFFF6F7F8);
  static const Color backgroundDark = Color(0xFF101922);
  static const Color cardDark = Color(0xFF182430);

  // States & Semantic
  static const Color liveRed = Color(0xFFFF3B30); // Stitch v4 Error/Live Red
  static const Color successGreen = Color(
    0xFF34C759,
  ); // Stitch v4 Success Green
  static const Color accentBlue = Color(0xFF00D2FF); // From HTML Design

  static const Color textDark = Color(0xFF0F172A); // Slate 900
  static const Color textLight = Color(0xFFF1F5F9); // Slate 100
  static const Color textGrey = Color(0xFF64748B); // Slate 500

  static const Color warning = Color(0xFFEAB308); // Yellow 500
  static const Color success = successGreen; // Alias for backward compatibility

  static const Color aiPurple = Color(0xFF8B5CF6);
  static const Color accentYellow = Color(
    0xFFFFCC00,
  ); // Yellow/Orange for stars/ratings
}
