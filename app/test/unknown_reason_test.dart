/// Each Unknown state must render as ITSELF.
///
/// Conflating them in the UI would repeat, where the user can see it, the
/// no-data/indeterminate conflation the backend found in three separate layers.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/enums.dart';
import 'package:pharmaguard/models/unknown_reason.dart';
import 'package:pharmaguard/widgets/unknown_panel.dart';

PharmacogenomicProfile _profile({
  String gene = 'CYP2C19',
  String diplotype = 'Unknown',
  List<String> candidates = const <String>[],
}) => PharmacogenomicProfile(
  primaryGene: gene,
  diplotype: diplotype,
  recommendationDiplotype: null,
  candidateDiplotypes: candidates,
  phenotype: Phenotype.unknown,
  activityScore: null,
  detectedVariants: const <DetectedVariant>[],
);

PerDrugResult _result({
  required PharmacogenomicProfile profile,
  String action = 'See recommendation',
  String source = 'CPIC',
}) => PerDrugResult(
  drug: 'clopidogrel',
  riskAssessment: const RiskAssessment(
    riskLabel: RiskLabel.unknown,
    confidenceScore: 0,
    severity: Severity.none,
  ),
  pharmacogenomicProfile: profile,
  clinicalRecommendation: ClinicalRecommendation(
    action: action,
    dosingGuidance: '',
    cpicRecommendation: '',
    cpicEvidenceLevel: CpicEvidenceLevel.unknown,
    alternatives: const <String>[],
    source: source,
  ),
  llmGeneratedExplanation: const LlmGeneratedExplanation(
    summary: '', mechanism: '', variantRationale: '',
    patientFriendly: '', disclaimer: '',
  ),
);

QualityMetrics _metrics({
  List<String> warnings = const <String>[],
  Map<String, GeneCoverage> coverage = const <String, GeneCoverage>{},
}) => QualityMetrics(
  vcfParsingSuccess: true,
  variantsDetectedCount: 4,
  processingTimeMs: 100,
  warnings: warnings,
  positionCoverage: coverage,
);

const GeneCoverage _short = GeneCoverage(
  positionsPresent: 4,
  positionsRequired: 35,
  percent: 11.4,
  minimumPercent: 100,
  sufficient: false,
);

void main() {
  group('classifyUnknown distinguishes all four states', () {
    test('low coverage wins, and comes from the TYPED field not prose', () {
      final UnknownReason r = classifyUnknown(
        _result(profile: _profile()),
        _metrics(coverage: <String, GeneCoverage>{'CYP2C19': _short}),
      );
      expect(r, UnknownReason.lowCoverage);
      expect(r.isActionable, isTrue, reason: 'the user can fix this one');
      expect(r.callToAction, isNotNull);
    });

    test('CYP2D6 structural variation is not callable', () {
      expect(
        classifyUnknown(
          _result(profile: _profile(gene: 'CYP2D6')),
          _metrics(warnings: <String>[
            'CYP2D6 structural/copy-number variation cannot be resolved from '
                'unphased VCF; outside diplotype input planned',
          ]),
        ),
        UnknownReason.notCallable,
      );
    });

    test('discordant candidates are ambiguous', () {
      expect(
        classifyUnknown(
          _result(
            profile: _profile(
              gene: 'SLCO1B1',
              diplotype: 'Undetermined (4 equally likely)',
              candidates: const <String>['*1/*37', '*1/*42', '*1/*52', '*1/*56'],
            ),
          ),
          _metrics(warnings: <String>[
            'SLCO1B1: candidate diplotypes disagree about function',
          ]),
        ),
        UnknownReason.ambiguous,
      );
    });

    test('absent CPIC guidance is its own state', () {
      expect(
        classifyUnknown(
          _result(
            profile: _profile(gene: 'CYP2C9', diplotype: '*1/*1'),
            action: 'No CPIC recommendation matched the called phenotype',
            source: 'CPIC',
          ),
          _metrics(),
        ),
        UnknownReason.noGuidance,
      );
    });

    test('an unexplained Unknown says so rather than guessing', () {
      expect(
        classifyUnknown(_result(profile: _profile()), _metrics()),
        UnknownReason.unspecified,
      );
    });

    test('no two states share a headline or an explanation', () {
      final Set<String> heads = UnknownReason.values.map((UnknownReason r) => r.headline).toSet();
      final Set<String> texts = UnknownReason.values.map((UnknownReason r) => r.explanation).toSet();
      expect(heads.length, UnknownReason.values.length);
      expect(texts.length, UnknownReason.values.length);
    });

    test('only low coverage is actionable', () {
      for (final UnknownReason r in UnknownReason.values) {
        expect(r.isActionable, r == UnknownReason.lowCoverage, reason: '$r');
        expect(r.callToAction != null, r == UnknownReason.lowCoverage, reason: '$r');
      }
    });
  });

  group('UnknownPanel renders each state distinctly', () {
    Future<void> pump(WidgetTester tester, UnknownPanel panel) =>
        tester.pumpWidget(MaterialApp(home: Scaffold(body: SingleChildScrollView(child: panel))));

    testWidgets('low coverage shows the numbers and what to upload', (WidgetTester tester) async {
      await pump(tester, UnknownPanel(
        reason: UnknownReason.lowCoverage,
        profile: _profile(),
        coverage: _short,
      ));
      expect(find.textContaining('4 of 35'), findsOneWidget);
      expect(find.textContaining('needs 100%'), findsOneWidget);
      expect(find.textContaining('ALL positions'), findsOneWidget);
    });

    testWidgets('ambiguous lists every candidate, never just one', (WidgetTester tester) async {
      await pump(tester, UnknownPanel(
        reason: UnknownReason.ambiguous,
        profile: _profile(
          gene: 'SLCO1B1',
          candidates: const <String>['*1/*37', '*1/*42', '*1/*52', '*1/*56'],
        ),
      ));
      expect(find.text('4 equally likely genotypes'), findsOneWidget);
      for (final String d in <String>['*1/*37', '*1/*42', '*1/*52', '*1/*56']) {
        expect(find.text(d), findsOneWidget, reason: '$d must be visible');
      }
    });

    testWidgets('not-callable offers no false hope of a fix', (WidgetTester tester) async {
      await pump(tester, UnknownPanel(
        reason: UnknownReason.notCallable,
        profile: _profile(gene: 'CYP2D6'),
      ));
      expect(find.textContaining('cannot represent'), findsOneWidget);
      expect(find.byIcon(Icons.lightbulb_outline), findsNothing,
          reason: 'no call to action when the user cannot act');
    });

    testWidgets('no-guidance says the genotype WAS determined', (WidgetTester tester) async {
      await pump(tester, UnknownPanel(
        reason: UnknownReason.noGuidance,
        profile: _profile(diplotype: '*1/*1'),
      ));
      expect(find.textContaining('determined successfully'), findsOneWidget);
    });
  });

  group('severity ranking survives the shared colour', () {
    test('critical outranks high', () {
      expect(severityRank(Severity.critical), greaterThan(severityRank(Severity.high)));
    });
    test('the ranking is strictly ordered', () {
      const List<Severity> order = <Severity>[
        Severity.none, Severity.low, Severity.moderate, Severity.high, Severity.critical,
      ];
      for (int i = 1; i < order.length; i++) {
        expect(severityRank(order[i]), greaterThan(severityRank(order[i - 1])));
      }
    });
  });
}
