"""
Android identity consistency — regression guard for the P0 launch crash.

WHAT WENT WRONG
    `build.gradle.kts` set `namespace = "com.pharmaguard.app"` while
    `MainActivity.kt` declared `package com.pharmaguard.pharmaguard`.
    `AndroidManifest.xml` declares the launcher activity relatively, as
    `android:name=".MainActivity"`, and Android resolves a leading-dot name
    against the **namespace**. So the built APK asked the system to launch
    `com.pharmaguard.app.MainActivity`, a class that existed nowhere in its own
    dex. The APK installed cleanly and then died with ClassNotFoundException the
    instant it was opened.

WHY NO TEST CAUGHT IT
    Nothing verified the manifest against the source tree. The Phase 4 checks
    confirmed the APK's *metadata* — package name, permissions, the baked-in
    API URL — all of which were individually correct. The defect lived in the
    relationship between two files, which is exactly what nobody was asserting.

WHY THIS LIVES IN THE PYTHON SUITE
    It is a static consistency check over text files, so it needs no Gradle, no
    Android SDK, no emulator and no built artifact. Putting it in `pytest` means
    it runs on every backend test invocation and in CI, in under a millisecond.
    A test that only runs when someone remembers to build an APK is a test that
    would not have caught this.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

APP_ROOT = Path(__file__).resolve().parents[2] / "app"
ANDROID_APP = APP_ROOT / "android" / "app"
MANIFEST = ANDROID_APP / "src" / "main" / "AndroidManifest.xml"
BUILD_GRADLE = ANDROID_APP / "build.gradle.kts"
IOS_PBXPROJ = APP_ROOT / "ios" / "Runner.xcodeproj" / "project.pbxproj"


def _gradle_value(key: str) -> str:
    """Read `key = "value"` out of build.gradle.kts, ignoring commented lines."""
    text = BUILD_GRADLE.read_text()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        match = re.match(rf'{key}\s*=\s*"([^"]+)"', stripped)
        if match:
            return match.group(1)
    raise AssertionError(f"{key} not found in {BUILD_GRADLE}")


def _manifest_activity_names() -> list[str]:
    """Every `android:name` on an `<activity>` element in the manifest."""
    text = MANIFEST.read_text()
    activities = re.findall(r"<activity\b(.*?)>", text, re.DOTALL)
    names: list[str] = []
    for block in activities:
        match = re.search(r'android:name="([^"]+)"', block)
        if match:
            names.append(match.group(1))
    return names


def _resolve(name: str, namespace: str) -> str:
    """
    Apply Android's manifest name resolution.

    A leading dot means "relative to the namespace"; a name with no dot at all
    is also treated as relative; anything else is already fully qualified.
    """
    if name.startswith("."):
        return namespace + name
    if "." not in name:
        return f"{namespace}.{name}"
    return name


def _source_file_for(fqcn: str) -> Path | None:
    """Locate the Kotlin or Java source file declaring `fqcn`, if it exists."""
    package, _, class_name = fqcn.rpartition(".")
    for lang in ("kotlin", "java"):
        for suffix in (".kt", ".java"):
            candidate = (
                ANDROID_APP
                / "src"
                / "main"
                / lang
                / Path(*package.split("."))
                / f"{class_name}{suffix}"
            )
            if candidate.is_file():
                return candidate
    return None


@pytest.mark.skipif(
    not MANIFEST.is_file() or not BUILD_GRADLE.is_file(),
    reason="Android project not present in this checkout",
)
class TestAndroidIdentity:
    def test_namespace_and_application_id_agree(self) -> None:
        """
        They may legitimately differ, but here they must not.

        `namespace` fixes where compiled classes live; `applicationId` is the
        published identity. Keeping them equal is what makes the relative
        `.MainActivity` in the manifest resolve to the class we actually ship.
        """
        assert _gradle_value("namespace") == _gradle_value("applicationId")

    def test_every_manifest_activity_resolves_to_a_real_source_file(self) -> None:
        """
        THE regression test. This is the assertion that was missing.

        Every activity the manifest names must exist as a source file at the
        path its fully-qualified name implies.
        """
        namespace = _gradle_value("namespace")
        names = _manifest_activity_names()
        assert names, "manifest declares no activities at all"

        unresolved: list[str] = []
        for name in names:
            fqcn = _resolve(name, namespace)
            if _source_file_for(fqcn) is None:
                unresolved.append(fqcn)

        assert not unresolved, (
            f"Manifest names {unresolved} but no such source file exists.\n"
            f"namespace={namespace!r}; the APK would install and then crash "
            f"with ClassNotFoundException on launch.\n"
            f"Fix by making the Kotlin package, the directory path, and the "
            f"gradle namespace agree."
        )

    def test_main_activity_package_matches_its_directory(self) -> None:
        """
        A `package` line that disagrees with the file's own directory compiles
        fine on some toolchains and then cannot be found at runtime.
        """
        sources = list((ANDROID_APP / "src" / "main").rglob("MainActivity.kt"))
        assert sources, "MainActivity.kt not found"

        for source in sources:
            declared = re.search(r"^package\s+([\w.]+)", source.read_text(), re.M)
            assert declared, f"{source} has no package declaration"

            # Directory path after src/main/<lang>/ must equal the package.
            parts = source.relative_to(ANDROID_APP / "src" / "main").parts[1:-1]
            from_path = ".".join(parts)
            assert declared.group(1) == from_path, (
                f"{source.name} declares package {declared.group(1)!r} but sits "
                f"in a directory implying {from_path!r}"
            )

    def test_launch_activity_is_the_main_activity(self) -> None:
        """The LAUNCHER intent filter must be on an activity we actually have."""
        text = MANIFEST.read_text()
        assert "android.intent.category.LAUNCHER" in text, (
            "no LAUNCHER category — the app would not appear in the launcher"
        )
        namespace = _gradle_value("namespace")
        resolved = [_resolve(n, namespace) for n in _manifest_activity_names()]
        assert any(r.endswith(".MainActivity") for r in resolved), resolved

    @pytest.mark.skipif(
        not IOS_PBXPROJ.is_file(), reason="iOS project not present"
    )
    def test_android_and_ios_identities_match(self) -> None:
        """
        Not strictly required by either platform — but a mismatch here is
        almost always an oversight rather than a decision, and it is how the
        Android side drifted in the first place. RunnerTests carries its own
        suffixed identifier, which is expected and excluded.
        """
        bundle_ids = {
            match
            for match in re.findall(
                r"PRODUCT_BUNDLE_IDENTIFIER = ([\w.]+);", IOS_PBXPROJ.read_text()
            )
            if not match.endswith(".RunnerTests")
        }
        assert bundle_ids == {_gradle_value("applicationId")}, (
            f"iOS bundle ids {sorted(bundle_ids)} vs Android applicationId "
            f"{_gradle_value('applicationId')!r}"
        )
