/// Shows what the backend is doing, in words.
///
/// The design rule here: never render an unexplained spinner. During a cold
/// start the user is told *why* they are waiting, how long it has taken, and
/// roughly how long it should take — because a wait you understand is tolerable
/// and a wait you don't looks like a crash.
library;

import 'package:flutter/material.dart';

import '../api/backend_status.dart';

class BackendStatusBanner extends StatelessWidget {
  const BackendStatusBanner({
    super.key,
    required this.status,
    required this.onRetry,
  });

  final BackendStatus status;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final bool dark = theme.brightness == Brightness.dark;

    final (Color fg, Color bg, IconData icon) = switch (status.phase) {
      BackendPhase.ready => (
        dark ? const Color(0xFF4CC66B) : const Color(0xFF1B7F3B),
        Colors.transparent,
        Icons.cloud_done_outlined,
      ),
      BackendPhase.checking => (
        theme.colorScheme.onSurfaceVariant,
        Colors.transparent,
        Icons.cloud_queue_outlined,
      ),
      BackendPhase.waking => (
        dark ? const Color(0xFFE8B33C) : const Color(0xFF8A5A00),
        dark ? const Color(0xFF3B2F12) : const Color(0xFFFFF6E0),
        Icons.bedtime_outlined,
      ),
      BackendPhase.unreachable => (
        theme.colorScheme.error,
        theme.colorScheme.errorContainer,
        Icons.cloud_off_outlined,
      ),
    };

    // Ready and checking are quiet one-liners — they do not deserve a card.
    if (status.phase == BackendPhase.ready ||
        status.phase == BackendPhase.checking) {
      return Row(
        children: <Widget>[
          if (status.phase == BackendPhase.checking)
            SizedBox(
              width: 13,
              height: 13,
              child: CircularProgressIndicator(strokeWidth: 2, color: fg),
            )
          else
            Icon(icon, size: 16, color: fg),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              '${status.title} · ${status.detail}',
              style: theme.textTheme.labelSmall?.copyWith(color: fg),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      );
    }

    // Waking and unreachable get a real explanation.
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: fg.withValues(alpha: 0.45)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(icon, size: 18, color: fg),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  status.title,
                  style: theme.textTheme.titleSmall?.copyWith(
                    color: fg,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              if (status.phase == BackendPhase.unreachable)
                TextButton.icon(
                  onPressed: onRetry,
                  icon: const Icon(Icons.refresh, size: 16),
                  label: const Text('Retry'),
                  style: TextButton.styleFrom(foregroundColor: fg),
                ),
            ],
          ),
          const SizedBox(height: 6),
          SelectableText(
            status.detail,
            style: theme.textTheme.bodySmall?.copyWith(height: 1.4),
          ),
          if (status.phase == BackendPhase.waking) ...<Widget>[
            const SizedBox(height: 10),
            // Determinate: an indeterminate bar communicates nothing about how
            // much longer this will take, which is the whole question.
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: _progress,
                minHeight: 5,
                backgroundColor: fg.withValues(alpha: 0.18),
                valueColor: AlwaysStoppedAnimation<Color>(fg),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Attempt ${status.attempts} · this is normal for a free-tier '
              'server and only happens after it has been idle.',
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ],
      ),
    );
  }

  /// Fraction of the wake-up budget spent, capped just below 1 so the bar never
  /// looks finished while we are still waiting.
  double get _progress {
    const double cap = 0.95;
    final double fraction =
        status.elapsed.inMilliseconds / _budgetMs;
    return fraction.clamp(0.02, cap);
  }

  static const double _budgetMs = 90 * 1000;
}
