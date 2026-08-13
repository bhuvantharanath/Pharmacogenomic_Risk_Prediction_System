/// A non-blocking notice when the two deployed halves disagree.
///
/// WHY THIS EXISTS
///
/// The web client and the backend deploy through different systems — Pages via
/// GitHub Actions, Render via an API call. For one release they drifted, and
/// nothing anywhere said so: Render's `autoDeploy` flag reports enabled while
/// doing nothing, so a push updated the client and left the server on older
/// code. The site looked entirely healthy and simply behaved like an older
/// server, which is the hardest kind of wrong to diagnose from the outside.
///
/// DELIBERATELY NOT A BLOCKER
///
/// A version skew is usually harmless — most commits change neither the wire
/// contract nor the clinical logic. Refusing to run would convert a cosmetic
/// mismatch into an outage, and would hand whoever deployed a broken pairing a
/// site that shows nothing at all. The useful behaviour is: keep working, and
/// say plainly that the halves differ, naming both so the discrepancy can be
/// acted on rather than guessed at.
library;

import 'package:flutter/material.dart';

import '../config.dart';

/// The comparison itself, separated from the widget so it can be tested
/// without a render tree.
class VersionSkew {
  const VersionSkew({required this.expected, required this.actual});

  /// The SHA compiled into this bundle. Empty in local development.
  final String expected;

  /// The SHA the backend reported at `/ready`. Null when unknown.
  final String? actual;

  /// True only when BOTH are known and they differ.
  ///
  /// Unknown is not mismatch. A local build has no expected SHA, and a backend
  /// that does not report one is older than this feature — neither is evidence
  /// of drift, and warning about them would train people to ignore the notice.
  bool get isMismatch {
    final String? seen = actual;
    if (expected.isEmpty) return false;
    if (seen == null || seen.isEmpty) return false;
    return seen != expected;
  }

  String get expectedShort => shortSha(expected);
  String get actualShort => actual == null ? 'unknown' : shortSha(actual!);
}

class VersionNotice extends StatelessWidget {
  const VersionNotice({super.key, required this.skew});

  final VersionSkew skew;

  @override
  Widget build(BuildContext context) {
    if (!skew.isMismatch) return const SizedBox.shrink();

    final ThemeData theme = Theme.of(context);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: theme.colorScheme.tertiaryContainer,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: theme.colorScheme.tertiary.withValues(alpha: 0.45),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(Icons.sync_problem_outlined,
              size: 20, color: theme.colorScheme.onTertiaryContainer),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'This page and the analysis server are different versions',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: theme.colorScheme.onTertiaryContainer,
                  ),
                ),
                const SizedBox(height: 4),
                SelectableText(
                  'This page expects ${skew.expectedShort}; the server is '
                  'running ${skew.actualShort}. Results are still real and '
                  'still come from the server — but if something looks wrong, '
                  'this is the first thing to check.',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onTertiaryContainer,
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
