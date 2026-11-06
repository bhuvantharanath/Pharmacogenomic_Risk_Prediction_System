/// Cross-platform "save these bytes as a file the user can get at" — the PDF
/// summary and the FHIR bundle.
///
/// Split by conditional import for the same reason as `json_export`: a browser
/// download and a file on disk are different operations, not one operation
/// with two backends.
library;

import 'dart:typed_data';

export 'file_download_io.dart'
    if (dart.library.js_interop) 'file_download_web.dart';

/// The download seam's shape, so a screen can be handed a fake in tests.
/// Returns a message to show the user.
typedef FileDownloader =
    Future<String> Function(String fileName, Uint8List bytes, String mediaType);
