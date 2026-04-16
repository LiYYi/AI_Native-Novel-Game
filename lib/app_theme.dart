import 'package:flutter/material.dart';

/// Finexy-inspired palette: light gray canvas, white cards, orange gradient accent,
/// deep purple-black for contrast.
abstract final class AppColors {
  static const Color canvas = Color(0xFFF5F5F7);
  static const Color card = Color(0xFFFFFFFF);
  static const Color contrast = Color(0xFF1A1625);
  static const Color orangeGradientStart = Color(0xFFFF8A50);
  static const Color orangeGradientEnd = Color(0xFFFF5E3A);
  static const Color textSecondary = Color(0xFF6B6B76);
  static const Color dividerSoft = Color(0xFFE8E8ED);

  static const LinearGradient orangeGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [orangeGradientStart, orangeGradientEnd],
  );
}
