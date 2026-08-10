/// Hand the printable summary to the platform.
///
/// Split by conditional import, the same way `json_export` is, because these
/// are genuinely different operations rather than one operation with two
/// backends: a browser can open a print dialog, and a phone saves a file its
/// own share sheet then handles.
library;

export 'print_summary_io.dart'
    if (dart.library.js_interop) 'print_summary_web.dart';
