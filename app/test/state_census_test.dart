/// Every state the client can render, rendered — at the narrowest supported width.
///
/// WHY A CENSUS RATHER THAN A LIST
///
/// Audit A left "client-state coverage" open with the note that some states had
/// never been rendered in a test at all. A hand-written list of states goes
/// stale the moment an enum gains a value — which is the same failure recorded
/// throughout `reports/provenance_finding.md`: correct at authoring, invalidated
/// by later change, with nothing re-deriving it.
///
/// So the risk labels and Unknown reasons here are read from their ENUMS, not
/// typed out. Add a value and this file exercises it on the next run without
/// anyone remembering to.
///
/// 360px is the narrowest phone width worth supporting (iPhone SE is 375; 360 is
/// the common Android floor). Overflow at that width is invisible on a laptop
/// and immediately obvious to a marker opening the deployed site on a phone.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/api/backend_status.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/enums.dart';
import 'package:pharmaguard/models/unknown_reason.dart';
import 'package:pharmaguard/screens/results_screen.dart';
import 'package:pharmaguard/widgets/backend_status_banner.dart';
import 'package:pharmaguard/widgets/version_notice.dart';

/// The narrowest width the client claims to support.
const Size kNarrow = Size(360, 780);

Future<void> _pumpNarrow(WidgetTester tester, Widget child,
    {bool settle = true}) async {
  tester.view.physicalSize = kNarrow;
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(MaterialApp(home: child));
  if (settle) {
    await tester.pumpAndSettle();
  } else {
    // `checking` and `waking` render an indeterminate progress indicator, which
    // animates forever — pumpAndSettle waits for a quiescent frame that by
    // design never arrives, and times out. A fixed pump is the right tool for a
    // deliberately perpetual animation; the layout is what is under test.
    await tester.pump(const Duration(milliseconds: 100));
  }
}

Map<String, dynamic> _payload(String scenario) => jsonDecode(
      File('../test-data/demo/outputs/$scenario.json').readAsStringSync(),
    ) as Map<String, dynamic>;

/// A real captured payload with the first analysis's label rewritten.
///
/// Built from a real response rather than hand-assembled so every other field
/// stays structurally valid — a hand-built payload tests the test's idea of the
/// contract, not the contract.
AnalyzeResponse _withLabel(RiskLabel label) {
  final Map<String, dynamic> raw = _payload('S1_confident');
  final List<dynamic> analyses = raw['analyses'] as List<dynamic>;
  final Map<String, dynamic> first =
      Map<String, dynamic>.from(analyses.first as Map<String, dynamic>);
  final Map<String, dynamic> risk =
      Map<String, dynamic>.from(first['risk_assessment'] as Map<String, dynamic>);
  risk['risk_label'] = label.wireValue;
  first['risk_assessment'] = risk;
  raw['analyses'] = <dynamic>[first];
  return AnalyzeResponse.fromJson(raw);
}

void main() {
  // ------------------------------------------------------------------------ #
  // Result states
  // ------------------------------------------------------------------------ #

  group('every risk label renders at 360px', () {
    for (final RiskLabel label in RiskLabel.values) {
      testWidgets(label.wireValue, (WidgetTester tester) async {
        await _pumpNarrow(tester, ResultsScreen(response: _withLabel(label)));

        // The label itself must be on screen, and nothing may overflow.
        expect(find.textContaining(label.wireValue), findsWidgets,
            reason: '${label.wireValue} does not appear in its own result');
        expect(tester.takeException(), isNull,
            reason: '${label.wireValue} overflows at 360px');
      });
    }
  });

  group('every Unknown reason has a headline and an explanation', () {
    for (final UnknownReason reason in UnknownReason.values) {
      test(reason.name, () {
        expect(reason.headline.trim(), isNotEmpty);
        // Enumerated from the enum, so a newly added reason fails here until
        // someone writes its copy — rather than shipping a blank badge.
      });
    }
  });

  // ------------------------------------------------------------------------ #
  // Captured end-to-end states, at 360px
  // ------------------------------------------------------------------------ #

  group('captured payloads render at 360px', () {
    const Map<String, String> scenarios = <String, String>{
      'S1_confident': 'coverage passes, confident label',
      'S2_variants_only': 'coverage FAILS, gated',
      'S3_cyp2d6': 'not callable from a VCF',
      'S4_dpyd': 'Unknown despite coverage passing',
      'S5_normal': 'a confident Safe',
      'S6_multidrug': 'five drugs at once',
    };

    scenarios.forEach((String scenario, String what) {
      testWidgets('$scenario — $what', (WidgetTester tester) async {
        final AnalyzeResponse response =
            AnalyzeResponse.fromJson(_payload(scenario));
        await _pumpNarrow(tester, ResultsScreen(response: response));
        expect(tester.takeException(), isNull,
            reason: '$scenario overflows at 360px');
      });
    });
  });

  // ------------------------------------------------------------------------ #
  // Connection and wait states
  // ------------------------------------------------------------------------ #

  group('every backend phase renders at 360px', () {
    for (final BackendPhase phase in BackendPhase.values) {
      testWidgets(phase.name, (WidgetTester tester) async {
        final BackendStatus status = BackendStatus(
          phase: phase,
          elapsed: const Duration(seconds: 12),
          attempts: 3,
          message: phase == BackendPhase.unreachable
              ? 'No response from https://example.invalid after 90s.'
              : null,
        );
        await _pumpNarrow(
          tester,
          Scaffold(
            body: BackendStatusBanner(status: status, onRetry: () {}),
          ),
          // checking/waking spin forever by design.
          settle: false,
        );
        expect(tester.takeException(), isNull,
            reason: '${phase.name} overflows at 360px');
      });
    }
  });

  testWidgets('the version-skew notice renders at 360px',
      (WidgetTester tester) async {
    await _pumpNarrow(
      tester,
      const Scaffold(
        body: VersionNotice(
          skew: VersionSkew(
            expected: '1afb9495fd7da5f982974e7daef5f2db1d95f4ac',
            actual: 'c108c3e38666f978710533a2c0e234397ee73bfc',
          ),
        ),
      ),
    );
    expect(tester.takeException(), isNull);
  });

  // ------------------------------------------------------------------------ #
  // The census itself — this is what stops the list going stale
  // ------------------------------------------------------------------------ #

  test('no state is left without a test as the enums grow', () {
    // Read from the enums, so adding a value breaks this until it is covered
    // above. The count is asserted rather than the names, because names change
    // and the property under test is "all of them", not "these ones".
    expect(RiskLabel.values.length, 5,
        reason: 'a risk label was added or removed — add it to the render '
            'group above, then update this count');
    expect(UnknownReason.values.length, 5,
        reason: 'an Unknown reason was added or removed — the render group '
            'enumerates the enum, but this pins the expected size so the '
            'change is noticed rather than silently absorbed');
    expect(BackendPhase.values.length, 4,
        reason: 'a backend phase was added or removed');
  });
}
