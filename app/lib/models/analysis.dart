/// Dart mirror of the JSON contract in `backend/app/models.py`.
///
/// These are hand-written rather than code-generated on purpose: the contract is
/// small, and a final-year reader can diff the two files side by side. If you
/// change a field here, change it in the Pydantic models too.
library;

import 'enums.dart';

/// Reads a `String` defensively — nulls and non-strings become [fallback].
String _str(Object? v, [String fallback = '']) => v is String ? v : fallback;

/// Reads a nullable `double`, accepting ints from JSON (0 vs 0.0).
double? _optDouble(Object? v) => v is num ? v.toDouble() : null;

/// Reads a `List<String>`, dropping anything that is not a string.
List<String> _strList(Object? v) => v is List
    ? v.whereType<String>().toList(growable: false)
    : const <String>[];

/// One pharmacogenomic variant call.
class DetectedVariant {
  const DetectedVariant({
    required this.rsid,
    required this.gene,
    required this.genotype,
    required this.starAllele,
    required this.function,
  });

  /// Null for structural variants (e.g. a gene duplication), which have no
  /// dbSNP identifier.
  final String? rsid;
  final String gene;
  final String genotype;
  final String? starAllele;
  final String function;

  factory DetectedVariant.fromJson(Map<String, dynamic> json) =>
      DetectedVariant(
        rsid: json['rsid'] as String?,
        gene: _str(json['gene'], 'Unknown'),
        genotype: _str(json['genotype'], 'Unknown'),
        starAllele: json['star_allele'] as String?,
        function: _str(json['function'], 'Unknown'),
      );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'rsid': rsid,
    'gene': gene,
    'genotype': genotype,
    'star_allele': starAllele,
    'function': function,
  };

  /// e.g. "rs3892097 (*4)" — falls back gracefully when either part is absent.
  String get displayName {
    final String id = rsid ?? 'structural variant';
    return starAllele == null ? id : '$id ($starAllele)';
  }
}

class RiskAssessment {
  const RiskAssessment({
    required this.riskLabel,
    required this.confidenceScore,
    required this.severity,
  });

  final RiskLabel riskLabel;

  /// 0.0 – 1.0.
  final double confidenceScore;
  final Severity severity;

  factory RiskAssessment.fromJson(Map<String, dynamic> json) => RiskAssessment(
    riskLabel: RiskLabel.fromJson(json['risk_label']),
    confidenceScore: _optDouble(json['confidence_score']) ?? 0.0,
    severity: Severity.fromJson(json['severity']),
  );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'risk_label': riskLabel.toJson(),
    'confidence_score': confidenceScore,
    'severity': severity.toJson(),
  };
}

class PharmacogenomicProfile {
  const PharmacogenomicProfile({
    required this.primaryGene,
    required this.diplotype,
    required this.phenotype,
    required this.activityScore,
    required this.detectedVariants,
  });

  final String primaryGene;
  final String diplotype;
  final Phenotype phenotype;

  /// Null for genes with no activity-score model — do not render as 0.
  final double? activityScore;
  final List<DetectedVariant> detectedVariants;

  factory PharmacogenomicProfile.fromJson(Map<String, dynamic> json) {
    final Object? raw = json['detected_variants'];
    return PharmacogenomicProfile(
      primaryGene: _str(json['primary_gene'], 'Unknown'),
      diplotype: _str(json['diplotype'], 'Unknown'),
      phenotype: Phenotype.fromJson(json['phenotype']),
      activityScore: _optDouble(json['activity_score']),
      detectedVariants: raw is List
          ? raw
                .whereType<Map<String, dynamic>>()
                .map(DetectedVariant.fromJson)
                .toList(growable: false)
          : const <DetectedVariant>[],
    );
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
    'primary_gene': primaryGene,
    'diplotype': diplotype,
    'phenotype': phenotype.toJson(),
    'activity_score': activityScore,
    'detected_variants': detectedVariants
        .map((DetectedVariant v) => v.toJson())
        .toList(),
  };
}

class ClinicalRecommendation {
  const ClinicalRecommendation({
    required this.action,
    required this.dosingGuidance,
    required this.cpicRecommendation,
    required this.cpicEvidenceLevel,
    required this.alternatives,
    required this.source,
  });

  final String action;
  final String dosingGuidance;
  final String cpicRecommendation;
  final CpicEvidenceLevel cpicEvidenceLevel;
  final List<String> alternatives;

  /// "STUB" in Phase 1; a real guideline citation later.
  final String source;

  factory ClinicalRecommendation.fromJson(Map<String, dynamic> json) =>
      ClinicalRecommendation(
        action: _str(json['action']),
        dosingGuidance: _str(json['dosing_guidance']),
        cpicRecommendation: _str(json['cpic_recommendation']),
        cpicEvidenceLevel: CpicEvidenceLevel.fromJson(
          json['cpic_evidence_level'],
        ),
        alternatives: _strList(json['alternatives']),
        source: _str(json['source'], 'STUB'),
      );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'action': action,
    'dosing_guidance': dosingGuidance,
    'cpic_recommendation': cpicRecommendation,
    'cpic_evidence_level': cpicEvidenceLevel.toJson(),
    'alternatives': alternatives,
    'source': source,
  };
}

