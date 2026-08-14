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
/// THE FOURTH SAMPLE IS DELIBERATELY ONE THAT FAILS
///
/// Three samples produce answers; `variants_only` is gated on every gene. It is
/// offered on equal footing because the coverage gate is the project's central
/// claim, and a demo that only shows successes hides it.
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

const List<SampleFile> kSampleFiles = <SampleFile>[
  SampleFile(
    asset: 'assets/samples/pharmaguard_sample_reduced_function.vcf',
    fileName: 'pharmaguard_sample_reduced_function.vcf',
    title: 'Reduced-function result',
    outcome: 'Answers confidently',
    detail: 'Complete coverage, CYP2C19 *2/*2. Clopidogrel comes back '
        'Ineffective — the case this system exists to catch.',
    gated: false,
  ),
  SampleFile(
    asset: 'assets/samples/pharmaguard_sample_normal.vcf',
    fileName: 'pharmaguard_sample_normal.vcf',
    title: 'Normal result',
    outcome: 'Answers confidently',
    detail: 'Complete coverage, all genes at reference. Shows the system is '
        'not merely cautious — it will say Safe when the data supports it.',
    gated: false,
  ),
  SampleFile(
    asset: 'assets/samples/pharmaguard_sample_variants_only.vcf',
    fileName: 'pharmaguard_sample_variants_only.vcf',
    title: 'Variants-only file',
    outcome: 'Declines every gene',
    detail: 'The SAME patient as the first sample, with reference rows '
        'removed — the common output of most pipelines. The genotype is '
        'unchanged; what is lost is the evidence that it was measured.',
    gated: true,
  ),
  SampleFile(
    asset: 'assets/samples/pharmaguard_sample_1000genomes.vcf',
    fileName: 'pharmaguard_sample_1000genomes.vcf',
    title: 'Real 1000 Genomes sample',
    outcome: 'Declines every gene',
    detail: 'Genuine public research data (NA12273), not synthetic. '
        'Polymorphic-filtered, so it is declined — which is what happens to '
        'most research VCFs, and why.',
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
          Text('No genome file? Use a sample',
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text(
            'Run one here, or download it and upload it yourself. Two of these '
            'are declined on purpose — that is the behaviour, not a fault.',
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
                sample.gated ? Icons.block_outlined : Icons.check_circle_outline,
                size: 18,
                color: accent,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  sample.title,
                  style: theme.textTheme.bodyMedium
                      ?.copyWith(fontWeight: FontWeight.w600),
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
              FilledButton.tonalIcon(
                onPressed: busy ? null : onTry,
                icon: const Icon(Icons.play_arrow, size: 18),
                label: const Text('Try this'),
              ),
              OutlinedButton.icon(
                onPressed: busy ? null : onDownload,
                icon: const Icon(Icons.download_outlined, size: 18),
                label: const Text('Download'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
