// One row per gene for a drug that depends on more than one (Phase 9 B5).
//
// Shown beside the verdict, never instead of it. Warfarin's verdict stays
// Unknown because CPIC's guidance is a dosing algorithm this application does
// not run; these rows are what the file did establish. A gene the backend did
// not assess shows no call at all — only why — because a call made from
// evidence that failed the gate is exactly what the gate keeps off the screen.

import 'package:flutter/material.dart';

import '../models/analysis.dart';
import '../theme/tokens.dart';

class GeneFindingsPanel extends StatelessWidget {
  const GeneFindingsPanel({super.key, required this.findings});

  final List<GeneFinding> findings;

  @override
  Widget build(BuildContext context) {
    if (findings.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          'Genes in this result',
          style: Tokens.uiSm.copyWith(color: Tokens.ink2),
        ),
        const SizedBox(height: 6),
        for (final GeneFinding f in findings) _row(f),
      ],
    );
  }

  Widget _row(GeneFinding f) => Padding(
    padding: const EdgeInsets.only(bottom: 6),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        SizedBox(width: 72, child: Text(f.gene, style: Tokens.monoSm)),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                f.assessed ? f.call : 'not assessed',
                style: Tokens.monoSm.copyWith(
                  color: f.assessed ? Tokens.ink : Tokens.ink2,
                ),
              ),
              if (f.assessed && f.phenotype.isNotEmpty)
                Text(
                  f.phenotype,
                  style: Tokens.uiSm.copyWith(color: Tokens.ink2),
                ),
              if (!f.assessed && f.note.isNotEmpty)
                Text(f.note, style: Tokens.uiSm.copyWith(color: Tokens.ink2)),
              if (f.isReference)
                Text(
                  'shown for reference only; it does not change this result',
                  style: Tokens.uiSm.copyWith(color: Tokens.ink2),
                ),
            ],
          ),
        ),
      ],
    ),
  );
}
