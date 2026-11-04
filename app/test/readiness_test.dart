/// The file-readiness screen, in each state a real file can produce.
///
/// The point of this screen is to say something true and specific before the
/// user commits to a run, so the tests are about what it SAYS, not that it
/// renders. Three claims are load-bearing:
///
///   1. it never blocks — every state leaves the analysis reachable;
///   2. "short on coverage" and "this application does not call it" stay apart, because the
///      remedies are opposite and one of them does not exist;
///   3. the drug lists are honest in both directions — a drug the file can
///      answer is named, and so is one it cannot.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/theme/tokens.dart';
import 'package:pharmaguard/widgets/coverage_census.dart';
import 'package:pharmaguard/widgets/file_readiness.dart';

GeneReadiness _gene({
  required String gene,
  required int found,
  required int required_,
  int threshold = 100,
  bool? passes,
  bool blocked = false,
  String reason = '',
}) => GeneReadiness(
  gene: gene,
  positionsFound: found,
  positionsRequired: required_,
  thresholdPercent: threshold,
  percent: required_ == 0 ? 0 : found / required_ * 100,
  passes: passes ?? (!blocked && found * 100 / required_ >= threshold),
  notReadableFromVcf: blocked,
  reason: reason,
);

/// CYP2D6 as the backend actually reports it: never a coverage failure.
final GeneReadiness _cyp2d6 = _gene(
  gene: 'CYP2D6',
  found: 157,
  required_: 157,
  blocked: true,
  reason: 'Not called from an uploaded VCF by this application: CYP2D6 results '
      'depend on copy-number and structural variation, which need specialised '
      'read-level calling. Uploading a different VCF here will not resolve it.',
);

CoverageResponse _readiness({
  required List<GeneReadiness> genes,
  List<String> answerable = const <String>[],
  List<String> unanswerable = const <String>[],
  bool variantsOnly = false,
  List<String> warnings = const <String>[],
  GuidelineProvenance? provenance,
}) => CoverageResponse(
  genes: genes,
  genesPassing: genes.where((GeneReadiness g) => g.passes).length,
  genesTotal: genes.length,
  answerableDrugs: answerable,
  unanswerableDrugs: unanswerable,
  variantsOnly: variantsOnly,
  warnings: warnings,
  guidelineProvenance: provenance,
);

Future<void> _pump(
  WidgetTester t,
  CoverageResponse readiness, {
  double width = 360,
  VoidCallback? onShowRequirements,
}) async {
  await t.binding.setSurfaceSize(Size(width, 3200));
  addTearDown(() => t.binding.setSurfaceSize(null));
  await t.pumpWidget(MaterialApp(
    theme: Tokens.theme(),
    home: Scaffold(
      body: SingleChildScrollView(
        child: FileReadinessPanel(
          readiness: readiness,
          onShowRequirements: onShowRequirements,
        ),
      ),
    ),
  ));
  await t.pumpAndSettle();
}

/// Matches the headline regardless of how it is split across TextSpans.
Finder _headline(String text) => find.byWidgetPredicate((Widget w) {
  if (w is! Text) return false;
  final String rendered = w.data ?? w.textSpan?.toPlainText() ?? '';
  return rendered.contains(text);
});

