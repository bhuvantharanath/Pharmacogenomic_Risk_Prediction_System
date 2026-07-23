/// Native (Android/iOS/desktop) implementation of [exportJson].
///
/// Writes to the system temp directory and reports the path. That is enough to
/// prove the seam and keeps the dependency list minimal.
///
/// TODO(phase2): for a real mobile release, swap this for `share_plus` +
/// `path_provider` so the file lands in Files/Downloads and can be shared to
/// another app, rather than sitting in a temp dir the user cannot browse to.
library;

import 'dart:io';

/// Writes [contents] to a file named [fileName]. Returns a message to show the user.
Future<String> exportJson(String fileName, String contents) async {
  final Directory dir = Directory.systemTemp.createTempSync('pharmaguard_');
  final File file = File('${dir.path}${Platform.pathSeparator}$fileName');
  await file.writeAsString(contents, flush: true);
  return 'Saved to ${file.path}';
}
