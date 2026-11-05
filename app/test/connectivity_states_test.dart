/// Telling asleep, blocked, broken and declined apart (Phase 9 B7, F-11).
///
/// Before B7 a page the server refused got no readable answer from `/health`,
/// so it looked exactly like a sleeping server for the full 180 s budget and
/// was then told the server "responded but did not report healthy". And one
/// red box covered a declined file, a failed server and a lost request alike.
/// These tests pin each case to its own state and its own heading.
library;

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/api/backend_status.dart';
import 'package:pharmaguard/api/pharmaguard_api.dart';
import 'package:pharmaguard/widgets/backend_status_banner.dart';
import 'package:pharmaguard/widgets/error_panel.dart';

/// Answers every request with [status] and [body], or throws [error]; keeps the
/// options of the last request so its timeouts can be checked.
class _HealthAdapter implements HttpClientAdapter {
  _HealthAdapter({
    this.status = 200,
    this.body = const <String, dynamic>{},
    this.error,
  });

  final int status;
  final Map<String, dynamic> body;
  final DioException Function(RequestOptions)? error;
  RequestOptions? last;

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    last = options;
    final DioException Function(RequestOptions)? fail = error;
    if (fail != null) throw fail(options);
    return ResponseBody.fromString(
      jsonEncode(body),
      status,
      headers: <String, List<String>>{
        Headers.contentTypeHeader: <String>['application/json'],
      },
    );
  }
}

Future<(HealthCheck, _HealthAdapter)> _ping({
  int status = 200,
  Map<String, dynamic> body = const <String, dynamic>{},
  DioException Function(RequestOptions)? error,
}) async {
  final _HealthAdapter adapter = _HealthAdapter(
    status: status,
    body: body,
    error: error,
  );
  final Dio dio = Dio(
    BaseOptions(
      baseUrl: 'http://test.invalid',
      validateStatus: (int? code) => code != null && code < 600,
    ),
  )..httpClientAdapter = adapter;
  final PharmaGuardApi api = PharmaGuardApi(
    dio: dio,
    baseUrl: 'http://test.invalid',
  );
  return (await api.healthCheck(), adapter);
}

const Map<String, dynamic> _ok = <String, dynamic>{
  'status': 'ok',
  'commit': '1360a7cca4ef98047c32531e632096b7d5a3339a',
  'commit_short': '1360a7c',
  'data': <String, String>{'cpic_guidance_sha256': 'abc'},
};

