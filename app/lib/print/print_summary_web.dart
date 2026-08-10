/// Web: open the summary in a print dialog.
///
/// Rendered into a hidden iframe rather than a popup window — a popup is
/// blocked by default in most browsers, and a blocked print looks to the user
/// exactly like a broken button.
library;

import 'dart:js_interop';

import 'package:web/web.dart' as web;

Future<String> printSummary(String html, String fileName) async {
  final web.HTMLIFrameElement frame =
      web.document.createElement('iframe') as web.HTMLIFrameElement
        ..style.position = 'fixed'
        ..style.right = '0'
        ..style.bottom = '0'
        ..style.width = '0'
        ..style.height = '0'
        ..style.border = '0';
  web.document.body?.append(frame);

  final web.Document? doc = frame.contentDocument;
  if (doc == null) {
    frame.remove();
    return 'Could not open the print view.';
  }
  doc.open();
  doc.write(html.toJS as JSAny);
  doc.close();

  frame.contentWindow?.focus();
  frame.contentWindow?.print();

  // Left in the DOM briefly: removing it synchronously cancels the dialog in
  // Safari, which prints asynchronously from the frame's own document.
  //
  // A closure, not a tear-off: `frame.remove` is an external extension-type
  // interop member, and dart2js rejects tearing one off. Only the web compiler
  // sees this file, so `flutter analyze` and the VM tests both pass without it
  // — `flutter build web` is the check that catches it.
  Future<void>.delayed(const Duration(seconds: 30), () => frame.remove());
  return 'Opened the print view.';
}
