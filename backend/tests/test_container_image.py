"""
The deployment image's definition, checked without building it (Phase 9 B4).

The image is built only on the host, so a regression in infra/Dockerfile is
otherwise found at deploy time. These checks pin the properties the slim image
was built to have: every stage pinned to bytes, only the jar on the served
path, the jar's digest enforced at build time, and a build context that holds
exactly what the image copies.
"""

from __future__ import annotations

import re

from tests.conftest import REPO_ROOT

DOCKERFILE = (REPO_ROOT / "infra/Dockerfile").read_text()
DOCKERIGNORE = (REPO_ROOT / ".dockerignore").read_text()
JAR_SHA = "9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741"


def _instructions() -> list[str]:
    """Dockerfile instructions with comments dropped and continuations joined."""
    lines = [line for line in DOCKERFILE.splitlines() if not line.lstrip().startswith("#")]
    return [i.strip() for i in re.sub(r"\\\n", " ", "\n".join(lines)).splitlines() if i.strip()]


def test_every_stage_is_pinned_by_tag_and_digest() -> None:
    stages = [i.split()[1] for i in _instructions() if i.startswith("FROM ")]
    assert len(stages) == 3, stages
    for image in stages:
        assert re.fullmatch(r"[\w./-]+:[\w.-]+@sha256:[0-9a-f]{64}", image), image
    assert stages[-1].startswith("python:3.14.6-slim-trixie@"), "served runtime changed"


def test_the_served_path_is_the_jar_and_nothing_else() -> None:
    body = "\n".join(_instructions())
    assert "ENV PHARMCAT_JAR=/pharmcat/pharmcat.jar" in body
    assert "pharmcat_pipeline" not in body, "the preprocessor wrapper is back in the image"
    copies_from = re.findall(r"COPY --from=(\w+) (\S+) (\S+)", body)
    assert copies_from == [
        ("jre", "/opt/java/openjdk", "/opt/java/openjdk"),
        ("pharmcat", "/pharmcat/pharmcat.jar", "/pharmcat/pharmcat.jar"),
    ]


def test_the_build_fails_on_any_other_jar() -> None:
    # Whitespace-normalised: line continuations leave runs of spaces.
    body = " ".join(" ".join(_instructions()).split())
    assert f'echo "{JAR_SHA} /pharmcat/pharmcat.jar" | sha256sum -c -' in body
    assert 'java -jar /pharmcat/pharmcat.jar -version | grep -q "PharmCAT 3.4.0"' in body


def test_runtime_shape_is_unchanged() -> None:
    body = "\n".join(_instructions())
    assert "USER 1000" in body
    assert "WORKDIR /home/user/app" in body
    assert 'ENTRYPOINT ["tini", "--"]' in body
    assert "--workers 1" in body


def test_the_build_context_holds_exactly_what_the_image_copies() -> None:
    rules = [r.strip() for r in DOCKERIGNORE.splitlines() if r.strip() and not r.startswith("#")]
    assert rules[0] == "*", "the context must be an allowlist"
    admitted = {r[1:] for r in rules if r.startswith("!")}
    sources = {
        m.group(1)
        for i in _instructions()
        if i.startswith("COPY ") and "--from=" not in i
        for m in [re.search(r"COPY (?:--\S+ )*(\S+) \S+$", i)]
        if m
    }
    assert sources == {"backend/requirements.txt", "backend/app", "rag-corpus"}
    assert sources == admitted, f"copied {sources} but admitted {admitted}"
