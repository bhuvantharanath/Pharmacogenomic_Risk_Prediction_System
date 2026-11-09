"""
The README's setup and test steps must work as written (Phase 9 F-10,
audit/phase9/F10.log).

Followed verbatim on a clean clone, they did not: the Quickstart never installed
pytest, so `cd backend && pytest` ran a global Python 3.13 pytest outside the
venv; it never downloaded the spaCy model, so two vocabulary tests failed; the
demo's recovery hint sourced the one file startup refuses. None of it was wrong
in CI, because CI installs things the README did not mention.

So these tests read the facts from where they live — CI's workflow, the
production Dockerfile, the env example — and require the README to agree,
rather than holding copies that can drift.
"""

from __future__ import annotations

import re

from tests.conftest import REPO_ROOT

README = REPO_ROOT / "README.md"
CI = REPO_ROOT / ".github" / "workflows" / "test.yml"
DOCKERFILE = REPO_ROOT / "infra" / "Dockerfile"
RUN_DEMO = REPO_ROOT / "scripts" / "run_demo.py"

DEV_INSTALL = "pip install -r requirements-dev.txt"
MODEL = "python -m spacy download en_core_web_sm"


def _read(path) -> str:
    assert path.is_file(), f"{path} is missing, so this check would pass on nothing"
    return path.read_text()


def test_the_readme_installs_what_ci_installs() -> None:
    ci, readme = _read(CI), _read(README)
    # The positive control: CI really does both, so the README is matched to a fact.
    assert "requirements-dev.txt" in ci and MODEL in ci, (
        "test.yml no longer installs the dev requirements and the spaCy model; "
        "re-derive what the README should say")
    assert DEV_INSTALL in readme, "README never installs requirements-dev.txt, so pytest is missing"
    assert MODEL in readme, "README never downloads the spaCy model, so two vocabulary tests fail"


def test_the_readme_runs_the_venvs_pytest() -> None:
    readme = _read(README)
    assert "python -m pytest" in readme
    assert "cd backend && pytest" not in readme, (
        "a bare `pytest` resolves to whichever is first on PATH; on a clean clone "
        "that was a global Python 3.13 pytest outside the venv")


def test_the_readme_names_the_python_versions_in_use() -> None:
    readme = _read(README)
    ci_versions = set(re.findall(r'python-version:\s*"?(\d+\.\d+)', _read(CI)))
    image = re.search(r"^FROM python:(\d+\.\d+)", _read(DOCKERFILE), re.M)
    assert ci_versions, "no python-version found in test.yml"
    assert image, "no python base image found in infra/Dockerfile"
    prerequisite = next((line for line in readme.splitlines() if line.startswith("**Prerequisites:**")), "")
    assert "3.11 or newer" in prerequisite, prerequisite
    for version in sorted(ci_versions) + [image.group(1)]:
        assert version in prerequisite, (
            f"README's prerequisite line does not name Python {version}, which CI or "
            f"the production image uses:\n  {prerequisite}")


def test_the_demo_points_at_the_env_file_startup_accepts() -> None:
    demo = _read(RUN_DEMO)
    assert "source backend/.env" not in demo, (
        "run_demo.py tells the user to source backend/.env, which assert_no_baked_secrets "
        "refuses to start with")
    assert "source infra/local-dev.env" in demo


def test_the_quickstart_says_what_to_edit() -> None:
    line = next((l for l in _read(README).splitlines() if "local-dev.env.example" in l and "cp " in l), "")
    assert line, "README no longer copies local-dev.env.example; this check would pass on nothing"
    assert "JAVA_HOME" in line, (
        f"the copy step does not say what to edit; the example already sets everything "
        f"else:\n  {line}")
