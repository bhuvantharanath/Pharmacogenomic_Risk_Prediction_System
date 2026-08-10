/// Home: pick a VCF, type some drug names, hit Analyze.
library;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../api/backend_status.dart';
import '../api/pharmaguard_api.dart';
import '../config.dart';
import '../models/analysis.dart';
import '../widgets/backend_status_banner.dart';
import '../widgets/disclaimer_banner.dart';
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
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = 'Could not open the file picker: $e');
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
      setState(() {
        _loading = false;
        _error = e.message;
      });
      // A failed call is the most likely moment for the backend to have gone
      // away; reflect that in the banner without starting a fresh ping storm.
      _backend.markUnreachable(e.message);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'Unexpected error: $e';
      });
    }
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

    return BannerScaffold(
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

              if (_error != null) ...<Widget>[
                const SizedBox(height: 16),
                _ErrorBox(message: _error!),
              ],
            ],
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
              f == null ? Icons.upload_file_outlined : Icons.description_outlined,
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
        border: Border.all(color: theme.colorScheme.error.withValues(alpha: 0.5)),
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
