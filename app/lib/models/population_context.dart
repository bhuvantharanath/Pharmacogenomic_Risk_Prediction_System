/// The project's own measured South Asian reduced-function figures (Phase 9
/// B11), parsed from the generated table.
///
/// Context only. Nothing in the app reads these to reach a call, a phenotype
/// or a label: they are shown beside a result, never used for it. The figures
/// come from scripts/generate_population_context.py, which reads the project's
/// 2026-08-14 measurement and types no number of its own.
library;

import 'dart:convert';

import '../generated/population_context.g.dart';

class CohortRate {
  const CohortRate({
    required this.cohort,
    required this.reduced,
    required this.n,
    required this.percent,
    required this.low,
    required this.high,
  });

  factory CohortRate.fromJson(Map<String, dynamic> json) => CohortRate(
    cohort: json['cohort'] as String? ?? 'pooled',
    reduced: json['reduced'] as int,
    n: json['n'] as int,
    percent: json['percent'] as String,
    low: json['low'] as String,
    high: json['high'] as String,
  );

  final String cohort;
  final int reduced;
  final int n;

  /// One decimal, as the generator wrote it: displayed, never recomputed.
  final String percent;
  final String low;
  final String high;
}

class PopulationContext {
  const PopulationContext({
    required this.gene,
    required this.reducedDefinition,
    required this.pooled,
    required this.cohorts,
    required this.positionsPresent,
    required this.positionsRequired,
    required this.uncertain,
  });

  factory PopulationContext.fromJson(String gene, Map<String, dynamic> json) =>
      PopulationContext(
        gene: gene,
        reducedDefinition: json['reduced_definition'] as String,
        pooled: CohortRate.fromJson(json['pooled'] as Map<String, dynamic>),
        cohorts: <CohortRate>[
          for (final dynamic c in json['cohorts'] as List<dynamic>)
            CohortRate.fromJson(c as Map<String, dynamic>),
        ],
        positionsPresent: json['positions_present'] as int?,
        positionsRequired: json['positions_required'] as int?,
        uncertain: <String, int>{
          for (final MapEntry<String, dynamic> e
              in (json['uncertain'] as Map<String, dynamic>).entries)
            e.key: e.value as int,
        },
      );

  final String gene;
  final String reducedDefinition;
  final CohortRate pooled;
  final List<CohortRate> cohorts;

  /// Null when how many of the gene's positions the measured data carried was
  /// not measured (DPYD).
  final int? positionsPresent;
  final int? positionsRequired;

  /// Indeterminate, no-result and n/a counts: in the total, never reduced.
  final Map<String, int> uncertain;
}

class SouthAsianContext {
  const SouthAsianContext({
    required this.measured,
    required this.samples,
    required this.cohorts,
    required this.genes,
  });

  factory SouthAsianContext.fromJson(Map<String, dynamic> json) =>
      SouthAsianContext(
        measured: json['measured'] as String,
        samples: json['samples'] as int,
        cohorts: <String>[
          for (final dynamic c in json['cohorts'] as List<dynamic>) c as String,
        ],
        genes: <String, PopulationContext>{
          for (final MapEntry<String, dynamic> e
              in (json['genes'] as Map<String, dynamic>).entries)
            e.key: PopulationContext.fromJson(
              e.key,
              e.value as Map<String, dynamic>,
            ),
        },
      );

  final String measured;
  final int samples;
  final List<String> cohorts;
  final Map<String, PopulationContext> genes;
}

final SouthAsianContext kSouthAsianContext = SouthAsianContext.fromJson(
  jsonDecode(kSouthAsianContextJson) as Map<String, dynamic>,
);

/// The measured context for [gene], or null when none was measured.
PopulationContext? southAsianContextFor(String gene) =>
    kSouthAsianContext.genes[gene.toUpperCase()];
