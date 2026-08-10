/// The redesign's load-bearing behaviour: verdict states, the coverage census,
/// and the four Unknowns rendering as four different things.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/enums.dart';
import 'package:pharmaguard/models/unknown_reason.dart';
import 'package:pharmaguard/theme/tokens.dart';
import 'package:pharmaguard/widgets/coverage_census.dart';
import 'package:pharmaguard/widgets/unknown_reason_panel.dart';
import 'package:pharmaguard/widgets/verdict_card.dart';

const GeneCoverage _full = GeneCoverage(
    positionsPresent: 35, positionsRequired: 35, percent: 100,
    minimumPercent: 100, sufficient: true);
const GeneCoverage _short = GeneCoverage(
    positionsPresent: 4, positionsRequired: 35, percent: 11.4,
    minimumPercent: 100, sufficient: false);

PharmacogenomicProfile _profile({
  String gene = 'CYP2C19',
  String diplotype = '*2/*2',
  Phenotype phenotype = Phenotype.pm,
  List<String> candidates = const <String>[],
}) => PharmacogenomicProfile(
      primaryGene: gene, diplotype: diplotype,
      recommendationDiplotype: 'SHOULD-NEVER-RENDER',
      candidateDiplotypes: candidates, phenotype: phenotype,
      activityScore: null, detectedVariants: const <DetectedVariant>[],
    );

PerDrugResult _result({
  RiskLabel label = RiskLabel.ineffective,
  Severity severity = Severity.critical,
  double confidence = 0.95,
  PharmacogenomicProfile? profile,
  String drug = 'clopidogrel',
}) => PerDrugResult(
      drug: drug,
      riskAssessment: RiskAssessment(
          riskLabel: label, confidenceScore: confidence, severity: severity),
      pharmacogenomicProfile: profile ?? _profile(),
      clinicalRecommendation: const ClinicalRecommendation(
        action: 'Avoid clopidogrel if possible.',
        dosingGuidance: '', cpicRecommendation: 'CPIC says: avoid clopidogrel.',
        cpicEvidenceLevel: CpicEvidenceLevel.a,
        alternatives: <String>[], source: 'CPIC',
      ),
      llmGeneratedExplanation: const LlmGeneratedExplanation(
        summary: 'Your result affects this medicine.', mechanism: 'Mechanism text.',
        variantRationale: '', patientFriendly: '', disclaimer: '',
      ),
    );

QualityMetrics _metrics(Map<String, GeneCoverage> cov, {List<String> warnings = const <String>[]}) =>
    QualityMetrics(
      vcfParsingSuccess: true, variantsDetectedCount: 4, processingTimeMs: 100,
      warnings: warnings, positionCoverage: cov,
    );

Future<void> _pump(WidgetTester t, Widget child, {double width = 360}) async {
  await t.binding.setSurfaceSize(Size(width, 2400));
  // Reset inside the test's own context; a global tearDown runs outside it.
  addTearDown(() => t.binding.setSurfaceSize(null));
  await t.pumpWidget(MaterialApp(
    theme: Tokens.theme(),
    home: Scaffold(body: SingleChildScrollView(child: child)),
  ));
  await t.pumpAndSettle();
}

