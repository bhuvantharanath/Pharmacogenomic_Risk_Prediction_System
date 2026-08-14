/// Native implementation of [exportText]: writes a file and reports the path.
library;

import 'dart:io';

/// Writes [contents] to [fileName]. Returns a message to show the user.
Future<String> exportText(String fileName, String contents) async {
  final Directory dir = Directory.systemTemp.createTempSync('pharmaguard_');
  final File file = File('${dir.path}${Platform.pathSeparator}$fileName');
  await file.writeAsString(contents, flush: true);
  return 'Saved to ${file.path}';
}
