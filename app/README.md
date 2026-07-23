# PharmaGuard — Flutter client

Web + Android/iOS from this one codebase. Material 3, null-safe.

**Phase 1: everything this app displays is a stub** served by the FastAPI
backend. See the [root README](../README.md).

## Run it

The backend must be running first (`cd ../backend && uvicorn app.main:app --reload --port 8000`).

```bash
flutter pub get
flutter run -d chrome     # web
flutter run               # connected Android/iOS device
```

The home screen shows a **Backend connected** indicator — check it first when
something does not work.

## Pointing at a different backend

The default is `http://localhost:8000`, defined as a top-level const in
[lib/config.dart](lib/config.dart). Either edit that line, or override without
touching the source:

```bash
# Android emulator: localhost is the emulator, not your machine
flutter run --dart-define=PHARMAGUARD_API_BASE_URL=http://10.0.2.2:8000

# Deployed backend
flutter build web --release \
  --dart-define=PHARMAGUARD_API_BASE_URL=https://YOURNAME-pharmaguard.hf.space
```

## Layout

```
lib/
├── main.dart                    App + Material 3 theme (light and dark)
├── config.dart                  Base URL, disclaimer text, demo drug list
├── api/pharmaguard_api.dart     Dio client; maps failures to readable messages
├── models/
│   ├── enums.dart               RiskLabel, Severity, Phenotype, CpicEvidenceLevel
│   └── analysis.dart            Contract mirrors with fromJson/toJson
├── screens/
│   ├── home_screen.dart         File picker + drugs field + Analyze
│   └── results_screen.dart      Cards, run summary, Copy/Export JSON
├── theme/risk_style.dart        RiskLabel → colour/icon (light + dark)
├── utils/
│   ├── json_export.dart         Conditional export barrel
│   ├── json_export_web.dart     Browser download via package:web
│   └── json_export_io.dart      Writes to a temp file on native
└── widgets/
    ├── disclaimer_banner.dart   Persistent banner + BannerScaffold
    └── result_card.dart         The colour-coded expandable card
```

`models/` mirrors `backend/app/models.py`. Change one, change the other.

## Tests

```bash
flutter test        # contract round-trip + results-screen widget tests
flutter analyze
```

`test/contract_test.dart` holds a real captured `/analyze` response and asserts
the models parse it, round-trip it byte-for-byte through `toJson()`, and degrade
gracefully on unknown enum values. It is the first thing that should fail if the
backend contract changes.

## Notes

- **File picking uses bytes, not paths**, on every platform — web has no
  filesystem path, and one code path is easier to reason about than two.
- **Export JSON** downloads a real file on web; on native it writes to a temp
  directory and reports the path. See the TODO in `json_export_io.dart` for the
  nicer mobile share story.
- **Colour never carries meaning alone** — every card shows the risk label as
  text and an icon alongside the colour.
