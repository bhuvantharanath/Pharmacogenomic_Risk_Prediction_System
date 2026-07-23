/// Cross-platform "save this JSON somewhere the user can get at it".
///
/// The two implementations are genuinely different operations — a browser
/// download versus a file on disk — so they are split by conditional import
/// rather than papered over with a plugin.
library;

export 'json_export_io.dart'
    if (dart.library.js_interop) 'json_export_web.dart';
