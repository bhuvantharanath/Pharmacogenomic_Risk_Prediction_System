/// HTTP client for the PharmaGuard backend.
library;

import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../config.dart';
import '../models/analysis.dart';

/// A failure worth showing the user, with a message written for a human rather
/// than for a log file.
class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

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
              // We want to inspect 4xx bodies ourselves rather than have Dio
              // throw before we can read FastAPI's `detail` field.
              validateStatus: (int? code) => code != null && code < 500,
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
      throw ApiException(_describeHttpError(status, res.data), statusCode: status);
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
