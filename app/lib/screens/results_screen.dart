/// Results: one colour-coded card per analysed drug, plus Copy/Export JSON.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/analysis.dart';
import '../models/enums.dart';
import '../theme/risk_style.dart';
import '../utils/json_export.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/result_card.dart';

class ResultsScreen extends StatelessWidget {
  const ResultsScreen({super.key, required this.response});

  final AnalyzeResponse response;

  /// Pretty-printed round-trip of the response, used by both Copy and Export.
  ///
  /// Round-tripping through `toJson()` (rather than holding the raw HTTP body)
  /// is deliberate: if the Dart models ever drop a field, it shows up here.
  String get _prettyJson =>
      const JsonEncoder.withIndent('  ').convert(response.toJson());

  String get _fileName {
    // Colons are illegal in filenames on Windows, so flatten the timestamp.
    final String stamp = response.timestamp
        .replaceAll(':', '-')
        .replaceAll('.', '-');
    return 'pharmaguard_${response.patientId}_$stamp.json';
  }

  Future<void> _copyJson(BuildContext context) async {
    final ScaffoldMessengerState messenger = ScaffoldMessenger.of(context);
    await Clipboard.setData(ClipboardData(text: _prettyJson));
    messenger.showSnackBar(
      const SnackBar(content: Text('Raw JSON copied to clipboard')),
    );
  }

  Future<void> _exportJson(BuildContext context) async {
    final ScaffoldMessengerState messenger = ScaffoldMessenger.of(context);
    try {
      final String message = await exportJson(_fileName, _prettyJson);
      messenger.showSnackBar(SnackBar(content: Text(message)));
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('Export failed: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return BannerScaffold(
      appBar: AppBar(
        title: const Text('Analysis results'),
        actions: <Widget>[
          IconButton(
            tooltip: 'Copy JSON',
            onPressed: () => _copyJson(context),
            icon: const Icon(Icons.copy_all_outlined),
          ),
          IconButton(
            tooltip: 'Export JSON',
            onPressed: () => _exportJson(context),
            icon: const Icon(Icons.download_outlined),
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 820),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: <Widget>[
              _RunSummary(response: response),
              const SizedBox(height: 16),

              Text(
                'DRUGS ANALYSED (${response.analyses.length})',
                style: theme.textTheme.labelSmall?.copyWith(
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.7,
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 8),

              if (response.analyses.isEmpty)
                const Text('The server returned no analyses.')
              else
                ...response.analyses.map(
                  (PerDrugResult r) => ResultCard(result: r),
                ),

              const SizedBox(height: 8),
              Row(
                children: <Widget>[
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _copyJson(context),
                      icon: const Icon(Icons.copy_all_outlined),
                      label: const Text('Copy JSON'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton.tonalIcon(
                      onPressed: () => _exportJson(context),
                      icon: const Icon(Icons.download_outlined),
                      label: const Text('Export JSON'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Header card: who/when, pipeline telemetry, and the colour legend.
class _RunSummary extends StatelessWidget {
  const _RunSummary({required this.response});

  final AnalyzeResponse response;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final QualityMetrics q = response.qualityMetrics;
    final DateTime? ts = response.timestampUtc;

    return Card(
      elevation: 0,
      color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: theme.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(
                  Icons.badge_outlined,
                  size: 18,
                  color: theme.colorScheme.primary,
                ),
                const SizedBox(width: 8),
                Text(
                  response.patientId,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const Spacer(),
                if (ts != null)
                  Text(
                    '${ts.toIso8601String().split('.').first}Z',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
              ],
            ),
            const Divider(height: 20),

            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <Widget>[
                _Metric(
                  icon: q.vcfParsingSuccess
                      ? Icons.check_circle_outline
                      : Icons.cancel_outlined,
                  label: q.vcfParsingSuccess
                      ? 'VCF accepted'
                      : 'VCF parsing failed',
                ),
                _Metric(
                  icon: Icons.bubble_chart_outlined,
                  label: '${q.variantsDetectedCount} variants',
                ),
                _Metric(
                  icon: Icons.timer_outlined,
                  label: '${q.processingTimeMs} ms',
                ),
              ],
            ),

            if (q.warnings.isNotEmpty) ...<Widget>[
              const SizedBox(height: 12),
              Theme(
                data: theme.copyWith(dividerColor: Colors.transparent),
                child: ExpansionTile(
                  dense: true,
                  tilePadding: EdgeInsets.zero,
                  childrenPadding: const EdgeInsets.only(bottom: 8),
                  expandedCrossAxisAlignment: CrossAxisAlignment.start,
                  leading: Icon(
                    Icons.warning_amber_rounded,
                    size: 18,
                    color: theme.colorScheme.tertiary,
                  ),
                  title: Text(
                    '${q.warnings.length} pipeline '
                    '${q.warnings.length == 1 ? 'warning' : 'warnings'}',
                    style: theme.textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  children: <Widget>[
                    for (final String w in q.warnings)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            const Text('• '),
                            Expanded(
                              child: Text(
                                w,
                                style: theme.textTheme.bodySmall?.copyWith(
                                  height: 1.4,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],

            const Divider(height: 20),
            const _Legend(),
          ],
        ),
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Icon(icon, size: 15, color: theme.colorScheme.onSurfaceVariant),
        const SizedBox(width: 5),
        Text(label, style: theme.textTheme.labelMedium),
        const SizedBox(width: 6),
      ],
    );
  }
}

/// Colour key, so the card colours are self-explanatory.
class _Legend extends StatelessWidget {
  const _Legend();

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 6,
      children: <Widget>[
        for (final RiskLabel label in RiskLabel.values)
          Builder(
            builder: (BuildContext context) {
              final RiskStyle s = RiskStyle.of(context, label);
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Container(
                    width: 10,
                    height: 10,
                    decoration: BoxDecoration(
                      color: s.accent,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                  const SizedBox(width: 5),
                  Text(
                    label.wireValue,
                    style: Theme.of(context).textTheme.labelSmall,
                  ),
                ],
              );
            },
          ),
      ],
    );
  }
}
