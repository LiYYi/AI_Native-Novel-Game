// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_native_avg_app/app.dart';

void main() {
  testWidgets('Simple game page shows start button', (WidgetTester tester) async {
    await tester.pumpWidget(const NovelGameApp());

    expect(find.text('魅力 3'), findsOneWidget);
    expect(find.text('财力 5'), findsOneWidget);
    expect(find.text('声望 2'), findsOneWidget);
    expect(find.text('开始游戏'), findsOneWidget);
  });
}
