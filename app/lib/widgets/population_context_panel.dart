/// South Asian reduced-function context for one gene (Phase 9 B11).
///
/// Shown beside a result, never used for it. Every caveat the measurement
/// carries is on the panel, because a frequency without them reads as a fact
/// about the person whose result this is, and it is not: it is a lower bound
/// from research-format data on five cohorts, four collected outside India.
library;

import 'package:flutter/material.dart';

import '../models/population_context.dart';
import '../theme/tokens.dart';

/// The row title: the label says what the panel is not, before it is opened.
const String kPopulationContextTitle =
    'South Asian context — not used for this result';

class PopulationContextPanel extends StatelessWidget {
  const PopulationContextPanel({super.key, required this.gene});

  final String gene;

  @override
  Widget build(BuildContext context) {
    final bool known =
        gene.trim().isNotEmpty && gene.trim().toLowerCase() != 'unknown';
    final PopulationContext? ctx = known ? southAsianContextFor(gene) : null;
    if (ctx == null) {
      return Text(
        known
            ? 'No South Asian figure was measured for $gene, so none is shown.'
            : 'No gene is assessed for this drug, so there is no South Asian '
                  'figure to show.',
        style: Tokens.proseSm,
      );
    }
    final SouthAsianContext all = kSouthAsianContext;
    final CohortRate p = ctx.pooled;
    final int uncertain = ctx.uncertain.values.fold(0, (int a, int b) => a + b);
    final String lowerBound = ctx.positionsPresent == null
        ? 'A lower bound: a missing position reads as normal, so the true share '
              'can only be higher. How many of $gene’s positions the measured '
              'data carried was not measured.'
        : 'A lower bound: the measured data carried ${ctx.positionsPresent} of '
              'the ${ctx.positionsRequired} positions $gene needs, and a variant '
              'at a missing position reads as normal, so the true share can '
              'only be higher.';
    final List<String> caveats = <String>[
      'Context only: it does not change this result, and nothing here was '
          'used to reach it.',
      lowerBound,
      if (uncertain > 0)
        '$uncertain more were '
            '${ctx.uncertain.keys.join(' or ')} and are counted in the total, '
            'not as reduced.',
      'These are PharmCAT’s calls on research-format 1000 Genomes data, which '
          'this application itself would decline as incomplete.',
      'Four of the five cohorts were collected outside India (Lahore, '
          'Bangladesh, the UK twice, Houston), so they are not a '
          'representative sample of India.',
      'A frequency is not an outcome: nobody in these cohorts was observed '
          'taking a drug.',
      'Measured ${all.measured} by this project '
          '(reports/sas_cohort_expansion.md).',
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          'At least ${p.percent}% (95% CI ${p.low}–${p.high}%) of '
          '${all.samples} people in five South Asian 1000 Genomes cohorts were '
          'called ${ctx.reducedDefinition.toLowerCase()} for $gene.',
          style: Tokens.proseSm,
        ),
        const SizedBox(height: 6),
        for (final CohortRate c in ctx.cohorts)
          Text(
            '${c.cohort}  ${c.percent}% (${c.low}–${c.high}%, n=${c.n})',
            style: Tokens.monoSm,
          ),
        const SizedBox(height: 8),
        for (final String caveat in caveats)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Text('• $caveat', style: Tokens.proseSm),
          ),
      ],
    );
  }
}
