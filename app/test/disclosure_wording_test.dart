/// Wording and state that must stay true to what the system actually does.
///
/// Each group pins a defect reproduced through the real local API, browser,
/// JSON export and printed PDF on 2026-10-14
/// (audit-output/2026-10-14-prompt8-4da1199df2/DEFECTS.md):
///
///   DEF-1  automated provenance described as a guarantee ("verifies nothing
///          was invented"), and served template text described as pre-generated
///          and source-checked;
///   DEF-2  this application's CYP2D6 limit described as a VCF format limit;
///   DEF-3  the upstream missing-is-reference hazard described as this
///          application's output;
///   DEF-4  present-but-unusable genotypes (failed FILTER, partial call)
///          described as "not reported", with an emit-all-sites remedy;
///   DEF-5  opened results collapsing after a long scroll to the exports;
///   DEF-6  warfarin and codeine listed under "Drugs with CPIC guidance in
///          this build", although this build always returns Unknown for both.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/config.dart';
import 'package:pharmaguard/glossary/glossary_text.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/enums.dart';
import 'package:pharmaguard/models/unknown_reason.dart';
import 'package:pharmaguard/print/summary_document.dart';
import 'package:pharmaguard/screens/about_screen.dart';
import 'package:pharmaguard/screens/results_screen.dart';
import 'package:pharmaguard/theme/tokens.dart';
import 'package:pharmaguard/widgets/coverage_census.dart';
import 'package:pharmaguard/widgets/file_readiness.dart';
import 'package:pharmaguard/widgets/unknown_reason_panel.dart';
import 'package:pharmaguard/widgets/verdict_card.dart';

/// Phrases that turn an automated provenance filter into a guarantee.
const List<String> _overclaims = <String>[
  'nothing was invented',
  'invented nothing',
  'every clinical statement is machine',
  'every clinical statement here is machine',
  'machine-checked to come from',
  'machine-checked to trace',
  'machine-verified to come from',
  'writes no clinical content of its own',
];

/// Phrases that attribute this application's CYP2D6 limit to the VCF format.
const List<String> _formatClaims = <String>[
  'cannot represent',
  'cannot express',
  'cannot be read from any vcf',
  'cannot be read from a vcf',
  'no way to express',
  'limit of the file format',
  'no vcf, however complete',
  'not determinable from a vcf',
];

void _expectNone(String text, List<String> phrases, String where) {
  final String lower = text.toLowerCase();
  for (final String phrase in phrases) {
    expect(lower.contains(phrase), isFalse, reason: '$where says "$phrase"');
  }
}

String _allText(WidgetTester tester) => tester
    .widgetList<Text>(find.byType(Text, skipOffstage: false))
    .map((Text t) => t.data ?? t.textSpan?.toPlainText() ?? '')
    .join('\n');

String _allRichText(WidgetTester tester) => <String>[
  // Glossary terms render as inline widgets, so a sentence is read from the
  // GlossaryText's own string rather than from its split rendering.
  ...tester
      .widgetList<GlossaryText>(find.byType(GlossaryText, skipOffstage: false))
      .map((GlossaryText g) => g.text),
  ...tester
      .widgetList<RichText>(find.byType(RichText, skipOffstage: false))
      .map((RichText t) => t.text.toPlainText()),
].join('\n');

PerDrugResult _unknown(String drug, String gene) => PerDrugResult(
  drug: drug,
  riskAssessment: const RiskAssessment(
    riskLabel: RiskLabel.unknown,
    confidenceScore: 0.0,
    severity: Severity.none,
  ),
  pharmacogenomicProfile: PharmacogenomicProfile(
    primaryGene: gene,
    diplotype: 'Unknown',
    recommendationDiplotype: null,
    candidateDiplotypes: const <String>[],
    phenotype: Phenotype.unknown,
    activityScore: null,
    detectedVariants: const <DetectedVariant>[],
  ),
  clinicalRecommendation: ClinicalRecommendation(
    action:
        'Required genomic evidence is incomplete for $gene. Available partner '
        'findings are partial evidence only; no complete drug-level PGx '
        'recommendation is made.',
    dosingGuidance: '',
    cpicRecommendation: '',
    cpicEvidenceLevel: CpicEvidenceLevel.unknown,
    alternatives: const <String>[],
    source: 'Annotation of CPIC Guideline for $drug and $gene',
  ),
  llmGeneratedExplanation: const LlmGeneratedExplanation(
    summary: '',
    mechanism: '',
    variantRationale: '',
    patientFriendly: '',
    disclaimer: '',
  ),
);

