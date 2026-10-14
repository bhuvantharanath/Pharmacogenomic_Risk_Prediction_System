/// Why a result came back `Unknown` — four distinct states, never one grey chip.
///
/// The project's contribution is representing uncertainty correctly, and the
/// backend found the same conflation three times in its own layers: treating
/// "no data" and "data we cannot classify" as one thing. Rendering every Unknown
/// identically would repeat that mistake in the UI, where the user actually sees
/// it.
///
/// These are clinically different, and only two of them are the user's to fix:
///
///   notCallable        this application does not call the gene from a VCF
///   lowCoverage        the uploaded file lacks required positions — ACTIONABLE
///   unusableGenotypes  every position is present, but a genotype failed its
///                      FILTER or was only partly called — ACTIONABLE
///   ambiguous          several genotypes fit and they disagree about function
///   noGuidance         CPIC publishes nothing for this gene/drug/phenotype
///
/// HOW THEY ARE DETECTED, and where that is fragile
///
/// `lowCoverage` is read from `quality_metrics.position_coverage`, a typed field —
/// reliable. The other three are inferred from warning *text*, because the API has
/// no machine-readable reason code. That is string matching against prose, which
/// is exactly the brittleness this project documented elsewhere; it is done here
/// only because the alternative is showing the user nothing. A `reason_code` on
/// the response would make this robust, and is recorded as the one API gap the
/// redesign could not paper over.
library;

import 'analysis.dart';
import 'enums.dart';
import '../generated/capabilities.g.dart';

enum UnknownReason {
  /// Structural and copy-number variation this application does not call from
  /// an uploaded VCF (CYP2D6).
  notCallable,

  /// The uploaded VCF lacks enough required positions. The user can fix this.
  lowCoverage,

  /// Every required position is in the file, but at least one genotype could
  /// not be used: a failed FILTER, a partial, missing or malformed call. Also
  /// the user's to fix — by re-calling, not by emitting more sites.
  unusableGenotypes,

  /// Several diplotypes fit and their phenotypes disagree about function.
  ambiguous,

  /// CPIC has no recommendation for this combination.
  noGuidance,

  /// Unknown for a reason the response does not explain. Shown as such rather
  /// than guessed at.
  unspecified;

  /// Short label for the badge.
  String get headline => switch (this) {
    UnknownReason.notCallable => 'Not called from an uploaded VCF',
    UnknownReason.lowCoverage => 'Your file is missing required positions',
    UnknownReason.unusableGenotypes => 'Required genotypes could not be used',
    UnknownReason.ambiguous => 'Several genotypes fit this data',
    UnknownReason.noGuidance => 'No CPIC guidance for this combination',
    UnknownReason.unspecified => 'Result withheld',
  };

  /// Whether the *user* can do something about it. Drives the call to action.
  bool get isActionable =>
      this == UnknownReason.lowCoverage ||
      this == UnknownReason.unusableGenotypes;

  String get explanation => switch (this) {
    UnknownReason.notCallable =>
      'This gene’s result depends on structural and copy-number changes that '
          'need specialised analysis of the sequencing reads, which this '
          'application does not perform. No VCF uploaded here will resolve it — '
          'it needs a specialised test or caller. The system declines to guess '
          'rather than report a genotype it cannot support.',
    UnknownReason.lowCoverage =>
      'Some of the positions needed to identify this gene carry no genotype in '
          'your file. That is not a small gap: a change whose key position is '
          'absent is invisible, so the genotype would read as normal and a '
          'reduced-function result could be reported as safe. The system declines '
          'rather than risk that.',
    UnknownReason.unusableGenotypes =>
      'Every position needed to identify this gene is in your file, but at '
          'least one carries a genotype that cannot be used — a failed FILTER, '
          'or a partial or missing call. A change at an unusable position is '
          'invisible, so a reduced-function result could be reported as normal. '
          'The system declines rather than risk that.',
    UnknownReason.ambiguous =>
      'More than one genotype is equally consistent with your data, and they do '
          'not agree on how this gene functions. Reporting whichever one happened to '
          'come first would present a coin-flip as a finding.',
    UnknownReason.noGuidance =>
      'The genotype was determined successfully. CPIC simply publishes no dosing '
          'recommendation for this particular gene, drug and phenotype combination — '
          'so there is nothing to report rather than nothing to find.',
    UnknownReason.unspecified =>
      'The system could not support a confident result here and did not record a '
          'specific reason. It declines rather than assert something it cannot back.',
  };

