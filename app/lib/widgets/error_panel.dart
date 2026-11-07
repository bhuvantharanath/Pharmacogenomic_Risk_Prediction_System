/// A failed request, headed by whose problem it is (Phase 9 B7).
///
/// One red box used to cover three situations with three different next steps:
/// a file the server read and refused (fix the file), a server that failed
/// (not the file — try later), and a request that never arrived (check the
/// connection). Shown with the same box, the first reads as an outage and the
/// second as the user's fault. The heading says which; the server's own
/// sentence underneath says what exactly.
library;

import 'package:flutter/material.dart';

import '../api/pharmaguard_api.dart';
import 'message_text.dart';

class ErrorPanel extends StatelessWidget {
  const ErrorPanel({super.key, required this.message, this.kind});

  final String message;

  /// Null for messages the screen writes itself ("Choose a VCF file first."),
  /// which need no heading.
  final ApiErrorKind? kind;

  /// The heading for [kind]; null when the message stands alone.
  static String? headingFor(ApiErrorKind? kind) => switch (kind) {
    ApiErrorKind.declined => 'This file was not analysed',
    ApiErrorKind.serverError => 'The analysis server could not finish',
    ApiErrorKind.network => 'Could not reach the analysis server',
    ApiErrorKind.rateLimited => 'Rate limit reached',
    ApiErrorKind.busy => 'The server is busy with another analysis',
    null => null,
  };

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final String? heading = headingFor(kind);
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
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                if (heading != null) ...<Widget>[
                  Text(
                    heading,
                    style: theme.textTheme.titleSmall?.copyWith(
                      color: theme.colorScheme.onErrorContainer,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                ],
                MessageText(
                  message,
                  kind: heading ?? 'Error',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onErrorContainer,
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
