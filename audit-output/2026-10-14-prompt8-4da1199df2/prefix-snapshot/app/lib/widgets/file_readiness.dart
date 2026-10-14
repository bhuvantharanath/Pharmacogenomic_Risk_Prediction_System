/// What this file can answer — shown after the file is chosen, before analysis.
///
/// WHY THIS SITS BEFORE THE ANALYSIS RATHER THAN AFTER
///
/// Four Unknowns arriving at the end of a run read as failure: the user waited,
/// and got nothing. The same four announced up front read as the system knowing
/// its own limits — and, crucially, they arrive while the user can still act on
/// them. Someone whose file cannot answer CYP2C19 wants to know that before they
/// type "clopidogrel", not after.
///
/// IT NEVER BLOCKS. Every state here is advisory. The gate that actually refuses
/// to assert a phenotype lives in the backend and runs regardless; this screen
/// only tells the user what that gate is going to conclude. Making it a barrier
/// would be worse than useless — a user with a partial file still gets real
/// answers for the genes that pass, and taking that away to enforce tidiness
/// would trade a real result for a tidy one.
///
/// TWO KINDS OF "NO", KEPT APART
///
///   short on coverage    the file could carry these positions and does not.
///                        Re-calling with all sites emitted fixes it.
///   not readable at all  no VCF can express this gene. CYP2D6 is defined by
///                        copy number. No re-call will ever help.
///
/// Collapsing those into one list would send someone hunting for a better file
/// that cannot exist. Same mistake, different layer, as conflating the four
/// Unknowns on the results screen.
library;

import 'package:flutter/material.dart';

import '../models/analysis.dart';
import '../theme/tokens.dart';
import 'coverage_census.dart';
import 'disclosure_row.dart';

class FileReadinessPanel extends StatelessWidget {
  const FileReadinessPanel({
    super.key,
    required this.readiness,
    this.onShowRequirements,
  });

  final CoverageResponse readiness;

  /// Opens the input-requirements reference. Only offered when there is
  /// something the user could actually do about the result.
  final VoidCallback? onShowRequirements;

  @override
  Widget build(BuildContext context) {
    final List<GeneReadiness> short = readiness.shortOnCoverage;
    final List<GeneReadiness> blocked = readiness.blockedByFormat;
    final bool nothingPasses = readiness.genesPassing == 0;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Tokens.card,
        borderRadius: Tokens.radiusLg,
        border: Border.all(
          color: nothingPasses ? Tokens.accentRule : Tokens.rule,
          width: Tokens.hairline,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          _headline(),
          if (readiness.variantsOnly) ...<Widget>[
            const SizedBox(height: 12),
            const _VariantsOnlyNote(),
          ],
          if (readiness.answerableDrugs.isNotEmpty) ...<Widget>[
            const SizedBox(height: 14),
            _DrugList(
              label: 'CAN BE ANSWERED',
              drugs: readiness.answerableDrugs,
              tone: Tokens.safe,
            ),
          ],
          if (readiness.unanswerableDrugs.isNotEmpty) ...<Widget>[
            const SizedBox(height: 10),
            _DrugList(
              label: 'WILL RETURN UNKNOWN',
              drugs: readiness.unanswerableDrugs,
              tone: Tokens.accent,
            ),
          ],
          if (nothingPasses) ...<Widget>[
            const SizedBox(height: 14),
            _NothingPasses(onShowRequirements: onShowRequirements),
          ],
          const SizedBox(height: 4),
          // The per-gene detail is collapsed by default. The headline is what
          // most users need; the census is for the one who wants to see which
          // positions were counted, and burying it would make the number look
          // like an assertion rather than a count.
          DisclosureRow(
            title: 'Per-gene detail',
            padding: EdgeInsets.zero,
            rule: false,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                for (final GeneReadiness g in readiness.genes) ...<Widget>[
                  CoverageCensus(
                    gene: g.gene,
                    coverage: g.notReadableFromVcf ? null : g.asCoverage,
                    notApplicableReason: g.notReadableFromVcf ? g.reason : null,
                  ),
                  const SizedBox(height: 14),
                ],
              ],
            ),
          ),
          if (short.isNotEmpty || blocked.isNotEmpty)
            _Footnote(short: short, blocked: blocked),
          if (readiness.guidelineProvenance != null) ...<Widget>[
            const SizedBox(height: 10),
            ProvenanceLine(provenance: readiness.guidelineProvenance!),
          ],
        ],
      ),
    );
  }

  Widget _headline() {
    final int pass = readiness.genesPassing;
    final int total = readiness.genesTotal;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text('THIS FILE', style: Tokens.monoLabel),
        const SizedBox(height: 4),
        // Counted, not estimated — so the figures are mono while the sentence
        // around them is not.
        Text.rich(
          TextSpan(
            style: Tokens.uiLg,
            children: <InlineSpan>[
              const TextSpan(text: 'can answer '),
              TextSpan(
                text: '$pass of $total',
                style: Tokens.uiLg.copyWith(
                  fontFamily: Tokens.mono,
                  color: pass == 0 ? Tokens.accent : Tokens.safe,
                ),
              ),
              const TextSpan(text: ' genes'),
            ],
          ),
        ),
      ],
    );
  }
}

