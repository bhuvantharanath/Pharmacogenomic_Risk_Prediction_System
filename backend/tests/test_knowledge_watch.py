"""
The weekly knowledge watch (Phase 9 B2): CPIC and PharmCAT vs the pinned data.

The watch is only worth having if a real change turns it red and a failure to
check is never read as "no change". These tests drive the script's offline mode
(`--compare-to`), which runs the same comparison as `--check-live` against a
directory instead of the network, and run the workflow's issue step with a fake
`gh` to count the issues it would open.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "scripts" / "cpic_snapshot.py"
SNAPSHOT = REPO_ROOT / "test-data" / "reference" / "cpic_snapshot"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "knowledge-watch.yml"
TITLE = "Knowledge watch: CPIC or PharmCAT differs from the pinned data"


def _watch(tmp_path: Path, *args: str) -> tuple[int, dict, str]:
    out = tmp_path / "report"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--report-dir", str(out)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    result = json.loads((out / "knowledge-watch.json").read_text())
    return proc.returncode, result, (out / "knowledge-watch.md").read_text()


@pytest.fixture
def current(tmp_path: Path) -> Path:
    """A copy of the pinned tables, standing in for what CPIC serves today."""
    target = tmp_path / "current"
    target.mkdir()
    for name in ("allele.json", "recommendation.json"):
        shutil.copy(SNAPSHOT / name, target / name)
    return target


def _edit(path: Path, change) -> None:
    rows = json.loads(path.read_text())
    change(rows)
    path.write_text(json.dumps(rows, indent=1, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# AC3 — a stale table turns the watch red, an identical one does not
# --------------------------------------------------------------------------- #


def test_identical_tables_are_no_change(tmp_path: Path, current: Path) -> None:
    code, result, report = _watch(tmp_path, "--compare-to", str(current))

    assert code == 0, report
    assert result["status"] == "unchanged"
    assert result["changes"] == []
    assert "No difference" in report


def test_a_changed_recommendation_text_is_reported(tmp_path: Path, current: Path) -> None:
    def reword(rows: list) -> None:
        row = next(r for r in rows if r["drugname"] == "clopidogrel")
        row["drugrecommendation"] = row["drugrecommendation"] + " Revised."

    _edit(current / "recommendation.json", reword)
    code, result, report = _watch(tmp_path, "--compare-to", str(current))

    assert code == 1, report
    assert [(c["table"], c["kind"]) for c in result["changes"]] == [("recommendation.json", "changed")]
    assert result["changes"][0]["key"]["drugname"] == "clopidogrel"
    assert "Revised." in report


def test_a_changed_allele_function_is_reported(tmp_path: Path, current: Path) -> None:
    def refunction(rows: list) -> None:
        row = next(r for r in rows if (r["genesymbol"], r["name"]) == ("CYP2C19", "*2"))
        row["clinicalfunctionalstatus"] = "Decreased function"

    _edit(current / "allele.json", refunction)
    code, result, report = _watch(tmp_path, "--compare-to", str(current))

    assert code == 1, report
    [change] = result["changes"]
    assert (change["table"], change["kind"]) == ("allele.json", "changed")
    assert change["key"] == {"genesymbol": "CYP2C19", "name": "*2"}
    assert change["before"][0]["clinicalfunctionalstatus"] == "No function"
    assert change["after"][0]["clinicalfunctionalstatus"] == "Decreased function"


def test_an_added_row_is_reported(tmp_path: Path, current: Path) -> None:
    _edit(current / "allele.json", lambda rows: rows.append({
        "genesymbol": "CYP2C19", "name": "*99", "clinicalfunctionalstatus": "No function",
        "activityvalue": None,
    }))
    code, result, report = _watch(tmp_path, "--compare-to", str(current))

    assert code == 1, report
    assert [(c["table"], c["kind"], c["key"]["name"]) for c in result["changes"]] == [
        ("allele.json", "added", "*99")
    ]


def test_a_removed_row_is_reported(tmp_path: Path, current: Path) -> None:
    _edit(current / "recommendation.json",
          lambda rows: rows.remove(next(r for r in rows if r["drugname"] == "codeine")))
    code, result, _ = _watch(tmp_path, "--compare-to", str(current))

    assert code == 1
    assert [(c["table"], c["kind"]) for c in result["changes"]] == [("recommendation.json", "removed")]


def test_a_check_that_cannot_run_is_not_no_change(tmp_path: Path) -> None:
    """Exit 2 and status "error", never 0: an unreadable source is not "unchanged"."""
    code, result, report = _watch(tmp_path, "--compare-to", str(tmp_path / "missing"))

    assert code == 2
    assert result["status"] == "error"
    assert "could not be completed" in report


# --------------------------------------------------------------------------- #
# AC4 — a newer PharmCAT release turns the watch red
# --------------------------------------------------------------------------- #


def test_the_pinned_release_is_no_change(tmp_path: Path, current: Path) -> None:
    code, result, _ = _watch(tmp_path, "--compare-to", str(current), "--pharmcat-tag", "v3.4.0")

    assert code == 0
    assert result["pinned_pharmcat"] == "3.4.0"
    assert result["release"] is None


@pytest.mark.parametrize("tag", ["v3.4.1", "v3.5.0", "4.0.0"])
def test_a_newer_release_is_reported(tmp_path: Path, current: Path, tag: str) -> None:
    code, result, report = _watch(tmp_path, "--compare-to", str(current), "--pharmcat-tag", tag)

    assert code == 1, report
    assert result["release"] == {"pinned": "3.4.0", "latest": tag}
    assert f"PharmCAT {tag} is newer" in report


def test_an_unreadable_release_tag_is_not_no_change(tmp_path: Path, current: Path) -> None:
    code, result, _ = _watch(tmp_path, "--compare-to", str(current), "--pharmcat-tag", "nightly")

    assert code == 2
    assert result["status"] == "error"


# --------------------------------------------------------------------------- #
# AC5 — the workflow: weekly, least privilege, red on change and on failure
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


def _steps(workflow: dict) -> list[dict]:
    [job] = workflow["jobs"].values()
    return job["steps"]


def test_it_runs_weekly_and_on_demand(workflow: dict) -> None:
    triggers = workflow.get("on", workflow.get(True))  # YAML 1.1 reads `on` as true
    [schedule] = triggers["schedule"]
    minute, hour, dom, month, dow = schedule["cron"].split()
    assert (dom, month) == ("*", "*") and dow.isdigit(), schedule["cron"]
    assert "workflow_dispatch" in triggers


def test_permissions_are_read_contents_and_write_issues_only(workflow: dict) -> None:
    assert workflow["permissions"] == {"contents": "read", "issues": "write"}
    [job] = workflow["jobs"].values()
    assert "permissions" not in job


def test_nothing_swallows_a_failure() -> None:
    text = WORKFLOW.read_text()
    assert "|| true" not in text
    assert "continue-on-error" not in text
    assert "set +e" not in text


def test_the_check_step_fails_the_job_on_change_and_on_error(workflow: dict) -> None:
    check = next(s for s in _steps(workflow) if s.get("id") == "check")
    # The command alone: its exit code (1 changed, 2 could not check) is the
    # step's, so either fails the job.
    assert check["run"].strip() == (
        'python scripts/cpic_snapshot.py --check-live --report-dir "$RUNNER_TEMP/watch"'
    )
    issue = next(s for s in _steps(workflow) if s.get("id") == "issue")
    assert issue["if"] == "failure() && steps.check.outcome == 'failure'"


def _fake_gh(tmp_path: Path, open_issues: list[dict]) -> tuple[dict, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "gh.log"
    listing = tmp_path / "issues.json"
    listing.write_text(json.dumps(open_issues))
    gh = bin_dir / "gh"
    gh.write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s\\n" "$*" >> "$GH_LOG"\n'
        'if [ "$1 $2" = "issue list" ]; then cat "$GH_LIST"; fi\n'
    )
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "GH_LOG": str(log), "GH_LIST": str(listing),
        "RUNNER_TEMP": str(tmp_path), "GITHUB_REPOSITORY": "owner/repo",
    }
    return env, log


def _run_issue_step(workflow: dict, tmp_path: Path, status: str, open_issues: list[dict]) -> list[str]:
    report = tmp_path / "watch"
    report.mkdir()
    (report / "knowledge-watch.json").write_text(json.dumps({"status": status}))
    (report / "knowledge-watch.md").write_text("## Knowledge watch\n")
    env, log = _fake_gh(tmp_path, open_issues)
    script = next(s for s in _steps(workflow) if s.get("id") == "issue")["run"]
    proc = subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
        env=env, capture_output=True, text=True, timeout=60, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return log.read_text().splitlines() if log.exists() else []


def test_a_first_change_opens_exactly_one_issue(workflow: dict, tmp_path: Path) -> None:
    calls = _run_issue_step(workflow, tmp_path, "changed", [{"number": 3, "title": "unrelated"}])

    writes = [c for c in calls if not c.startswith("issue list")]
    assert len(writes) == 1 and writes[0].startswith("issue create"), calls
    assert TITLE in writes[0]


def test_a_later_change_comments_on_the_open_issue(workflow: dict, tmp_path: Path) -> None:
    calls = _run_issue_step(workflow, tmp_path, "changed",
                            [{"number": 3, "title": "unrelated"}, {"number": 7, "title": TITLE}])

    writes = [c for c in calls if not c.startswith("issue list")]
    assert len(writes) == 1 and writes[0].startswith("issue comment 7 "), calls


def test_a_check_that_could_not_run_opens_no_issue(workflow: dict, tmp_path: Path) -> None:
    assert _run_issue_step(workflow, tmp_path, "error", []) == []
