/// HTTP client for the PharmaGuard backend.
library;

import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../config.dart';
import '../models/analysis.dart';

/// A failure worth showing the user, with a message written for a human rather
/// than for a log file.
class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode, this.errorCode});

  final String message;
  final int? statusCode;

  /// The backend's `error_code`, when it sent one.
  ///
  /// Needed because the status code alone is ambiguous: the backend returns 503
  /// both when this deployment's analysis engine is unreachable
  /// (`PHARMCAT_UNAVAILABLE` — broken, nothing the user can do) and when every
  /// analysis slot is busy (`SERVER_BUSY` — fine, try again shortly). Those
  /// deserve opposite messages, and only this field separates them.
  final String? errorCode;

  /// The server is small and someone else is mid-analysis. Not a fault.
  bool get isBusy => errorCode == 'SERVER_BUSY';

  /// This deployment cannot analyse anything at all.
  bool get isBackendUnavailable => errorCode == 'PHARMCAT_UNAVAILABLE';

  /// Too many requests from this client, within the rate-limit window.
  bool get isRateLimited => statusCode == 429;

  @override
  String toString() => message;
}

class PharmaGuardApi {
  // `baseUrl` is nullable rather than defaulting to kApiBaseUrl directly:
  // kApiBaseUrl normalises trailing slashes at runtime, so it is `final`, not
  // `const`, and Dart requires optional defaults to be compile-time constants.
  PharmaGuardApi({Dio? dio, String? baseUrl})
    : _baseUrl = baseUrl ?? kApiBaseUrl,
      _dio =
          dio ??
          Dio(
            BaseOptions(
              baseUrl: baseUrl ?? kApiBaseUrl,
              // Short: this is the cold-start ping's timeout too, and the
              // wake-up loop wants to retry rather than block for a minute.
              connectTimeout: const Duration(seconds: 10),
              // Generous: Phase 2 runs PharmCAT (a JVM process) inside this call.
              receiveTimeout: const Duration(seconds: 60),
              sendTimeout: const Duration(seconds: 60),
              // We want to inspect error bodies ourselves rather than have Dio
              // throw before we can read FastAPI's `detail` field.
              //
              // WAS `< 500`, WHICH SILENTLY SWALLOWED EVERY 503. The backend
              // uses 503 for both of its most user-visible states —
              // PHARMCAT_UNAVAILABLE and SERVER_BUSY — and under the old bound
              // Dio raised a DioException before the body was parsed, so both
              // reached the user as "Network error talking to <url>". The
              // server's actual sentence, which says what happened and whether
              // to retry, was discarded every time. Found while adding
              // SERVER_BUSY; it had been true for PHARMCAT_UNAVAILABLE all
              // along.
              validateStatus: (int? code) => code != null && code < 600,
            ),
          );

  final Dio _dio;
  final String _baseUrl;

  String get baseUrl => _baseUrl;

  /// Liveness check. Returns true only on a 200 with `{"status": "ok"}`.
  Future<bool> health() async {
    try {
      final Response<dynamic> res = await _dio.get<dynamic>('/health');
      final dynamic body = res.data;
      return res.statusCode == 200 &&
          body is Map &&
          body['status'] == 'ok';
    } on DioException {
      return false;
    }
  }

  /// POST /analyze — multipart upload of [fileBytes] plus a comma-separated
  /// [drugs] string.
  ///
  /// [fileBytes] rather than a path because on web there is no filesystem path;
  /// `file_picker` hands back bytes. Using bytes everywhere keeps one code path.
  Future<AnalyzeResponse> analyze({
    required Uint8List fileBytes,
    required String fileName,
    required String drugs,
  }) async {
    final FormData form = FormData.fromMap(<String, dynamic>{
      'file': MultipartFile.fromBytes(fileBytes, filename: fileName),
      'drugs': drugs,
    });

    final Response<dynamic> res;
    try {
      res = await _dio.post<dynamic>('/analyze', data: form);
    } on DioException catch (e) {
      throw ApiException(_describeDioError(e));
    }

    final int status = res.statusCode ?? 0;
    if (status != 200) {
      // 429 is rendered distinctly. It arrives in ~1 ms, so a generic error
      // message makes a working rate limiter look like a crashed backend —
      // which is bad on stage and worse for a real user, who would retry
      // immediately and stay limited.
      if (status == 429) {
        throw ApiException(
          _describeRateLimit(res.data, res.headers.value('retry-after')),
          statusCode: status,
          errorCode: _errorCode(res.data),
        );
      }

      // 503 SERVER_BUSY is a QUEUE, not a failure. The instance runs one
      // analysis at a time because two concurrent ones measured 594 MB against
      // a 512 MB limit, so a second visitor is asked to wait rather than
      // OOM-killing the container for both of them. Rendering that with the
      // generic message ("Request failed (HTTP 503)") would tell a user their
      // file was rejected when it has not even been read yet.
      //
      // Distinct from the other two waits on purpose:
      //   cold start  — the container is starting; wait, no action, ~1 min
      //   429         — YOU have made too many requests; wait, your fault
      //   SERVER_BUSY — SOMEONE ELSE is analysing; wait, nobody's fault
      final String? code = _errorCode(res.data);
      if (status == 503 && code == 'SERVER_BUSY') {
        throw ApiException(
          _describeBusy(res.data, res.headers.value('retry-after')),
          statusCode: status,
          errorCode: code,
        );
      }

      throw ApiException(
        _describeHttpError(status, res.data),
        statusCode: status,
        errorCode: code,
      );
    }

    final dynamic body = res.data;
    if (body is! Map) {
      throw const ApiException('Server returned an unexpected (non-JSON) body.');
    }

    try {
      return AnalyzeResponse.fromJson(body.cast<String, dynamic>());
    } catch (e) {
      throw ApiException('Could not read the server response: $e');
    }
  }

