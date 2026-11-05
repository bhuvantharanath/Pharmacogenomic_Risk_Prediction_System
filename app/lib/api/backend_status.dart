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

  /// The server answered, and does not accept requests from this page's
  /// origin (Phase 9 B7). A setting, not a cold start: said after one ping,
  /// where it used to wait out the whole budget looking like a sleeping server.
  blocked,

  /// The server answered with an error rather than reporting healthy. It is
  /// up, so this is not a cold start either, and the upload is not the cause.
  serverError,

  /// Still nothing after the wake-up budget. Now it is fair to call it broken.
  unreachable,
}

/// This page's origin, for the `blocked` message; empty off the web.
String get _pageOrigin {
  final Uri base = Uri.base;
  return base.scheme == 'http' || base.scheme == 'https' ? base.origin : '';
}

@immutable
class BackendStatus {
  const BackendStatus({
    required this.phase,
    this.elapsed = Duration.zero,
    this.attempts = 0,
    this.message,
    this.budget = kWakeupBudget,
  });

  final BackendPhase phase;

  /// Time spent waiting so far — shown during `waking` so the user can see
  /// progress rather than guessing.
  final Duration elapsed;
  final int attempts;

  /// Detail for the terminal non-ready phases.
  final String? message;

  /// How long the controller waits before giving up. The wake bar and its
  /// countdown are measured against THIS, not a constant of their own: the bar
  /// once divided by 90 s while the client waited 180 s (finding F-11).
  final Duration budget;

  bool get isReady => phase == BackendPhase.ready;
  bool get isBusy =>
      phase == BackendPhase.checking || phase == BackendPhase.waking;

  /// Seconds left before the controller stops waiting, never negative.
  int get secondsLeft {
    final int left = budget.inSeconds - elapsed.inSeconds;
    return left < 0 ? 0 : left;
  }

  /// Fraction of the budget spent, kept short of full so the bar never looks
  /// finished while the wait goes on.
  double get budgetFraction {
    if (budget <= Duration.zero) return 0.95;
    final double fraction = elapsed.inMilliseconds / budget.inMilliseconds;
    return fraction.clamp(0.0, 0.95);
  }

  /// Headline text. Never a bare "Loading…".
  String get title => switch (phase) {
    BackendPhase.checking => 'Checking the analysis server…',
    BackendPhase.waking => 'Waking up the analysis server…',
    BackendPhase.ready => 'Analysis server ready',
    BackendPhase.blocked => 'This page cannot use the analysis server',
    BackendPhase.serverError => 'The analysis server reported an error',
    BackendPhase.unreachable => 'Cannot reach the analysis server',
  };

  /// The explanation. This is the part that stops a cold start reading as a bug.
  String get detail => switch (phase) {
    BackendPhase.checking => 'Contacting $kApiBaseUrl',
    BackendPhase.waking =>
      kIsLocalBackend
          // A local backend does not cold-start; if it is slow, it is not running.
          ? 'Still waiting on $kApiBaseUrl — is uvicorn running?'
          : 'The server sleeps when idle to stay on the free tier, so the '
                'first request has to wake it — $kColdStartExpectation. '
                'Nothing is stuck. (${elapsed.inSeconds}s elapsed)',
    BackendPhase.ready => kApiBaseUrl,
    BackendPhase.blocked =>
      message ??
          'The analysis server at $kApiBaseUrl is up, but it does not accept '
              'requests from this page${_pageOrigin.isEmpty ? '' : ' ($_pageOrigin)'}. '
              'That is a setting on the server, not a cold start, so waiting '
              'will not help: whoever runs this site has to allow this '
              'address on the server.',
    BackendPhase.serverError =>
      message ??
          'The server at $kApiBaseUrl answered with an error instead of '
              'reporting that it is healthy. Nothing about your file caused '
              'this; try again in a few minutes.',
    BackendPhase.unreachable =>
      message ??
          'No response from $kApiBaseUrl after '
              '${budget.inSeconds} seconds and $attempts attempts. '
              'This is no longer a cold start — the server is unreachable, '
              'not waking.',
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
    budget: budget,
  );
}

