import 'package:flutter/material.dart';

import 'app_theme.dart';
import 'pages/simple_game_page.dart';

class NovelGameApp extends StatelessWidget {
  const NovelGameApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        scaffoldBackgroundColor: AppColors.canvas,
        colorScheme: ColorScheme.light(
          surface: AppColors.card,
          onSurface: AppColors.contrast,
          primary: AppColors.orangeGradientEnd,
          onPrimary: Colors.white,
          secondary: AppColors.textSecondary,
          surfaceContainerHighest: const Color(0xFFEFEFF4),
          outlineVariant: AppColors.dividerSoft,
        ),
        appBarTheme: const AppBarTheme(
          elevation: 0,
          scrolledUnderElevation: 0,
          backgroundColor: AppColors.canvas,
          foregroundColor: AppColors.contrast,
          centerTitle: false,
        ),
        cardTheme: CardThemeData(
          color: AppColors.card,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          shadowColor: Colors.black.withValues(alpha: 0.06),
        ),
      ),
      home: const SimpleGamePage(),
    );
  }
}
