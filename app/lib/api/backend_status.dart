/// Tracks whether the backend is awake, and says so honestly while it wakes.
///
/// The deployed backend runs on a free tier that scales to zero. The first
/// request after an idle period pays the whole container cold start, which can
/// be most of a minute. That is the single largest demo risk in this project.
///
/// A bare spinner is the wrong response to that: it looks identical to a hang,
/// so a user waits ten seconds, concludes the app is broken, and leaves. This
/// controller instead reports *which* state it is in — checking, waking (with
/// elapsed time), ready, or unreachable — so the wait is explained rather than
/// merely endured.
library;

import 'dart:async';

import 'package:flutter/foundation.dart';

import '../config.dart';
import 'pharmaguard_api.dart';

enum BackendPhase {
  /// First ping in flight. Usually resolves in well under a second.
  checking,

  /// The first ping did not answer quickly. Almost always a cold start rather
  /// than a fault, and the UI should say so.
  waking,

  /// `/health` answered. Analyses can proceed.
  ready,

  /// Still nothing after the wake-up budget. Now it is fair to call it broken.
  unreachable,
}

@immutable
class BackendStatus {
  const BackendStatus({
    required this.phase,
    this.elapsed = Duration.zero,
    this.attempts = 0,
    this.message,
  });

  final BackendPhase phase;

  /// Time spent waiting so far — shown during `waking` so the user can see
  /// progress rather than guessing.
  final Duration elapsed;
  final int attempts;

  /// Detail for the `unreachable` case only.
  final String? message;

  bool get isReady => phase == BackendPhase.ready;
  bool get isBusy =>
      phase == BackendPhase.checking || phase == BackendPhase.waking;

  /// Headline text. Never a bare "Loading…".
  String get title => switch (phase) {
    BackendPhase.checking => 'Checking the analysis server…',
    BackendPhase.waking => 'Waking up the analysis server…',
    BackendPhase.ready => 'Analysis server ready',
    BackendPhase.unreachable => 'Cannot reach the analysis server',
  };

  /// The explanation. This is the part that stops a cold start reading as a bug.
  String get detail => switch (phase) {
    BackendPhase.checking => 'Contacting $kApiBaseUrl',
    BackendPhase.waking => kIsLocalBackend
        // A local backend does not cold-start; if it is slow, it is not running.
        ? 'Still waiting on $kApiBaseUrl — is uvicorn running?'
        : 'The server sleeps when idle to stay on the free tier. The first '
              'request after a nap can take up to a minute. '
              '(${elapsed.inSeconds}s elapsed)',
    BackendPhase.ready => kApiBaseUrl,
    BackendPhase.unreachable =>
      message ??
          'No response from $kApiBaseUrl after '
              '${kWakeupBudget.inSeconds} seconds.',
  };

  BackendStatus copyWith({
    BackendPhase? phase,
    Duration? elapsed,
    int? attempts,
    String? message,
  }) => BackendStatus(
    phase: phase ?? this.phase,
    elapsed: elapsed ?? this.elapsed,
    attempts: attempts ?? this.attempts,
    message: message ?? this.message,
  );
}

/// Drives the wake-up ping and publishes [BackendStatus] updates.
class BackendStatusController extends ChangeNotifier {
  BackendStatusController({PharmaGuardApi? api})
    : _api = api ?? PharmaGuardApi();

  final PharmaGuardApi _api;

  BackendStatus _status = const BackendStatus(phase: BackendPhase.checking);
  BackendStatus get status => _status;

  Timer? _ticker;
  bool _running = false;
  bool _disposed = false;

  /// After this long without an answer we stop calling it "checking" and start
  /// explaining the cold start. Short enough that a warm backend never shows
  /// the waking state at all.
  static const Duration _wakingThreshold = Duration(seconds: 2);

  /// Ping `/health` until it answers or the budget runs out.
  ///
  /// Safe to call repeatedly — a second call while one is in flight is ignored,
  /// so a rebuild or a user mashing "retry" cannot start parallel loops.
  Future<void> wake() async {
    if (_running) return;
    _running = true;

    _set(const BackendStatus(phase: BackendPhase.checking));

    final Stopwatch clock = Stopwatch()..start();
    // Republish once a second so the elapsed counter in the UI actually moves
    // while we are blocked waiting on a slow request.
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (_status.isBusy) {
        _set(
          _status.copyWith(
            elapsed: clock.elapsed,
            phase: clock.elapsed >= _wakingThreshold
                ? BackendPhase.waking
                : _status.phase,
          ),
        );
      }
    });

    int attempt = 0;
    String? lastError;

    try {
      while (clock.elapsed < kWakeupBudget) {
        attempt += 1;
        try {
          if (await _api.health()) {
            _set(
              BackendStatus(
                phase: BackendPhase.ready,
                elapsed: clock.elapsed,
                attempts: attempt,
              ),
            );
            return;
          }
          lastError = 'The server responded but did not report healthy.';
        } catch (e) {
          lastError = e.toString();
        }

        if (_disposed) return;

        _set(
          _status.copyWith(
            phase: clock.elapsed >= _wakingThreshold
                ? BackendPhase.waking
                : BackendPhase.checking,
            elapsed: clock.elapsed,
            attempts: attempt,
          ),
        );

        // Backoff, clamped so we never sleep past the budget.
        final Duration wait = kWakeupBackoff[
            attempt - 1 < kWakeupBackoff.length
                ? attempt - 1
                : kWakeupBackoff.length - 1];
        final Duration remaining = kWakeupBudget - clock.elapsed;
        if (remaining <= Duration.zero) break;
        await Future<void>.delayed(wait < remaining ? wait : remaining);
      }

      _set(
        BackendStatus(
          phase: BackendPhase.unreachable,
          elapsed: clock.elapsed,
          attempts: attempt,
          message: kIsLocalBackend
              ? 'No response from $kApiBaseUrl.\n'
                    'Start the backend with:\n'
                    '  cd backend && uvicorn app.main:app --reload --port 8000'
              : 'No response from $kApiBaseUrl after '
                    '${clock.elapsed.inSeconds}s and $attempt attempts.\n'
                    '${lastError ?? ''}',
        ),
      );
    } finally {
      _ticker?.cancel();
      _ticker = null;
      _running = false;
    }
  }

  /// Mark the backend as down after a failed analysis, without re-pinging.
  void markUnreachable(String message) {
    _set(
      BackendStatus(
        phase: BackendPhase.unreachable,
        elapsed: _status.elapsed,
        attempts: _status.attempts,
        message: message,
      ),
    );
  }

  void _set(BackendStatus next) {
    if (_disposed) return;
    _status = next;
    notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _ticker?.cancel();
    super.dispose();
  }
}
