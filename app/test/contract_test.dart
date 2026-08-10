/// Contract tests for the Dart models plus a smoke test for the results UI.
///
/// The JSON fixture below is a trimmed copy of a real `POST /analyze` response.
/// If the backend contract changes, this test should be the first thing to fail.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/models/enums.dart';
import 'package:pharmaguard/screens/results_screen.dart';

const String _fixture = '''
{
  "patient_id": "PATIENT_001",
  "timestamp": "2026-07-21T16:28:03.362243Z",
  "analyses": [
    {
      "drug": "codeine",
      "risk_assessment": {
        "risk_label": "Toxic",
        "confidence_score": 0.88,
        "severity": "high"
      },
      "pharmacogenomic_profile": {
        "primary_gene": "CYP2D6",
        "diplotype": "*1/*2xN",
        "recommendation_diplotype": null,
        "candidate_diplotypes": [],
        "phenotype": "URM",
        "activity_score": 3.0,
        "detected_variants": [
          {
            "rsid": "rs16947",
            "gene": "CYP2D6",
            "genotype": "1/1",
            "star_allele": "*2",
            "function": "Normal function"
          },
          {
            "rsid": null,
            "gene": "CYP2D6",
            "genotype": "N/A",
            "star_allele": "*2xN",
            "function": "Increased function (gene duplication)"
          }
        ]
      },
      "clinical_recommendation": {
        "action": "Avoid codeine; select an alternative analgesic.",
        "dosing_guidance": "STUB",
        "cpic_recommendation": "STUB",
        "cpic_evidence_level": "Unknown",
        "alternatives": ["morphine"],
        "source": "STUB"
      },
      "llm_generated_explanation": {
        "summary": "STUB summary",
        "mechanism": "STUB mechanism",
        "variant_rationale": "STUB rationale",
        "patient_friendly": "STUB plain-language text",
        "disclaimer": "Research/educational decision support only. Not a medical device. Not for clinical use."
      }
    },
    {
      "drug": "aspirin",
      "risk_assessment": {
        "risk_label": "Unknown",
        "confidence_score": 0.0,
        "severity": "none"
      },
      "pharmacogenomic_profile": {
        "primary_gene": "Unknown",
        "diplotype": "Unknown",
        "recommendation_diplotype": null,
        "candidate_diplotypes": [],
        "phenotype": "Unknown",
        "activity_score": null,
        "detected_variants": []
      },
      "clinical_recommendation": {
        "action": "No pharmacogenomic association available.",
        "dosing_guidance": "Not applicable.",
        "cpic_recommendation": "No CPIC guideline loaded.",
        "cpic_evidence_level": "Unknown",
        "alternatives": [],
        "source": "STUB"
      },
      "llm_generated_explanation": {
        "summary": "Not in the demo set.",
        "mechanism": "Not available.",
        "variant_rationale": "No variants evaluated.",
        "patient_friendly": "No information for this drug.",
        "disclaimer": "Research/educational decision support only. Not a medical device. Not for clinical use."
      }
    }
  ],
  "quality_metrics": {
    "vcf_parsing_success": true,
    "variants_detected_count": 2,
    "processing_time_ms": 1,
    "warnings": ["STUB: PharmCAT not integrated yet"],
      "position_coverage": {
        "CYP2D6": {
          "positions_present": 157,
          "positions_required": 157,
          "percent": 100.0,
          "minimum_percent": 100,
          "sufficient": true
        }
      },
      "guideline_provenance": {
        "pharmcat_version": "3.4.0",
        "cpic_data_version": "2026-07-13-11-40",
        "explanations_generated_at": "2026-07-24T09:53:53.175011+00:00",
        "cpic_source": "CPIC guidelines, retrieved via PharmCAT",
        "note": "Guidance reflects what CPIC published when this data was captured. CPIC revises its guidelines; this build does not monitor for changes."
      }
  }
}
''';

AnalyzeResponse _parseFixture() =>
    AnalyzeResponse.fromJson(jsonDecode(_fixture) as Map<String, dynamic>);

