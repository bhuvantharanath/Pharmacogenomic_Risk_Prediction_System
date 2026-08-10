/// Enums mirroring the Python enums in `backend/app/models.py`.
///
/// Every `fromJson` is deliberately tolerant: an unrecognised wire value falls
/// back to the enum's "unknown" member rather than throwing. A backend that
/// gains a new risk label should not crash an older client.
library;

/// Top-line verdict for one drug. Drives the result card's colour.
enum RiskLabel {
  safe('Safe'),
  adjustDosage('Adjust Dosage'),
  toxic('Toxic'),
  ineffective('Ineffective'),
  unknown('Unknown');

  const RiskLabel(this.wireValue);

  /// The exact string used on the wire — do not derive this from `name`.
  final String wireValue;

  /// Ordering by CONSEQUENCE, for any list a user scans rather than reads.
  ///
  /// Alphabetical order is the wrong default here: it puts "azathioprine —
  /// Safe" above "clopidogrel — Ineffective", so the row that changes what
  /// someone should do arrives after two rows that do not.
  ///
  /// Toxic and Ineffective share rank 0 deliberately. They are different
  /// mechanisms — harm from exposure versus therapeutic failure — but both mean
  /// "do not proceed as written", and ranking one above the other would assert
  /// a clinical priority this project has no basis for. Severity breaks the tie.
  ///
  /// Unknown sits LAST, not because it is unimportant — it is frequently the
  /// hard-won correct answer — but because it is the one row where nothing about
  /// the prescription changes on the strength of this result alone.
  int get consequenceRank => switch (this) {
    RiskLabel.toxic => 0,
    RiskLabel.ineffective => 0,
    RiskLabel.adjustDosage => 1,
    RiskLabel.safe => 2,
    RiskLabel.unknown => 3,
  };

  static RiskLabel fromJson(Object? value) => values.firstWhere(
    (RiskLabel e) => e.wireValue == value,
    orElse: () => RiskLabel.unknown,
  );

  String toJson() => wireValue;
}

/// How bad the consequence is if the risk is ignored.
enum Severity {
  none('none'),
  low('low'),
  moderate('moderate'),
  high('high'),
  critical('critical');

  const Severity(this.wireValue);

  final String wireValue;

  static Severity fromJson(Object? value) => values.firstWhere(
    (Severity e) => e.wireValue == value,
    orElse: () => Severity.none,
  );

  String toJson() => wireValue;
}

/// CPIC metaboliser phenotype.
enum Phenotype {
  pm('PM', 'Poor metaboliser'),
  im('IM', 'Intermediate metaboliser'),
  nm('NM', 'Normal metaboliser'),
  rm('RM', 'Rapid metaboliser'),
  urm('URM', 'Ultrarapid metaboliser'),
  unknown('Unknown', 'Unknown');

  const Phenotype(this.wireValue, this.label);

  final String wireValue;

  /// Spelled-out form, for tooltips and the expanded card ("PM" alone is opaque
  /// to anyone outside the field).
  final String label;

  static Phenotype fromJson(Object? value) => values.firstWhere(
    (Phenotype e) => e.wireValue == value,
    orElse: () => Phenotype.unknown,
  );

  String toJson() => wireValue;
}

/// CPIC strength-of-evidence grade.
enum CpicEvidenceLevel {
  a('A'),
  b('B'),
  c('C'),
  d('D'),
  unknown('Unknown');

  const CpicEvidenceLevel(this.wireValue);

  final String wireValue;

  static CpicEvidenceLevel fromJson(Object? value) => values.firstWhere(
    (CpicEvidenceLevel e) => e.wireValue == value,
    orElse: () => CpicEvidenceLevel.unknown,
  );

  String toJson() => wireValue;
}
