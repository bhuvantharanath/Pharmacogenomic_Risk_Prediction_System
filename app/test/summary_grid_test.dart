/// The check-everything grid: ordering, and what a mixed result set looks like.
///
/// Ordering is the load-bearing part. The grid exists so someone who does not
/// know which drug to ask about can ask about all of them — and a six-row list
/// is only useful if the row that changes something is the first one they meet.
/// An alphabetical regression here would be invisible in a screenshot and
/// obvious only to the person it failed.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/enums.dart';
import 'package:pharmaguard/theme/tokens.dart';
import 'package:pharmaguard/widgets/summary_grid.dart';
import 'package:pharmaguard/widgets/view_mode.dart';
import 'package:pharmaguard/widgets/verdict_card.dart';

PerDrugResult _result(String drug, RiskLabel label, Severity severity) =>
    PerDrugResult(
      drug: drug,
      riskAssessment: RiskAssessment(
          riskLabel: label, confidenceScore: 0.9, severity: severity),
      pharmacogenomicProfile: const PharmacogenomicProfile(
        primaryGene: 'CYP2C19', diplotype: '*1/*2',
        recommendationDiplotype: null, candidateDiplotypes: <String>[],
        phenotype: Phenotype.im, activityScore: null,
        detectedVariants: <DetectedVariant>[],
      ),
      clinicalRecommendation: const ClinicalRecommendation(
        action: 'Some action.', dosingGuidance: '',
        cpicRecommendation: 'CPIC text.',
        cpicEvidenceLevel: CpicEvidenceLevel.a,
        alternatives: <String>[], source: 'CPIC',
      ),
      llmGeneratedExplanation: const LlmGeneratedExplanation(
        summary: 'Summary.', mechanism: '', variantRationale: '',
        patientFriendly: '', disclaimer: '',
      ),
    );

const QualityMetrics _metrics = QualityMetrics(
  vcfParsingSuccess: true, variantsDetectedCount: 3, processingTimeMs: 1200,
  warnings: <String>[], positionCoverage: <String, GeneCoverage>{},
);

List<String> _drugsInOrder(List<PerDrugResult> analyses) =>
    orderByConsequence(analyses).map((PerDrugResult r) => r.drug).toList();

Future<void> _pump(WidgetTester t, List<PerDrugResult> analyses,
    {double width = 360, bool expanded = false}) async {
  await t.binding.setSurfaceSize(Size(width, 4000));
  addTearDown(() => t.binding.setSurfaceSize(null));
  await t.pumpWidget(MaterialApp(
    theme: Tokens.theme(),
    home: Scaffold(
      body: SingleChildScrollView(
        child: SummaryGrid(
          analyses: analyses, metrics: _metrics,
          mode: ViewMode.patient, startExpanded: expanded),
      ),
    ),
  ));
  await t.pumpAndSettle();
}

