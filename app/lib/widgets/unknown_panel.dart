/// Explains an `Unknown` result in its own terms.
///
/// DESIGN PRINCIPLE: uncertainty gets equal visual weight to certainty. A grey
/// chip reading "Unknown" tells the user the system failed; in fact an Unknown is
/// usually the system working — declining to assert something it cannot support.
/// So this panel is as prominent as a risk badge, states WHICH of four distinct
/// states applies, and where the user can act, says exactly what to do.
library;

import 'package:flutter/material.dart';

import '../models/analysis.dart';
import '../models/unknown_reason.dart';

class UnknownPanel extends StatelessWidget {
  const UnknownPanel({
    super.key,
    required this.reason,
    required this.profile,
    this.coverage,
  });

  final UnknownReason reason;
  final PharmacogenomicProfile profile;
  final GeneCoverage? coverage;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final bool dark = theme.brightness == Brightness.dark;

    // Actionable states are amber (you can fix this); inherent limits are slate
    // (nothing to fix). Neither is red: an honest decline is not an error.
    final Color accent = reason.isActionable
        ? (dark ? const Color(0xFFE8B33C) : const Color(0xFF9A6B00))
        : (dark ? const Color(0xFF8AB4F8) : const Color(0xFF1A5FB4));
    final IconData icon = switch (reason) {
      UnknownReason.lowCoverage => Icons.upload_file_outlined,
      UnknownReason.notCallable => Icons.biotech_outlined,
      UnknownReason.ambiguous => Icons.alt_route,
      UnknownReason.noGuidance => Icons.menu_book_outlined,
      UnknownReason.unspecified => Icons.help_outline,
    };

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: dark ? 0.14 : 0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: accent.withValues(alpha: 0.45)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Icon(icon, size: 20, color: accent),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  reason.headline,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: accent,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(reason.explanation, style: theme.textTheme.bodyMedium),

          // The measured numbers, for the one state where they exist.
          if (reason == UnknownReason.lowCoverage && coverage != null) ...<Widget>[
            const SizedBox(height: 12),
            _CoverageBar(coverage: coverage!, accent: accent),
          ],

          // The candidates, so an ambiguous call is never rendered as an answer.
          if (reason == UnknownReason.ambiguous &&
              profile.candidateDiplotypes.isNotEmpty) ...<Widget>[
            const SizedBox(height: 12),
            Text(
              '${profile.candidateDiplotypes.length} equally likely genotypes',
              style: theme.textTheme.labelMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: <Widget>[
                for (final String d in profile.candidateDiplotypes)
                  Chip(
                    label: Text(d, style: const TextStyle(fontSize: 12)),
                    visualDensity: VisualDensity.compact,
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
              ],
            ),
          ],

          if (reason.callToAction != null) ...<Widget>[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: accent.withValues(alpha: dark ? 0.18 : 0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Icon(Icons.lightbulb_outline, size: 18, color: accent),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      reason.callToAction!,
                      style: theme.textTheme.bodySmall
                          ?.copyWith(fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _CoverageBar extends StatelessWidget {
  const _CoverageBar({required this.coverage, required this.accent});

  final GeneCoverage coverage;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final double frac = (coverage.percent / 100).clamp(0.0, 1.0);
    final double need = (coverage.minimumPercent / 100).clamp(0.0, 1.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          '${coverage.positionsPresent} of ${coverage.positionsRequired} '
          'required positions present '
          '(${coverage.percent.toStringAsFixed(0)}%) — '
          'this gene needs ${coverage.minimumPercent}%',
          style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 6),
        // The required level is drawn as a marker on the same track, so the size
        // of the shortfall is visible rather than arithmetic the user must do.
        LayoutBuilder(
          builder: (BuildContext context, BoxConstraints c) => SizedBox(
            height: 12,
            child: Stack(
              children: <Widget>[
                Container(
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(6),
                  ),
                ),
                FractionallySizedBox(
                  widthFactor: frac,
                  child: Container(
                    decoration: BoxDecoration(
                      color: accent,
                      borderRadius: BorderRadius.circular(6),
                    ),
                  ),
                ),
                Positioned(
                  left: (c.maxWidth * need).clamp(0.0, c.maxWidth - 2),
                  child: Container(width: 2, height: 12, color: theme.colorScheme.onSurface),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'The marker shows the minimum this gene requires.',
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}