/// The F4 NA12878 read-backed file with FILTER=LowQual at chr10:94781859, as
/// the API actually reports it: every position present, one unusable.
const GeneCoverage _filterFailed = GeneCoverage(
  positionsPresent: 34,
  positionsRequired: 35,
  percent: 97.1,
  minimumPercent: 100,
  sufficient: false,
  evidenceCounts: <String, int>{
    'valid_observed_genotype': 34,
    'partial_genotype': 0,
    'no_call': 0,
    'gt_not_provided': 0,
    'filter_failed': 1,
    'quality_not_established': 0,
    'malformed_genotype': 0,
    'absent_position': 0,
  },
);

/// The same file with that row deleted instead: genuinely not reported.
const GeneCoverage _oneAbsent = GeneCoverage(
  positionsPresent: 34,
  positionsRequired: 35,
  percent: 97.1,
  minimumPercent: 100,
  sufficient: false,
  evidenceCounts: <String, int>{
    'valid_observed_genotype': 34,
    'filter_failed': 0,
    'absent_position': 1,
  },
);

const GeneCoverage _full = GeneCoverage(
  positionsPresent: 157,
  positionsRequired: 157,
  percent: 100,
  minimumPercent: 100,
  sufficient: true,
);

AnalyzeResponse _response(
  List<PerDrugResult> analyses,
  Map<String, GeneCoverage> coverage,
) => AnalyzeResponse(
  patientId: 'NA12878',
  timestamp: '2026-10-14T11:54:04.078805Z',
  analyses: analyses,
  qualityMetrics: QualityMetrics(
    vcfParsingSuccess: true,
    variantsDetectedCount: 0,
    processingTimeMs: 1500,
    warnings: const <String>[],
    positionCoverage: coverage,
  ),
);

Future<void> _pump(WidgetTester tester, Widget child, {Size size = const Size(1280, 3000)}) async {
  await tester.binding.setSurfaceSize(size);
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(theme: Tokens.theme(), home: Scaffold(body: SingleChildScrollView(child: child))),
  );
  await tester.pumpAndSettle();
}

