/// The printable summary — asserted as text, because it leaves the app.
///
/// This is the one output that reaches someone who never saw the screen. It has
/// to carry its own context: the disclaimer, what was NOT checked, and every
/// declined answer with the reason it was declined. A page that printed only
/// the confident rows would misrepresent the analysis by omission, and nothing
/// downstream would catch it.
///
/// The negative assertions matter as much as the positive ones. A page that
/// looks like a laboratory report claims an authority this project does not
/// have, and a reader decides that in about a second from letterhead and
/// signature lines alone — before reading a word of the disclaimer.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/enums.dart';
import 'package:pharmaguard/print/print_summary.dart';
import 'package:pharmaguard/print/summary_document.dart';

const GeneCoverage _full = GeneCoverage(
  positionsPresent: 35, positionsRequired: 35, percent: 100,
  minimumPercent: 100, sufficient: true);
const GeneCoverage _short = GeneCoverage(
  positionsPresent: 4, positionsRequired: 35, percent: 11.4,
  minimumPercent: 100, sufficient: false);

PerDrugResult _result({
  required String drug,
  required RiskLabel label,
  String gene = 'CYP2C19',
  Severity severity = Severity.critical,
  List<String> candidates = const <String>[],
}) => PerDrugResult(
  drug: drug,
  riskAssessment: RiskAssessment(
      riskLabel: label, confidenceScore: 0.9, severity: severity),
  pharmacogenomicProfile: PharmacogenomicProfile(
    primaryGene: gene, diplotype: '*2/*2', recommendationDiplotype: null,
    candidateDiplotypes: candidates, phenotype: Phenotype.pm,
    activityScore: 0.0, detectedVariants: const <DetectedVariant>[],
  ),
  clinicalRecommendation: const ClinicalRecommendation(
    action: 'Avoid clopidogrel if possible & consider an alternative.',
    dosingGuidance: '',
    cpicRecommendation: 'Strong recommendation, adult population.',
    cpicEvidenceLevel: CpicEvidenceLevel.a,
    alternatives: <String>['prasugrel'], source: 'CPIC',
  ),
  llmGeneratedExplanation: const LlmGeneratedExplanation(
    summary: 'This medicine may not work for you.',
    mechanism: '', variantRationale: '', patientFriendly: '', disclaimer: '',
  ),
);

AnalyzeResponse _response({
  List<PerDrugResult>? analyses,
  Map<String, GeneCoverage> coverage = const <String, GeneCoverage>{
    'CYP2C19': _full, 'SLCO1B1': _short,
  },
  List<String> warnings = const <String>[],
  GuidelineProvenance? provenance = const GuidelineProvenance(
    pharmcatVersion: '3.4.0',
    cpicDataVersion: '2026-07-13-11-40',
    explanationsGeneratedAt: '2026-07-24T09:53:53.175011+00:00',
    cpicSource: 'CPIC guidelines, retrieved via PharmCAT',
    note: 'Guidance reflects what CPIC published when this data was captured. '
        'CPIC revises its guidelines; this build does not monitor for changes.',
  ),
}) => AnalyzeResponse(
  patientId: 'HG00276',
  timestamp: '2026-08-10T09:00:00.000Z',
  analyses: analyses ?? <PerDrugResult>[
    _result(drug: 'clopidogrel', label: RiskLabel.ineffective),
    _result(
        drug: 'simvastatin', label: RiskLabel.unknown, gene: 'SLCO1B1',
        severity: Severity.none),
  ],
  qualityMetrics: QualityMetrics(
    vcfParsingSuccess: true, variantsDetectedCount: 12, processingTimeMs: 1250,
    warnings: warnings, positionCoverage: coverage,
    guidelineProvenance: provenance,
  ),
);

