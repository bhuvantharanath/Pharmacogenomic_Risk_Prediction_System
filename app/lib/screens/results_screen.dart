/// Results: one colour-coded card per analysed drug, plus Copy/Export JSON.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../glossary/glossary_text.dart';
import '../models/analysis.dart';
import '../models/enums.dart';
import '../theme/risk_style.dart';
import '../theme/tokens.dart';
import '../print/print_summary.dart';
import '../print/summary_document.dart';
import '../utils/json_export.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/coverage_summary.dart';
import '../widgets/disclosure_row.dart';
import '../widgets/file_readiness.dart';
import '../widgets/summary_grid.dart';
import '../widgets/view_mode.dart';
import '../widgets/view_toggle.dart';
import 'about_screen.dart';

/// The backend's variants-only warning, if it fired. Matched on its opening
/// phrase rather than the whole string so wording can be improved server-side
/// without silently disabling the alert here.
String? _variantsOnlyWarning(QualityMetrics metrics) {
  for (final String w in metrics.warnings) {
    if (w.contains('no homozygous-reference genotypes')) return w;
  }
  return null;
}

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
      const SnackBar(content: Text('Result data copied')),
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

  Future<void> _printSummary(BuildContext context) async {
    final ScaffoldMessengerState messenger = ScaffoldMessenger.of(context);
    try {
      final String message = await printSummary(
        buildSummaryHtml(response),
        _fileName.replaceAll('.json', '.html'),
      );
      messenger.showSnackBar(SnackBar(content: Text(message)));
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text('Could not build the summary: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) => ValueListenableBuilder<ViewMode>(
    valueListenable: viewMode,
    builder: (BuildContext context, ViewMode mode, _) => _build(context, mode),
  );

  Widget _build(BuildContext context, ViewMode mode) {
    final ThemeData theme = Theme.of(context);

    // One scope per screen: first use is per screen, not per app.
    return GlossaryScope(
      child: BannerScaffold(
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

                Wrap(
                  spacing: 12,
                  runSpacing: 8,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: <Widget>[
                    Text(
                      // Names the ordering, because a reader who assumes
                      // alphabetical and finds it is not will distrust the list
                      // rather than read it.
                      'DRUGS CHECKED (${response.analyses.length}) — MOST '
                      'SERIOUS FIRST',
                      style: theme.textTheme.labelSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.7,
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    ViewToggle(
                      mode: mode,
                      onChanged: (ViewMode m) => viewMode.value = m,
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // ABOVE the results, not below them. A variants-only file is the
                // most likely way a real user gets a wrong answer, and burying the
                // warning under the cards would let them read the results first.
                if (_variantsOnlyWarning(response.qualityMetrics) != null)
                  VariantsOnlyAlert(
                    message: _variantsOnlyWarning(response.qualityMetrics)!,
                  ),

                // Shown on every analysis, pass or fail — see CoverageSummary.
                CoverageSummary(
                  coverage: response.qualityMetrics.positionCoverage,
                ),

                if (response.analyses.isEmpty)
                  const Text('The server returned no analyses.')
                else
                  SummaryGrid(
                    analyses: response.analyses,
                    metrics: response.qualityMetrics,
                    mode: mode,
                    // One or two drugs is a reading task, not a scanning one:
                    // collapsing them would add a tap that buys nothing. The grid
                    // still orders them, so a two-drug result still leads with
                    // the one that matters.
                    startExpanded: response.analyses.length <= 2,
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
                const SizedBox(height: 10),
                // The artifact a person actually hands over. Full width and named
                // plainly, because it is the only output of this system that
                // reaches someone who can act on it.
                OutlinedButton.icon(
                  onPressed: () => _printSummary(context),
                  icon: const Icon(Icons.print_outlined),
                  label: const Text('Printable summary'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                ),

                // Unobtrusive by design, and at the foot rather than the head: the
                // versions behind a result are context a reader wants when they go
                // looking, not a finding competing with the verdict. Tapping opens
                // About, where the same stamp is explained rather than merely
                // stated.
                if (response.qualityMetrics.guidelineProvenance !=
                    null) ...<Widget>[
                  const SizedBox(height: 18),
                  Center(
                    child: InkWell(
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => AboutScreen(
                            provenance:
                                response.qualityMetrics.guidelineProvenance,
                          ),
                        ),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 6,
                        ),
                        child: ProvenanceLine(
                          provenance:
                              response.qualityMetrics.guidelineProvenance!,
                        ),
                      ),
                    ),
                  ),
                ],
              ],
            ),
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
            // A Wrap, not a Row with a Spacer: at 360px — or at any width once
            // a user has raised their system font size — the sample id and a
            // full ISO timestamp do not fit on one line, and clipping either
            // one loses the two facts that identify this run.
            Wrap(
              spacing: 10,
              runSpacing: 4,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: <Widget>[
                Row(
                  mainAxisSize: MainAxisSize.min,
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
                  ],
                ),
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
              DisclosureRow(
                padding: EdgeInsets.zero,
                rule: false,
                leading: Icon(Icons.warning_amber_rounded,
                    size: 18, color: theme.colorScheme.tertiary),
                title: '${q.warnings.length} pipeline '
                    '${q.warnings.length == 1 ? 'warning' : 'warnings'}',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    for (final String w in q.warnings)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: Text(w, style: Tokens.uiSm),
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
