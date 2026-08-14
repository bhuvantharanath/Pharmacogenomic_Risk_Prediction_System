/// Web implementation of [exportText]: a real browser download.
///
/// `package:web` + `dart:js_interop` rather than the deprecated `dart:html`,
/// so this also compiles under WebAssembly.
library;

import 'dart:convert';
import 'dart:js_interop';

import 'package:web/web.dart' as web;

/// Downloads [contents] as [fileName]. Returns a message to show the user.
Future<String> exportText(String fileName, String contents) async {
  final web.Blob blob = web.Blob(
    <JSUint8Array>[utf8.encode(contents).toJS].toJS,
    // text/plain rather than a VCF-specific type: browsers have no registered
    // handler for VCF, and an unknown type makes some of them offer "open
    // with" instead of saving.
    web.BlobPropertyBag(type: 'text/plain;charset=utf-8'),
  );

  final String url = web.URL.createObjectURL(blob);
  final web.HTMLAnchorElement anchor =
      web.document.createElement('a') as web.HTMLAnchorElement
        ..href = url
        ..download = fileName
        ..style.display = 'none';

  web.document.body?.append(anchor);
  anchor.click();
  anchor.remove();

  web.URL.revokeObjectURL(url);
  return 'Downloaded $fileName';
}
