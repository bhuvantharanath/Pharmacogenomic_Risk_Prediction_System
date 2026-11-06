/// The PDF summary says exactly what the printable HTML summary says
/// (audit/phase9/B9_PLAN.md, AC5).
///
/// The PDF is a second layout of a safety-critical page. These tests are what
/// keep it from becoming a second page: for every real response, the strings
/// it places must be the HTML's text nodes, in order; the disclaimer header
/// must be on every page; and every character must be in the font that draws
/// it, so nothing is silently dropped as a missing glyph.
library;

import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pdf/pdf.dart';
import 'package:pharmaguard/models/analysis.dart';
import 'package:pharmaguard/print/summary_document.dart';
import 'package:pharmaguard/print/summary_pdf.dart';

import 'support/fixtures.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late SummaryPdfFonts fonts;
  final Map<PdfFontRole, Set<int>> glyphs = <PdfFontRole, Set<int>>{};

  setUpAll(() async {
    fonts = await SummaryPdfFonts.load();
    for (final MapEntry<PdfFontRole, String> e
        in SummaryPdfFonts.assets.entries) {
      glyphs[e.key] = TtfParser(
        await rootBundle.load(e.value),
      ).charToGlyphIndexMap.keys.toSet();
    }
  });

  test('draws only static fonts, so the text layer keeps its spaces', () async {
    // A variable font has an `fvar` table. With one, pypdf read the PDF's
    // prose back with no spaces between words (audit/phase9/B9.log).
    for (final String asset in SummaryPdfFonts.assets.values.toSet()) {
      final ByteData font = await rootBundle.load(asset);
      final List<String> tables = <String>[
        for (int i = 0; i < font.getUint16(4); i++)
          String.fromCharCodes(
            font.buffer.asUint8List(font.offsetInBytes + 12 + 16 * i, 4),
          ),
      ];
      expect(tables, contains('glyf'), reason: asset);
      expect(tables, isNot(contains('fvar')), reason: asset);
    }
  });

  for (final File file in fixtureFiles()) {
    final String name = fixtureName(file);

    group(name, () {
      late AnalyzeResponse response;
      late Uint8List bytes;
      final List<(String, PdfFontRole)> placed = <(String, PdfFontRole)>[];
      final Set<int> headerPages = <int>{};
      int pageCount = 0;

      setUpAll(() async {
        response = loadFixture(file);
        bytes = await buildSummaryPdf(
          response,
          fonts: fonts,
          printedAt: kFixturePrintedAt,
          sink: (String text, PdfFontRole role) => placed.add((text, role)),
          onHeader: headerPages.add,
          onPageCount: (int count) => pageCount = count,
        );
      });

      test('is a PDF', () {
        expect(String.fromCharCodes(bytes.take(5)), '%PDF-');
        expect(pageCount, greaterThanOrEqualTo(1));
      });

      test('places exactly the HTML summary\'s text, in order', () {
        final List<String> html = htmlTextNodes(
          buildSummaryHtml(response, printedAt: kFixturePrintedAt),
        );
        // The HTML's first node is its running header, which the PDF draws
        // per page instead; that is checked below.
        expect(html.first, kPrintHeaderLine);
        final List<String> pdf = <String>[
          for (final (String text, PdfFontRole _) in placed)
            if (normalizeText(text).isNotEmpty) normalizeText(text),
        ];
        expect(pdf, html.sublist(1));
      });

      test('carries the disclaimer header on every page', () {
        expect(headerPages, <int>{for (int p = 1; p <= pageCount; p++) p});
      });

      test('has every character it places in the font that draws it', () {
        for (final (String text, PdfFontRole role) in placed) {
          for (final int rune in text.runes) {
            expect(
              glyphs[role],
              contains(rune),
              reason:
                  'U+${rune.toRadixString(16).toUpperCase().padLeft(4, '0')} '
                  '(${String.fromCharCode(rune)}) in "$text" is not in '
                  '${SummaryPdfFonts.assets[role]}',
            );
          }
        }
        // The running header bypasses the sink; check its glyphs directly.
        expect(
          glyphs[PdfFontRole.mono],
          containsAll(kPrintHeaderLine.runes.toSet()),
        );
      });
    });
  }
}
