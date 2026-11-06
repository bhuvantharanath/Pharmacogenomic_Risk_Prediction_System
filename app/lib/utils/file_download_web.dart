/// Web implementation of [downloadFile]: a real browser download, the same
/// way `json_export_web` does it.
library;

import 'dart:js_interop';
import 'dart:typed_data';

import 'package:web/web.dart' as web;

/// Downloads [bytes] as [fileName]. Returns a message to show the user.
Future<String> downloadFile(
  String fileName,
  Uint8List bytes,
  String mediaType,
) async {
  final web.Blob blob = web.Blob(
    <JSUint8Array>[bytes.toJS].toJS,
    web.BlobPropertyBag(type: mediaType),
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

  // Safe straight after click(): the download holds its own reference.
  web.URL.revokeObjectURL(url);

  return 'Downloaded $fileName';
}