/// The one-line provenance stamp. Deliberately quiet: it is context, not a
/// finding, and it must never read as a freshness guarantee.
class ProvenanceLine extends StatelessWidget {
  const ProvenanceLine({super.key, required this.provenance});

  final GuidelineProvenance provenance;

  @override
  Widget build(BuildContext context) {
    final String line = provenance.summaryLine;
    if (line.isEmpty) return const SizedBox.shrink();
    return Tooltip(
      message: provenance.note,
      child: Text(line, style: Tokens.monoSm.copyWith(color: Tokens.ink3)),
    );
  }
}

class _VariantsOnlyNote extends StatelessWidget {
  const _VariantsOnlyNote();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: Tokens.adjustBg,
      borderRadius: Tokens.radius,
      border: Border.all(color: Tokens.adjust, width: Tokens.hairline),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Row(
          children: <Widget>[
            const Icon(Icons.report_problem_outlined,
                size: 17, color: Tokens.adjust),
            const SizedBox(width: 7),
            Flexible(
              child: Text(
                'This file lists variants only',
                style: Tokens.uiMd.copyWith(
                    fontWeight: FontWeight.w600, color: Tokens.adjust),
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          // The sharp end of this project's central finding, said before the
          // analysis rather than after it: a missing position is not a gap in
          // the answer, it is a wrong answer that looks fine.
          'It carries no homozygous-reference calls, so it is indistinguishable '
          'from a file where those positions were never tested. A position that '
          'is absent reads as reference — which means the error runs one way: '
          'reduced function reported as normal.',
          style: Tokens.proseSm,
        ),
      ],
    ),
  );
}

class _DrugList extends StatelessWidget {
  const _DrugList({required this.label, required this.drugs, required this.tone});

  final String label;
  final List<String> drugs;
  final Color tone;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: <Widget>[
      Text(label, style: Tokens.monoLabel.copyWith(color: tone)),
      const SizedBox(height: 5),
      Wrap(
        spacing: 5,
        runSpacing: 5,
        children: <Widget>[
          for (final String drug in drugs)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
              decoration: BoxDecoration(
                borderRadius: Tokens.radius,
                border: Border.all(color: tone, width: Tokens.hairline),
              ),
              child: Text(drug, style: Tokens.monoSm.copyWith(color: tone)),
            ),
        ],
      ),
    ],
  );
}

class _NothingPasses extends StatelessWidget {
  const _NothingPasses({required this.onShowRequirements});

  final VoidCallback? onShowRequirements;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: <Widget>[
      Text(
        // Plainly, and without blaming the user for a file they may not have
        // produced. It also does not stop them: the analysis will run and will
        // report Unknown honestly, which is a legitimate thing to want to see.
        'No gene in this file has enough called positions to support a result. '
        'You can still run the analysis — every drug will come back Unknown, '
        'with the reason.',
        style: Tokens.proseSm.copyWith(color: Tokens.ink),
      ),
      if (onShowRequirements != null) ...<Widget>[
        const SizedBox(height: 8),
        TextButton.icon(
          onPressed: onShowRequirements,
          style: TextButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          icon: const Icon(Icons.description_outlined, size: 16),
          label: Text('What a usable file looks like', style: Tokens.uiSm),
        ),
      ],
    ],
  );
}

class _Footnote extends StatelessWidget {
  const _Footnote({required this.short, required this.blocked});

  final List<GeneReadiness> short;
  final List<GeneReadiness> blocked;

  @override
  Widget build(BuildContext context) {
    final List<String> lines = <String>[
      if (short.isNotEmpty)
        '${short.map((GeneReadiness g) => g.gene).join(', ')}: not enough '
            'called positions in this file. Re-calling with all sites emitted '
            'would fix it.',
      if (blocked.isNotEmpty)
        '${blocked.map((GeneReadiness g) => g.gene).join(', ')}: cannot be '
            'read from any VCF. A different kind of genetic test is needed — a '
            'different file will not help.',
    ];

    return Padding(
      padding: const EdgeInsets.only(top: 2),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          for (final String line in lines) ...<Widget>[
            Text(line, style: Tokens.uiSm),
            const SizedBox(height: 6),
          ],
        ],
      ),
    );
  }
}
