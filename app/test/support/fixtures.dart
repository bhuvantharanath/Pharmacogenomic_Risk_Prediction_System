/// Real `/analyze` responses for the export tests, and the text helpers the
/// parity tests share (audit/phase9/B9_PLAN.md, section 5).
library;

import 'dart:convert';
import 'dart:io';

import 'package:pharmaguard/models/analysis.dart';

/// Fixed, so the same response always prints the same page.
final DateTime kFixturePrintedAt = DateTime.utc(2026, 11, 6);

/// The fixture responses, or the directory in `PHARMAGUARD_EXPORT_RESPONSES`
/// (used by scripts/validate_fhir_exports.py to export a live run's
/// responses).
List<File> fixtureFiles() =>
    Directory(
          Platform.environment['PHARMAGUARD_EXPORT_RESPONSES'] ??
              'test/fixtures/responses',
        )
        .listSync()
        .whereType<File>()
        .where((File f) => f.path.endsWith('.json'))
        .toList()
      ..sort((File a, File b) => a.path.compareTo(b.path));

AnalyzeResponse loadFixture(File file) => AnalyzeResponse.fromJson(
  jsonDecode(file.readAsStringSync()) as Map<String, dynamic>,
);

/// The raw JSON, for asserting against what the server actually sent.
Map<String, dynamic> rawFixture(File file) =>
    jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;

String fixtureName(File file) =>
    file.uri.pathSegments.last.replaceAll('.json', '');

/// Collapse whitespace the way a reader (and HTML) does.
String normalizeText(String s) => s.replaceAll(RegExp(r'\s+'), ' ').trim();

/// The text nodes of an HTML document's body, in document order, unescaped
/// and whitespace-normalised, empties dropped.
List<String> htmlTextNodes(String html) {
  final String body = html.substring(
    html.indexOf('<body>'),
    html.indexOf('</body>'),
  );
  return body
      .split(RegExp(r'<[^>]*>'))
      .map(
        (String s) => s
            .replaceAll('&lt;', '<')
            .replaceAll('&gt;', '>')
            .replaceAll('&quot;', '"')
            .replaceAll('&amp;', '&'),
      )
      .map(normalizeText)
      .where((String s) => s.isNotEmpty)
      .toList();
}
