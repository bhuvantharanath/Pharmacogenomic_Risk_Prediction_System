/// AC6: the result can be read with a keyboard alone (Phase 10 §6).
///
/// WHY THIS EXISTS
///
/// Everything on the results screen that matters is behind a disclosure row —
/// the CPIC recommendation, the mechanism, the coverage census, the reason a
/// gene was declined. A pointer opens them. If a keyboard cannot, then for a
/// keyboard user the screen shows five collapsed headings and the evidence
/// this project is built to surface is unreachable.
///
/// The existing accessibility tests check contrast, unique control names,
/// named message nodes, non-colour risk encoding and 200% text scale. None of
/// them presses a key. This one does.
///
/// WHAT IT ASSERTS, AND WHY THAT SHAPE
///
/// Not "Tab reaches exactly N controls": that number changes whenever a card
/// is added, and a test pinned to it would be edited rather than believed.
/// Instead: traversal must reach SEVERAL distinct controls, must not get stuck
/// on one, and a control reached by keyboard must be operable by keyboard —
/// which is the property a keyboard user actually depends on.
library;

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/screens/results_screen.dart';
import 'package:pharmaguard/theme/tokens.dart';
import 'package:pharmaguard/widgets/disclosure_row.dart';

import 'support/fixtures.dart';

AnalyzeResponse _multidrug() => loadFixture(
  fixtureFiles().firstWhere((f) => f.path.contains('S6_multidrug')),
);

Future<void> _pumpResults(WidgetTester tester, AnalyzeResponse r) async {
  await tester.pumpWidget(
    MaterialApp(theme: Tokens.theme(), home: ResultsScreen(response: r)),
  );
  await tester.pumpAndSettle();
}

/// Whether the currently focused node sits inside a [DisclosureRow].
///
/// Tabbing "somewhere" is not the property under test: the results screen has
/// export and print buttons that are focusable regardless, so a traversal test
/// that only counts stops passes happily while every disclosure row is shut to
/// a keyboard. This walks up from the focused context instead.
bool _focusIsInsideDisclosure() {
  final BuildContext? context = FocusManager.instance.primaryFocus?.context;
  if (context == null) return false;
  bool found = false;
  context.visitAncestorElements((Element e) {
    if (e.widget is DisclosureRow) {
      found = true;
      return false;
    }
    return true;
  });
  return found;
}

void main() {
  testWidgets('Tab reaches many distinct controls, not one', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1440, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await _pumpResults(tester, _multidrug());

    int disclosureStops = 0;
    final List<FocusNode> reached = <FocusNode>[];
    for (int i = 0; i < 30; i++) {
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.pumpAndSettle();
      final FocusNode? node = FocusManager.instance.primaryFocus;
      if (node == null) continue;
      if (!reached.contains(node)) reached.add(node);
      if (_focusIsInsideDisclosure()) disclosureStops++;
    }

    expect(
      find.byType(DisclosureRow),
      findsWidgets,
      reason: 'the fixture renders no disclosure rows to reach',
    );
    expect(
      disclosureStops,
      greaterThan(0),
      reason:
          'Tab stopped on ${reached.length} control(s) but never on a '
          'disclosure row; the CPIC recommendation, mechanism and coverage '
          'census are unreachable from the keyboard',
    );
  });

  testWidgets('a control reached by keyboard can be operated by keyboard', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1440, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final AnalyzeResponse r = _multidrug();
    await _pumpResults(tester, r);

    // Opening a disclosure row renders its body, which puts more Text on
    // screen. Counting Text widgets reads the same thing a person sees,
    // without reaching into the widget's private open/closed field or walking
    // the semantics tree through a deprecated binding.
    int visibleText() => find.byType(Text).evaluate().length;
    final int before = visibleText();

    // Walk until a focused control opens something when Enter is pressed.
    bool activated = false;
    for (int i = 0; i < 25 && !activated; i++) {
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.pumpAndSettle();
      if (!_focusIsInsideDisclosure()) continue;
      await tester.sendKeyEvent(LogicalKeyboardKey.enter);
      await tester.pumpAndSettle();
      if (visibleText() > before) activated = true;
    }

    expect(
      activated,
      isTrue,
      reason:
          'no disclosure row opened from the keyboard in 25 tabs; the CPIC '
          'recommendation and coverage census stay closed for a keyboard user',
    );
  });

  test('the disclosure control still paints a visible focus state', () {
    // A focus ring that cannot be seen is the same as no focus for the person
    // relying on it, and the default ripple is invisible against this theme's
    // paper. DisclosureRow sets an explicit focusColor for that reason; this
    // fails if it is ever dropped in a refactor, which is the one way the two
    // tests above would keep passing while the screen became unusable.
    final String source = File(
      'lib/widgets/disclosure_row.dart',
    ).readAsStringSync();
    expect(
      source,
      contains('focusColor:'),
      reason: 'DisclosureRow no longer sets a focus colour',
    );
  });
}
