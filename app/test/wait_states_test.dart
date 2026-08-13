/// Three waits, three messages — and none of them a bare spinner.
///
/// Measured against the deployed backend (reports/deployment_verification.md):
///
///   cold start                12.85 s   the container was asleep
///   analysis running          ~52 s     p50 51.27 s, p95 53.56 s
///   queued behind another     ~109 s    or 503 SERVER_BUSY at the 90 s bound
///
/// One spinner covering all three reads as a hang, and a user who believes it
/// has hung reloads — which on the first two costs them the whole wait again.
/// These tests pin the distinctions, and specifically pin that the ~1 minute
/// cost is STATED rather than hidden behind an indeterminate animation.
library;

import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/api/backend_status.dart';

/// The screen source, read from disk.
///
/// A source-level assertion on purpose: the progress panel only renders with a
/// picked file and a request in flight, which a widget test cannot supply
/// without standing up a backend. The SENTENCE is what is under test, and it
/// must not quietly decay into "Please wait…".
String _homeScreenSource() =>
    File('lib/screens/home_screen.dart').readAsStringSync();

void main() {
  group('cold start', () {
    test('names what is waking, and why, rather than "loading"', () {
      const BackendStatus waking = BackendStatus(
        phase: BackendPhase.waking,
        elapsed: Duration(seconds: 8),
        attempts: 3,
      );

      expect(waking.title.toLowerCase(), contains('waking'));
      expect(waking.title.toLowerCase(), contains('server'));
      // "Loading…" would be true and useless: nothing to reason about, and no
      // reason to keep waiting.
      expect(waking.title.toLowerCase(), isNot('loading…'));

      // Under `flutter test` there is no --dart-define, so kApiBaseUrl is
      // localhost and the LOCAL branch is taken. That branch is right to say
      // "is uvicorn running?" — a local backend does not cold-start, so a slow
      // one is not asleep, it is absent.
      expect(waking.detail, contains('uvicorn'),
          reason: 'the local branch should diagnose a dev machine, not blame '
              'a cold start that cannot happen locally');

      // The DEPLOYED branch cannot be selected here: it needs a compile-time
      // define this test cannot set. Assert it at source level instead, so the
      // explanation and its elapsed counter cannot quietly disappear.
      final String source =
          File('lib/api/backend_status.dart').readAsStringSync();
      expect(source, contains('sleeps when idle'),
          reason: 'the deployed cold-start explanation is what stops a 13 s '
              'wait reading as a broken site');
      expect(source, contains(r'${elapsed.inSeconds}s elapsed'),
          reason: 'the cold-start wait shows no progress without it');
    });
  });

  group('analysis running', () {
    test('the ~1 minute cost is stated, with its reason', () {
      final String source = _homeScreenSource();
      const Map<String, String> required = <String, String>{
        'about a minute': 'the cost, stated up front',
        'Java': 'the reason, not merely the number',
        'free shared': 'whose cost it is — the hosting, not the pipeline',
        'Nothing is stuck': 'what a user staring at a spinner assumes',
        'do not reload': 'the action that makes the wait worse',
      };
      required.forEach((String phrase, String why) {
        expect(source.contains(phrase), isTrue,
            reason: 'the analysis-progress copy no longer says "$phrase" '
                '($why). A ~52 s wait without it reads as a hang.');
      });
    });

    test('elapsed seconds are shown and actually advance', () {
      final String source = _homeScreenSource();
      // A number that visibly moves is the difference between "working" and
      // "broken" when nothing else is on screen.
      expect(source, contains('Timer.periodic'));
      expect(source, contains('_elapsed += 1'));
      expect(source, contains(r"'${elapsed}s'"));
      // And it must not outlive the screen.
      expect(source, contains('_ticker?.cancel()'));
    });

    test('the progress bar never reaches full while still waiting', () {
      // Hitting 100% and then continuing to wait is worse than showing no bar
      // at all — it converts "slow" into "broken".
      expect(_homeScreenSource(), contains('clamp(0.0, 0.95)'));
    });
  });

  group('the three waits are distinguishable', () {
    test('cold start, busy and rate limit share no wording', () {
      const BackendStatus waking = BackendStatus(
        phase: BackendPhase.waking,
        elapsed: Duration(seconds: 5),
        attempts: 2,
      );
      const String busy = 'The server is busy with another analysis';
      const String limited = 'Rate limit reached';

      final Set<String> distinct = <String>{waking.title, busy, limited};
      expect(distinct.length, 3,
          reason: 'two waits share wording, so a user cannot tell which they '
              'are in, nor whether waiting will help');
    });
  });
}