  /// What the user should do. Null when there is nothing they can do.
  String? get callToAction => switch (this) {
    UnknownReason.lowCoverage =>
      'Upload a VCF that reports ALL positions, including those matching the '
          'reference — a clinical pharmacogenomic panel, or data covering all your '
          'genes, produced with every position reported. A variants-only file '
          'cannot work here.',
    UnknownReason.unusableGenotypes =>
      'Check the genotype and FILTER values your caller wrote at the affected '
          'positions, and re-call them so each carries a complete genotype that '
          'passed its filters.',
    _ => null,
  };
}

/// Detect why [result] is Unknown, using the typed coverage data first and
/// falling back to warning text.
UnknownReason classifyUnknown(PerDrugResult result, QualityMetrics metrics) {
  final String gene = geneForResult(result);
  final DrugCapability? capability = capabilityForDrug(result.drug);

  // No uploaded VCF enables this app's CYP2D6 calling or its unsupported
  // warfarin dosing. These limits take precedence over a short position census.
  if (gene == 'CYP2D6' && capability?.guidanceCapable == false) {
    return UnknownReason.notCallable;
  }
  if (capability != null && !capability.guidanceCapable) {
    return UnknownReason.unspecified;
  }

  // 1. TYPED SIGNAL, preferred. Coverage is a real field, not prose, and its
  // evidence counts separate an absent row from one whose genotype failed —
  // the two need different fixes.
  final GeneCoverage? cov = metrics.positionCoverage[gene];
  if (cov != null && !cov.sufficient) {
    return cov.absentPositions == 0 && cov.unusablePositions > 0
        ? UnknownReason.unusableGenotypes
        : UnknownReason.lowCoverage;
  }

  // 2. Warning text. Fragile by nature — see the library doc.
  final String joined = metrics.warnings.join(' ').toLowerCase();

  if (joined.contains('structural/copy-number') ||
      joined.contains('copy-number variation cannot be resolved')) {
    if (gene.toUpperCase() == 'CYP2D6') return UnknownReason.notCallable;
  }
  if (joined.contains('disagree about function')) {
    return UnknownReason.ambiguous;
  }
  if (result.pharmacogenomicProfile.candidateDiplotypes.length > 1) {
    return UnknownReason.ambiguous;
  }
  final String recommendation =
      '${result.clinicalRecommendation.action} '
              '${result.clinicalRecommendation.source}'
          .toLowerCase();
  if (recommendation.contains('no cpic') ||
      recommendation.contains('not covered by any cpic') ||
      recommendation.contains('no pharmacogenomic recommendation')) {
    return UnknownReason.noGuidance;
  }
  return UnknownReason.unspecified;
}

/// The API may redact the called gene to `Unknown` when it abstains. The
/// audited capability registry still identifies which gene's evidence matters.
String geneForResult(PerDrugResult result) {
  final String reported = result.pharmacogenomicProfile.primaryGene;
  if (reported.isNotEmpty && reported.toLowerCase() != 'unknown') {
    return reported;
  }
  return capabilityForDrug(result.drug)?.primaryGene ?? reported;
}

/// An explicit backend abstention is a reason, even when it fits none of the
/// four more specific UI categories. Do not claim no reason was recorded.
String unknownExplanation(PerDrugResult result, UnknownReason reason) {
  if (reason == UnknownReason.unspecified &&
      result.clinicalRecommendation.action.trim().isNotEmpty) {
    return result.clinicalRecommendation.action;
  }
  return reason.explanation;
}

/// Severity ranks. `critical` must visibly outrank `high` even though both
/// Ineffective and Toxic render red.
int severityRank(Severity s) => switch (s) {
  Severity.none => 0,
  Severity.low => 1,
  Severity.moderate => 2,
  Severity.high => 3,
  Severity.critical => 4,
};