void main() {
  group('DEF-1 automated provenance is not a guarantee', () {
    test('the shared disclaimer bounds the automated check', () {
      _expectNone(kDisclaimer, _overclaims, 'kDisclaimer');
      expect(kDisclaimer.toLowerCase(), contains('not human review'));
      expect(kDisclaimer, contains('No qualified clinical expert has reviewed'));
    });

    test('the printed page bounds the automated check', () {
      final String html = buildSummaryHtml(
        _response(<PerDrugResult>[_unknown('codeine', 'CYP2D6')], const <String, GeneCoverage>{'CYP2D6': _full}),
      );
      _expectNone(html, _overclaims, 'printed summary');
      expect(html.toLowerCase(), contains('not human review'));
      expect(html, contains('no qualified clinical expert has reviewed'));
    });

    testWidgets('the About page bounds the automated check', (WidgetTester tester) async {
      await tester.binding.setSurfaceSize(const Size(1280, 4000));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await tester.pumpWidget(
        MaterialApp(
          theme: Tokens.theme(),
          home: const AboutScreen(
            provenance: GuidelineProvenance(
              pharmcatVersion: '3.4.0',
              cpicDataVersion: '2026-07-13-11-40',
              explanationsGeneratedAt: '2026-07-24T09:53:53.175011+00:00',
              cpicSource: 'CPIC guidelines, retrieved via PharmCAT',
              note: '',
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final String text = '${_allText(tester)}\n${_allRichText(tester)}';
      _expectNone(text, _overclaims, 'About page');
      expect(text.toLowerCase(), contains('not human review'));
    });

    test('the home subtitle does not call served text pre-generated and source-checked', () {
      // HomeScreen builds its own network client and wake-up timers, so its
      // copy is pinned at source, as the backend does for kDisclaimer.
      final String source = File('lib/screens/home_screen.dart').readAsStringSync();
      expect(source, isNot(contains('pre-generated and checked against their source')));
    });
  });

  group('DEF-2 the CYP2D6 limit belongs to this application, not to VCF', () {
    test('the Unknown reason used on the printed page', () {
      final UnknownReason reason = classifyUnknown(
        _unknown('codeine', 'CYP2D6'),
        const QualityMetrics(
          vcfParsingSuccess: true,
          variantsDetectedCount: 0,
          processingTimeMs: 1,
          warnings: <String>[],
          positionCoverage: <String, GeneCoverage>{'CYP2D6': _full},
        ),
      );
      expect(reason, UnknownReason.notCallable);
      _expectNone('${reason.headline}\n${reason.explanation}', _formatClaims, 'notCallable copy');
      expect(reason.explanation.toLowerCase(), contains('this application'));
    });

    testWidgets('the Unknown panel on the result card', (WidgetTester tester) async {
      await _pump(
        tester,
        UnknownReasonPanel(
          reason: UnknownReason.notCallable,
          profile: _unknown('codeine', 'CYP2D6').pharmacogenomicProfile,
        ),
      );
      final String text = '${_allText(tester)}\n${_allRichText(tester)}';
      _expectNone(text, _formatClaims, 'notCallable panel');
      expect(text.toLowerCase(), contains('this application'));
    });

    testWidgets('the census line on the codeine card', (WidgetTester tester) async {
      final PerDrugResult codeine = _unknown('codeine', 'CYP2D6');
      await _pump(
        tester,
        VerdictCard(
          result: codeine,
          metrics: _response(<PerDrugResult>[codeine], const <String, GeneCoverage>{'CYP2D6': _full}).qualityMetrics,
        ),
      );
      _expectNone('${_allText(tester)}\n${_allRichText(tester)}', _formatClaims, 'codeine card');
    });

    testWidgets('the readiness footnote before analysis', (WidgetTester tester) async {
      await _pump(
        tester,
        FileReadinessPanel(
          readiness: const CoverageResponse(
            genes: <GeneReadiness>[
              GeneReadiness(
                gene: 'CYP2D6',
                positionsFound: 157,
                positionsRequired: 157,
                thresholdPercent: 100,
                percent: 100,
                passes: false,
                notReadableFromVcf: true,
                reason: 'reason text supplied by the backend',
              ),
            ],
            genesPassing: 0,
            genesTotal: 1,
            answerableDrugs: <String>[],
            unanswerableDrugs: <String>['codeine'],
            variantsOnly: false,
            warnings: <String>[],
          ),
          onShowRequirements: () {},
        ),
      );
      final String text = '${_allText(tester)}\n${_allRichText(tester)}';
      _expectNone(text, _formatClaims, 'readiness footnote');
      expect(text, contains('CYP2D6'));
    });
  });

  group('DEF-3 the missing-is-reference hazard belongs to callers', () {
    test('the printed census note says this application withholds', () {
      final String html = buildSummaryHtml(
        _response(<PerDrugResult>[_unknown('clopidogrel', 'CYP2C19')], const <String, GeneCoverage>{'CYP2C19': _oneAbsent}),
      );
      expect(
        html,
        isNot(contains('A position that is absent reads as matching the reference, so missing data produces confident results')),
      );
      expect(html.toLowerCase(), contains('genotype caller'));
    });
  });

  group('DEF-4 an unusable genotype is not a missing position', () {
    const QualityMetrics filtered = QualityMetrics(
      vcfParsingSuccess: true,
      variantsDetectedCount: 0,
      processingTimeMs: 1,
      warnings: <String>[],
      positionCoverage: <String, GeneCoverage>{'CYP2C19': _filterFailed},
    );

    test('it is classified apart from absent positions', () {
      final UnknownReason reason = classifyUnknown(_unknown('clopidogrel', 'CYP2C19'), filtered);
      expect(reason, isNot(UnknownReason.lowCoverage));
      expect(reason.headline.toLowerCase(), isNot(contains('missing required positions')));
      expect(reason.explanation.toLowerCase(), isNot(contains('carry no genotype')));
      expect(reason.explanation.toLowerCase(), contains('filter'));
      expect(reason.callToAction ?? '', isNot(contains('variants-only')));
      expect(reason.isActionable, isTrue);
    });

    test('a genuinely absent position keeps the absence explanation', () {
      final UnknownReason reason = classifyUnknown(
        _unknown('clopidogrel', 'CYP2C19'),
        const QualityMetrics(
          vcfParsingSuccess: true,
          variantsDetectedCount: 0,
          processingTimeMs: 1,
          warnings: <String>[],
          positionCoverage: <String, GeneCoverage>{'CYP2C19': _oneAbsent},
        ),
      );
      expect(reason, UnknownReason.lowCoverage);
    });

    testWidgets('the census line counts the unusable row as unusable', (WidgetTester tester) async {
      await _pump(tester, const CoverageCensus(gene: 'CYP2C19', coverage: _filterFailed));
      final String text = '${_allText(tester)}\n${_allRichText(tester)}';
      expect(text, isNot(contains('1 of 35 positions were not reported in your file')));
      expect(text.toLowerCase(), contains('could not be used'));
    });

    testWidgets('the panel does not ask for an all-sites file', (WidgetTester tester) async {
      final PerDrugResult r = _unknown('clopidogrel', 'CYP2C19');
      await _pump(
        tester,
        UnknownReasonPanel(
          reason: classifyUnknown(r, filtered),
          profile: r.pharmacogenomicProfile,
          coverage: _filterFailed,
          gene: 'CYP2C19',
        ),
      );
      final String text = '${_allText(tester)}\n${_allRichText(tester)}'.toLowerCase();
      expect(text, isNot(contains('did not report enough positions')));
      expect(text, isNot(contains('variants-only file cannot work')));
      expect(text, contains('filter'));
    });

    test('the printed page gives the same account', () {
      final String html = buildSummaryHtml(
        _response(<PerDrugResult>[_unknown('clopidogrel', 'CYP2C19')], const <String, GeneCoverage>{'CYP2C19': _filterFailed}),
      );
      expect(html, isNot(contains('Your file is missing required positions')));
      expect(html, isNot(contains('reports ALL positions')));
      // Two reasons are actionable now; the section intro must not say one.
      expect(html, isNot(contains('Only one of these reasons')));
    });
  });

  group('DEF-5 opened results stay open', () {
    testWidgets('after a long scroll to the exports and back', (WidgetTester tester) async {
      await tester.binding.setSurfaceSize(const Size(1280, 720));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final AnalyzeResponse r = AnalyzeResponse.fromJson(
        jsonDecode(File('../test-data/demo/outputs/S6_multidrug.json').readAsStringSync())
            as Map<String, dynamic>,
      );
      await tester.pumpWidget(MaterialApp(theme: Tokens.theme(), home: ResultsScreen(response: r)));
      await tester.pumpAndSettle();
      final Finder list = find.byType(Scrollable).first;
      for (final PerDrugResult a in r.analyses) {
        final Finder header = find.byWidgetPredicate(
          (Widget w) =>
              w is Semantics &&
              w.properties.label == '${a.drug}: ${a.riskAssessment.riskLabel.displayValue}',
        );
        await tester.ensureVisible(header);
        await tester.pumpAndSettle();
        await tester.tap(header);
        await tester.pumpAndSettle();
      }
      expect(find.byType(VerdictCard, skipOffstage: false), findsNWidgets(r.analyses.length));

      // Large wheel steps, as a mouse wheel or trackpad fling delivers them.
      final Offset centre = tester.getCenter(list);
      for (int i = 0; i < 8; i++) {
        await tester.sendEventToBinding(PointerScrollEvent(position: centre, scrollDelta: const Offset(0, 3000)));
        await tester.pump();
      }
      await tester.pumpAndSettle();
      expect(find.text('Printable summary'), findsOneWidget);
      for (int i = 0; i < 8; i++) {
        await tester.sendEventToBinding(PointerScrollEvent(position: centre, scrollDelta: const Offset(0, -3000)));
        await tester.pump();
      }
      await tester.pumpAndSettle();
      expect(
        find.byType(VerdictCard, skipOffstage: false),
        findsNWidgets(r.analyses.length),
        reason: 'opened result cards were closed by scrolling',
      );
    });
  });

  group('DEF-6 the drug list does not promise guidance it never gives', () {
    test('warfarin and codeine are not listed as drugs with CPIC guidance', () {
      final String source = File('lib/screens/home_screen.dart').readAsStringSync();
      expect(source, isNot(contains('Drugs with CPIC guidance in this build')));
    });
  });
}
