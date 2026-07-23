/// Web implementation of [exportJson]: triggers a real browser download.
///
/// Uses `package:web` + `dart:js_interop` (the modern replacement for the
/// deprecated `dart:html`), so this also compiles under WebAssembly.
library;

import 'dart:convert';
import 'dart:js_interop';

import 'package:web/web.dart' as web;

/// Downloads [contents] as [fileName]. Returns a message to show the user.
Future<String> exportJson(String fileName, String contents) async {
  final web.Blob blob = web.Blob(
    <JSUint8Array>[utf8.encode(contents).toJS].toJS,
    web.BlobPropertyBag(type: 'application/json;charset=utf-8'),
  );

  final String url = web.URL.createObjectURL(blob);
  final web.HTMLAnchorElement anchor =
      web.document.createElement('a') as web.HTMLAnchorElement
        ..href = url
        ..download = fileName
        // Keep it out of the layout; we only need it to be clickable.
        ..style.display = 'none';

  web.document.body?.append(anchor);
  anchor.click();
  anchor.remove();

  // Release the blob so the browser can reclaim the memory. Safe immediately
  // after click() — the download has already taken its own reference.
  web.URL.revokeObjectURL(url);

  return 'Downloaded $fileName';
}
