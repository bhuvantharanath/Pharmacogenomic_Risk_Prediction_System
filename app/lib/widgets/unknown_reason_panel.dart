/// The Unknown reasons, each looking and reading like itself.
///
/// Conflating "no data" with "data we cannot classify" is an error this project
/// documented in THREE separate backend layers before it was named. Rendering
/// every Unknown identically would reproduce it in the one place a user can
/// actually see, so each reason gets its own copy, its own icon, and its own
/// remedy — or an explicit statement that there is no remedy.
///
/// Only the two file-evidence reasons (missing positions, unusable genotypes)
/// are the user's to fix. Saying so plainly is the whole
/// point: an actionable problem dressed up as a limit wastes their time, and a
/// hard limit dressed up as actionable sends them looking for a better file that
/// does not exist.
library;

import 'package:flutter/material.dart';

import '../glossary/glossary_text.dart';
import '../models/analysis.dart';
import '../models/unknown_reason.dart';
import '../theme/tokens.dart';
import 'coverage_census.dart';

class UnknownReasonPanel extends StatelessWidget {
  const UnknownReasonPanel({
    super.key,
    required this.reason,
    required this.profile,
    this.coverage,
    this.gene,
    this.fallbackReason,
  });

  final UnknownReason reason;
  final PharmacogenomicProfile profile;
  final GeneCoverage? coverage;
  final String? gene;
  final String? fallbackReason;

  /// Heading, body, and what to do — null remedy means nothing can be done.
  (String heading, String body, String? remedy) get _copy => switch (reason) {
    UnknownReason.lowCoverage => (
      'Your file did not report enough positions',
      'Some of the positions needed to identify this gene carry no genotype '
          'in your file. That gap is not neutral. A variant whose defining '
          'position is absent is invisible, so the genotype would read as '
          'reference — and a reduced-function result would be reported as '
          'normal. The system declines rather than risk that.',
      'Upload a VCF that reports every position, including the ones that '
          'match the reference. A clinical pharmacogenomic panel does this, '
          'as does whole-genome or exome data called with all sites emitted. '
          'A variants-only file cannot work here.',
    ),
    UnknownReason.unusableGenotypes => (
      'A required genotype could not be used',
      'Every position this gene needs is in your file, but at least one '
          'carries a genotype that cannot be used — a failed FILTER, or a '
          'partial or missing call. A variant at an unusable position is '
          'invisible, so a reduced-function result would be reported as '
          'normal. The system declines rather than risk that.',
      'Check the genotype and FILTER values your caller wrote at the '
          'affected positions, and re-call them so each carries a complete '
          'genotype that passed its filters.',
    ),
    UnknownReason.notCallable => (
      'This gene is not called from a VCF here',
      'This gene’s result depends on structural and copy-number variation — '
          'whole stretches duplicated, deleted or rearranged. Calling that '
          'needs specialised analysis of the sequencing reads, which this '
          'application does not perform. This is a limit of this application, '
          'not of your sample.',
      'A specialised CYP2D6 test or caller can resolve it. A different VCF '
          'uploaded here will not.',
    ),
    UnknownReason.ambiguous => (
      'The evidence was adequate but not decisive',
      'Your file reported enough positions. More than one genotype is '
          'equally consistent with what it contains, and they do not agree '
          'about how this gene functions. Reporting whichever came first '
          'would present a coin-flip as a finding.',
      null,
    ),
    UnknownReason.noGuidance => (
      'No published guidance for this combination',
      'The genotype was determined successfully. CPIC simply publishes no '
          'dosing recommendation for this particular gene, drug and result. '
          'There is nothing to report here rather than nothing to find.',
      null,
    ),
    UnknownReason.unspecified => (
      'Result withheld',
      fallbackReason?.trim().isNotEmpty == true
          ? fallbackReason!
          : 'The system could not support a confident result here and did not '
                'record a specific reason. It declines rather than assert '
                'something it cannot back.',
      null,
    ),
  };

  IconData get _icon => switch (reason) {
    UnknownReason.lowCoverage => Icons.upload_file_outlined,
    // The existing actionable-file icon, not a new one: the fix is a new file.
    UnknownReason.unusableGenotypes => Icons.upload_file_outlined,
    UnknownReason.notCallable => Icons.biotech_outlined,
    UnknownReason.ambiguous => Icons.alt_route_outlined,
    UnknownReason.noGuidance => Icons.menu_book_outlined,
    UnknownReason.unspecified => Icons.help_outline,
  };

  @override
  Widget build(BuildContext context) {
    final (String heading, String body, String? remedy) = _copy;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Tokens.accentBg,
        borderRadius: Tokens.radiusLg,
        border: Border.all(color: Tokens.accentRule, width: Tokens.hairline),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Icon(_icon, size: 18, color: Tokens.accent),
              const SizedBox(width: 9),
              Expanded(
                child: Text(
                  heading,
                  style: Tokens.uiMd.copyWith(
                    fontWeight: FontWeight.w600,
                    color: Tokens.accent,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 9),
          // Prose, because a person reads it.
          GlossaryText(body, style: Tokens.proseSm),

          // The census carries the argument for the coverage cases, so it is
          // shown here rather than left further down the card.
          if ((reason == UnknownReason.lowCoverage ||
                  reason == UnknownReason.unusableGenotypes) &&
              coverage != null) ...<Widget>[
            const SizedBox(height: 13),
            CoverageCensus(
              gene: gene ?? profile.primaryGene,
              coverage: coverage,
            ),
          ],

          // Candidates, so an ambiguous call is never rendered as an answer.
          if (reason == UnknownReason.ambiguous &&
              profile.candidateDiplotypes.isNotEmpty) ...<Widget>[
            const SizedBox(height: 13),
            Text(
              '${profile.candidateDiplotypes.length} equally consistent genotypes',
              style: Tokens.monoLabel,
            ),
            const SizedBox(height: 5),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: <Widget>[
                for (final String d in profile.candidateDiplotypes)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 7,
                      vertical: 3,
                    ),
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: Tokens.accentRule,
                        width: Tokens.hairline,
                      ),
                      borderRadius: Tokens.radius,
                    ),
                    child: Text(d, style: Tokens.monoSm),
                  ),
              ],
            ),
          ],

          if (remedy != null) ...<Widget>[
            const SizedBox(height: 13),
            Container(
              padding: const EdgeInsets.all(11),
              decoration: BoxDecoration(
                border: Border.all(
                  color: Tokens.accentRule,
                  width: Tokens.hairline,
                ),
                borderRadius: Tokens.radius,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    reason.isActionable ? 'WHAT WOULD WORK' : 'WHAT THIS MEANS',
                    style: Tokens.monoLabel,
                  ),
                  const SizedBox(height: 5),
                  GlossaryText(
                    remedy,
                    style: Tokens.proseSm.copyWith(color: Tokens.ink),
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
