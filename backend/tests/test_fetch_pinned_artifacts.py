"""
The CI fetch of the pinned binaries must take every expectation from the
hash-bound manifests, and must fail closed. A wrong download is never moved
into place, and a mismatched file on disk is never replaced.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    # The script imports its siblings, as every script here does when run.
    if str(REPO / "scripts") not in sys.path:
        sys.path.insert(0, str(REPO / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "fetch_pinned_artifacts", REPO / "scripts/fetch_pinned_artifacts.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["fetch_pinned_artifacts"] = module
    spec.loader.exec_module(module)
    return module


fetch = _load()


def _pin(source: Path, content: bytes, *, sha: str | None = None, size: int | None = None):
    source.write_bytes(content)
    return fetch.Pin(
        path="pinned/blob.bin",
        sha256=sha or hashlib.sha256(content).hexdigest(),
        bytes=len(content) if size is None else size,
        url=source.as_uri(),
    )


def test_pins_come_from_the_hash_bound_manifests() -> None:
    bundle = json.loads((REPO / fetch.BUNDLE_RELATIVE).read_text())
    pharmcat = bundle["pharmcat"]
    evaluation = json.loads((REPO / bundle["evaluation_current"]["manifest"]["path"]).read_text())
    expected = {
        (ref["path"], ref["sha256"], ref["bytes"])
        for ref in (pharmcat["jar"], pharmcat["positions"], pharmcat["positions_index"],
                    evaluation["frozen_combined_vcf"])
    }
    pins = fetch.load_pins(REPO)
    assert {(pin.path, pin.sha256, pin.bytes) for pin in pins} == expected
    assert all(pin.url.startswith("https://github.com/") for pin in pins)
    assert all(pin.url.endswith("/" + Path(pin.path).name) for pin in pins)


def test_an_evaluation_manifest_the_bundle_does_not_vouch_for_is_not_trusted(tmp_path) -> None:
    bundle_relative = Path(fetch.BUNDLE_RELATIVE)
    bundle = json.loads((REPO / bundle_relative).read_text())
    manifest_relative = Path(bundle["evaluation_current"]["manifest"]["path"])
    for relative, content in (
        (bundle_relative, (REPO / bundle_relative).read_bytes()),
        (manifest_relative, (REPO / manifest_relative).read_bytes() + b" "),
    ):
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / relative).write_bytes(content)

    with pytest.raises(fetch.PinError, match="does not match the hash"):
        fetch.load_pins(tmp_path)


def test_a_matching_download_is_moved_into_place(tmp_path) -> None:
    pin = _pin(tmp_path / "source.bin", b"pinned bytes")
    root = tmp_path / "repo"

    assert fetch.ensure(pin, root) == "fetched"
    assert (root / pin.path).read_bytes() == b"pinned bytes"
    assert fetch.ensure(pin, root) == "present"
    assert list((root / "pinned").iterdir()) == [root / pin.path], "a partial file was left behind"


def test_a_wrong_download_is_never_moved_into_place(tmp_path) -> None:
    pin = _pin(tmp_path / "source.bin", b"tampered", sha="0" * 64)
    root = tmp_path / "repo"

    with pytest.raises(fetch.PinError, match="downloaded 8 bytes"):
        fetch.ensure(pin, root)
    assert list((root / "pinned").iterdir()) == []


def test_a_download_larger_than_its_pin_is_refused(tmp_path) -> None:
    pin = _pin(tmp_path / "source.bin", b"x" * 64, size=8)
    root = tmp_path / "repo"

    with pytest.raises(fetch.PinError, match="larger than the pinned"):
        fetch.ensure(pin, root)
    assert list((root / "pinned").iterdir()) == []


def test_a_mismatched_file_on_disk_is_not_replaced(tmp_path) -> None:
    pin = _pin(tmp_path / "source.bin", b"pinned bytes")
    root = tmp_path / "repo"
    target = root / pin.path
    target.parent.mkdir(parents=True)
    target.write_bytes(b"local edit")

    with pytest.raises(fetch.PinError, match="does not match its pin"):
        fetch.ensure(pin, root)
    assert target.read_bytes() == b"local edit"


def test_check_mode_reports_a_missing_file_without_fetching(tmp_path) -> None:
    pin = _pin(tmp_path / "source.bin", b"pinned bytes")
    root = tmp_path / "repo"

    with pytest.raises(fetch.PinError, match="is missing"):
        fetch.ensure(pin, root, fetch=False)
    assert not (root / pin.path).exists()


@pytest.mark.parametrize(("workflow", "check"), [
    (".github/workflows/test.yml", "python -m pytest -q"),
    (".github/workflows/deploy-web.yml", "python scripts/release_status.py --run-required"),
])
def test_ci_fetches_the_pins_before_it_checks_them(workflow: str, check: str) -> None:
    text = (REPO / workflow).read_text()
    fetch_at = text.find("python scripts/fetch_pinned_artifacts.py")
    assert fetch_at != -1, f"{workflow} no longer fetches the pinned binaries"
    assert fetch_at < text.find(check), f"{workflow} runs its checks before fetching"
    assert 'java-version: "17"' in text, f"{workflow} no longer pins the JDK PharmCAT 3.4.0 needs"