  /// GET /provenance — when the shipped guidance was captured.
  ///
  /// A GET, and separate from an analysis, because the About screen has to be
  /// able to state the version without anyone having uploaded anything. Returns
  /// null on any failure: a missing date stamp is a missing line of context, not
  /// a reason to show an error.
  Future<GuidelineProvenance?> provenance() async {
    try {
      final Response<dynamic> res = await _dio.get<dynamic>('/provenance');
      final dynamic body = res.data;
      if (res.statusCode != 200 || body is! Map) return null;
      return GuidelineProvenance.fromJson(body.cast<String, dynamic>());
    } catch (_) {
      return null;
    }
  }

  /// POST /coverage — what this file can answer, without running PharmCAT.
  ///
  /// Called after the user picks a file and before they commit to an analysis.
  /// It is cheap by construction (measured at ~2 ms against ~1250 ms for
  /// /analyze on the same file), so it costs the user nothing to be told the
  /// shape of their result in advance — and four Unknowns announced up front
  /// read as the system knowing its limits, where the same four arriving
  /// unannounced read as failure.
  ///
  /// Never blocks the analysis: a failure here is reported and stepped over,
  /// which is why this returns null rather than throwing.
  Future<CoverageResponse?> coverage({
    required Uint8List fileBytes,
    required String fileName,
  }) async {
    final FormData form = FormData.fromMap(<String, dynamic>{
      'file': MultipartFile.fromBytes(fileBytes, filename: fileName),
    });

    final Response<dynamic> res;
    try {
      res = await _dio.post<dynamic>('/coverage', data: form);
    } on DioException catch (e) {
      throw ApiException(_describeDioError(e));
    }

    final int status = res.statusCode ?? 0;
    if (status != 200) {
      // A file /coverage rejects is a file /analyze would reject too — both go
      // through the same validation — so surfacing the error here saves the
      // user a round trip through a JVM to learn the same thing.
      throw ApiException(_describeHttpError(status, res.data), statusCode: status);
    }

    final dynamic body = res.data;
    if (body is! Map) return null;
    try {
      return CoverageResponse.fromJson(body.cast<String, dynamic>());
    } catch (_) {
      // A preview that cannot be parsed is not worth failing an upload over.
      return null;
    }
  }

  /// Turns transport-level failures into something a user can act on.
  String _describeDioError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.connectionError:
        // Two genuinely different situations, so two different messages: a
        // local backend that is not running needs a command, while a deployed
        // one is almost always mid-cold-start and needs patience.
        return kIsLocalBackend
            ? 'Could not reach the backend at $_baseUrl.\n'
                  'Is uvicorn running? Start it with:\n'
                  '  cd backend && uvicorn app.main:app --reload --port 8000'
            : 'Could not reach the analysis server at $_baseUrl.\n'
                  'It sleeps when idle and can take up to a minute to wake. '
                  'Wait a moment and try again.';
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.transformTimeout:
        return 'The backend took too long to respond. Try a smaller file.';
      case DioExceptionType.cancel:
        return 'Request cancelled.';
      case DioExceptionType.badCertificate:
        return 'The backend presented an invalid TLS certificate.';
      case DioExceptionType.badResponse:
      case DioExceptionType.unknown:
        return 'Network error talking to $_baseUrl: ${e.message ?? e.type.name}';
    }
  }

  /// FastAPI puts human-readable text in `detail`; surface it verbatim when it
  /// is a plain string, and summarise it when it is a validation-error list.
  /// The 429 message. Says it is a rate limit and when to retry — never a bare
  /// failure, because "try again in 42 seconds" and "the server is broken" call
  /// for completely different responses from the user.
  String _describeRateLimit(dynamic body, String? retryAfter) {
    final int? seconds = int.tryParse(retryAfter ?? '');
    final String when = seconds != null
        ? 'Try again in $seconds second${seconds == 1 ? '' : 's'}.'
        : 'Please wait a short while and try again.';
    if (body is Map && body['detail'] is String) {
      return '${body['detail']}';
    }
    return 'Too many requests — this demo limits how many analyses can run in '
        'a short window. $when';
  }

  /// The backend's machine-readable `error_code`, if it sent one.
  String? _errorCode(dynamic body) {
    if (body is Map && body['error_code'] is String) {
      return body['error_code'] as String;
    }
    return null;
  }

  /// The SERVER_BUSY message. Leads with the fact that the upload is fine,
  /// because the natural reading of any error after clicking Analyze is "my
  /// file was wrong" — and that sends the user off to re-export a VCF that
  /// never had anything wrong with it.
  String _describeBusy(dynamic body, String? retryAfter) {
    final int? seconds = int.tryParse(retryAfter ?? '');
    final String when = seconds != null
        ? 'Try again in $seconds second${seconds == 1 ? '' : 's'}.'
        : 'Please try again in a moment.';
    if (body is Map && body['detail'] is String) {
      return '${body['detail']}';
    }
    return 'The server is busy with another analysis. Nothing is wrong with '
        'your file — this demo runs one analysis at a time. $when';
  }

  String _describeHttpError(int status, dynamic body) {
    if (body is Map && body['detail'] != null) {
      final dynamic detail = body['detail'];
      if (detail is String) return detail;
      if (detail is List && detail.isNotEmpty) {
        final Iterable<String> msgs = detail
            .whereType<Map>()
            .map((Map m) => m['msg']?.toString() ?? '')
            .where((String s) => s.isNotEmpty);
        if (msgs.isNotEmpty) return msgs.join('\n');
      }
    }
    return 'Request failed (HTTP $status).';
  }
}
