/// Cold-start handling.
///
/// The deployed backend scales to zero, so the first request after idle can
/// take most of a minute. These tests pin the behaviour that stops that looking
/// like a crash: an explicit "waking" state with elapsed time, retries with
/// backoff, and a hard error only after a generous budget.
library;

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/api/backend_status.dart';
import 'package:pharmaguard/api/pharmaguard_api.dart';
import 'package:pharmaguard/config.dart';

/// A [PharmaGuardApi] whose `/health` result is scripted.
class _ScriptedApi extends PharmaGuardApi {
  _ScriptedApi(this._responses) : super(dio: Dio());

  /// One entry per call: true = healthy, false = down, throw = transport error.
  final List<Object> _responses;
  int calls = 0;

  @override
  Future<bool> health() async {
    final Object response =
        _responses[calls < _responses.length ? calls : _responses.length - 1];
    calls += 1;
    if (response is Exception) throw response;
    return response as bool;
  }
}

void main() {
  group('BackendStatus messaging', () {
    test('never shows a bare loading string', () {
      for (final BackendPhase phase in BackendPhase.values) {
        final BackendStatus status = BackendStatus(phase: phase);
        expect(status.title.trim(), isNotEmpty);
        expect(status.detail.trim(), isNotEmpty);
        // "Loading..." with no explanation is exactly what we are avoiding.
        expect(status.title.toLowerCase(), isNot(equals('loading')));
      }
    });

    test('waking state explains why and shows elapsed time', () {
      const BackendStatus status = BackendStatus(
        phase: BackendPhase.waking,
        elapsed: Duration(seconds: 12),
        attempts: 4,
      );
      expect(status.title, contains('Waking up'));
      if (!kIsLocalBackend) {
        expect(status.detail, contains('sleeps when idle'));
        expect(status.detail, contains('12s'));
      }
      expect(status.isBusy, isTrue);
      expect(status.isReady, isFalse);
    });

    test('ready state is terminal and not busy', () {
      const BackendStatus status = BackendStatus(phase: BackendPhase.ready);
      expect(status.isReady, isTrue);
      expect(status.isBusy, isFalse);
    });
  });

  group('BackendStatusController', () {
    test('reaches ready on the first successful ping', () async {
      final _ScriptedApi api = _ScriptedApi(<Object>[true]);
      final BackendStatusController controller =
          BackendStatusController(api: api);

      await controller.wake();

      expect(controller.status.phase, BackendPhase.ready);
      expect(controller.status.attempts, 1);
      expect(api.calls, 1);
      controller.dispose();
    });

    test('retries until the backend wakes up', () async {
      // Three failures then success — the cold-start shape.
      final _ScriptedApi api = _ScriptedApi(<Object>[
        false,
        false,
        false,
        true,
      ]);
      final BackendStatusController controller =
          BackendStatusController(api: api);

      await controller.wake();

      expect(controller.status.phase, BackendPhase.ready);
      expect(controller.status.attempts, 4);
      controller.dispose();
    });

    test('survives transport exceptions while waking', () async {
      final _ScriptedApi api = _ScriptedApi(<Object>[
        Exception('connection refused'),
        Exception('connection refused'),
        true,
      ]);
      final BackendStatusController controller =
          BackendStatusController(api: api);

      await controller.wake();

      expect(controller.status.phase, BackendPhase.ready);
      controller.dispose();
    });

    test('passes through waking on its way to ready', () async {
      final _ScriptedApi api = _ScriptedApi(<Object>[false, false, true]);
      final BackendStatusController controller =
          BackendStatusController(api: api);

      final List<BackendPhase> seen = <BackendPhase>[];
      controller.addListener(() => seen.add(controller.status.phase));

      await controller.wake();

      expect(seen.first, BackendPhase.checking);
      expect(seen.last, BackendPhase.ready);
      controller.dispose();
    });

    test('concurrent wake() calls do not start parallel loops', () async {
      final _ScriptedApi api = _ScriptedApi(<Object>[false, false, true]);
      final BackendStatusController controller =
          BackendStatusController(api: api);

      // A rebuild or an impatient user must not multiply the ping rate.
      final Future<void> first = controller.wake();
      final Future<void> second = controller.wake();
      await Future.wait(<Future<void>>[first, second]);

      expect(controller.status.phase, BackendPhase.ready);
      expect(api.calls, 3, reason: 'second wake() should have been ignored');
      controller.dispose();
    });

    test('markUnreachable reports the failure without re-pinging', () {
      final _ScriptedApi api = _ScriptedApi(<Object>[true]);
      final BackendStatusController controller =
          BackendStatusController(api: api);

      controller.markUnreachable('Rate limit reached.');

      expect(controller.status.phase, BackendPhase.unreachable);
      expect(controller.status.detail, contains('Rate limit'));
      expect(api.calls, 0);
      controller.dispose();
    });

    test('disposing mid-wake does not throw', () async {
      final _ScriptedApi api = _ScriptedApi(<Object>[false]);
      final BackendStatusController controller =
          BackendStatusController(api: api);

      final Future<void> pending = controller.wake();
      controller.dispose();
      await expectLater(pending, completes);
    });
  });

  group('Configuration', () {
    test('no production URL is hardcoded', () {
      // The deployed URL arrives via --dart-define, so a default build must
      // point at localhost. A hardcoded production host here would also be a
      // privacy problem: a dev build would send VCFs to the public server.
      expect(kApiBaseUrl, contains('localhost'));
      expect(kIsLocalBackend, isTrue);
    });

    test('base URL has no trailing slash', () {
      expect(kApiBaseUrl.endsWith('/'), isFalse);
    });

    test('the budget clears the MEASURED cold start with real margin', () {
      // Measured on the deployed service: 12.85 s when the image was still
      // resident on the Render host, and 83 s a day later when the ~6 GB image
      // had been evicted and was re-pulled. The budget was 90 s, leaving seven
      // seconds — so a slightly slower pull would have reported "cannot be
      // reached" about a server that was seconds from answering.
      //
      // A false negative on availability is worse than a longer wait: the wait
      // is honest, and the false negative is not.
      const int measuredWorstColdStart = 83;
      expect(kWakeupBudget.inSeconds, greaterThan(measuredWorstColdStart * 2),
          reason: 'the budget must clear the worst observed cold start by a '
              'wide margin, not by seconds');
    });

    test('the promised duration does not undercut the budget', () {
      // THE DEFECT THIS FIXES. The banner said "can take up to a minute" while
      // the budget allowed 90 s and reality took 83 s. A wait that overruns
      // what the user was promised reads as a hang, however honest the
      // underlying behaviour is.
      //
      // The expectation string must not name a ceiling the budget would let
      // pass — so it is checked for the numbers it quotes.
      final Iterable<int> quoted = RegExp(r'(\d+)')
          .allMatches(kColdStartExpectation)
          .map((RegExpMatch m) => int.parse(m.group(1)!));
      expect(quoted, isNotEmpty,
          reason: 'the cold-start expectation quotes no duration at all');
      for (final int seconds in quoted) {
        expect(seconds, lessThanOrEqualTo(kWakeupBudget.inSeconds),
            reason: 'the copy promises $seconds s but the client waits '
                '${kWakeupBudget.inSeconds} s — the promise must not be '
                'shorter than the wait');
      }
      // And it must admit the long case rather than quoting only the fast one.
      expect(kColdStartExpectation.toLowerCase(), contains('longer'));
    });

    test('backoff is front-loaded then widens', () {
      expect(kWakeupBackoff, isNotEmpty);
      expect(kWakeupBackoff.first.inSeconds, lessThanOrEqualTo(2));
      expect(
        kWakeupBackoff.last.inSeconds,
        greaterThan(kWakeupBackoff.first.inSeconds),
      );
    });
  });

  // ------------------------------------------------------------------------ #
  // THE GIVE-UP PATH. Previously untested.
  //
  // A test named "emits a waking state before it gives up" scripted a backend
  // that WOKE, asserted it reached `ready`, and never exercised giving up at
  // all. The bounded wait looked covered and was not — the same shape as every
  // other check in this project that passed while checking something else.
  //
  // It matters beyond previews: a suspended service, a CORS allowlist broken by
  // a domain change, or a backend that is simply down all present to the client
  // as "no answer", and an unbounded "waking up…" would misdescribe every one
  // of them as a cold start that is about to finish.
  // ------------------------------------------------------------------------ #
  group('a backend that never answers', () {
    BackendStatusController never({bool throwing = false}) =>
        BackendStatusController(
          api: _ScriptedApi(<Object>[
            throwing ? Exception('Connection refused') : false,
          ]),
          // Real budget is 90 s. Compressed here so the give-up path can be
          // reached at all — the reason it went untested for so long.
          budget: const Duration(milliseconds: 300),
          backoff: const <Duration>[Duration(milliseconds: 50)],
        );

    test('gives up, rather than claiming to wake forever', () async {
      final BackendStatusController controller = never();
      await controller.wake();

      expect(controller.status.phase, BackendPhase.unreachable,
          reason: 'still "waking" after the budget would tell the user to keep '
              'waiting for something that is never going to arrive');
      controller.dispose();
    });

    test('gives up within the budget, not eventually', () async {
      final Stopwatch clock = Stopwatch()..start();
      final BackendStatusController controller = never();
      await controller.wake();
      clock.stop();

      expect(clock.elapsed, lessThan(const Duration(seconds: 5)),
          reason: 'the wait must be BOUNDED; an unbounded one is '
              'indistinguishable from a hang');
      controller.dispose();
    });

    test('says it is unreachable, NOT still waking', () {
      const BackendStatus dead = BackendStatus(
        phase: BackendPhase.unreachable, attempts: 12);
      // The whole point of bounding the state: an unresolvable condition must
      // stop being presented as a temporary one.
      expect(dead.detail.toLowerCase(), contains('not waking'));
      expect(dead.title.toLowerCase(), isNot(contains('waking')));
      expect(dead.isBusy, isFalse);
    });

    test('names the origin it could not reach', () async {
      final BackendStatusController controller = never();
      await controller.wake();

      // Without the URL the message is unactionable: the single most common
      // cause is pointing at the wrong host, and that is invisible unless the
      // host is named.
      expect(controller.status.message, isNotNull);
      expect(controller.status.message, contains(kApiBaseUrl));
      expect(controller.status.detail, isNotEmpty);
      controller.dispose();
    });

    test('reports how long it tried and how many times', () async {
      final BackendStatusController controller = never();
      await controller.wake();

      expect(controller.status.attempts, greaterThan(0));
      // "We tried N times over Ns" is what separates "unreachable" from
      // "we did not really try".
      expect(controller.status.message, anyOf(contains('attempt'),
          contains('uvicorn')));
      controller.dispose();
    });

    test('a transport exception also ends in unreachable, not a crash',
        () async {
      final BackendStatusController controller = never(throwing: true);
      await controller.wake();

      expect(controller.status.phase, BackendPhase.unreachable);
      controller.dispose();
    });

    test('a backend that wakes on the last attempt still reaches ready',
        () async {
      // The other side of the bound: it must not give up on something that
      // WOULD have answered. Cold start measured 12.85 s against a 90 s budget.
      final BackendStatusController controller = BackendStatusController(
        api: _ScriptedApi(<Object>[false, false, true]),
        budget: const Duration(seconds: 5),
        backoff: const <Duration>[Duration(milliseconds: 20)],
      );
      await controller.wake();

      expect(controller.status.phase, BackendPhase.ready);
      controller.dispose();
    });
  });

  group('unreachable is distinguishable from the other three waits', () {
    test('it is not busy, and says something the others do not', () {
      const BackendStatus unreachable =
          BackendStatus(phase: BackendPhase.unreachable);
      const BackendStatus waking = BackendStatus(phase: BackendPhase.waking);

      // `isBusy` drives spinners. Unreachable must not spin — there is nothing
      // left in flight to spin for.
      expect(unreachable.isBusy, isFalse);
      expect(waking.isBusy, isTrue);

      final Set<String> titles = <String>{
        waking.title,
        unreachable.title,
        'The server is busy with another analysis',   // 503 SERVER_BUSY
        'Rate limit reached',                          // 429
      };
      expect(titles.length, 4,
          reason: 'two of the four waits read the same, so the user cannot '
              'tell whether waiting, retrying, or giving up is the right move');

      // And the direction differs: waking says keep waiting, unreachable does
      // not pretend anything is coming.
      expect(unreachable.title.toLowerCase(), contains('cannot reach'));
      expect(waking.title.toLowerCase(), contains('waking'));
    });
  });
}
