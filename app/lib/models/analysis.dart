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
    required this.recommendationDiplotype,
    required this.candidateDiplotypes,
    required this.phenotype,
    required this.activityScore,
    required this.detectedVariants,
  });

  final String primaryGene;

  /// What PharmCAT called — the patient's genotype, compound alleles intact.
  final String diplotype;

  /// The reduced diplotype CPIC guidance was found by. Differs from [diplotype]
  /// only for compound genotypes (DPYD in practice).
  ///
  /// PROVENANCE, NOT PATIENT-FACING — deliberately not rendered anywhere. It is
  /// carried so the client stays in sync with the response contract and so an
  /// audit can see why a recommendation applied. Conflating it with [diplotype]
  /// was a real defect on the backend; showing it to a patient would repeat the
  /// confusion in the UI instead of the parser.
  final String? recommendationDiplotype;

  /// Every equally-likely diplotype, when PharmCAT could not narrow to one.
  /// Empty for an unambiguous call. When non-empty, [diplotype] is a marker
  /// ("Undetermined (4 equally likely)") rather than a call.
  final List<String> candidateDiplotypes;
  final Phenotype phenotype;

  /// Null for genes with no activity-score model — do not render as 0.
  final double? activityScore;
  final List<DetectedVariant> detectedVariants;

  factory PharmacogenomicProfile.fromJson(Map<String, dynamic> json) {
    final Object? raw = json['detected_variants'];
    return PharmacogenomicProfile(
      primaryGene: _str(json['primary_gene'], 'Unknown'),
      diplotype: _str(json['diplotype'], 'Unknown'),
      recommendationDiplotype: json['recommendation_diplotype'] as String?,
      candidateDiplotypes: (json['candidate_diplotypes'] as List<dynamic>?)
              ?.whereType<String>()
              .toList(growable: false) ??
          const <String>[],
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
    'recommendation_diplotype': recommendationDiplotype,
    'candidate_diplotypes': candidateDiplotypes,
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
/// Coverage of one gene's required defining positions in the uploaded VCF.
///
/// A position counts only when the file carries an EXPLICIT genotype for it,
/// including homozygous-reference. `./.` and absent rows do not count — that
/// distinction is the whole point, because a variants-only file looks exactly
/// like one where those positions were never assayed.
class GeneCoverage {
  const GeneCoverage({
    required this.positionsPresent,
    required this.positionsRequired,
    required this.percent,
    required this.minimumPercent,
    required this.sufficient,
  });

  final int positionsPresent;
  final int positionsRequired;
  final double percent;
  final int minimumPercent;
  final bool sufficient;

  factory GeneCoverage.fromJson(Map<String, dynamic> json) => GeneCoverage(
    positionsPresent: (json['positions_present'] as num?)?.toInt() ?? 0,
    positionsRequired: (json['positions_required'] as num?)?.toInt() ?? 0,
    percent: (json['percent'] as num?)?.toDouble() ?? 0,
    minimumPercent: (json['minimum_percent'] as num?)?.toInt() ?? 100,
    sufficient: json['sufficient'] == true,
  );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'positions_present': positionsPresent,
    'positions_required': positionsRequired,
    'percent': percent,
    'minimum_percent': minimumPercent,
    'sufficient': sufficient,
  };
}

/// One gene's readiness, as reported by `POST /coverage` before any analysis.
///
/// Mirrors the backend's `GeneReadiness`. Distinct from [GeneCoverage], which
/// describes the same gene *after* a run: this one also carries whether the gene
/// is readable from a VCF at all, and the sentence to show when it is not.
class GeneReadiness {
  const GeneReadiness({
    required this.gene,
    required this.positionsFound,
    required this.positionsRequired,
    required this.thresholdPercent,
    required this.percent,
    required this.passes,
    required this.notReadableFromVcf,
    required this.reason,
  });

  final String gene;
  final int positionsFound;
  final int positionsRequired;
  final int thresholdPercent;
  final double percent;
  final bool passes;

  /// True for genes no VCF can resolve, whatever the coverage — CYP2D6 is
  /// defined by copy number. The UI must show [reason] rather than a zero bar:
  /// zero says "your file is deficient", when the limit is the file format.
  final bool notReadableFromVcf;

  /// Empty when the gene passes. There is nothing to explain about a pass.
  final String reason;

  /// The shape [CoverageCensus] draws, so the readiness screen and the results
  /// screen render identical tick rows from the two different endpoints.
  GeneCoverage get asCoverage => GeneCoverage(
    positionsPresent: positionsFound,
    positionsRequired: positionsRequired,
    percent: percent,
    minimumPercent: thresholdPercent,
    sufficient: passes,
  );

  factory GeneReadiness.fromJson(Map<String, dynamic> json) => GeneReadiness(
    gene: _str(json['gene']),
    positionsFound: (json['positions_found'] as num?)?.toInt() ?? 0,
    positionsRequired: (json['positions_required'] as num?)?.toInt() ?? 0,
    thresholdPercent: (json['threshold_percent'] as num?)?.toInt() ?? 100,
    percent: (json['percent'] as num?)?.toDouble() ?? 0,
    passes: json['passes'] == true,
    notReadableFromVcf: json['not_readable_from_vcf'] == true,
    reason: _str(json['reason']),
  );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'gene': gene,
    'positions_found': positionsFound,
    'positions_required': positionsRequired,
    'threshold_percent': thresholdPercent,
    'percent': percent,
    'passes': passes,
    'not_readable_from_vcf': notReadableFromVcf,
    'reason': reason,
  };
}

