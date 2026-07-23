"""
Infrastructure config consistency — regression guards for two silent failures.

Both defects here shared a shape: a value in one file had to agree with a value
in another file, nothing checked that they did, and when they drifted the
system kept *appearing* to work.

  P1-3  CORS_ALLOWED_ORIGINS was documented in DEPLOY_NOTES but set in no deploy
        config. Default empty -> health checks pass, `curl` works, and every
        browser request from the real frontend is blocked.
  P1-4  docker-compose mounted /opt/pharmaguard/* after the Dockerfile's WORKDIR
        moved to /home/user/app. The mounts landed on paths nothing read, so
        compose silently ran baked-in code and --reload did nothing.

These are static text checks: no Docker, no network, no built image.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

INFRA = Path(__file__).resolve().parents[2] / "infra"
DOCKERFILE = INFRA / "Dockerfile"
COMPOSE = INFRA / "docker-compose.yml"
ENV_EXAMPLE = Path(__file__).resolve().parents[1] / ".env.example"


def _dockerfile_workdir() -> str:
    return re.findall(r"^WORKDIR\s+(\S+)", DOCKERFILE.read_text(), re.M)[-1]


def _compose_service() -> dict:
    return yaml.safe_load(COMPOSE.read_text())["services"]["backend"]


class TestComposeMountsMatchWorkdir:
    """P1-4 regression."""

    def test_every_mount_target_is_inside_the_workdir(self) -> None:
        workdir = _dockerfile_workdir()
        mounts = [v.split(":")[1] for v in _compose_service()["volumes"]]
        assert mounts, "compose declares no volumes"

        misaligned = [m for m in mounts if not m.startswith(workdir)]
        assert not misaligned, (
            f"compose mounts {misaligned} but the image WORKDIR is {workdir!r}.\n"
            f"The mounts would land outside the app directory, so the container "
            f"would run its baked-in copy and live-reload would do nothing."
        )

    def test_app_code_mounts_over_the_copied_app_directory(self) -> None:
        """The code mount must shadow `COPY backend/app ./app`, not sit beside it."""
        workdir = _dockerfile_workdir()
        targets = [v.split(":")[1] for v in _compose_service()["volumes"]]
        assert f"{workdir}/app" in targets, targets

    def test_corpus_mount_matches_the_configured_corpus_dir(self) -> None:
        """
        `PHARMAGUARD_CORPUS_DIR` points at .../rag-corpus/mechanisms; the mount
        must land on its parent or the corpus silently disappears and every
        explanation loses its mechanism section.
        """
        corpus_dir = re.findall(
            r"PHARMAGUARD_CORPUS_DIR=(\S+)", DOCKERFILE.read_text()
        )[0]
        targets = [v.split(":")[1] for v in _compose_service()["volumes"]]
        assert any(corpus_dir.startswith(t) for t in targets), (
            f"no compose mount covers {corpus_dir}; mounts are {targets}"
        )


class TestCorsIsConfiguredEverywhere:
    """P1-3 regression."""

    def test_compose_sets_cors_allowed_origins(self) -> None:
        env = _compose_service()["environment"]
        assert "CORS_ALLOWED_ORIGINS" in env, (
            "docker-compose does not set CORS_ALLOWED_ORIGINS; a container "
            "started from it would reject the dev frontend"
        )
        assert env["CORS_ALLOWED_ORIGINS"].strip(), "value is empty"

    def test_compose_marks_itself_as_development(self) -> None:
        """
        Without this, compose's own `PORT`-free env still trips the hosted
        sniffer on some platforms; being explicit keeps local runs startable.
        """
        assert _compose_service()["environment"].get("PHARMAGUARD_ENV") == (
            "development"
        )

    def test_dockerfile_declares_the_variable(self) -> None:
        """
        Declared (empty) rather than defaulted: an empty value makes a hosted
        deploy fail loudly, whereas a placeholder origin would fail silently.
        """
        assert "CORS_ALLOWED_ORIGINS" in DOCKERFILE.read_text()

    def test_env_example_documents_it(self) -> None:
        assert "CORS_ALLOWED_ORIGINS" in ENV_EXAMPLE.read_text()

    @pytest.mark.parametrize(
        "doc", ["DEPLOY_NOTES.md", "hf-space/README.md"]
    )
    def test_deploy_docs_mention_it(self, doc: str) -> None:
        assert "CORS_ALLOWED_ORIGINS" in (INFRA / doc).read_text()
