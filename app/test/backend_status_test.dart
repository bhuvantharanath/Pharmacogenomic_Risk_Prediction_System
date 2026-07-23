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

    test('emits a waking state before it gives up', () async {
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

    test('wake-up budget is generous enough for a cold start', () {
      expect(kWakeupBudget.inSeconds, greaterThanOrEqualTo(60));
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
}
