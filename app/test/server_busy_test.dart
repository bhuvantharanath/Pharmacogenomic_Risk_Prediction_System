/// Three different waits must read as three different things.
///
/// The backend answers 503 for two opposite situations:
///
///   PHARMCAT_UNAVAILABLE  this deployment cannot analyse anything. Broken.
///   SERVER_BUSY           every slot is occupied. Working, just not yet.
///
/// and 429 for a third — you personally have asked too often. The status code
/// alone cannot separate the first two, so the client branches on `error_code`.
///
/// SERVER_BUSY exists because the instance runs one PharmCAT at a time: two
/// concurrent analyses measured 594 MB against a 512 MB limit
/// (reports/memory_measurement.md). Queueing the second visitor is the whole
/// point, so telling them their upload failed would be a lie about the one
/// thing they can act on.
library;

import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/api/pharmaguard_api.dart';

/// Serves one canned response to any request.
Dio _dioReturning({
  required int status,
  required Map<String, dynamic> body,
  Map<String, List<String>> headers = const <String, List<String>>{},
}) {
  // Mirrors the production `validateStatus` deliberately. Dio's default throws
  // on anything >= 400, so a test Dio left at the default would never reach the
  // status handling under test and every assertion here would pass or fail for
  // the wrong reason.
  final Dio dio = Dio(BaseOptions(
    baseUrl: 'http://test.invalid',
    validateStatus: (int? code) => code != null && code < 600,
  ));
  dio.httpClientAdapter = _CannedAdapter(
    status: status,
    body: body,
    headers: headers,
  );
  return dio;
}

class _CannedAdapter implements HttpClientAdapter {
  _CannedAdapter({
    required this.status,
    required this.body,
    required this.headers,
  });

  final int status;
  final Map<String, dynamic> body;
  final Map<String, List<String>> headers;

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    return ResponseBody.fromString(
      _encode(body),
      status,
      headers: <String, List<String>>{
        Headers.contentTypeHeader: <String>['application/json'],
        ...headers,
      },
    );
  }

  String _encode(Map<String, dynamic> map) {
    final StringBuffer buffer = StringBuffer('{');
    bool first = true;
    map.forEach((String key, dynamic value) {
      if (!first) buffer.write(',');
      first = false;
      buffer.write('"$key":');
      buffer.write(value is String ? '"$value"' : '$value');
    });
    buffer.write('}');
    return buffer.toString();
  }
}

Future<ApiException> _captureAnalyzeError(Dio dio) async {
  final PharmaGuardApi api = PharmaGuardApi(
    dio: dio,
    baseUrl: 'http://test.invalid',
  );
  try {
    await api.analyze(
      fileBytes: Uint8List.fromList(<int>[1, 2, 3]),
      fileName: 'demo.vcf',
      drugs: 'clopidogrel',
    );
  } on ApiException catch (e) {
    return e;
  }
  fail('analyze() did not throw');
}

void main() {
  group('503 SERVER_BUSY', () {
    test('is flagged as busy, not as a broken backend', () async {
      final ApiException e = await _captureAnalyzeError(
        _dioReturning(
          status: 503,
          body: <String, dynamic>{
            'detail': 'The server is busy with another analysis and could not '
                'start yours within 25 seconds. Nothing is wrong with your '
                'file. Please try again in a moment.',
            'error_code': 'SERVER_BUSY',
          },
          headers: <String, List<String>>{
            'retry-after': <String>['30'],
          },
        ),
      );

      expect(e.isBusy, isTrue);
      expect(e.isBackendUnavailable, isFalse);
      expect(e.isRateLimited, isFalse);
      expect(e.statusCode, 503);
    });

    test('says the upload is fine', () async {
      final ApiException e = await _captureAnalyzeError(
        _dioReturning(
          status: 503,
          body: <String, dynamic>{
            'detail': 'The server is busy with another analysis and could not '
                'start yours within 25 seconds. Nothing is wrong with your '
                'file. Please try again in a moment.',
            'error_code': 'SERVER_BUSY',
          },
        ),
      );

      // The one thing the user would otherwise get wrong.
      expect(e.message.toLowerCase(), contains('nothing is wrong with your'));
      expect(e.message, isNot(contains('HTTP 503')));
    });

    test('falls back to a written message when detail is missing', () async {
      final ApiException e = await _captureAnalyzeError(
        _dioReturning(
          status: 503,
          body: <String, dynamic>{'error_code': 'SERVER_BUSY'},
          headers: <String, List<String>>{
            'retry-after': <String>['30'],
          },
        ),
      );

      expect(e.message, contains('busy'));
      expect(e.message, contains('30 seconds'));
      expect(e.message, isNot(contains('Request failed')));
    });
  });

  group('the three waits stay distinct', () {
    test('PHARMCAT_UNAVAILABLE is not busy', () async {
      final ApiException e = await _captureAnalyzeError(
        _dioReturning(
          status: 503,
          body: <String, dynamic>{
            'detail': 'The analysis service is not available right now.',
            'error_code': 'PHARMCAT_UNAVAILABLE',
          },
        ),
      );

      expect(e.isBackendUnavailable, isTrue);
      expect(e.isBusy, isFalse,
          reason: 'a broken deployment must not be shown as a queue — '
              'retrying does not help');
    });

    test('429 is rate-limited, not busy', () async {
      final ApiException e = await _captureAnalyzeError(
        _dioReturning(
          status: 429,
          body: <String, dynamic>{
            'detail': 'Rate limit reached: 10 analyses per 5 minutes.',
            'error_code': 'RATE_LIMITED',
          },
          headers: <String, List<String>>{
            'retry-after': <String>['42'],
          },
        ),
      );

      expect(e.isRateLimited, isTrue);
      expect(e.isBusy, isFalse);
      expect(e.isBackendUnavailable, isFalse);
    });

    test('no two of the three share a classification', () async {
      final List<ApiException> all = <ApiException>[
        await _captureAnalyzeError(_dioReturning(
          status: 503,
          body: <String, dynamic>{'error_code': 'SERVER_BUSY'},
        )),
        await _captureAnalyzeError(_dioReturning(
          status: 503,
          body: <String, dynamic>{'error_code': 'PHARMCAT_UNAVAILABLE'},
        )),
        await _captureAnalyzeError(_dioReturning(
          status: 429,
          body: <String, dynamic>{'error_code': 'RATE_LIMITED'},
        )),
      ];

      final List<String> signatures = all
          .map((ApiException e) =>
              '${e.isBusy}/${e.isBackendUnavailable}/${e.isRateLimited}')
          .toList();

      expect(signatures.toSet().length, 3,
          reason: 'two of the three states are indistinguishable to the UI: '
              '$signatures');
    });
  });
}