class LlmGeneratedExplanation {
  const LlmGeneratedExplanation({
    required this.summary,
    required this.mechanism,
    required this.variantRationale,
    required this.patientFriendly,
    required this.disclaimer,
  });

  final String summary;
  final String mechanism;
  final String variantRationale;
  final String patientFriendly;
  final String disclaimer;

  factory LlmGeneratedExplanation.fromJson(Map<String, dynamic> json) =>
      LlmGeneratedExplanation(
        summary: _str(json['summary']),
        mechanism: _str(json['mechanism']),
        variantRationale: _str(json['variant_rationale']),
        patientFriendly: _str(json['patient_friendly']),
        disclaimer: _str(json['disclaimer']),
      );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'summary': summary,
    'mechanism': mechanism,
    'variant_rationale': variantRationale,
    'patient_friendly': patientFriendly,
    'disclaimer': disclaimer,
  };
}

/// One entry in [AnalyzeResponse.analyses] — exactly one per requested drug.
class PerDrugResult {
  const PerDrugResult({
    required this.drug,
    required this.riskAssessment,
    required this.pharmacogenomicProfile,
    required this.clinicalRecommendation,
    required this.llmGeneratedExplanation,
  });

  final String drug;
  final RiskAssessment riskAssessment;
  final PharmacogenomicProfile pharmacogenomicProfile;
  final ClinicalRecommendation clinicalRecommendation;
  final LlmGeneratedExplanation llmGeneratedExplanation;

  factory PerDrugResult.fromJson(Map<String, dynamic> json) => PerDrugResult(
    drug: _str(json['drug'], 'unknown'),
    riskAssessment: RiskAssessment.fromJson(
      (json['risk_assessment'] as Map?)?.cast<String, dynamic>() ??
          const <String, dynamic>{},
    ),
    pharmacogenomicProfile: PharmacogenomicProfile.fromJson(
      (json['pharmacogenomic_profile'] as Map?)?.cast<String, dynamic>() ??
          const <String, dynamic>{},
    ),
    clinicalRecommendation: ClinicalRecommendation.fromJson(
      (json['clinical_recommendation'] as Map?)?.cast<String, dynamic>() ??
          const <String, dynamic>{},
    ),
    llmGeneratedExplanation: LlmGeneratedExplanation.fromJson(
      (json['llm_generated_explanation'] as Map?)?.cast<String, dynamic>() ??
          const <String, dynamic>{},
    ),
  );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'drug': drug,
    'risk_assessment': riskAssessment.toJson(),
    'pharmacogenomic_profile': pharmacogenomicProfile.toJson(),
    'clinical_recommendation': clinicalRecommendation.toJson(),
    'llm_generated_explanation': llmGeneratedExplanation.toJson(),
  };
}

/// Pipeline telemetry — lets the UI show how much to trust the result.
class QualityMetrics {
  const QualityMetrics({
    required this.vcfParsingSuccess,
    required this.variantsDetectedCount,
    required this.processingTimeMs,
    required this.warnings,
  });

  final bool vcfParsingSuccess;
  final int variantsDetectedCount;
  final int processingTimeMs;
  final List<String> warnings;

  factory QualityMetrics.fromJson(Map<String, dynamic> json) => QualityMetrics(
    vcfParsingSuccess: json['vcf_parsing_success'] == true,
    variantsDetectedCount: (json['variants_detected_count'] as num?)?.toInt() ?? 0,
    processingTimeMs: (json['processing_time_ms'] as num?)?.toInt() ?? 0,
    warnings: _strList(json['warnings']),
  );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'vcf_parsing_success': vcfParsingSuccess,
    'variants_detected_count': variantsDetectedCount,
    'processing_time_ms': processingTimeMs,
    'warnings': warnings,
  };
}

/// The 200 body of `POST /analyze`.
class AnalyzeResponse {
  const AnalyzeResponse({
    required this.patientId,
    required this.timestamp,
    required this.analyses,
    required this.qualityMetrics,
  });

  final String patientId;

  /// Kept as the raw ISO 8601 string as well as a parsed value — the raw form is
  /// what gets exported, and re-formatting it would break round-tripping.
  final String timestamp;
  final List<PerDrugResult> analyses;
  final QualityMetrics qualityMetrics;

  DateTime? get timestampUtc => DateTime.tryParse(timestamp)?.toUtc();

  factory AnalyzeResponse.fromJson(Map<String, dynamic> json) {
    final Object? raw = json['analyses'];
    return AnalyzeResponse(
      patientId: _str(json['patient_id'], 'UNKNOWN'),
      timestamp: _str(json['timestamp']),
      analyses: raw is List
          ? raw
                .whereType<Map<String, dynamic>>()
                .map(PerDrugResult.fromJson)
                .toList(growable: false)
          : const <PerDrugResult>[],
      qualityMetrics: QualityMetrics.fromJson(
        (json['quality_metrics'] as Map?)?.cast<String, dynamic>() ??
            const <String, dynamic>{},
      ),
    );
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
    'patient_id': patientId,
    'timestamp': timestamp,
    'analyses': analyses.map((PerDrugResult a) => a.toJson()).toList(),
    'quality_metrics': qualityMetrics.toJson(),
  };
}
