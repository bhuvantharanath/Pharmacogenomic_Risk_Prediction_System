/// Home: pick a VCF, type some drug names, hit Analyze.
library;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../api/backend_status.dart';
import '../api/pharmaguard_api.dart';
import '../config.dart';
import '../glossary/glossary_text.dart';
import '../models/analysis.dart';
import '../theme/tokens.dart';
import '../widgets/backend_status_banner.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/file_readiness.dart';
import 'about_screen.dart';
import 'results_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final PharmaGuardApi _api = PharmaGuardApi();
  final TextEditingController _drugsController = TextEditingController(
    text: 'codeine,warfarin,clopidogrel',
  );

  PlatformFile? _file;
  bool _loading = false;
  String? _error;

  /// A 503 SERVER_BUSY, held separately from `_error`.
  ///
  /// Not an error: the upload is fine and the server is working — someone else
  /// is simply mid-analysis, because this instance runs one at a time (two
  /// concurrent analyses measured 594 MB against a 512 MB limit). Rendering it
  /// in the red error box would tell the user their file was rejected, and the
  /// natural response to that is to go and re-export a VCF that was never wrong.
  String? _busy;

  /// What the chosen file can answer, fetched before the user commits to an
  /// analysis. Null until a file is picked, or when the preview could not be
  /// obtained — which is never fatal, because it is only a preview.
  CoverageResponse? _readiness;
  bool _checkingReadiness = false;

  late final BackendStatusController _backend = BackendStatusController(
    api: _api,
  );

  @override
  void initState() {
    super.initState();
    // Fire the wake-up ping immediately on load. On a free-tier backend that
    // has scaled to zero this starts the cold start now, in parallel with the
    // user picking a file, rather than at Analyze time.
    _backend.addListener(_onBackendChanged);
    _backend.wake();
  }

  void _onBackendChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _backend.removeListener(_onBackendChanged);
    _backend.dispose();
    _drugsController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    try {
      // NB: `pickFiles` is static in file_picker 11+ (it was
      // `FilePicker.platform.pickFiles` in earlier versions).
      final FilePickerResult? picked = await FilePicker.pickFiles(
        // Any file is accepted in Phase 1 — parsing is stubbed, and restricting
        // to .vcf here would make the "any file works" behaviour untestable.
        type: FileType.any,
        // Required on mobile/desktop; web always returns bytes anyway. Using
        // bytes uniformly means one upload path across all platforms.
        withData: true,
      );
      if (picked == null || picked.files.isEmpty) return; // user cancelled
      if (!mounted) return;
      setState(() {
        _file = picked.files.first;
        _error = null;
        _readiness = null;
      });
      await _checkReadiness();
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = 'Could not open the file chooser: $e');
    }
  }

  /// Ask the backend what this file can answer. Cheap — it does not run
  /// PharmCAT — so it costs the user nothing to know in advance.
  ///
  /// Failures are swallowed on purpose. This is advisory: a user whose preview
  /// did not load must still be able to run the analysis, and an error box for
  /// a feature they did not ask for would read as though their file were bad.
  Future<void> _checkReadiness() async {
    final PlatformFile? file = _file;
    if (file?.bytes == null) return;

    setState(() => _checkingReadiness = true);
    try {
      final CoverageResponse? readiness = await _api.coverage(
        fileBytes: file!.bytes!,
        fileName: file.name,
      );
      if (!mounted) return;
      setState(() {
        _readiness = readiness;
        _checkingReadiness = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _checkingReadiness = false;
        // One exception to swallowing: a file the preview rejects is a file
        // /analyze would reject too, so showing it here saves a wasted run.
        if (e.statusCode == 400 || e.statusCode == 413) _error = e.message;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _checkingReadiness = false);
    }
  }

  Future<void> _analyze() async {
    final PlatformFile? file = _file;
    if (file == null) {
      setState(() => _error = 'Choose a VCF file first.');
      return;
    }
    if (file.bytes == null) {
      setState(
        () => _error =
            'Could not read the contents of "${file.name}". Try another file.',
      );
      return;
    }
    if (_drugsController.text.trim().isEmpty) {
      setState(() => _error = 'Enter at least one drug name.');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
      _busy = null;
    });

    try {
      final AnalyzeResponse response = await _api.analyze(
        fileBytes: file.bytes!,
        fileName: file.name,
        drugs: _drugsController.text.trim(),
      );
      if (!mounted) return;
      setState(() => _loading = false);
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ResultsScreen(response: response),
        ),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      final bool serverIsFine = e.isBusy || e.isRateLimited;
      setState(() {
        _loading = false;
        if (e.isBusy) {
          _busy = e.message;
        } else {
          _error = e.message;
        }
      });
      // A failed call is the most likely moment for the backend to have gone
      // away; reflect that in the banner without starting a fresh ping storm.
      //
      // But NOT for busy or rate-limited. Both are answers from a healthy
      // server — a queue and a limit, respectively — and marking it unreachable
      // would flip the status banner to "backend down" at the exact moment the
      // backend is demonstrably up and talking to us. That is the confusion
      // these three states exist to prevent.
      if (!serverIsFine) _backend.markUnreachable(e.message);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'Unexpected error: $e';
      });
    }
  }

  /// Run every drug this build covers, in one action.
  ///
  /// THE DISCOVERY PATH. Naming a drug requires already suspecting it, and the
  /// person best served by this system is precisely the one who does not know
  /// which of their medicines is affected. This asks the question for them.
  Future<void> _checkEverything() async {
    _drugsController.text = kDemoDrugs.join(',');
    await _analyze();
  }

  /// Append a demo drug to the field if it is not already listed.
  void _addDrug(String drug) {
    final List<String> current = _drugsController.text
        .split(',')
        .map((String s) => s.trim())
        .where((String s) => s.isNotEmpty)
        .toList();
    if (current.any((String d) => d.toLowerCase() == drug)) return;
    current.add(drug);
    _drugsController.text = current.join(',');
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    // One scope per screen: first use is per screen, not per app.
    return GlossaryScope(
      child: BannerScaffold(
        appBar: AppBar(
          title: const Text('PharmaGuard'),
          actions: <Widget>[
            IconButton(
              icon: const Icon(Icons.info_outline),
              tooltip: 'About PharmaGuard',
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(builder: (_) => const AboutScreen()),
              ),
            ),
            IconButton(
              tooltip: 'Re-check backend connection',
              onPressed: _backend.wake,
              icon: const Icon(Icons.refresh),
            ),
          ],
        ),
        body: Center(
          child: ConstrainedBox(
            // Keeps the form readable on a wide desktop browser window.
            constraints: const BoxConstraints(maxWidth: 720),
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: <Widget>[
                Text(
                  'Pharmacogenomic risk prediction',
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  // The old copy called the explanations "placeholders". They are
                  // pre-generated, guard-checked and provenance-verified — the line
                  // undersold the work and contradicted the README.
                  'Upload a GRCh38 VCF and list the drugs to check. Genotypes are '
                  'called by PharmCAT, dosing guidance is quoted from CPIC, and the '
                  'explanations are pre-generated and checked against their source.',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 16),
                BackendStatusBanner(
                  status: _backend.status,
                  onRetry: _backend.wake,
                ),
                const SizedBox(height: 20),

                // --- Step 1: file ------------------------------------------
                _StepHeader(number: 1, title: 'Choose a VCF file'),
                const SizedBox(height: 8),
                _FileDropCard(file: _file, onPick: _loading ? null : _pickFile),
                if (_checkingReadiness) ...<Widget>[
                  const SizedBox(height: 10),
                  const _ReadinessPending(),
                ] else if (_readiness != null) ...<Widget>[
                  const SizedBox(height: 12),
                  FileReadinessPanel(
                    readiness: _readiness!,
                    onShowRequirements: () => Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => const AboutScreen(),
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 24),

                // --- Step 2: drugs -----------------------------------------
                _StepHeader(number: 2, title: 'List the drugs'),
                const SizedBox(height: 8),
                TextField(
                  controller: _drugsController,
                  enabled: !_loading,
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _loading ? null : _analyze(),
                  decoration: const InputDecoration(
                    labelText: 'Drugs (comma-separated)',
                    hintText: 'codeine,warfarin,clopidogrel',
                    prefixIcon: Icon(Icons.medication_outlined),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  'Drugs with CPIC guidance in this build — anything else returns '
                  '"Unknown":',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: <Widget>[
                    for (final String drug in kDemoDrugs)
                      ActionChip(
                        visualDensity: VisualDensity.compact,
                        label: Text(drug),
                        onPressed: _loading ? null : () => _addDrug(drug),
                      ),
                  ],
                ),
                const SizedBox(height: 24),

                // --- Step 3: go --------------------------------------------
                FilledButton.icon(
                  onPressed: _loading ? null : _analyze,
                  icon: _loading
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2.4),
                        )
                      : const Icon(Icons.analytics_outlined),
                  label: Text(_loading ? 'Analyzing…' : 'Analyze'),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    textStyle: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),

                const SizedBox(height: 10),
                OutlinedButton.icon(
                  onPressed: _loading ? null : _checkEverything,
                  icon: const Icon(Icons.checklist_outlined, size: 19),
                  label: Text(
                    'Check all ${kDemoDrugs.length} medicines',
                    style: Tokens.uiMd.copyWith(fontWeight: FontWeight.w600),
                  ),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    side: const BorderSide(
                      color: Tokens.rule2,
                      width: Tokens.hairline,
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Results are ordered by consequence, not alphabetically — the '
                  'row that changes something comes first.',
                  style: Tokens.uiSm,
                ),

                if (_busy != null) ...<Widget>[
              const SizedBox(height: 14),
              _BusyBox(message: _busy!, onRetry: _loading ? null : _analyze),
            ],
            if (_error != null) ...<Widget>[
                  const SizedBox(height: 16),
                  _ErrorBox(message: _error!),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// --------------------------------------------------------------------------- //

class _StepHeader extends StatelessWidget {
  const _StepHeader({required this.number, required this.title});

  final int number;
  final String title;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Row(
      children: <Widget>[
        CircleAvatar(
          radius: 11,
          backgroundColor: theme.colorScheme.primary,
          child: Text(
            '$number',
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.onPrimary,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          title,
          style: theme.textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}

/// The gap between choosing a file and knowing what it can answer. Measured at
/// a couple of milliseconds locally, so this is rarely seen — but a silent gap
/// would look like nothing happened.
class _ReadinessPending extends StatelessWidget {
  const _ReadinessPending();

  @override
  Widget build(BuildContext context) => Row(
    children: <Widget>[
      const SizedBox(
        width: 13,
        height: 13,
        child: CircularProgressIndicator(strokeWidth: 2),
      ),
      const SizedBox(width: 9),
      Text(
        'Checking what this file can answer…',
        style: Theme.of(context).textTheme.bodySmall,
      ),
    ],
  );
}

class _FileDropCard extends StatelessWidget {
  const _FileDropCard({required this.file, required this.onPick});

  final PlatformFile? file;
  final VoidCallback? onPick;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final PlatformFile? f = file;

    return InkWell(
      onTap: onPick,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: f == null
                ? theme.colorScheme.outlineVariant
                : theme.colorScheme.primary,
          ),
          color: f == null
              ? null
              : theme.colorScheme.primaryContainer.withValues(alpha: 0.35),
        ),
        child: Row(
          children: <Widget>[
            Icon(
              f == null
                  ? Icons.upload_file_outlined
                  : Icons.description_outlined,
              size: 30,
              color: f == null
                  ? theme.colorScheme.onSurfaceVariant
                  : theme.colorScheme.primary,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    f?.name ?? 'No file selected',
                    style: theme.textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    f == null
                        ? 'Tap to browse — try '
                              'test-data/cyp2c19_poor_metabolizer.vcf'
                        : '${_humanSize(f.size)} · tap to change',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  static String _humanSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}

/// The 503 SERVER_BUSY panel.
///
/// Deliberately NOT the error colour. Three different waits reach this screen
/// and each needs its own reading:
///
///   cold start   the container is booting        — wait, nothing to do
///   429          you asked too many times        — wait, and it is your doing
///   SERVER_BUSY  someone else is analysing now   — wait, and it is nobody's
///
/// Given the same red box, a user cannot tell which they are in, and the
/// reasonable guess after clicking Analyze is always "my file is bad".
class _BusyBox extends StatelessWidget {
  const _BusyBox({required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: theme.colorScheme.secondaryContainer,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: theme.colorScheme.secondary.withValues(alpha: 0.5),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(Icons.hourglass_top,
              color: theme.colorScheme.onSecondaryContainer),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                SelectableText(
                  message,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSecondaryContainer,
                    height: 1.45,
                  ),
                ),
                if (onRetry != null) ...<Widget>[
                  const SizedBox(height: 8),
                  FilledButton.tonalIcon(
                    onPressed: onRetry,
                    icon: const Icon(Icons.refresh, size: 18),
                    label: const Text('Try again'),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorBox extends StatelessWidget {
  const _ErrorBox({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: theme.colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: theme.colorScheme.error.withValues(alpha: 0.5),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(Icons.error_outline, color: theme.colorScheme.onErrorContainer),
          const SizedBox(width: 10),
          Expanded(
            child: SelectableText(
              message,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onErrorContainer,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