void main() {
  group('ordering by consequence', () {
    test('urgent first, Unknown last, whatever order they arrive in', () {
      final List<PerDrugResult> arrived = <PerDrugResult>[
        _result('azathioprine', RiskLabel.safe, Severity.none),
        _result('codeine', RiskLabel.unknown, Severity.none),
        _result('simvastatin', RiskLabel.adjustDosage, Severity.moderate),
        _result('fluorouracil', RiskLabel.toxic, Severity.critical),
        _result('clopidogrel', RiskLabel.ineffective, Severity.high),
      ];

      expect(_drugsInOrder(arrived), <String>[
        'fluorouracil',  // Toxic, critical
        'clopidogrel',   // Ineffective, high — same band, lower severity
        'simvastatin',   // Adjust Dosage
        'azathioprine',  // Safe
        'codeine',       // Unknown, always last
      ]);
    });

    test('Toxic and Ineffective share a band; severity separates them', () {
      // Neither label outranks the other — they are different mechanisms, and
      // asserting a clinical priority between them is not this project's to make.
      expect(RiskLabel.toxic.consequenceRank,
          RiskLabel.ineffective.consequenceRank);

      final List<String> order = _drugsInOrder(<PerDrugResult>[
        _result('a-ineffective-critical', RiskLabel.ineffective, Severity.critical),
        _result('b-toxic-moderate', RiskLabel.toxic, Severity.moderate),
      ]);
      expect(order.first, 'a-ineffective-critical');
    });

    test('a tie falls back to alphabetical, not to arrival order', () {
      // Otherwise the same file analysed twice could list the same two results
      // in different orders, purely from how the drugs were typed.
      final List<PerDrugResult> typed = <PerDrugResult>[
        _result('simvastatin', RiskLabel.safe, Severity.none),
        _result('azathioprine', RiskLabel.safe, Severity.none),
      ];
      expect(_drugsInOrder(typed), <String>['azathioprine', 'simvastatin']);
      expect(_drugsInOrder(typed.reversed.toList()),
          <String>['azathioprine', 'simvastatin']);
    });

    test('the caller\'s list is never reordered in place', () {
      // The exported JSON must keep the order the API sent.
      final List<PerDrugResult> original = <PerDrugResult>[
        _result('codeine', RiskLabel.unknown, Severity.none),
        _result('fluorouracil', RiskLabel.toxic, Severity.critical),
      ];
      orderByConsequence(original);
      expect(original.first.drug, 'codeine');
    });

    test('the real five-drug payload orders as expected', () {
      final File payload =
          File('../test-data/demo/outputs/S6_multidrug.json');
      if (!payload.existsSync()) return; // artifact not present in this checkout

      final AnalyzeResponse r = AnalyzeResponse.fromJson(
          jsonDecode(payload.readAsStringSync()) as Map<String, dynamic>);

      // clopidogrel is Ineffective/critical; two Safe; two Unknown. The Safe
      // pair and the Unknown pair each tie, so each falls to alphabetical.
      expect(_drugsInOrder(r.analyses), <String>[
        'clopidogrel', 'fluorouracil', 'simvastatin', 'codeine', 'ibuprofen',
      ]);
    });
  });

  group('the grid as rendered', () {
    final List<PerDrugResult> mixed = <PerDrugResult>[
      _result('azathioprine', RiskLabel.safe, Severity.none),
      _result('clopidogrel', RiskLabel.ineffective, Severity.critical),
      _result('codeine', RiskLabel.unknown, Severity.none),
    ];

    testWidgets('rows appear in consequence order on screen',
        (WidgetTester t) async {
      await _pump(t, mixed);

      final double urgent = t.getTopLeft(find.text('clopidogrel')).dy;
      final double safe = t.getTopLeft(find.text('azathioprine')).dy;
      final double unknown = t.getTopLeft(find.text('codeine')).dy;

      expect(urgent, lessThan(safe));
      expect(safe, lessThan(unknown));
    });

    testWidgets('every row shows drug, verdict and severity',
        (WidgetTester t) async {
      await _pump(t, mixed);

      expect(find.text('clopidogrel'), findsOneWidget);
      expect(find.text('Ineffective'), findsOneWidget);
      expect(find.text('severity critical'), findsOneWidget);
      // Severity `none` is omitted rather than printed: "severity none" on a
      // Safe row is noise that makes the critical row harder to spot.
      expect(find.text('severity none'), findsNothing);
    });

    testWidgets('a row opens in place, and only that row',
        (WidgetTester t) async {
      await _pump(t, mixed);
      expect(find.byType(VerdictCard), findsNothing);

      await t.tap(find.text('clopidogrel'));
      await t.pumpAndSettle();
      expect(find.byType(VerdictCard), findsOneWidget);

      // Opening one row must not collapse or open the others — a user
      // comparing two results needs both open at once.
      await t.tap(find.text('codeine'));
      await t.pumpAndSettle();
      expect(find.byType(VerdictCard), findsNWidgets(2));
    });

    testWidgets('an opened card does not repeat the row it opened from',
        (WidgetTester t) async {
      await _pump(t, mixed);
      await t.tap(find.text('clopidogrel'));
      await t.pumpAndSettle();

      // The row already carries the verdict; a second copy inside the card
      // would push the detail the user tapped for further down the screen.
      expect(find.text('Ineffective'), findsOneWidget);
    });

    testWidgets('short result sets arrive already open', (WidgetTester t) async {
      await _pump(t, mixed.take(2).toList(), expanded: true);
      expect(find.byType(VerdictCard), findsNWidgets(2));
    });

    testWidgets('nothing overflows at 360px', (WidgetTester t) async {
      await _pump(t, mixed, width: 360);
      expect(TestWidgetsFlutterBinding.instance.takeException(), isNull);
    });
  });
}
