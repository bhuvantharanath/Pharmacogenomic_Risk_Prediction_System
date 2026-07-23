/// App-wide configuration.
library;

/// Base URL of the PharmaGuard backend.
///
/// **No production URL is hardcoded here.** The default is localhost so a fresh
/// clone works for development; the deployed build supplies the real URL at
/// build time:
///
///   flutter build web --release \
///     --dart-define=API_BASE_URL=https://YOURNAME-pharmaguard.hf.space
///
/// The GitHub Actions web deploy passes it from a repository secret, so the
/// backend URL is configuration rather than source.
///
/// `PHARMAGUARD_API_BASE_URL` is accepted as a legacy alias from Phase 1 so
/// existing local scripts and docs keep working.
///
/// Android emulator note: `localhost` there is the emulator itself, not your
/// machine. Use `--dart-define=API_BASE_URL=http://10.0.2.2:8000`.
const String _apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: String.fromEnvironment(
    'PHARMAGUARD_API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  ),
);

/// Normalised base URL — trailing slashes stripped so `'$base/health'` is safe.
final String kApiBaseUrl = _apiBaseUrl.replaceAll(RegExp(r'/+$'), '');

/// True when the app is pointed at a local development backend.
///
/// Used to soften the cold-start messaging: a localhost backend either responds
/// immediately or is not running, so telling the user to "wait a minute for the
/// server to wake up" would be misleading.
final bool kIsLocalBackend =
    kApiBaseUrl.contains('localhost') ||
    kApiBaseUrl.contains('127.0.0.1') ||
    kApiBaseUrl.contains('10.0.2.2');

/// Shown persistently in the UI. Must stay in sync with `DISCLAIMER` in
/// backend/app/models.py.
const String kDisclaimer =
    'Research/educational decision support only. '
    'Not a medical device. Not for clinical use.';

/// How long to keep trying to wake the backend before calling it unreachable.
///
/// Generous on purpose. A free-tier container that has scaled to zero can take
/// the better part of a minute to serve its first request, and reporting a hard
/// error at 10 seconds would make a working deployment look broken.
const Duration kWakeupBudget = Duration(seconds: 90);

/// Backoff schedule for the wake-up ping.
///
/// Front-loaded: an already-warm backend answers on the first try, so the early
/// retries are cheap and fast. The later gaps widen so a genuinely cold start
/// is not hammered with dozens of requests while it boots.
const List<Duration> kWakeupBackoff = <Duration>[
  Duration(seconds: 1),
  Duration(seconds: 2),
  Duration(seconds: 3),
  Duration(seconds: 5),
  Duration(seconds: 8),
  Duration(seconds: 10),
];

/// Quick-fill chips for the drugs this build demonstrates. UI hint only —
/// anything else is still accepted and comes back as "Unknown".
///
/// Two of these are honest negatives worth showing:
///   codeine  — keyed to CYP2D6, which PharmCAT cannot call from a plain VCF,
///              so it always returns Unknown with an explanatory warning.
///   warfarin — CPIC's guidance is a dosing algorithm rather than per-phenotype
///              text, so PharmCAT returns no usable recommendation.
const List<String> kDemoDrugs = <String>[
  'clopidogrel',
  'fluorouracil',
  'azathioprine',
  'simvastatin',
  'warfarin',
  'codeine',
];
