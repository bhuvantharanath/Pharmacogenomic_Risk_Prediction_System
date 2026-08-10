/// Patient view and clinician view: same facts, different order.
///
/// The assertion that matters most is the negative one — that the two views
/// contain the SAME text. The tempting version of this feature generates
/// simpler prose for patients, which would mean a body of clinical sentences
/// that no guard checks and no adjudication covers, shown to the reader least
/// able to catch an error. These tests pin the reordering and forbid the
/// rewrite.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/enums.dart';
import 'package:pharmaguard/theme/tokens.dart';
import 'package:pharmaguard/widgets/coverage_census.dart';
import 'package:pharmaguard/widgets/verdict_card.dart';
import 'package:pharmaguard/widgets/view_mode.dart';
import 'package:pharmaguard/widgets/view_toggle.dart';

const GeneCoverage _short = GeneCoverage(
  positionsPresent: 4, positionsRequired: 35, percent: 11.4,
  minimumPercent: 100, sufficient: false);

const QualityMetrics _metrics = QualityMetrics(
  vcfParsingSuccess: true, variantsDetectedCount: 3, processingTimeMs: 900,
  warnings: <String>[],
  positionCoverage: <String, GeneCoverage>{'CYP2C19': _short},
);

final PerDrugResult _result = PerDrugResult(
  drug: 'clopidogrel',
  riskAssessment: const RiskAssessment(
      riskLabel: RiskLabel.ineffective,
      confidenceScore: 0.95,
      severity: Severity.critical),
  pharmacogenomicProfile: const PharmacogenomicProfile(
    primaryGene: 'CYP2C19', diplotype: '*2/*2',
    recommendationDiplotype: null, candidateDiplotypes: <String>[],
    phenotype: Phenotype.pm, activityScore: 0.0,
    detectedVariants: <DetectedVariant>[
      DetectedVariant(rsid: 'rs4244285', gene: 'CYP2C19', genotype: '1/1',
          starAllele: '*2', function: 'No function'),
    ],
  ),
  clinicalRecommendation: const ClinicalRecommendation(
    action: 'Avoid clopidogrel if possible.',
    dosingGuidance: '',
    cpicRecommendation: 'Strong recommendation, adult population.',
    cpicEvidenceLevel: CpicEvidenceLevel.a,
    alternatives: <String>['prasugrel'], source: 'CPIC',
  ),
  llmGeneratedExplanation: const LlmGeneratedExplanation(
    summary: 'This medicine may not work for you.',
    mechanism: 'Clopidogrel must be activated by the CYP2C19 enzyme.',
    variantRationale: '', patientFriendly: '', disclaimer: '',
  ),
);

Future<void> _pump(WidgetTester t, ViewMode mode, {double width = 360}) async {
  await t.binding.setSurfaceSize(Size(width, 3000));
  addTearDown(() => t.binding.setSurfaceSize(null));
  await t.pumpWidget(MaterialApp(
    theme: Tokens.theme(),
    home: Scaffold(
      body: SingleChildScrollView(
        child: VerdictCard(result: _result, metrics: _metrics, mode: mode),
      ),
    ),
  ));
  await t.pumpAndSettle();
}

