"""
CI must be able to say that something broke (Phase 9 F-08, audit/phase9/F08.log).

The content gate is red by decision while review is incomplete. It used to be
the last step of the `test` workflow, so `test` was red on every push and a real
regression looked exactly like the expected red. It now has its own workflow.
These tests keep it there, keep it from being quietly deleted on the way, and
keep `|| true` out of every workflow, which is standing rule 3.
"""

from __future__ import annotations

import yaml

from tests.conftest import REPO_ROOT

WORKFLOWS = REPO_ROOT / ".github" / "workflows"
CONTENT_GATE = "release_status.py --content-only"


def _workflow(name: str) -> dict:
    path = WORKFLOWS / name
    assert path.is_file(), f"{name} is missing, so this check would pass on nothing"
    return yaml.safe_load(path.read_text())


def _runs(workflow: dict) -> list[tuple[str, str, str]]:
    """(job, step name, run text) for every step that runs a command."""
    return [(job, step.get("name", ""), step["run"])
            for job, spec in workflow["jobs"].items()
            for step in spec.get("steps", [])
            if "run" in step]


def test_no_workflow_swallows_a_return_code() -> None:
    files = sorted(WORKFLOWS.glob("*.yml"))
    assert files, "no workflows found, so this check would pass on nothing"
    offenders = []
    for path in files:
        for number, line in enumerate(path.read_text().splitlines(), 1):
            code = line.split("#", 1)[0]  # a comment may name the pattern; only code may not use it
            if "|| true" in code:
                offenders.append(f"{path.name}:{number}: {line.strip()}")
    assert not offenders, "`|| true` accepts a crash as success:\n  " + "\n  ".join(offenders)


def test_the_test_workflow_does_not_carry_the_always_red_gate() -> None:
    carrying = [f"{job}/{name}" for job, name, run in _runs(_workflow("test.yml")) if CONTENT_GATE in run]
    assert not carrying, (
        f"test.yml runs the content gate again ({carrying}); it is red by decision, so "
        "`test` would be red on every push and a regression would be invisible")


def test_the_content_gate_runs_in_its_own_workflow() -> None:
    workflow = _workflow("content-review.yml")
    triggers = workflow.get("on", workflow.get(True))  # YAML 1.1 reads a bare `on` as True
    assert "push" in triggers, "content-review.yml must run on every push"
    gates = [name for _job, name, run in _runs(workflow) if CONTENT_GATE in run]
    assert gates, "the content gate was dropped rather than moved"


def test_the_detail_reports_must_produce_their_output() -> None:
    detail = [run for _job, name, run in _runs(_workflow("content-review.yml"))
              if name == "Explanation review detail"]
    assert detail, "the detail step is gone"
    assert "json.load" in detail[0], (
        "the detail reports no longer check that a report was produced, so a crash "
        "would pass as an incomplete review")