/// When the guidance behind a result was captured.
///
/// A frozen explanation store carries an implicit "as of" that would otherwise
/// be invisible. This is a date stamp, NOT a staleness check — the backend does
/// not monitor CPIC, and the UI must not imply that it does.
class GuidelineProvenance {
  const GuidelineProvenance({
    required this.pharmcatVersion,
    required this.cpicDataVersion,
    required this.explanationsGeneratedAt,
    required this.cpicSource,
    required this.note,
  });

  final String pharmcatVersion;

  /// PharmCAT's own data-bundle stamp. Empty on `/coverage`, which does not run
  /// PharmCAT and so has not observed one.
  final String cpicDataVersion;
  final String explanationsGeneratedAt;
  final String cpicSource;
  final String note;

  /// `2026-07-24T09:53:53Z` -> `24 Jul 2026`. Returns the raw string when it is
  /// not parseable, rather than hiding a value the backend did send.
  String get explanationsDate => _formatDate(explanationsGeneratedAt);

  /// The one-line form for a results footer: versions, comma separated, with
  /// empty parts dropped so `/coverage` does not render a dangling separator.
  String get summaryLine => <String>[
    if (pharmcatVersion.isNotEmpty) 'PharmCAT $pharmcatVersion',
    if (cpicDataVersion.isNotEmpty) 'CPIC data $cpicDataVersion',
    if (explanationsDate.isNotEmpty) 'explanations $explanationsDate',
  ].join(' · ');

  factory GuidelineProvenance.fromJson(Map<String, dynamic> json) =>
      GuidelineProvenance(
        pharmcatVersion: _str(json['pharmcat_version']),
        cpicDataVersion: _str(json['cpic_data_version']),
        explanationsGeneratedAt: _str(json['explanations_generated_at']),
        cpicSource: _str(json['cpic_source']),
        note: _str(json['note']),
      );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'pharmcat_version': pharmcatVersion,
    'cpic_data_version': cpicDataVersion,
    'explanations_generated_at': explanationsGeneratedAt,
    'cpic_source': cpicSource,
    'note': note,
  };
}