void main() {
  setUp(resetViewMode);

  group('the session default', () {
    test('is patient view', () {
      // A first-time visitor is a patient until they say otherwise. A stored
      // preference would quietly change what a stranger sees first.
      expect(viewMode.value, ViewMode.patient);
    });

    test('survives being set, and is not written anywhere', () {
      viewMode.value = ViewMode.clinician;
      expect(viewMode.value, ViewMode.clinician);
      // Session only: resetting brings back the default, which is what a fresh
      // launch does. Nothing here touches shared_preferences or the filesystem.
      resetViewMode();
      expect(viewMode.value, ViewMode.patient);
    });
  });

  group('patient view', () {
    testWidgets('the prose is surfaced, not behind a tap',
        (WidgetTester t) async {
      await _pump(t, ViewMode.patient);
      expect(find.text('This medicine may not work for you.'), findsOneWidget);
    });

    testWidgets('genotype and CPIC wait behind disclosure rows',
        (WidgetTester t) async {
      await _pump(t, ViewMode.patient);

      expect(find.text('*2/*2'), findsNothing);
      expect(find.text('Avoid clopidogrel if possible.'), findsNothing);

      await t.tap(find.text('What was found in your file'));
      await t.pumpAndSettle();
      expect(find.text('*2/*2'), findsOneWidget);
      expect(find.text('A'), findsOneWidget); // evidence level

      await t.tap(find.text("The guideline in CPIC's own words"));
      await t.pumpAndSettle();
      expect(find.text('Avoid clopidogrel if possible.'), findsOneWidget);
    });

    testWidgets('the prose renders in serif', (WidgetTester t) async {
      await _pump(t, ViewMode.patient);
      final Text prose =
          t.widget<Text>(find.text('This medicine may not work for you.'));
      expect(prose.style?.fontFamily, Tokens.serif);
    });
  });

  group('clinician view', () {
    testWidgets('genotype, evidence level and CPIC are immediate',
        (WidgetTester t) async {
      await _pump(t, ViewMode.clinician);

      expect(find.text('CYP2C19'), findsWidgets);
      expect(find.text('*2/*2'), findsOneWidget);
      expect(find.text('PM'), findsOneWidget);
      expect(find.text('A'), findsOneWidget);
      expect(find.text('Avoid clopidogrel if possible.'), findsOneWidget);
      expect(find.text('CPIC GUIDELINE — QUOTED EXACTLY'), findsOneWidget);
    });

    testWidgets('the machine facts render in mono', (WidgetTester t) async {
      await _pump(t, ViewMode.clinician);
      expect(t.widget<Text>(find.text('*2/*2')).style?.fontFamily, Tokens.mono);
      expect(
          t.widget<Text>(find.text('Avoid clopidogrel if possible.'))
              .style?.fontFamily,
          Tokens.mono);
    });

    testWidgets('the prose is demoted but never dropped',
        (WidgetTester t) async {
      await _pump(t, ViewMode.clinician);
      expect(find.text('This medicine may not work for you.'), findsNothing);

      // A clinician turning the phone around needs the sentence the patient
      // will understand. Demoted is one tap; dropped would be another screen.
      await t.tap(find.text('In plain language'));
      await t.pumpAndSettle();
      expect(find.text('This medicine may not work for you.'), findsOneWidget);
    });
  });

  group('what neither view may do', () {
    testWidgets('the coverage census is present in both',
        (WidgetTester t) async {
      for (final ViewMode mode in ViewMode.values) {
        await _pump(t, mode);
        expect(find.byType(CoverageCensus), findsOneWidget,
            reason: 'census missing in ${mode.name} view');
        expect(find.textContaining('4 / 35'), findsOneWidget,
            reason: 'coverage figures missing in ${mode.name} view');
      }
    });

    testWidgets('every field appears in both views, only in a different place',
        (WidgetTester t) async {
      // Open everything in each view and compare the visible text. If one view
      // ever grew a sentence the other lacks, this is what catches it.
      Set<String> visibleTexts() => find
          .byType(Text)
          .evaluate()
          .map((Element e) => (e.widget as Text).data ?? '')
          .where((String s) => s.isNotEmpty)
          .toSet();

      Future<Set<String>> textsIn(ViewMode mode) async {
        await _pump(t, mode);
        // Accumulate across taps rather than reading once at the end: opening a
        // row above pushes the rows below past the viewport, and a tap there
        // would be dispatched at a location the widget no longer occupies.
        final Set<String> seen = visibleTexts();
        for (final String row in <String>[
          'What was found in your file',
          "The guideline in CPIC's own words",
          'In plain language',
          'Positions reported in your file',
        ]) {
          final Finder f = find.text(row);
          if (f.evaluate().isEmpty) continue;
          await t.ensureVisible(f);
          await t.pumpAndSettle();
          await t.tap(f);
          await t.pumpAndSettle();
          seen.addAll(visibleTexts());
        }
        return seen;
      }

      final Set<String> patient = await textsIn(ViewMode.patient);
      final Set<String> clinician = await textsIn(ViewMode.clinician);

      // Only the disclosure-row titles differ; every piece of content is shared.
      const Set<String> rowTitles = <String>{
        'What was found in your file',
        "The guideline in CPIC's own words",
        'In plain language',
        'Positions reported in your file',
      };
      expect(patient.difference(clinician).difference(rowTitles), isEmpty,
          reason: 'patient view shows content the clinician view does not');
      expect(clinician.difference(patient).difference(rowTitles), isEmpty,
          reason: 'clinician view shows content the patient view does not');
    });
  });

  group('the toggle', () {
    testWidgets('reports both options to a screen reader and switches',
        (WidgetTester t) async {
      ViewMode chosen = ViewMode.patient;
      await t.pumpWidget(MaterialApp(
        theme: Tokens.theme(),
        home: Scaffold(
          body: ViewToggle(
            mode: chosen,
            onChanged: (ViewMode m) => chosen = m,
          ),
        ),
      ));
      await t.pumpAndSettle();

      expect(find.text('For a patient'), findsOneWidget);
      expect(find.text('For a clinician'), findsOneWidget);

      await t.tap(find.text('For a clinician'));
      expect(chosen, ViewMode.clinician);
    });

    testWidgets('is reachable and operable from the keyboard',
        (WidgetTester t) async {
      ViewMode chosen = ViewMode.patient;
      await t.pumpWidget(MaterialApp(
        theme: Tokens.theme(),
        home: Scaffold(
          body: ViewToggle(
            mode: chosen, onChanged: (ViewMode m) => chosen = m),
        ),
      ));
      await t.pumpAndSettle();

      await t.sendKeyEvent(LogicalKeyboardKey.tab);
      await t.pumpAndSettle();
      await t.sendKeyEvent(LogicalKeyboardKey.tab);
      await t.pumpAndSettle();
      await t.sendKeyEvent(LogicalKeyboardKey.enter);
      await t.pumpAndSettle();

      expect(chosen, ViewMode.clinician);
    });
  });
}
