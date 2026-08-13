"""
The backend must be able to say which commit it is running.

WHY

The two deployed halves ship through different systems — the web client via
GitHub Actions, the backend via a Render API call — and for one release they
drifted with nothing anywhere reporting it. Render's `autoDeploy` flag reads
"yes" on this service and does nothing, because it was created from a public
repo URL through the REST API and no GitHub App exists to deliver the webhook.
A push updated the client and left the server on older code; the site looked
entirely healthy and merely behaved like an older backend.

The same shape as a CI step under `|| true`, and as the thirteen checks in
`reports/provenance_finding.md` that passed while checking nothing: a control
that reports enabled while doing nothing, discovered only by pushing a commit
and noticing the backend had not moved.

This is the reporting half of the fix. The lockstep half is the deploy workflow,
which now deploys the backend first, waits for `live`, and then asserts this
very field equals the commit it built before it will ship the client.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as main_mod

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture()
def client() -> TestClient:
    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        yield c


# --------------------------------------------------------------------------- #
# Where the commit comes from
# --------------------------------------------------------------------------- #

def test_render_supplies_the_commit_without_a_build_arg(monkeypatch) -> None:
    """
    `RENDER_GIT_COMMIT` is set automatically by Render at runtime (verified
    against render.com/docs/environment-variables, 2026-08-13). Reading it
    means the image needs no build argument and no baked-in version file —
    which matters because a baked file is exactly the kind of thing that goes
    stale without anyone noticing.
    """
    monkeypatch.setenv("RENDER_GIT_COMMIT", "1afb9495fd7da5f982974e7daef5f2db1d95f4ac")
    assert main_mod.build_commit() == "1afb9495fd7da5f982974e7daef5f2db1d95f4ac"


@pytest.mark.parametrize("var", ["GIT_COMMIT", "SOURCE_COMMIT"])
def test_a_generic_variable_works_on_any_other_host(monkeypatch, var: str) -> None:
    """The same code must report a real SHA under compose or another platform."""
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.setenv(var, "abcdef1234567890")
    assert main_mod.build_commit() == "abcdef1234567890"


def test_render_wins_when_several_are_set(monkeypatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "aaaaaaa")
    monkeypatch.setenv("GIT_COMMIT", "bbbbbbb")
    assert main_mod.build_commit() == "aaaaaaa"


def test_unknown_rather_than_a_lie_when_nothing_is_set(monkeypatch) -> None:
    """
    "unknown" is honest and the client treats it as *no information*, which is
    the right reading. Inventing a plausible value — a version constant, a
    build date — would produce a comparison that silently always passes.
    """
    for var in ("RENDER_GIT_COMMIT", "GIT_COMMIT", "SOURCE_COMMIT"):
        monkeypatch.delenv(var, raising=False)
    assert main_mod.build_commit() == "unknown"


def test_blank_is_treated_as_absent(monkeypatch) -> None:
    """Render sets the variable empty rather than unset in some contexts."""
    monkeypatch.setenv("RENDER_GIT_COMMIT", "   ")
    monkeypatch.setenv("GIT_COMMIT", "realsha123")
    assert main_mod.build_commit() == "realsha123"


# --------------------------------------------------------------------------- #
# How it is reported
# --------------------------------------------------------------------------- #

def test_ready_reports_the_commit(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "1afb9495fd7da5f982974e7daef5f2db1d95f4ac")
    body = client.get("/ready").json()

    assert body["build"]["commit"] == "1afb9495fd7da5f982974e7daef5f2db1d95f4ac"
    assert body["build"]["commit_short"] == "1afb949"


def test_an_unknown_commit_does_not_make_the_service_unready(
    client: TestClient, monkeypatch
) -> None:
    """
    THE PROPERTY THAT KEEPS THIS SAFE. A version label is diagnostic, not a
    dependency. Gating readiness on it would take a working analysis backend
    out of service over a missing environment variable — turning an
    observability feature into an outage, which is a strictly worse failure
    than the drift it was added to reveal.
    """
    for var in ("RENDER_GIT_COMMIT", "GIT_COMMIT", "SOURCE_COMMIT"):
        monkeypatch.delenv(var, raising=False)

    response = client.get("/ready")
    body = response.json()

    assert body["build"]["commit"] == "unknown"
    # Readiness reflects PharmCAT, the corpus, the store and the mapping —
    # never the version label.
    assert "build" not in body["checks"]
    assert body["status"] == ("ready" if response.status_code == 200 else "not_ready")


def test_health_stays_trivial(client: TestClient) -> None:
    """
    `/health` is the cold-start ping and the platform's health check. Adding a
    version lookup here would make the cheap probe less cheap for no gain —
    the client asks `/ready` once on load, not on every poll.
    """
    body = client.get("/health").json()
    assert body == {"status": "ok"}


# --------------------------------------------------------------------------- #
# The lockstep workflow — the half that prevents drift rather than reporting it
# --------------------------------------------------------------------------- #

def _workflow() -> str:
    return (REPO / ".github/workflows/deploy-web.yml").read_text()


def test_the_backend_deploys_before_the_client() -> None:
    """
    Order is the whole point. Client-first would leave it, for the length of a
    backend build, strictly NEWER than the API it calls. Backend-first means
    the only transient state is a slightly old client against a new API, which
    a backwards-compatible API is built to survive.
    """
    import yaml
    spec = yaml.safe_load(_workflow())
    assert "backend" in spec["jobs"], "the backend deploy job is gone"
    assert spec["jobs"]["deploy"].get("needs") == "backend", (
        "the web deploy no longer waits for the backend — the two halves can "
        "drift again, which is exactly what this workflow exists to prevent")


def test_the_deploy_is_pinned_to_this_commit() -> None:
    """
    Without `commitId`, Render deploys "latest on the connected branch". Under
    two quick pushes that can be a DIFFERENT commit from the one the client is
    compiled against — reintroducing drift as a race rather than as a missing
    webhook.
    """
    workflow = _workflow()
    # The key is backslash-escaped inside the shell string that builds the JSON
    # body, so match on the bare word plus the SHA it is paired with rather
    # than on a quoting style that is incidental.
    assert "commitId" in workflow, "the deploy is no longer pinned to a commit"
    assert "${GITHUB_SHA}" in workflow

    # And specifically: the pin uses the RUNNING commit, not a branch name.
    import re
    assert re.search(r"commitId[^\n]*GITHUB_SHA", workflow), (
        "commitId is present but not set from GITHUB_SHA — pinning to "
        "anything else reintroduces the race this prevents")


def test_the_workflow_fails_loudly_if_the_backend_never_goes_live() -> None:
    workflow = _workflow()
    for status in ("build_failed", "update_failed", "canceled",
                   "pre_deploy_failed", "deactivated"):
        assert status in workflow, f"'{status}' is not treated as a failure"
    assert "did not finish within" in workflow, "no timeout guard"


def test_the_workflow_verifies_the_serving_process_not_just_the_deploy_record() -> None:
    """
    `live` means Render finished, not that the new code is answering. The
    original drift was invisible precisely because every *record* looked fine.
    """
    workflow = _workflow()
    assert "/ready" in workflow
    assert "EXPECTED_BACKEND_SHA" in workflow, (
        "the client is no longer built with the SHA it expects, so the "
        "mismatch notice can never fire")


def test_backend_changes_also_trigger_the_deploy() -> None:
    """
    The path filter listed only `app/**` when this workflow deployed the client
    alone. Leaving it that way once the backend joined would mean a
    backend-only commit deploys nothing at all — a quieter version of the same
    bug.
    """
    import yaml
    spec = yaml.safe_load(_workflow())
    paths = spec[True]["push"]["paths"]  # `on:` parses as the boolean True
    for required in ("backend/**", "infra/Dockerfile"):
        assert required in paths, f"{required} does not trigger a deploy"