void main() {
  group('JSON contract', () {
    test('parses a full /analyze response', () {
      final AnalyzeResponse r = _parseFixture();

      expect(r.patientId, 'PATIENT_001');
      expect(r.analyses, hasLength(2));
      expect(r.qualityMetrics.vcfParsingSuccess, isTrue);
      expect(r.qualityMetrics.warnings.single, contains('PharmCAT'));

      final PerDrugResult codeine = r.analyses.first;
      expect(codeine.riskAssessment.riskLabel, RiskLabel.toxic);
      expect(codeine.riskAssessment.severity, Severity.high);
      expect(codeine.riskAssessment.confidenceScore, closeTo(0.88, 1e-9));
      expect(codeine.pharmacogenomicProfile.phenotype, Phenotype.urm);
      expect(codeine.pharmacogenomicProfile.activityScore, 3.0);
      expect(codeine.pharmacogenomicProfile.detectedVariants, hasLength(2));
    });

    test('an unknown drug parses as a well-formed Unknown result', () {
      final PerDrugResult aspirin = _parseFixture().analyses[1];

      expect(aspirin.riskAssessment.riskLabel, RiskLabel.unknown);
      expect(aspirin.pharmacogenomicProfile.phenotype, Phenotype.unknown);
      // Null must survive as null — rendering it as 0 would be a clinical lie.
      expect(aspirin.pharmacogenomicProfile.activityScore, isNull);
      expect(aspirin.pharmacogenomicProfile.detectedVariants, isEmpty);
    });

    test('a structural variant keeps a null rsid', () {
      final DetectedVariant cnv = _parseFixture()
          .analyses
          .first
          .pharmacogenomicProfile
          .detectedVariants[1];

      expect(cnv.rsid, isNull);
      expect(cnv.starAllele, '*2xN');
      expect(cnv.displayName, 'structural variant (*2xN)');
    });

    test('toJson round-trips back to the original structure', () {
      final Map<String, dynamic> original =
          jsonDecode(_fixture) as Map<String, dynamic>;
      final Map<String, dynamic> roundTripped = _parseFixture().toJson();

      // Compare as normalised JSON so key order does not matter.
      expect(jsonDecode(jsonEncode(roundTripped)), equals(original));
    });

    test('unrecognised enum values fall back instead of throwing', () {
      expect(RiskLabel.fromJson('Something New'), RiskLabel.unknown);
      expect(RiskLabel.fromJson(null), RiskLabel.unknown);
      expect(Severity.fromJson(42), Severity.none);
      expect(Phenotype.fromJson('XYZ'), Phenotype.unknown);
      expect(CpicEvidenceLevel.fromJson(''), CpicEvidenceLevel.unknown);
    });
  });

  group('ResultsScreen', () {
    testWidgets('renders one card per analysis, plus the disclaimer', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(home: ResultsScreen(response: _parseFixture())),
      );
      await tester.pumpAndSettle();

      // The redesign renders the drug as a mono IDENTIFIER (lowercase), not a
      // title — it is the string the request carried, so it reads as machine
      // output like the diplotype beside it.
      expect(find.text('codeine'), findsOneWidget);
      // The verdict card is taller than the old one, so the second drug now
      // starts below the fold in a lazily-built list. Scrolling to it asserts
      // a user can actually reach it.
      await tester.dragUntilVisible(
        find.text('aspirin'),
        find.byType(Scrollable).first,
        const Offset(0, -200),
      );
      expect(find.text('aspirin'), findsOneWidget);
      expect(find.text('Toxic'), findsWidgets);
      expect(find.text('Unknown'), findsWidgets);
      expect(find.textContaining('Not a medical device'), findsWidgets);

      // The export buttons sit below the coverage summary, so in a lazily-built
      // list they are not constructed until scrolled to. Scroll rather than
      // enlarging the surface: this asserts a user can actually reach them.
      await tester.dragUntilVisible(
        find.text('Copy JSON'),
        find.byType(Scrollable).first,
        const Offset(0, -200),
      );
      expect(find.text('Copy JSON'), findsOneWidget);
      expect(find.text('Export JSON'), findsOneWidget);
    });

    testWidgets('expanding a card reveals the recommendation and explanation', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(home: ResultsScreen(response: _parseFixture())),
      );
      await tester.pumpAndSettle();

      // CPIC's text sits under a mono label that names it as quoted, which is
      // the point: the reader can see which words are the guideline's own.
      // Feature Set B gave it its own disclosure row — in patient view (the
      // default) the prose is already surfaced, so only the quote is behind a
      // tap. Target the first card's row explicitly, and scroll to it.
      final Finder cpicRow = find.text("The guideline in CPIC's own words");
      await tester.ensureVisible(cpicRow.first);
      await tester.pumpAndSettle();
      await tester.tap(cpicRow.first);
      await tester.pumpAndSettle();

      expect(find.text('CPIC GUIDELINE — QUOTED EXACTLY'), findsWidgets);
      expect(find.textContaining('Avoid codeine'), findsOneWidget);

      await tester.ensureVisible(find.text('What was found in your file').first);
      await tester.pumpAndSettle();
      await tester.tap(find.text('What was found in your file').first);
      await tester.pumpAndSettle();
      expect(find.text('diplotype'), findsWidgets);
    });
  });
}