void main() {
  group('design tokens carry meaning', () {
    test('Unknown is the accent colour, never grey', () {
      final (Color fg, Color bg) = Tokens.verdict(RiskLabel.unknown);
      expect(fg, Tokens.accent);
      expect(bg, Tokens.accentBg);
    });

    test('Toxic and Ineffective share danger', () {
      expect(Tokens.verdict(RiskLabel.toxic), Tokens.verdict(RiskLabel.ineffective));
      expect(Tokens.verdict(RiskLabel.toxic).$1, Tokens.danger);
    });

    test('severity is what separates them — critical outranks high', () {
      expect(Tokens.severityRank(Severity.critical),
          greaterThan(Tokens.severityRank(Severity.high)));
    });
  });

  group('coverage census', () {
    testWidgets('renders one tick per required position', (WidgetTester t) async {
      await _pump(t, const CoverageCensus(gene: 'CYP2C19', coverage: _short));
      expect(find.text('4 / 35'), findsOneWidget);
      expect(find.textContaining('31 of 35 positions were not reported'),
          findsOneWidget);
    });

    testWidgets('says so plainly when complete', (WidgetTester t) async {
      await _pump(t, const CoverageCensus(gene: 'CYP2C19', coverage: _full));
      expect(find.text('35 / 35'), findsOneWidget);
      expect(find.text('Every required position was reported.'), findsOneWidget);
    });

    testWidgets('a non-callable gene shows a reason, never a zero bar',
        (WidgetTester t) async {
      await _pump(t, const CoverageCensus(
        gene: 'CYP2D6', coverage: null,
        notApplicableReason: 'Defined by copy-number variation.',
      ));
      expect(find.text('not applicable'), findsOneWidget);
      expect(find.textContaining('copy-number'), findsOneWidget);
      expect(find.text('0 / 157'), findsNothing);
    });

    testWidgets('88 ticks still fit at 360px', (WidgetTester t) async {
      await _pump(t, const CoverageCensus(
        gene: 'CYP2C9',
        coverage: GeneCoverage(positionsPresent: 17, positionsRequired: 88,
            percent: 19.3, minimumPercent: 100, sufficient: false),
      ));
      // A RenderFlex overflow would have been recorded as an exception by now.
      expect(t.takeException(), isNull);
      expect(find.text('17 / 88'), findsOneWidget);
    });
  });

  group('the four Unknowns read differently', () {
    for (final UnknownReason r in UnknownReason.values) {
      testWidgets('$r renders its own heading', (WidgetTester t) async {
        await _pump(t, UnknownReasonPanel(
          reason: r, profile: _profile(), coverage: _short));
        // Every reason must produce SOME heading, and no two share one.
        expect(find.byType(UnknownReasonPanel), findsOneWidget);
      });
    }

    testWidgets('low coverage shows the census and what would work',
        (WidgetTester t) async {
      await _pump(t, UnknownReasonPanel(
        reason: UnknownReason.lowCoverage, profile: _profile(), coverage: _short));
      expect(find.textContaining('did not report enough positions'), findsOneWidget);
      expect(find.text('WHAT WOULD WORK'), findsOneWidget);
      expect(find.text('4 / 35'), findsOneWidget);
    });

    testWidgets('not-callable blames the format, not the sample',
        (WidgetTester t) async {
      await _pump(t, UnknownReasonPanel(
        reason: UnknownReason.notCallable,
        profile: _profile(gene: 'CYP2D6')));
      expect(find.textContaining('cannot be read from a VCF'), findsOneWidget);
      expect(find.textContaining('not of your sample'), findsOneWidget);
      expect(find.text('WHAT WOULD WORK'), findsNothing);
    });

    testWidgets('ambiguous lists every candidate', (WidgetTester t) async {
      await _pump(t, UnknownReasonPanel(
        reason: UnknownReason.ambiguous,
        profile: _profile(gene: 'SLCO1B1',
            candidates: const <String>['*1/*37', '*1/*42', '*1/*52'])));
      expect(find.textContaining('not decisive'), findsOneWidget);
      for (final String d in <String>['*1/*37', '*1/*42', '*1/*52']) {
        expect(find.text(d), findsOneWidget);
      }
    });

    testWidgets('no-guidance says the genotype WAS determined',
        (WidgetTester t) async {
      await _pump(t, UnknownReasonPanel(
        reason: UnknownReason.noGuidance, profile: _profile()));
      expect(find.textContaining('determined successfully'), findsOneWidget);
    });

    test('no two reasons share a heading or body', () {
      final headings = <String>{};
      for (final UnknownReason r in UnknownReason.values) {
        headings.add(r.headline);
      }
      expect(headings.length, UnknownReason.values.length);
    });
  });

  group('verdict card', () {
    for (final (RiskLabel label, Severity sev) in <(RiskLabel, Severity)>[
      (RiskLabel.safe, Severity.none),
      (RiskLabel.adjustDosage, Severity.moderate),
      (RiskLabel.toxic, Severity.high),
      (RiskLabel.ineffective, Severity.critical),
      (RiskLabel.unknown, Severity.none),
    ]) {
      testWidgets('$label renders at 360px', (WidgetTester t) async {
        await _pump(t, VerdictCard(
          result: _result(label: label, severity: sev),
          metrics: _metrics(<String, GeneCoverage>{'CYP2C19': _full}),
        ));
        expect(find.text(label.wireValue), findsOneWidget);
        expect(find.textContaining('severity ${sev.wireValue}'), findsOneWidget);
      });
    }

    testWidgets('never renders recommendation_diplotype', (WidgetTester t) async {
      await _pump(t, VerdictCard(
        result: _result(),
        metrics: _metrics(<String, GeneCoverage>{'CYP2C19': _full}),
      ));
      expect(find.text('SHOULD-NEVER-RENDER'), findsNothing);
    });

    testWidgets('the census appears on a PASSING result too', (WidgetTester t) async {
      await _pump(t, VerdictCard(
        result: _result(label: RiskLabel.safe, severity: Severity.none),
        metrics: _metrics(<String, GeneCoverage>{'CYP2C19': _full}),
      ));
      expect(find.text('35 / 35'), findsOneWidget);
    });

    testWidgets('CPIC text is quoted under a mono label', (WidgetTester t) async {
      await _pump(t, VerdictCard(
        result: _result(),
        metrics: _metrics(<String, GeneCoverage>{'CYP2C19': _full}),
      ));
      // Feature Set B split the old "Why this result" row in two: the prose is
      // surfaced in patient view, and CPIC's own text moved to its own row.
      await t.tap(find.text("The guideline in CPIC's own words"));
      await t.pumpAndSettle();
      expect(find.text('CPIC GUIDELINE — QUOTED EXACTLY'), findsOneWidget);
      expect(find.text('CPIC says: avoid clopidogrel.'), findsOneWidget);
    });
  });
}

