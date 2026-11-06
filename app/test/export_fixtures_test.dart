/// The export artifacts for every real `/analyze` response in
/// `test/fixtures/responses/`, written to disk when asked.
///
/// Set `PHARMAGUARD_EXPORT_DIR` and this writes, per fixture, the printable
/// HTML summary, the PDF summary and the FHIR bundle.
/// `scripts/validate_fhir_exports.py` and the B9 audit read what it writes.
/// Without the variable it still builds every artifact, so a fixture that no
/// longer parses fails here first.
library;

import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:pharmaguard/export/fhir_report.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/print/summary_document.dart';
import 'package:pharmaguard/print/summary_pdf.dart';

import 'support/fixtures.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final String? outDir = Platform.environment['PHARMAGUARD_EXPORT_DIR'];
  late SummaryPdfFonts fonts;

  setUpAll(() async => fonts = await SummaryPdfFonts.load());

  test('there are responses to export', () {
    final bool overridden = Platform.environment.containsKey(
      'PHARMAGUARD_EXPORT_RESPONSES',
    );
    expect(fixtureFiles(), hasLength(greaterThanOrEqualTo(overridden ? 1 : 7)));
  });

  for (final File file in fixtureFiles()) {
    final String name = fixtureName(file);
    test('$name: every export builds', () async {
      final AnalyzeResponse response = loadFixture(file);
      final String html = buildSummaryHtml(
        response,
        printedAt: kFixturePrintedAt,
      );
      final String fhir = encodeFhirReport(
        buildFhirReport(response, exportedAt: kFixturePrintedAt),
      );
      final Uint8List pdf = await buildSummaryPdf(
        response,
        fonts: fonts,
        printedAt: kFixturePrintedAt,
      );
      expect(html, isNotEmpty);
      expect(fhir, isNotEmpty);
      expect(pdf, isNotEmpty);
      if (outDir != null) {
        Directory(outDir).createSync(recursive: true);
        File('$outDir/$name.summary.html').writeAsStringSync(html);
        File('$outDir/$name.fhir.json').writeAsStringSync(fhir);
        File('$outDir/$name.summary.pdf').writeAsBytesSync(pdf);
      }
    });
  }
}
