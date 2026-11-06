/// Native implementation of [downloadFile]: writes to the system temp
/// directory and reports the path, as `json_export_io` does.
library;

import 'dart:io';
import 'dart:typed_data';

/// Writes [bytes] to a file named [fileName]. Returns a message to show the
/// user. [mediaType] has no use on disk; it is part of the shared signature.
Future<String> downloadFile(
  String fileName,
  Uint8List bytes,
  String mediaType,
) async {
  final Directory dir = Directory.systemTemp.createTempSync('pharmaguard_');
  final File file = File('${dir.path}${Platform.pathSeparator}$fileName');
  await file.writeAsBytes(bytes, flush: true);
  return 'Saved to ${file.path}';
}
