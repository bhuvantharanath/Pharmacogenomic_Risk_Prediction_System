/// Bundled sample VCFs, with "try it" and "download" for each.
///
/// WHY THIS EXISTS
///
/// The deployed site asked visitors to upload a VCF. Almost nobody reaching it
/// has one, and the only hint pointed at a path inside the source repository —
/// which a browser cannot open. The site was, in practice, unusable to anyone
/// who had not already built the project.
///
/// WHY BOTH ACTIONS
///
/// **Try** runs the sample immediately: the fastest route to seeing a real
/// result, and the one that matters on a phone.
///
/// **Download** hands over the actual file so it can be re-uploaded. Slower,
/// and worth it — a visitor who has held a usable VCF understands what the
/// input requirements mean in a way no prose achieves. It is also the only way
/// to compare their own file against one that works.
///
/// TWO SAMPLES ARE DELIBERATELY ONES THAT FAIL
///
/// Three produce answers; two are gated on every gene. They are offered on
/// equal footing because the coverage gate is the project's central claim, and
/// a demo that only shows successes hides it.
///
/// The pair that matters is the first and the fourth: the same real person,
/// once with every required position reported and once with only the
/// non-reference rows. Same genotype, same pipeline, and the Toxic
/// fluorouracil result vanishes. Nothing about the code differs between those
/// two runs — only the shape of the file.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;

/// One bundled file, and what it demonstrates.
@immutable
class SampleFile {
  const SampleFile({
    required this.asset,
    required this.fileName,
    required this.title,
    required this.outcome,
    required this.detail,
    required this.gated,
  });

  final String asset;
  final String fileName;
  final String title;

  /// What the pipeline returns for it — stated up front, so a gated result
  /// reads as the demonstration it is rather than as a malfunction.
  final String outcome;
  final String detail;

  /// True when every gene is declined. Rendered differently, not hidden.
  final bool gated;

  Future<String> load() => rootBundle.loadString(asset);
}

/// Every bundled sample is a real, named public genome.
///
/// They were transcribed from the Illumina/AWS DRAGEN v4.4.7 reanalysis of the
/// 1000 Genomes Project — one row per required position, reference blocks
/// expanded, genotypes and FILTER carried from the caller, nothing inferred.
/// `scripts/build_showcase_inputs.py` made them and refuses to write a file
/// that does not carry an observed genotype at every position it needs.
///
/// They replaced four hand-built files. Those were honest about their alleles,
/// which came from PharmCAT's own definitions, but the genotypes were chosen
/// to produce a chosen answer, and the card never said so. A demo whose good
/// results are authored is not evidence of anything.
const List<SampleFile> kSampleFiles = <SampleFile>[
  SampleFile(
    asset: 'assets/samples/HG02684.vcf',
    fileName: 'HG02684.vcf',
    title: 'HG02684 — a dangerous result',
    outcome: 'Answers confidently',
    detail:
        'Real genome, Punjabi in Lahore (1000 Genomes). DPYD '
        'c.1905+1G>A on both copies: this person cannot clear fluorouracil, '
        'and the result is Toxic. Two other callers and the family pedigree '
        'agree on that genotype.',
    gated: false,
  ),
  SampleFile(
    asset: 'assets/samples/HG00525.vcf',
    fileName: 'HG00525.vcf',
    title: 'HG00525 — two findings at once',
    outcome: 'Answers confidently',
    detail:
        'Real genome, Southern Han Chinese. CYP2C19 *2/*2 makes '
        'clopidogrel Ineffective, and SLCO1B1 *45/*45 makes simvastatin '
        'Toxic — from one upload, on two unrelated drugs.',
    gated: false,
  ),
  SampleFile(
    asset: 'assets/samples/HG02661.vcf',
    fileName: 'HG02661.vcf',
    title: 'HG02661 — nothing to flag',
    outcome: 'Answers confidently',
    detail:
        'Real genome, Punjabi in Lahore. Normal function across every '
        'gene read. Shows the system is not merely cautious: it will say when '
        'no PGx-guided adjustment was identified.',
    gated: false,
  ),
  SampleFile(
    asset: 'assets/samples/HG02684_variants_only.vcf',
    fileName: 'HG02684_variants_only.vcf',
    title: 'HG02684 again, variants only',
    outcome: 'Declines every gene',
    detail:
        'The SAME person as the first sample, with the '
        'reference-matching rows removed — the ordinary output of most '
        'pipelines. The DPYD variant is still there. What is gone is the '
        'evidence that anything else was measured, so the Toxic result '
        'disappears.',
    gated: true,
  ),
  SampleFile(
    asset: 'assets/samples/pharmaguard_sample_1000genomes.vcf',
    fileName: 'pharmaguard_sample_1000genomes.vcf',
    title: 'A research VCF, as published',
    outcome: 'Declines every gene',
    detail:
        'NA12273 from the 1000 Genomes phased panel. '
        'Polymorphic-filtered, so it is declined — which is what happens to '
        'most research VCFs, and why the file above had to be built from a '
        'different kind of source.',
    gated: true,
  ),
];

class SampleFilesCard extends StatelessWidget {
  const SampleFilesCard({
    super.key,
    required this.onTry,
    required this.onDownload,
    this.busy = false,
  });

  final void Function(SampleFile) onTry;
  final void Function(SampleFile) onDownload;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            'No genome file? Use a sample',
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Every one is a real, named public genome from the 1000 Genomes '
            'Project — none is made up. Run one here, or download it and '
            'upload it yourself. Two are declined on purpose; that is the '
            'behaviour, not a fault.',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 12),
          for (final SampleFile sample in kSampleFiles) ...<Widget>[
            _SampleRow(
              sample: sample,
              busy: busy,
              onTry: () => onTry(sample),
              onDownload: () => onDownload(sample),
            ),
            if (sample != kSampleFiles.last) const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}

class _SampleRow extends StatelessWidget {
  const _SampleRow({
    required this.sample,
    required this.onTry,
    required this.onDownload,
    required this.busy,
  });

  final SampleFile sample;
  final VoidCallback onTry;
  final VoidCallback onDownload;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final Color accent = sample.gated
        ? theme.colorScheme.tertiary
        : theme.colorScheme.primary;

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      // Column rather than Row: at 360px a title, an outcome chip and two
      // buttons on one line either overflow or truncate the outcome, which is
      // the part that stops a declined sample reading as a bug.
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(
                sample.gated
                    ? Icons.block_outlined
                    : Icons.check_circle_outline,
                size: 18,
                color: accent,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  sample.title,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            sample.outcome,
            style: theme.textTheme.labelMedium?.copyWith(
              color: accent,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            sample.detail,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              // The visible labels stay short, because four cards of
              // "Try the reduced-function result" is a wall of words. The
              // accessible names carry the sample, because a screen-reader
              // user hears the buttons as a list, away from the card that
              // would have said which sample this is (Phase 9 B12, A8/F-17).
              FilledButton.tonalIcon(
                onPressed: busy ? null : onTry,
                icon: const Icon(Icons.play_arrow, size: 18),
                label: Text(
                  'Try this',
                  semanticsLabel: 'Try this sample: ${sample.title}',
                ),
              ),
              OutlinedButton.icon(
                onPressed: busy ? null : onDownload,
                icon: const Icon(Icons.download_outlined, size: 18),
                label: Text(
                  'Download',
                  semanticsLabel: 'Download the sample file: ${sample.title}',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