void main() {
  group('every gene passes', () {
    final CoverageResponse all = _readiness(
      genes: <GeneReadiness>[
        _gene(gene: 'CYP2C19', found: 35, required_: 35),
        _gene(gene: 'CYP2C9', found: 88, required_: 88),
        _gene(gene: 'DPYD', found: 20, required_: 100, threshold: 20),
      ],
      answerable: <String>['clopidogrel', 'fluorouracil', 'warfarin'],
    );

    testWidgets('states the count as a count', (WidgetTester t) async {
      await _pump(t, all);
      expect(_headline('3 of 3'), findsOneWidget);
    });

    testWidgets('names what it can answer', (WidgetTester t) async {
      await _pump(t, all);
      expect(find.text('CAN BE ANSWERED'), findsOneWidget);
      expect(find.text('clopidogrel'), findsOneWidget);
      // Nothing to warn about, so nothing is warned about — a clean file must
      // not be decorated with caveats it has not earned.
      expect(find.text('WILL RETURN UNKNOWN'), findsNothing);
      expect(find.textContaining('No gene in this file'), findsNothing);
    });

    testWidgets('the census is available but not forced', (WidgetTester t) async {
      await _pump(t, all);
      // Collapsed by default: the headline is the answer, the per-position
      // count is for the reader who wants to check it.
      expect(find.byType(CoverageCensus), findsNothing);
      await t.tap(find.text('Per-gene detail'));
      await t.pumpAndSettle();
      expect(find.byType(CoverageCensus), findsNWidgets(3));
    });
  });

  group('partial — some genes pass', () {
    final CoverageResponse partial = _readiness(
      genes: <GeneReadiness>[
        _gene(gene: 'CYP2C19', found: 35, required_: 35),
        _gene(
          gene: 'SLCO1B1',
          found: 4,
          required_: 35,
          reason: '4 of 35 required positions were reported; this gene needs 100%.',
        ),
        _cyp2d6,
      ],
      answerable: <String>['clopidogrel'],
      unanswerable: <String>['codeine', 'simvastatin'],
    );

    testWidgets('both drug lists appear, each labelled', (WidgetTester t) async {
      await _pump(t, partial);
      expect(_headline('1 of 3'), findsOneWidget);
      expect(find.text('CAN BE ANSWERED'), findsOneWidget);
      expect(find.text('WILL RETURN UNKNOWN'), findsOneWidget);
      expect(find.text('clopidogrel'), findsOneWidget);
      expect(find.text('codeine'), findsOneWidget);
    });

    testWidgets('a fixable gap and a permanent one read differently',
        (WidgetTester t) async {
      await _pump(t, partial);

      // SLCO1B1: the file could carry these positions. Say re-calling helps.
      expect(find.textContaining('SLCO1B1: not enough called positions'),
          findsOneWidget);
      expect(find.textContaining('Re-calling with all sites emitted'),
          findsOneWidget);

      // CYP2D6: this application does not call it from any upload. Say so, and
      // do not send the user looking for a better file.
      expect(
          find.textContaining(
              'CYP2D6: not called from an uploaded VCF by this application'),
          findsOneWidget);
      expect(
          find.textContaining(
              'specialised copy-number and structural-variant calling'),
          findsOneWidget);
      expect(find.textContaining('a different file will not help'),
          findsOneWidget);
    });

    testWidgets('CYP2D6 shows a reason, never a zero bar', (WidgetTester t) async {
      await _pump(t, partial);
      await t.tap(find.text('Per-gene detail'));
      await t.pumpAndSettle();

      // "not applicable" is the census's own not-readable rendering. A bar of
      // 157 empty ticks would say the file was deficient; the limit is this
      // application's.
      expect(find.text('not applicable'), findsOneWidget);
      expect(find.textContaining('Uploading a different VCF here will not resolve it'),
          findsWidgets);
    });
  });

  group('nothing passes', () {
    final CoverageResponse none = _readiness(
      genes: <GeneReadiness>[
        _gene(
          gene: 'CYP2C19',
          found: 4,
          required_: 35,
          reason: '4 of 35 required positions were reported; this gene needs 100%.',
        ),
        _cyp2d6,
      ],
      unanswerable: <String>['clopidogrel', 'codeine'],
      variantsOnly: true,
      warnings: <String>['This VCF contains no homozygous-reference genotypes…'],
    );

    testWidgets('says so plainly, and says the run is still available',
        (WidgetTester t) async {
      await _pump(t, none);

      expect(_headline('0 of 2'), findsOneWidget);
      expect(find.textContaining('No gene in this file has enough called '
          'positions'), findsOneWidget);
      // THE point. An advisory screen that reads as a wall would push users to
      // fabricate a file rather than accept an honest Unknown.
      expect(find.textContaining('You can still run the analysis'),
          findsOneWidget);
    });

    testWidgets('offers the requirements reference and calls back',
        (WidgetTester t) async {
      int taps = 0;
      await _pump(t, none, onShowRequirements: () => taps++);

      final Finder link = find.text('What a usable file looks like');
      expect(link, findsOneWidget);
      await t.tap(link);
      expect(taps, 1);
    });

    testWidgets('the variants-only case gets its own warning',
        (WidgetTester t) async {
      await _pump(t, none);
      expect(find.text('This file lists variants only'), findsOneWidget);
      // The direction of the error is the whole finding; it must survive here.
      expect(find.textContaining('reduced function reported as normal'),
          findsOneWidget);
    });

    testWidgets('a fully-called file gets no variants-only warning',
        (WidgetTester t) async {
      await _pump(t, _readiness(
        genes: <GeneReadiness>[_gene(gene: 'CYP2C19', found: 35, required_: 35)],
        answerable: <String>['clopidogrel'],
      ));
      expect(find.text('This file lists variants only'), findsNothing);
    });
  });

  group('provenance', () {
    const GuidelineProvenance provenance = GuidelineProvenance(
      pharmcatVersion: '3.4.0',
      cpicDataVersion: '2026-07-13-11-40',
      explanationsGeneratedAt: '2026-07-24T09:53:53.175011+00:00',
      cpicSource: 'CPIC guidelines, retrieved via PharmCAT',
      note: 'Guidance reflects what CPIC published when this data was captured. '
          'CPIC revises its guidelines. A weekly repository check compares this '
          'build\'s CPIC data with CPIC\'s current release and flags differences '
          'for review; an analysis does not check at the time it runs.',
    );

    // The shape /analyze sends since B2: the version the run reported plus the
    // content hashes of the jar's CPIC data (values from the pinned 3.4.0 jar).
    const Map<String, dynamic> analyzeJson = <String, dynamic>{
      'pharmcat_version': '3.4.0',
      'cpic_data_version': '2026-07-13-11-40',
      'explanations_generated_at': '2026-07-24T09:53:53.175011+00:00',
      'cpic_guidance_sha256':
          '5010bb813ed6aaacf504c689e1f74924ddc7c58383d5e35604074d299345d6a8',
      'allele_definitions_version': '2026-07-13-11-40',
      'allele_definitions_sha256':
          '7044c87682de18646a74b890739e2cc145ef0a3a21718a17b371dc013c7afe8f',
      'pharmvar_release': '',
      'cpic_source': 'CPIC guidelines, retrieved via PharmCAT',
      'note': 'n',
    };

    test('the knowledge hashes are parsed and survive a round trip', () {
      final GuidelineProvenance p = GuidelineProvenance.fromJson(analyzeJson);
      expect(p.cpicGuidanceSha256, analyzeJson['cpic_guidance_sha256']);
      expect(p.alleleDefinitionsVersion, '2026-07-13-11-40');
      expect(p.alleleDefinitionsSha256, analyzeJson['allele_definitions_sha256']);
      expect(p.pharmvarRelease, '');
      expect(p.toJson(), analyzeJson);
    });

    test('the footer names the CPIC data and definitions by version and hash',
        () {
      final GuidelineProvenance p = GuidelineProvenance.fromJson(analyzeJson);
      expect(
        p.summaryLine,
        'PharmCAT 3.4.0 · CPIC data 2026-07-13-11-40 (5010bb81) · '
        'definitions 2026-07-13-11-40 (7044c876) · explanations 24 Jul 2026',
      );
      // No PharmVar number is invented when the backend sends none.
      expect(p.summaryLine.contains('PharmVar'), isFalse);
    });

    test('/coverage, with no run, still identifies the CPIC data by hash', () {
      final GuidelineProvenance p = GuidelineProvenance.fromJson(
          <String, dynamic>{...analyzeJson, 'cpic_data_version': ''});
      expect(p.summaryLine, startsWith('PharmCAT 3.4.0 · CPIC data (5010bb81) · '));
    });

    testWidgets('the results footer shows the hashes', (WidgetTester t) async {
      await t.pumpWidget(MaterialApp(
        home: Scaffold(
          body: ProvenanceLine(
              provenance: GuidelineProvenance.fromJson(analyzeJson)),
        ),
      ));
      expect(find.textContaining('CPIC data 2026-07-13-11-40 (5010bb81)'),
          findsOneWidget);
      expect(find.textContaining('definitions 2026-07-13-11-40 (7044c876)'),
          findsOneWidget);
    });

    test('the summary line drops parts the backend did not send', () {
      const GuidelineProvenance preview = GuidelineProvenance(
        pharmcatVersion: '3.4.0',
        cpicDataVersion: '', // /coverage never observed a run
        explanationsGeneratedAt: '2026-07-24T09:53:53.175011+00:00',
        cpicSource: '',
        note: '',
      );
      expect(preview.summaryLine, 'PharmCAT 3.4.0 · explanations 24 Jul 2026');
      expect(preview.summaryLine.contains('CPIC data'), isFalse);
    });

    test('an unparseable date is shown rather than hidden', () {
      const GuidelineProvenance odd = GuidelineProvenance(
        pharmcatVersion: '3.4.0', cpicDataVersion: '',
        explanationsGeneratedAt: 'unknown', cpicSource: '', note: '',
      );
      // Dropping it would quietly hide something the backend did send.
      expect(odd.explanationsDate, 'unknown');
    });

    testWidgets('renders quietly under the panel', (WidgetTester t) async {
      await _pump(t, _readiness(
        genes: <GeneReadiness>[_gene(gene: 'CYP2C19', found: 35, required_: 35)],
        answerable: <String>['clopidogrel'],
        provenance: provenance,
      ));
      expect(find.textContaining('PharmCAT 3.4.0'), findsOneWidget);
      // Muted, and in mono — it is a version string, not a claim.
      final Text line = t.widget<Text>(find.textContaining('PharmCAT 3.4.0'));
      expect(line.style?.color, Tokens.ink3);
      expect(line.style?.fontFamily, Tokens.mono);
    });
  });

  group('layout floor', () {
    testWidgets('nothing overflows at 360px with every section showing',
        (WidgetTester t) async {
      await _pump(t, _readiness(
        genes: <GeneReadiness>[
          _gene(gene: 'CYP2C19', found: 4, required_: 35, reason: 'short'),
          _cyp2d6,
        ],
        answerable: <String>['clopidogrel'],
        unanswerable: <String>['codeine', 'simvastatin', 'fluorouracil',
            'azathioprine', 'capecitabine'],
        variantsOnly: true,
      ), width: 360);
      expect(takeOverflowException(), isNull);
    });
  });
}

/// A RenderFlex overflow is reported as a caught exception rather than a test
/// failure, so it has to be asked for. 360px is this project's stated floor and
/// the census header overflowed it once already.
Object? takeOverflowException() =>
    TestWidgetsFlutterBinding.instance.takeException();
