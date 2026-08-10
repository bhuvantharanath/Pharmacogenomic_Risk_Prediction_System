/// Per-gene input coverage, shown on EVERY analysis — pass or fail.
///
/// Deliberately not failure-only. The dangerous case measured by this project is
/// a *confident* result produced from thin input: at 60% position coverage up to
/// 28.6% of calls were confidently wrong, and every one of them reported reduced
/// function as normal. Showing coverage only when it fails would hide precisely
/// the situation the reader needs to judge.
library;

import 'package:flutter/material.dart';

import '../models/analysis.dart';
import '../theme/tokens.dart';
import 'disclosure_row.dart';

/// The prominent alert for a variants-only file — the single most likely way a
/// real user gets a wrong answer, so it is not a footnote.
class VariantsOnlyAlert extends StatelessWidget {
  const VariantsOnlyAlert({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final bool dark = theme.brightness == Brightness.dark;
    final Color accent = dark ? const Color(0xFFF16A6A) : const Color(0xFFB3261E);

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: dark ? 0.16 : 0.09),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: accent, width: 1.5),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(Icons.report_problem_outlined, color: accent),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'This file appears to list only variants',
                  style: theme.textTheme.titleSmall
                      ?.copyWith(fontWeight: FontWeight.w700, color: accent),
                ),
                const SizedBox(height: 6),
                Text(message, style: theme.textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class CoverageSummary extends StatelessWidget {
  const CoverageSummary({super.key, required this.coverage});

  final Map<String, GeneCoverage> coverage;

  @override
  Widget build(BuildContext context) {
    if (coverage.isEmpty) return const SizedBox.shrink();
    final ThemeData theme = Theme.of(context);
    final List<String> genes = coverage.keys.toList()..sort();
    final int ok = coverage.values.where((GeneCoverage c) => c.sufficient).length;

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: DisclosureRow(
        title: 'Input coverage',
        subtitle: '$ok of ${coverage.length} genes have enough positions to '
            'call',
        rule: false,
        leading: Icon(
          ok == coverage.length ? Icons.verified_outlined : Icons.rule,
          color: theme.colorScheme.primary,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'How much of the data each gene needs was present in your file. '
              'Genes below their minimum are reported as Unknown rather than '
              'guessed at.',
              style: Tokens.uiSm,
            ),
            const SizedBox(height: 10),
            for (final String gene in genes)
              _CoverageRow(gene: gene, coverage: coverage[gene]!),
          ],
        ),
      ),
    );
  }
}

class _CoverageRow extends StatelessWidget {
  const _CoverageRow({required this.gene, required this.coverage});

  final String gene;
  final GeneCoverage coverage;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final bool dark = theme.brightness == Brightness.dark;
    final Color accent = coverage.sufficient
        ? (dark ? const Color(0xFF4CC66B) : const Color(0xFF1B7F3B))
        : (dark ? const Color(0xFFE8B33C) : const Color(0xFF9A6B00));

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: <Widget>[
          SizedBox(
            width: 78,
            child: Text(gene, style: theme.textTheme.labelMedium),
          ),
          Icon(
            coverage.sufficient ? Icons.check_circle : Icons.error_outline,
            size: 16,
            color: accent,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: (coverage.percent / 100).clamp(0.0, 1.0),
                minHeight: 8,
                backgroundColor: theme.colorScheme.surfaceContainerHighest,
                valueColor: AlwaysStoppedAnimation<Color>(accent),
              ),
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            width: 108,
            child: Text(
              '${coverage.positionsPresent}/${coverage.positionsRequired}'
              '  (min ${coverage.minimumPercent}%)',
              style: theme.textTheme.labelSmall,
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );
  }
}
