/// Cross-platform "save this text file where the user can get at it".
///
/// Mirrors `json_export.dart` — a browser download and a file on disk are
/// genuinely different operations, so they are split by conditional import
/// rather than papered over with a plugin.
///
/// Exists so a visitor can DOWNLOAD a sample VCF and re-upload it, rather than
/// only being able to run one in place. Downloading is the slower path, and the
/// one that teaches what a usable file looks like.
library;

export 'text_export_io.dart'
    if (dart.library.js_interop) 'text_export_web.dart';
