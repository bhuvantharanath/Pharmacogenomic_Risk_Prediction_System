/// The coverage census — one tick per required position, filled if reported.
///
/// WHY A CENSUS AND NOT A PERCENTAGE BAR
///
/// A bar showing "11%" invites the reading "mostly missing, roughly". The census
/// shows what was actually counted: 35 discrete positions, 4 of them reported.
/// That is the literal shape of the evidence, and it makes the failure legible —
/// you can see the gaps rather than infer them from a ratio.
///
/// It renders on EVERY result, pass or fail. Showing it only on failure would
/// hide the dangerous case: a confident answer built on thin input. This project
/// measured that at 60% coverage up to 28.6% of calls were confidently WRONG,
/// every one of them reporting reduced function as normal — so the count is
/// exactly what a reader needs when the answer looks fine.
///
/// A gene that cannot be called from a VCF at all shows "not applicable" with a
/// reason, never a zero bar. Zero would say "your file is deficient"; the truth
/// is that no VCF can carry this information.
library;

import 'package:flutter/material.dart';

import '../models/analysis.dart';
import '../theme/tokens.dart';

class CoverageCensus extends StatelessWidget {
  const CoverageCensus({
    super.key,
    required this.gene,
    required this.coverage,
    this.notApplicableReason,
  });

  final String gene;
  final GeneCoverage? coverage;

  /// Set for genes that cannot be resolved from a VCF regardless of coverage.
  /// When present, ticks are suppressed entirely.
  final String? notApplicableReason;

  @override
  Widget build(BuildContext context) {
    if (notApplicableReason != null) return _notApplicable(context);
    final c = coverage;
    if (c == null) return const SizedBox.shrink();

    final bool complete = c.positionsPresent >= c.positionsRequired;
    final Color tick = c.sufficient ? Tokens.safe : Tokens.adjust;

    return Semantics(
      // One spoken sentence beats 35 unlabelled ticks for a screen reader.
      label: '$gene coverage: ${c.positionsPresent} of '
          '${c.positionsRequired} required positions reported'
          '${c.sufficient ? '' : ', below the ${c.minimumPercent} percent minimum'}',
      excludeSemantics: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              // Flexible, not fixed: at 360px a long gene name plus the count
              // overflows, and the count is the part that must never be clipped.
              Flexible(
                child: Text('$gene  positions',
                    style: Tokens.monoLabel, overflow: TextOverflow.ellipsis),
              ),
              const SizedBox(width: 8),
              // have / need, in mono — it is a count, not a claim.
              Text('${c.positionsPresent} / ${c.positionsRequired}',
                  style: Tokens.monoMd.copyWith(
                      fontWeight: FontWeight.w600, color: tick)),
            ],
          ),
          const SizedBox(height: 6),
          // Wrap, so 88 CYP2C9 ticks still fit at 360px.
          Wrap(
            spacing: 3,
            runSpacing: 3,
            children: <Widget>[
              for (int i = 0; i < c.positionsRequired; i++)
                _Tick(filled: i < c.positionsPresent, colour: tick),
            ],
          ),
          const SizedBox(height: 7),
          Text(
            complete
                ? 'Every required position was reported.'
                : '${c.positionsRequired - c.positionsPresent} of '
                    '${c.positionsRequired} positions were not reported in your file.',
            style: Tokens.uiSm.copyWith(color: complete ? Tokens.ink2 : tick),
          ),
        ],
      ),
    );
  }

  Widget _notApplicable(BuildContext context) => Semantics(
        label: '$gene: not applicable. $notApplicableReason',
        excludeSemantics: true,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Flexible(
                  child: Text('$gene  positions',
                      style: Tokens.monoLabel, overflow: TextOverflow.ellipsis),
                ),
                const SizedBox(width: 8),
                Text('not applicable',
                    style: Tokens.monoMd.copyWith(color: Tokens.ink3)),
              ],
            ),
            const SizedBox(height: 6),
            Text(notApplicableReason!, style: Tokens.uiSm),
          ],
        ),
      );
}

class _Tick extends StatelessWidget {
  const _Tick({required this.filled, required this.colour});

  final bool filled;
  final Color colour;

  @override
  Widget build(BuildContext context) => Container(
        width: 7,
        height: 12,
        decoration: BoxDecoration(
          color: filled ? colour : Colors.transparent,
          border: Border.all(
            color: filled ? colour : Tokens.rule2,
            width: Tokens.hairline,
          ),
          borderRadius: const BorderRadius.all(Radius.circular(1.5)),
        ),
      );
}
