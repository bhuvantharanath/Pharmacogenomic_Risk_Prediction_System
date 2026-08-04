/// Why a result came back `Unknown` — four distinct states, never one grey chip.
///
/// The project's contribution is representing uncertainty correctly, and the
/// backend found the same conflation three times in its own layers: treating
/// "no data" and "data we cannot classify" as one thing. Rendering every Unknown
/// identically would repeat that mistake in the UI, where the user actually sees
/// it.
///
/// These four are clinically different, and only one of them is the user's to fix:
///
///   notCallable   the gene cannot be resolved from a VCF at all, ever
///   lowCoverage   the uploaded file lacks required positions — ACTIONABLE
///   ambiguous     several genotypes fit and they disagree about function
///   noGuidance    CPIC publishes nothing for this gene/drug/phenotype
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

enum UnknownReason {
  /// Structural variation a VCF cannot express (CYP2D6 copy number).
  notCallable,

  /// The uploaded VCF lacks enough required positions. The user can fix this.
  lowCoverage,

  /// Several diplotypes fit and their phenotypes disagree about function.
  ambiguous,

  /// CPIC has no recommendation for this combination.
  noGuidance,

  /// Unknown for a reason the response does not explain. Shown as such rather
  /// than guessed at.
  unspecified;

  /// Short label for the badge.
  String get headline => switch (this) {
    UnknownReason.notCallable => 'Not determinable from a VCF',
    UnknownReason.lowCoverage => 'Your file is missing required positions',
    UnknownReason.ambiguous => 'Several genotypes fit this data',
    UnknownReason.noGuidance => 'No CPIC guidance for this combination',
    UnknownReason.unspecified => 'Result withheld',
  };

  /// Whether the *user* can do something about it. Drives the call to action.
  bool get isActionable => this == UnknownReason.lowCoverage;

  String get explanation => switch (this) {
    UnknownReason.notCallable =>
      'This gene is defined by structural and copy-number variation, which a VCF '
      'file cannot represent. No amount of extra sequencing depth in a VCF will '
      'resolve it — it needs a different assay. The system declines to guess '
      'rather than report a genotype it cannot support.',
    UnknownReason.lowCoverage =>
      'Some of the positions needed to identify this gene carry no genotype in '
      'your file. That is not a small gap: a variant whose defining position is '
      'absent is invisible, so the genotype would read as normal and a '
      'reduced-function result could be reported as safe. The system declines '
      'rather than risk that.',
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
      'reference — a clinical pharmacogenomic panel, or whole-genome/exome data '
      'called with all sites emitted. A variants-only file cannot work here.',
    _ => null,
  };
}

/// Detect why [result] is Unknown, using the typed coverage data first and
/// falling back to warning text.
UnknownReason classifyUnknown(
  PerDrugResult result,
  QualityMetrics metrics,
) {
  final String gene = result.pharmacogenomicProfile.primaryGene;

  // 1. TYPED SIGNAL, preferred. Coverage is a real field, not prose.
  final GeneCoverage? cov = metrics.positionCoverage[gene];
  if (cov != null && !cov.sufficient) {
    return UnknownReason.lowCoverage;
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
      '${result.clinicalRecommendation.source}'.toLowerCase();
  if (recommendation.contains('no cpic') ||
      recommendation.contains('not covered by any cpic') ||
      recommendation.contains('no pharmacogenomic recommendation')) {
    return UnknownReason.noGuidance;
  }
  return UnknownReason.unspecified;
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
