import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/screens/results_screen.dart';

void main() {
  testWidgets('live S2 payload renders the coverage gate honestly', (WidgetTester tester) async {
    final String raw = File('../test-data/demo/outputs/S2_variants_only.json').readAsStringSync();
    final AnalyzeResponse r = AnalyzeResponse.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    await tester.pumpWidget(MaterialApp(home: ResultsScreen(response: r)));
    await tester.pumpAndSettle();
    expect(find.textContaining('appears to list only variants'), findsOneWidget);
    // The variants-only alert is tall, so the coverage card sits below the fold
    // in a lazily-built list. Scrolling asserts a presenter can actually reach it.
    await tester.dragUntilVisible(
      find.text('Input coverage'),
      find.byType(Scrollable).first,
      const Offset(0, -200),
    );
    expect(find.text('Input coverage'), findsOneWidget);
    expect(find.textContaining('0 of 7 genes'), findsOneWidget);
  });

  testWidgets('live S1 payload renders a confident result', (WidgetTester tester) async {
    final String raw = File('../test-data/demo/outputs/S1_confident.json').readAsStringSync();
    final AnalyzeResponse r = AnalyzeResponse.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    await tester.pumpWidget(MaterialApp(home: ResultsScreen(response: r)));
    await tester.pumpAndSettle();
    expect(find.text('Ineffective'), findsWidgets);
    await tester.dragUntilVisible(
      find.text('Input coverage'),
      find.byType(Scrollable).first,
      const Offset(0, -200),
    );
    expect(find.textContaining('7 of 7 genes'), findsOneWidget);
    expect(find.textContaining('appears to list only variants'), findsNothing);
  });

  testWidgets('live S4 payload: Unknown even though coverage passes', (WidgetTester tester) async {
    final String raw = File('../test-data/demo/outputs/S4_dpyd_indeterminate.json').readAsStringSync();
    final AnalyzeResponse r = AnalyzeResponse.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    await tester.pumpWidget(MaterialApp(home: ResultsScreen(response: r)));
    await tester.pumpAndSettle();
    expect(find.text('Unknown'), findsWidgets);
  });
}
