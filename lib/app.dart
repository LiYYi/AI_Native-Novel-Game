import 'package:flutter/material.dart';

import 'pages/simple_game_page.dart';

class NovelGameApp extends StatelessWidget {
  const NovelGameApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
      ),
      home: const SimpleGamePage(),
    );
  }
}
