"""
The demo is covered like everything else.

Three walkthroughs each died on a different environmental blocker — a CORS guard
firing on an env marker, a rate limit exhausted by rehearsal, shell word-splitting
mangling paths into six 422s. All three would have happened on stage, and none was
a product defect. The demo path was simply the least-tested path in the system.

These tests run the real script against a live backend when one is reachable, and
otherwise verify everything that can be checked without one. A demo that can
regress silently is not a demo.
"""

from __future__ import annotations

import importlib.util
import sys
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = REPO_ROOT / "test-data" / "demo"
BASE = "http://127.0.0.1:8000"


def _load():
    spec = importlib.util.spec_from_file_location(
        "run_demo", REPO_ROOT / "scripts" / "run_demo.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_demo"] = module
    spec.loader.exec_module(module)
    return module


def _backend_up() -> bool:
    try:
        with urllib.request.urlopen(f"{BASE}/ready", timeout=5) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


demo = _load()


class TestDemoDefinition:
    """Checks that need no backend, so they run everywhere including CI."""

    def test_six_scenarios_numbered_one_to_six(self) -> None:
        assert [s.number for s in demo.SCENARIOS] == [1, 2, 3, 4, 5, 6]

    def test_every_scenario_file_ships(self) -> None:
        missing = [s.vcf for s in demo.SCENARIOS if not (DEMO_DIR / s.vcf).is_file()]
        assert not missing, f"demo references files that do not ship: {missing}"

    def test_the_contrast_pair_uses_the_same_genotype(self) -> None:
        """
        S1 and S2 must differ ONLY in shape. If someone regenerates one without
        the other the centrepiece silently becomes two different patients, and the
        argument collapses without anything failing.
        """
        s1 = (DEMO_DIR / "demo_confident.vcf").read_text().splitlines()
        s2 = (DEMO_DIR / "demo_variants_only.vcf").read_text().splitlines()

        def variant_rows(lines: list[str]) -> set[tuple[str, str, str]]:
            out = set()
            for line in lines:
                if line.startswith("#"):
                    continue
                f = line.split("\t")
                gt = f[9].split(":")[0]
                if gt not in ("0/0", "0|0"):
                    out.add((f[0], f[1], gt))
            return out

        assert variant_rows(s1) == variant_rows(s2), (
            "the two demo files no longer describe the same genotype"
        )
        # And they must still differ in the way that matters.
        hom_ref = sum(
            1 for line in s2
            if not line.startswith("#") and line.split("\t")[9].split(":")[0] in ("0/0", "0|0")
        )
        assert hom_ref == 0, "demo_variants_only.vcf must contain no hom-ref rows"

    def test_expected_labels_are_declared(self) -> None:
        for s in demo.SCENARIOS:
            assert s.expect, f"S{s.number} declares no expected label"

    def test_narration_exists_so_runbook_cannot_drift(self) -> None:
        for s in demo.SCENARIOS:
            assert len(s.narration) > 60, f"S{s.number} has no usable narration"


@pytest.mark.skipif(not _backend_up(), reason="no backend on 127.0.0.1:8000")
class TestDemoAgainstLiveApi:
    """The real thing: runs each scenario and asserts its label class."""

    def test_each_scenario_returns_its_expected_label(self) -> None:
        failures: list[str] = []
        for s in demo.SCENARIOS:
            result = demo.post_analyze(BASE, DEMO_DIR / s.vcf, s.drugs)
            if result is None or result.status != 200:
                failures.append(f"S{s.number}: HTTP {getattr(result, 'status', '?')}")
                continue
            first = s.drugs.split(",")[0]
            got = result.label_of(first)
            if s.expect != "mixed" and got != s.expect:
                failures.append(f"S{s.number} {first}: expected {s.expect}, got {got}")
        assert not failures, "\n".join(failures)

    def test_the_contrast_actually_contrasts(self) -> None:
        """S1 and S2 must call the same diplotype and reach opposite conclusions."""
        a = demo.post_analyze(BASE, DEMO_DIR / "demo_confident.vcf", "clopidogrel")
        b = demo.post_analyze(BASE, DEMO_DIR / "demo_variants_only.vcf", "clopidogrel")
        assert a.status == 200 and b.status == 200

        pa = a.primary["pharmacogenomic_profile"]
        pb = b.primary["pharmacogenomic_profile"]
        assert pa["diplotype"] == pb["diplotype"] == "*2/*2", (
            "the demo's whole point is that the genotype is NOT lost"
        )
        assert a.primary["risk_assessment"]["risk_label"] == "Ineffective"
        assert b.primary["risk_assessment"]["risk_label"] == "Unknown"

        joined = " ".join(b.body["quality_metrics"]["warnings"])
        assert "homozygous-reference" in joined, "variants-only warning missing"

    def test_loopback_is_not_rate_limited(self) -> None:
        """
        The rehearsal killer. Twelve requests exceeds the 10-per-5-minutes budget;
        from loopback every one must still succeed.
        """
        vcf = DEMO_DIR / "demo_normal.vcf"
        codes = [demo.post_analyze(BASE, vcf, "clopidogrel").status for _ in range(12)]
        assert all(c == 200 for c in codes), f"rate limited on loopback: {codes}"
