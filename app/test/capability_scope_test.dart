/// Phase 2 capability and wording regressions on user-visible/export surfaces.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/generated/capabilities.g.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/enums.dart';
import 'package:pharmaguard/print/summary_document.dart';
import 'package:pharmaguard/theme/tokens.dart';
import 'package:pharmaguard/widgets/verdict_card.dart';

const QualityMetrics _metrics = QualityMetrics(
  vcfParsingSuccess: true,
  variantsDetectedCount: 0,
  processingTimeMs: 1,
  warnings: <String>[],
  positionCoverage: <String, GeneCoverage>{},
);

const PerDrugResult _result = PerDrugResult(
  drug: 'clopidogrel',
  riskAssessment: RiskAssessment(
    riskLabel: RiskLabel.safe,
    confidenceScore: 0.95,
    severity: Severity.critical,
  ),
  pharmacogenomicProfile: PharmacogenomicProfile(
    primaryGene: 'CYP2C19',
    diplotype: '*1/*1',
    recommendationDiplotype: null,
    candidateDiplotypes: <String>[],
    phenotype: Phenotype.nm,
    activityScore: null,
    detectedVariants: <DetectedVariant>[],
  ),
  clinicalRecommendation: ClinicalRecommendation(
    action: 'Use the standard dose for the stated indication.',
    dosingGuidance: '',
    cpicRecommendation: 'CPIC strength: Strong. Population: ACS/PCI.',
    cpicEvidenceLevel: CpicEvidenceLevel.a,
    alternatives: <String>[],
    source: 'CPIC via PharmCAT',
  ),
  llmGeneratedExplanation: LlmGeneratedExplanation(
    summary:
        'No PGx-guided adjustment was identified from the assessed evidence.',
    mechanism: '',
    variantRationale: '',
    patientFriendly: '',
    disclaimer: '',
  ),
);

AnalyzeResponse _response() => const AnalyzeResponse(
  patientId: 'sample',
  timestamp: '2026-09-23T00:00:00Z',
  analyses: <PerDrugResult>[_result],
  qualityMetrics: _metrics,
);

void main() {
  test('generated registry exposes exactly six and four guidance pathways', () {
    expect(
      kDrugCapabilities.map((DrugCapability c) => c.drug).toSet(),
      <String>{
        'azathioprine',
        'clopidogrel',
        'codeine',
        'fluorouracil',
        'simvastatin',
        'warfarin',
      },
    );
    expect(
      kDrugCapabilities
          .where((DrugCapability c) => c.guidanceCapable)
          .map((DrugCapability c) => c.drug)
          .toSet(),
      <String>{'azathioprine', 'clopidogrel', 'fluorouracil', 'simvastatin'},
    );
  });

  testWidgets('result card shows no percentage confidence or severity claim', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: Tokens.theme(),
        home: const Scaffold(
          body: VerdictCard(result: _result, metrics: _metrics),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('95%'), findsNothing);
    expect(find.textContaining('confidence'), findsNothing);
    expect(find.textContaining('severity critical'), findsNothing);
    expect(
      find.textContaining('not a clinical safety assessment'),
      findsOneWidget,
    );
  });

  test('user export omits deprecated certainty fields', () {
    final Map<String, dynamic> exported = _response().toExportJson();
    final Map<String, dynamic> risk =
        (exported['analyses'] as List<dynamic>).single['risk_assessment'];
    final Map<String, dynamic> capability =
        (exported['analyses'] as List<dynamic>)
            .single['application_capability'];
    expect(risk, isNot(contains('confidence_score')));
    expect(risk, isNot(contains('severity')));
    expect(risk['assessment_scope'], contains('not a clinical safety'));
    expect(capability['drug'], 'clopidogrel');
    expect(capability['guidance_capable'], isTrue);
    expect(capability['export_available'], isTrue);
  });

  test('print summary preserves CPIC context without legacy severity', () {
    final String html = buildSummaryHtml(_response());
    expect(html, contains('CPIC strength: Strong. Population: ACS/PCI.'));
    expect(html, isNot(contains('<td>severity</td>')));
    expect(html, isNot(contains('95%')));
    expect(html, contains('No PGx-guided adjustment identified'));
  });
}