/// Drives the wake-up ping and publishes [BackendStatus] updates.
class BackendStatusController extends ChangeNotifier {
  BackendStatusController({
    PharmaGuardApi? api,
    Duration? budget,
    List<Duration>? backoff,
  }) : _api = api ?? PharmaGuardApi(),
       _budget = budget ?? kWakeupBudget,
       _backoff = backoff ?? kWakeupBackoff;

  final PharmaGuardApi _api;

  /// Injectable ONLY so the give-up path can be tested.
  ///
  /// The real budget is 180 s, which no test can wait out — and the consequence
  /// of that was a test literally named "emits a waking state before it gives
  /// up" that scripted a backend which *woke*, asserted it reached `ready`,
  /// and never exercised the give-up path at all. The bounded-wait behaviour
  /// was therefore unverified while appearing covered.
  final Duration _budget;
  final List<Duration> _backoff;

  late BackendStatus _status = BackendStatus(
    phase: BackendPhase.checking,
    budget: _budget,
  );
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

    _set(BackendStatus(phase: BackendPhase.checking, budget: _budget));

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
    int? gatewayStatus;

    try {
      while (clock.elapsed < _budget) {
        attempt += 1;
        HealthCheck check;
        try {
          check = await _api.healthCheck();
        } catch (_) {
          check = const HealthCheck(HealthOutcome.noAnswer);
        }
        if (_disposed) return;

        // Every answer but silence ends the wait at once. Only silence (or the
        // host's gateway standing in for a server still starting) is what a
        // cold start looks like, so only silence earns more waiting.
        switch (check.outcome) {
          case HealthOutcome.ready:
            _set(
              BackendStatus(
                phase: BackendPhase.ready,
                elapsed: clock.elapsed,
                attempts: attempt,
                budget: _budget,
              ),
            );
            return;
          case HealthOutcome.blocked:
            _set(
              BackendStatus(
                phase: BackendPhase.blocked,
                elapsed: clock.elapsed,
                attempts: attempt,
                budget: _budget,
              ),
            );
            return;
          case HealthOutcome.serverError:
            _set(
              BackendStatus(
                phase: BackendPhase.serverError,
                elapsed: clock.elapsed,
                attempts: attempt,
                budget: _budget,
                message:
                    'The server at $kApiBaseUrl answered with HTTP '
                    '${check.statusCode ?? 'an unreadable reply'} instead of '
                    'reporting that it is healthy. Nothing about your file '
                    'caused this; try again in a few minutes.',
              ),
            );
            return;
          case HealthOutcome.noAnswer:
            gatewayStatus = check.statusCode ?? gatewayStatus;
        }

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
        final Duration wait =
            _backoff[attempt - 1 < _backoff.length
                ? attempt - 1
                : _backoff.length - 1];
        final Duration remaining = _budget - clock.elapsed;
        if (remaining <= Duration.zero) break;
        await Future<void>.delayed(wait < remaining ? wait : remaining);
      }

      // Only silence reaches this point, so the message says silence. It used
      // to append "The server responded but did not report healthy" — false
      // for a page the server refused, which got no readable answer at all.
      _set(
        BackendStatus(
          phase: BackendPhase.unreachable,
          elapsed: clock.elapsed,
          attempts: attempt,
          budget: _budget,
          message: kIsLocalBackend
              ? 'No response from $kApiBaseUrl.\n'
                    'Start the backend with:\n'
                    '  cd backend && uvicorn app.main:app --reload --port 8000'
              : 'No response from $kApiBaseUrl after '
                    '${clock.elapsed.inSeconds}s and $attempt attempts.'
                    '${gatewayStatus == null ? '' : ' The hosting service '
                              'answered HTTP $gatewayStatus in its place, so the '
                              'server itself never started.'}',
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
        budget: _budget,
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