const List<String> _months = <String>[
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

String _formatDate(String iso) {
  if (iso.isEmpty) return '';
  final DateTime? at = DateTime.tryParse(iso);
  if (at == null) return iso;
  return '${at.day} ${_months[at.month - 1]} ${at.year}';
}

/// The 200 body of `POST /coverage` — what a file can answer, before analysis.
class CoverageResponse {
  const CoverageResponse({
    required this.genes,
    required this.genesPassing,
    required this.genesTotal,
    required this.answerableDrugs,
    required this.unanswerableDrugs,
    required this.variantsOnly,
    required this.warnings,
    this.guidelineProvenance,
  });

  final List<GeneReadiness> genes;
  final int genesPassing;
  final int genesTotal;
  final List<String> answerableDrugs;
  final List<String> unanswerableDrugs;
  final bool variantsOnly;
  final List<String> warnings;
  final GuidelineProvenance? guidelineProvenance;

  /// Genes held back by the file format rather than by its coverage. Separated
  /// because the remedy differs: re-calling helps one group and never the other.
  List<GeneReadiness> get blockedByFormat =>
      genes.where((GeneReadiness g) => g.notReadableFromVcf).toList();

  List<GeneReadiness> get shortOnCoverage => genes
      .where((GeneReadiness g) => !g.passes && !g.notReadableFromVcf)
      .toList();

  factory CoverageResponse.fromJson(Map<String, dynamic> json) {
    final Object? raw = json['genes'];
    final Object? provenance = json['guideline_provenance'];
    return CoverageResponse(
      genes: raw is List
          ? raw
                .whereType<Map<String, dynamic>>()
                .map(GeneReadiness.fromJson)
                .toList()
          : const <GeneReadiness>[],
      genesPassing: (json['genes_passing'] as num?)?.toInt() ?? 0,
      genesTotal: (json['genes_total'] as num?)?.toInt() ?? 0,
      answerableDrugs: _strList(json['answerable_drugs']),
      unanswerableDrugs: _strList(json['unanswerable_drugs']),
      variantsOnly: json['variants_only'] == true,
      warnings: _strList(json['warnings']),
      guidelineProvenance: provenance is Map<String, dynamic>
          ? GuidelineProvenance.fromJson(provenance)
          : null,
    );
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
    'genes': <Map<String, dynamic>>[
      for (final GeneReadiness g in genes) g.toJson(),
    ],
    'genes_passing': genesPassing,
    'genes_total': genesTotal,
    'answerable_drugs': answerableDrugs,
    'unanswerable_drugs': unanswerableDrugs,
    'variants_only': variantsOnly,
    'warnings': warnings,
    'guideline_provenance': guidelineProvenance?.toJson(),
  };
}

class QualityMetrics {
  const QualityMetrics({
    required this.vcfParsingSuccess,
    required this.variantsDetectedCount,
    required this.processingTimeMs,
    required this.warnings,
    required this.positionCoverage,
    this.guidelineProvenance,
  });

  final bool vcfParsingSuccess;
  final int variantsDetectedCount;
  final int processingTimeMs;
  final List<String> warnings;

  /// When the guidance behind this result was captured. Nullable because it was
  /// added after Phase 1 and an older backend will not send it.
  final GuidelineProvenance? guidelineProvenance;

  /// Per-gene coverage of PharmCAT's required defining positions, keyed by gene.
  /// Present on every response, pass or fail — a confident result at low
  /// coverage is the dangerous case, so the number is needed either way.
  final Map<String, GeneCoverage> positionCoverage;

  factory QualityMetrics.fromJson(Map<String, dynamic> json) => QualityMetrics(
    vcfParsingSuccess: json['vcf_parsing_success'] == true,
    variantsDetectedCount: (json['variants_detected_count'] as num?)?.toInt() ?? 0,
    processingTimeMs: (json['processing_time_ms'] as num?)?.toInt() ?? 0,
    warnings: _strList(json['warnings']),
    positionCoverage: <String, GeneCoverage>{
      for (final MapEntry<String, dynamic> e
          in ((json['position_coverage'] as Map<String, dynamic>?) ??
                  const <String, dynamic>{})
              .entries)
        if (e.value is Map<String, dynamic>)
          e.key: GeneCoverage.fromJson(e.value as Map<String, dynamic>),
    },
    guidelineProvenance: json['guideline_provenance'] is Map<String, dynamic>
        ? GuidelineProvenance.fromJson(
            json['guideline_provenance'] as Map<String, dynamic>,
          )
        : null,
  );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'vcf_parsing_success': vcfParsingSuccess,
    'variants_detected_count': variantsDetectedCount,
    'processing_time_ms': processingTimeMs,
    'warnings': warnings,
    'position_coverage': <String, dynamic>{
      for (final MapEntry<String, GeneCoverage> e in positionCoverage.entries)
        e.key: e.value.toJson(),
    },
    'guideline_provenance': guidelineProvenance?.toJson(),
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
