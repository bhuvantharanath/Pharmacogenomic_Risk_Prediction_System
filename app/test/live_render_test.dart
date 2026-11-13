import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/screens/results_screen.dart';

/// How many genes the payload reports, and how many of them cleared coverage.
///
/// Read from the response rather than written down, so that adding a gene to
/// the requirements cannot leave these tests asserting a number the product
/// stopped producing.
int _total(AnalyzeResponse r) => r.qualityMetrics.positionCoverage.length;

int _passing(AnalyzeResponse r) => r.qualityMetrics.positionCoverage.values
    .where((GeneCoverage c) => c.sufficient)
    .length;

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
    // Derived from the payload, not hardcoded. These fixtures are captured
    // from a real run, so the gene count follows whatever the backend
    // currently requires -- Phase 9 added VKORC1 and CYP4F2 and took it from
    // seven to nine, which silently stranded a literal written here. What the
    // test is actually for is that EVERY gene is declined on a variants-only
    // file, so that is what it now says.
    expect(_passing(r), 0, reason: 'a variants-only file declined no genes');
    expect(find.textContaining('0 of ${_total(r)} genes'), findsOneWidget);
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
    // The count on screen must be the count in the payload, and this half of
    // the contrast must clear genes where the variants-only half clears none.
    //
    // Not asserted: that every gene passes. This fixture comes from a file
    // written before VKORC1 and CYP4F2 joined the requirements, so it clears
    // seven of nine — which is a fact about that file, not about the client,
    // and pinning it here would hide the next such drift rather than catch it.
    expect(_passing(r), greaterThan(0),
        reason: 'the complete-coverage half of the contrast cleared no genes');
    expect(find.textContaining('${_passing(r)} of ${_total(r)} genes'),
        findsOneWidget);
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