void main() {
  group('what the page must always carry', () {
    test('the disclaimer, on the page and as a per-page running header', () {
      final String html = buildSummaryHtml(_response());

      expect(html, contains(kPrintHeaderLine));
      // Twice: once in the repeated table header and once as the block a reader
      // stops on. Pages get separated; page two must still say what it is.
      expect(kPrintHeaderLine.allMatches(html).length, greaterThanOrEqualTo(2));

      // The repeat mechanism, pinned. `position: fixed` also repeats in a
      // desktop browser but is not honoured by the OS HTML-to-PDF renderers
      // this document now goes through on iOS and Android, so a switch back to
      // it would drop the disclaimer from page two on mobile — invisibly.
      expect(html, contains('<table class="page"><thead>'));
      expect(html, contains('display: table-header-group'));
      expect(html, isNot(contains('position: fixed')));

      expect(html, contains('not a clinical report'));
      expect(html, contains('no qualified clinical expert has reviewed'));
      expect(html, contains('Do not change a medicine on the strength of this '
          'page'));
    });

    test('the coverage census, including what was NOT resolved', () {
      final String html = buildSummaryHtml(_response());

      expect(html, contains('Input coverage'));
      // The figures themselves, not a summary of them.
      expect(html, contains('<td class="mono">35</td>'));
      expect(html, contains('<td class="mono">4</td>'));
      expect(html, contains('CYP2C19'));
      expect(html, contains('SLCO1B1'));
      // A failed gene must be legible as failed at a glance.
      expect(html, contains('NO'));
      expect(html, contains('Not resolved from this file:'));
    });

    test('every Unknown, with its own reason and whether it is fixable', () {
      final String html = buildSummaryHtml(_response());

      expect(html, contains('Unknown results (1)'));
      // SLCO1B1 is short on coverage, so this Unknown is the actionable one.
      expect(html, contains('Your file is missing required positions'));
      expect(html, contains('What would fix it:'));
      expect(html, contains('reports ALL positions'));
    });

    test('an Unknown nobody can fix says so rather than going quiet', () {
      final String html = buildSummaryHtml(_response(
        analyses: <PerDrugResult>[
          _result(
            drug: 'codeine', label: RiskLabel.unknown, gene: 'CYP2D6',
            severity: Severity.none),
        ],
        coverage: const <String, GeneCoverage>{'CYP2D6': _full},
        warnings: const <String>[
          'CYP2D6 structural/copy-number variation cannot be resolved from a VCF.',
        ],
      ));

      expect(html, contains('Not determinable from a VCF'));
      expect(html, contains('needs a different kind of genetic test'));
      expect(html,
          contains('Nothing about the uploaded file would change this result.'));
    });

    test('the verbatim CPIC text, with its attribution attached', () {
      final String html = buildSummaryHtml(_response());

      expect(html, contains('CPIC GUIDELINE — QUOTED EXACTLY'));
      // Escaped, but still verbatim: the ampersand in CPIC's sentence survives
      // as an ampersand rather than being dropped or mangled.
      expect(html, contains('Avoid clopidogrel if possible &amp; consider an '
          'alternative.'));
      expect(html, contains('— CPIC'));
    });

    test('the CPIC data version and the explanation generation date', () {
      final String html = buildSummaryHtml(_response());

      expect(html, contains('3.4.0'));
      expect(html, contains('2026-07-13-11-40'));
      expect(html, contains('24 Jul 2026'));
      expect(html, contains('does not monitor for changes'));
    });

    test('results are ordered by consequence here too', () {
      final String html = buildSummaryHtml(_response());
      // A printed page a reader scans top-down must lead with the same row the
      // screen led with, or the two artifacts disagree about what matters.
      expect(html.indexOf('clopidogrel'), lessThan(html.indexOf('simvastatin')));
    });
  });

  group('what the page must never look like', () {
    late String html;
    setUp(() => html = buildSummaryHtml(_response()).toLowerCase());

    test('no signature line, seal, or authorisation block', () {
      for (final String forbidden in <String>[
        'signature', 'signed by', 'authorised by', 'authorized by',
        'seal', 'accession', 'certified', 'laboratory director',
      ]) {
        expect(html, isNot(contains(forbidden)),
            reason: 'the page uses a laboratory-report convention: $forbidden');
      }
    });

    test('no letterhead — no logo slot and no colour fills', () {
      expect(html, isNot(contains('<img')));
      expect(html, isNot(contains('logo')));
      expect(html, isNot(contains('letterhead')));
      // Black on white. A colour fill is the other half of how a page performs
      // officialdom; hairline rules carry all the structure this needs. White
      // is the absence of a fill, not one — so the check is for any background
      // that is NOT white.
      final Iterable<String> fills = RegExp(r'background:\s*([^;]+);')
          .allMatches(html)
          .map((RegExpMatch m) => m.group(1)!.trim());
      expect(fills.where((String f) => f != '#fff' && f != 'white'), isEmpty,
          reason: 'the page uses a colour fill: $fills');
      expect(html, isNot(contains('linear-gradient')));
      expect(html, isNot(contains('box-shadow')));
    });

    test('it does not call itself a report', () {
      // The page is titled a summary, and the only place "report" describes
      // THIS page is the sentence denying it is one. Matching the word alone
      // would be wrong — "a VCF that reports all positions" is a verb, and
      // "coverage was reported" is what the census is about.
      expect(html, contains('<h1>pharmacogenomic analysis summary</h1>'));
      for (final String selfDescription in <String>[
        'this report', 'the report', 'laboratory report', 'lab report',
        'test report', 'patient report', 'report id', 'report date',
      ]) {
        expect(html, isNot(contains(selfDescription)),
            reason: 'the page describes itself as a report: $selfDescription');
      }
      expect(html, contains('this is not a clinical report'));
    });
  });

  group('delivery', _delivery);

  group('robustness', () {
    test('a response with no coverage and no provenance still renders', () {
      final String html = buildSummaryHtml(_response(
        coverage: const <String, GeneCoverage>{}, provenance: null));

      // Degraded, but never silently: an absent census is stated as absent
      // rather than omitted, which would read as "everything was checked".
      expect(html, contains('No per-gene coverage was reported'));
      expect(html, contains(kPrintHeaderLine));
      expect(html, contains('not a clinical report'));
    });

    test('a clean run says so instead of leaving the section blank', () {
      final String html = buildSummaryHtml(_response(
        analyses: <PerDrugResult>[
          _result(drug: 'clopidogrel', label: RiskLabel.ineffective),
        ],
        coverage: const <String, GeneCoverage>{'CYP2C19': _full},
      ));
      expect(html, contains('None — every drug checked returned a result.'));
    });

    test('markup in the data cannot escape into the document', () {
      final String html = buildSummaryHtml(_response(
        analyses: <PerDrugResult>[
          _result(drug: '<script>alert(1)</script>', label: RiskLabel.safe),
        ],
      ));
      expect(html, isNot(contains('<script>alert(1)</script>')));
      expect(html, contains('&lt;script&gt;'));
    });

    test('the real five-drug payload prints every drug and every Unknown', () {
      final File payload = File('../test-data/demo/outputs/S6_multidrug.json');
      if (!payload.existsSync()) return;

      final AnalyzeResponse r = AnalyzeResponse.fromJson(
          jsonDecode(payload.readAsStringSync()) as Map<String, dynamic>);
      final String html = buildSummaryHtml(r);

      for (final PerDrugResult d in r.analyses) {
        expect(html, contains(d.drug), reason: '${d.drug} missing from print');
      }
      // Two Unknowns in this payload; neither may be dropped for tidiness.
      expect(html, contains('Unknown results (2)'));
      expect(html, contains('codeine'));
      expect(html, contains('ibuprofen'));
    });
  });
}

/// The delivery path, exercised where the platform channel does not exist.
///
/// A VM test host has no `printing` plugin, which is exactly the condition a
/// desktop platform without an HTML renderer hits. The document is already
/// built by then, so losing it to an error dialog would be the worst outcome —
/// the fallback writes it out instead, and this asserts that what lands on disk
/// is the real page and not a stub.
void _delivery() {
  test('a platform that cannot print still produces the document', () async {
    final String html = buildSummaryHtml(_response());
    final String message = await printSummary(html, 'summary.html');

    expect(message, contains('Saved to'));
    final String path =
        RegExp(r'Saved to (.+?)\.$').firstMatch(message)!.group(1)!;
    final String written = File(path).readAsStringSync();

    expect(written, contains(kPrintHeaderLine));
    expect(written, contains('not a clinical report'));
    expect(written, contains('Input coverage'));
    expect(written, contains('Unknown results (1)'));

    File(path).parent.deleteSync(recursive: true);
  });
}
