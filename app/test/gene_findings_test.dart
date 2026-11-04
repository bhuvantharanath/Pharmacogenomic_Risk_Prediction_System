/// Warfarin's genes on the result card (Phase 9 B5).
///
/// The verdict stays Unknown; the card shows what the file established for
/// CYP2C9, VKORC1 and CYP4F2, marks CYP4F2 as reference only, and shows no call
/// for a gene the backend did not assess.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/theme/tokens.dart';
import 'package:pharmaguard/widgets/verdict_card.dart';

const String _vkorc1Tt = 'rs9923231 variant (T)/rs9923231 variant (T)';

Map<String, dynamic> _warfarinJson(List<Map<String, dynamic>> findings) =>
    <String, dynamic>{
      'drug': 'warfarin',
      'risk_assessment': <String, dynamic>{
        'risk_label': 'Unknown',
        'confidence_score': 0.0,
        'severity': 'none',
      },
      'pharmacogenomic_profile': <String, dynamic>{
        'primary_gene': 'CYP2C9',
        'diplotype': '*3/*3',
        'recommendation_diplotype': null,
        'candidate_diplotypes': <String>[],
        'phenotype': 'Unknown',
        'activity_score': null,
        'detected_variants': <Map<String, dynamic>>[],
      },
      'clinical_recommendation': <String, dynamic>{
        'action':
            'No validated automated warfarin-dose implementation is '
            'provided by this application.',
        'dosing_guidance': '',
        'cpic_recommendation': '',
        'cpic_evidence_level': 'Unknown',
        'alternatives': <String>[],
        'source': 'CPIC via PharmCAT',
      },
      'llm_generated_explanation': <String, dynamic>{
        'summary': '',
        'mechanism': '',
        'variant_rationale': '',
        'patient_friendly': '',
        'disclaimer': '',
      },
      'gene_findings': findings,
    };

const List<Map<String, dynamic>> _assessed = <Map<String, dynamic>>[
  <String, dynamic>{
    'gene': 'CYP2C9',
    'role': 'required',
    'assessed': true,
    'call': '*3/*3',
    'phenotype': 'Poor Metabolizer',
    'note': '',
  },
  <String, dynamic>{
    'gene': 'VKORC1',
    'role': 'required',
    'assessed': true,
    'call': _vkorc1Tt,
    'phenotype': '',
    'note': '',
  },
  <String, dynamic>{
    'gene': 'CYP4F2',
    'role': 'reference',
    'assessed': true,
    'call': '*1/*3',
    'phenotype': '',
    'note': '',
  },
];

const QualityMetrics _metrics = QualityMetrics(
  vcfParsingSuccess: true,
  variantsDetectedCount: 0,
  processingTimeMs: 1,
  warnings: <String>[],
  positionCoverage: <String, GeneCoverage>{},
);

Future<void> _pump(WidgetTester t, PerDrugResult result) async {
  await t.pumpWidget(
    MaterialApp(
      theme: Tokens.theme(),
      home: Scaffold(
        body: SingleChildScrollView(
          child: VerdictCard(result: result, metrics: _metrics),
        ),
      ),
    ),
  );
  await t.pumpAndSettle();
}

void main() {
  test('gene findings are parsed and round-trip', () {
    final Map<String, dynamic> json = _warfarinJson(_assessed);
    final PerDrugResult r = PerDrugResult.fromJson(json);
    expect(r.geneFindings.map((GeneFinding f) => f.gene), <String>[
      'CYP2C9',
      'VKORC1',
      'CYP4F2',
    ]);
    expect(r.geneFindings[2].isReference, isTrue);
    expect(r.toJson()['gene_findings'], _assessed);
  });

  test('a result without gene findings round-trips without the key', () {
    final Map<String, dynamic> json = _warfarinJson(<Map<String, dynamic>>[])
      ..remove('gene_findings');
    expect(
      PerDrugResult.fromJson(json).toJson().containsKey('gene_findings'),
      isFalse,
    );
  });

  testWidgets('the card lists CYP2C9, VKORC1 and CYP4F2 with their calls', (
    WidgetTester t,
  ) async {
    await _pump(t, PerDrugResult.fromJson(_warfarinJson(_assessed)));
    expect(find.text('Genes in this result'), findsOneWidget);
    expect(find.text('VKORC1'), findsOneWidget);
    expect(find.text(_vkorc1Tt), findsOneWidget);
    expect(find.text('CYP4F2'), findsOneWidget);
    expect(find.text('*1/*3'), findsOneWidget);
    expect(
      find.text('shown for reference only; it does not change this result'),
      findsOneWidget,
    );
  });

  testWidgets('a gene that was not assessed shows why, and no call', (
    WidgetTester t,
  ) async {
    final List<Map<String, dynamic>> findings = <Map<String, dynamic>>[
      _assessed[0],
      <String, dynamic>{
        'gene': 'VKORC1',
        'role': 'required',
        'assessed': false,
        'call': '',
        'phenotype': '',
        'note':
            "Coverage of this gene's positions is below what it needs; "
            'see the coverage panel.',
      },
    ];
    await _pump(t, PerDrugResult.fromJson(_warfarinJson(findings)));
    expect(find.text('not assessed'), findsOneWidget);
    expect(find.textContaining('below what it needs'), findsOneWidget);
    expect(find.text(_vkorc1Tt), findsNothing);
  });
}
