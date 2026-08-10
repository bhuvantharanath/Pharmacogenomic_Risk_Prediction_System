/// Mobile and desktop: the platform's own print dialog.
///
/// `Printing.convertHtml` hands the HTML to the OS renderer — WKWebView on
/// iOS, WebView on Android — and `layoutPdf` then opens the system print sheet,
/// from which the user can print, save as PDF, or share. That is the same
/// pipeline the browser uses on web, so both platforms print the same document
/// from the same source rather than from two layouts that could drift.
///
/// Not every platform can render HTML: some Linux and Windows builds report
/// `canConvertHtml: false`. There the file is written instead and the path is
/// returned, because telling a user their document printed when no dialog
/// appeared is worse than telling them where it went.
///
/// ON THE DEPRECATION
///
/// `Printing.convertHtml` is deprecated upstream — the package would rather you
/// compose the document with `pdf` widgets. That is deliberately NOT done here.
/// Doing it would mean a second layout of a safety-critical page, maintained
/// separately from the HTML one and covered by none of its tests, so a
/// disclaimer or an Unknown reason could go missing from the mobile printout
/// while every existing test stayed green. One document with a deprecated
/// converter is a smaller risk than two documents that can disagree.
///
/// If the API is removed in a future major version, the replacement is to
/// render this same HTML through a headless webview and keep one source — not
/// to rewrite the page. Pinned below `6.0.0` in pubspec for that reason.
library;

import 'dart:io';

import 'package:pdf/pdf.dart';
import 'package:printing/printing.dart';

Future<String> printSummary(String html, String fileName) async {
  try {
    final PrintingInfo info = await Printing.info();
    if (info.canConvertHtml && info.canPrint) {
      final bool printed = await Printing.layoutPdf(
        name: fileName,
        // See ON THE DEPRECATION in the library doc: one document with a
        // deprecated converter beats two documents that can disagree.
        onLayout: (PdfPageFormat format) =>
            // ignore: deprecated_member_use
            Printing.convertHtml(html: html, format: format),
      );
      // `layoutPdf` returns false when the user backs out of the sheet.
      // Reporting that honestly matters: a silent "done" after a cancelled
      // print leaves someone believing they have a page they do not have.
      return printed ? 'Sent to the print dialog.' : 'Printing cancelled.';
    }
  } catch (_) {
    // The plugin is missing or the channel is unavailable — a headless test
    // host, or a platform the plugin does not implement. The document is
    // already built and correct, so fall through to writing it rather than
    // losing it to an error dialog.
  }

  return _writeFile(html, fileName);
}

Future<String> _writeFile(String html, String fileName) async {
  final Directory dir = Directory.systemTemp.createTempSync('pharmaguard');
  final File out = File('${dir.path}/$fileName');
  await out.writeAsString(html, flush: true);
  return 'This platform cannot print directly. Saved to ${out.path}.';
}