void main() {
  group('one /health ping, classified', () {
    test('an allowed origin is ready, with the build it reports', () async {
      final (HealthCheck check, _) = await _ping(
        body: <String, dynamic>{..._ok, 'origin_allowed': true},
      );
      expect(check.outcome, HealthOutcome.ready);
      expect(check.report?.commitShort, '1360a7c');
      expect(check.report?.data['cpic_guidance_sha256'], 'abc');
    });

    test('a refused origin is blocked, not asleep', () async {
      final (HealthCheck check, _) = await _ping(
        body: <String, dynamic>{..._ok, 'origin_allowed': false},
      );
      expect(check.outcome, HealthOutcome.blocked);
    });

    test(
      'no origin reported (a native app, an older server) is ready',
      () async {
        final (HealthCheck check, _) = await _ping(body: _ok);
        expect(check.outcome, HealthOutcome.ready);
        expect(check.report?.originAllowed, isNull);
      },
    );

    test('an error status is a server error, carrying the status', () async {
      final (HealthCheck check, _) = await _ping(
        status: 500,
        body: <String, dynamic>{'detail': 'boom'},
      );
      expect(check.outcome, HealthOutcome.serverError);
      expect(check.statusCode, 500);
    });

    test('a 200 that is not ok is a server error too', () async {
      final (HealthCheck check, _) = await _ping(
        body: <String, dynamic>{'status': 'starting'},
      );
      expect(check.outcome, HealthOutcome.serverError);
    });

    for (final int gateway in <int>[502, 503, 504]) {
      test('the host gateway answering $gateway is no answer yet', () async {
        final (HealthCheck check, _) = await _ping(status: gateway);
        expect(check.outcome, HealthOutcome.noAnswer);
        expect(check.statusCode, gateway);
      });
    }

    test('a timeout is no answer yet', () async {
      final (HealthCheck check, _) = await _ping(
        error: (RequestOptions o) => DioException.connectionTimeout(
          timeout: const Duration(seconds: 10),
          requestOptions: o,
        ),
      );
      expect(check.outcome, HealthOutcome.noAnswer);
    });

    test('the ping gives up after 10 s on every platform', () async {
      // On Android connectTimeout covers only the TCP connect, so without its
      // own receive timeout a ping could be held for the 180 s analysis budget.
      final (_, _HealthAdapter adapter) = await _ping(body: _ok);
      expect(adapter.last?.receiveTimeout, const Duration(seconds: 10));
      expect(adapter.last?.path, '/health');
    });
  });

  group('whose problem a failed request is', () {
    test('each status maps to its kind', () {
      expect(
        const ApiException('x', statusCode: 400, errorCode: 'NOT_VCF').kind,
        ApiErrorKind.declined,
      );
      expect(
        const ApiException(
          'x',
          statusCode: 413,
          errorCode: 'FILE_TOO_LARGE',
        ).kind,
        ApiErrorKind.declined,
      );
      expect(
        const ApiException(
          'x',
          statusCode: 400,
          errorCode: 'REFERENCE_ALLELE_MISMATCH',
        ).kind,
        ApiErrorKind.declined,
      );
      expect(
        const ApiException('x', statusCode: 500).kind,
        ApiErrorKind.serverError,
      );
      expect(
        const ApiException(
          'x',
          statusCode: 503,
          errorCode: 'PHARMCAT_UNAVAILABLE',
        ).kind,
        ApiErrorKind.serverError,
      );
      expect(
        const ApiException('x', statusCode: 503, errorCode: 'SERVER_BUSY').kind,
        ApiErrorKind.busy,
      );
      expect(
        const ApiException('x', statusCode: 429).kind,
        ApiErrorKind.rateLimited,
      );
      expect(const ApiException('x').kind, ApiErrorKind.network);
    });

    test(
      'declined, server error and network have three different headings',
      () {
        final Set<String?> headings = <String?>{
          ErrorPanel.headingFor(ApiErrorKind.declined),
          ErrorPanel.headingFor(ApiErrorKind.serverError),
          ErrorPanel.headingFor(ApiErrorKind.network),
        };
        expect(headings.length, 3);
        expect(headings, isNot(contains(null)));
        expect(ErrorPanel.headingFor(null), isNull);
      },
    );

    for (final (ApiErrorKind kind, String heading) in <(ApiErrorKind, String)>[
      (ApiErrorKind.declined, 'This file was not analysed'),
      (ApiErrorKind.serverError, 'The analysis server could not finish'),
      (ApiErrorKind.network, 'Could not reach the analysis server'),
    ]) {
      testWidgets('the panel heads a ${kind.name} with "$heading"', (
        WidgetTester tester,
      ) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: ErrorPanel(message: 'the server said why', kind: kind),
            ),
          ),
        );
        expect(find.text(heading), findsOneWidget);
        expect(find.text('the server said why'), findsOneWidget);
      });
    }

    testWidgets('a message the screen wrote itself has no heading', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: ErrorPanel(message: 'Choose a VCF file first.')),
        ),
      );
      expect(find.text('Choose a VCF file first.'), findsOneWidget);
      expect(find.text('This file was not analysed'), findsNothing);
    });

    test('the home screen passes each server error its kind', () {
      // Source-level: the panel only renders with a request in flight, which a
      // widget test cannot stage without a backend.
      final String source = File(
        'lib/screens/home_screen.dart',
      ).readAsStringSync();
      expect(
        source,
        contains('ErrorPanel(message: _error!, kind: _errorKind)'),
      );
      expect(
        '_errorKind = e.kind'.allMatches(source).length,
        2,
        reason:
            'both the preview and the analysis must record whose error it is',
      );
    });
  });

  group('the analysis wait names the queue', () {
    test('a queued request is told it waits for the running one', () {
      final String source = File(
        'lib/screens/home_screen.dart',
      ).readAsStringSync();
      expect(source, contains('yours waits for it to finish first'));
      expect(
        source,
        isNot(contains('50–60 seconds')),
        reason: 'measured since B4: 58–68 s live, so the old range undercut it',
      );
    });
  });

  group('the wake banner counts down the real budget', () {
    testWidgets('90 s in, it shows 90 s left of 180 s and a half-full bar', (
      WidgetTester tester,
    ) async {
      const BackendStatus waking = BackendStatus(
        phase: BackendPhase.waking,
        elapsed: Duration(seconds: 90),
        attempts: 7,
      );
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BackendStatusBanner(status: waking, onRetry: () {}),
          ),
        ),
      );
      expect(find.textContaining('90s left of the 180s'), findsOneWidget);
      final LinearProgressIndicator bar = tester.widget(
        find.byType(LinearProgressIndicator),
      );
      expect(bar.value, closeTo(0.5, 0.001));
    });

    testWidgets('blocked and server error offer a retry and no spinner', (
      WidgetTester tester,
    ) async {
      for (final BackendPhase phase in <BackendPhase>[
        BackendPhase.blocked,
        BackendPhase.serverError,
      ]) {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: BackendStatusBanner(
                status: BackendStatus(phase: phase),
                onRetry: () {},
              ),
            ),
          ),
        );
        expect(find.text('Retry'), findsOneWidget, reason: phase.name);
        expect(
          find.byType(LinearProgressIndicator),
          findsNothing,
          reason: phase.name,
        );
        expect(find.text(BackendStatus(phase: phase).title), findsOneWidget);
      }
    });
  });
}
