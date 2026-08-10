"""Shared fixtures. All tests run WITHOUT PharmCAT or Docker installed."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make `app` importable when pytest is run from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.pharmcat_models import PharmcatReport  # noqa: E402
from app.pharmcat_runner import parse_report  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_DATA = REPO_ROOT / "test-data"


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """
    Clear the rate limiter between tests.

    `security.limiter` is a deliberate process-global singleton (the app is
    stateless and single-instance on every free tier we target). Without this
    reset, the 11th `/analyze` call *in the whole session* gets a 429 and a
    dozen unrelated tests fail with confusing assertions.
    """
    from app.security import limiter

    limiter.reset()
    yield
    limiter.reset()


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def cyp2c19_pm_report() -> PharmcatReport:
    """Real PharmCAT output for a CYP2C19 *2/*2 poor metaboliser."""
    return parse_report(load_fixture("pharmcat_report_cyp2c19_pm.json"))


@pytest.fixture
def dpyd_im_report() -> PharmcatReport:
    """Real PharmCAT output for a DPYD c.1905+1G>A heterozygote."""
    return parse_report(load_fixture("pharmcat_report_dpyd_im.json"))


@pytest.fixture
def valid_vcf_bytes() -> bytes:
    """A real generated GRCh38 VCF from test-data/."""
    return (TEST_DATA / "cyp2c19_poor_metabolizer.vcf").read_bytes()
