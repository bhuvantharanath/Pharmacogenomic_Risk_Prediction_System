"""
Abuse and privacy hardening (Phase 9 B8, audit/phase9/B8_PLAN.md).

Finding F-04: the per-client limit keyed on Render's internal proxy hops, so
one client spread over several buckets and strangers shared one, and a client
sending back to back could hold the only analysis slot. Finding F-16: a
PharmCAT run that exited non-zero could still be served. And the brief:
deletion of the uploaded VCF on every path, with a test that injects a failure
mid-run, and logs free of genotypes and identifiers.

The PharmCAT failures are injected through the real `Invoker` path, with a
small script standing in for PharmCAT, so the code under test is the code that
runs in production.
"""

from __future__ import annotations

import asyncio
import io
import logging
import re
import sys
import tempfile
import textwrap
import time
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

import app.main as main
from app import pharmcat_runner, security
from app.pharmcat_runner import Invoker, PharmcatExecutionError, remove_workdir, run_pharmcat
from tests.conftest import REPO_ROOT

DEMO = REPO_ROOT / "test-data/demo/demo_confident.vcf"
SECRET_SAMPLE = "SAMPLE-SECRET-77"
SECRET_NAME = "PRIVATE-NAME-9f3a.vcf"


def _request(peer: str, headers: dict[str, str] | list[tuple[str, str]] = ()) -> Request:
    items = headers.items() if isinstance(headers, dict) else headers
    return Request({"type": "http", "method": "POST", "path": "/analyze", "client": (peer, 1234),
                    "headers": [(k.lower().encode(), v.encode()) for k, v in items]})


@pytest.fixture
def render_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "10.0.0.0/8")
    monkeypatch.setenv("CLIENT_IP_HEADER", "cf-connecting-ip")


# --------------------------------------------------------------------------- #
# AC1 — who the client is
# --------------------------------------------------------------------------- #


def test_the_edge_header_names_the_client_behind_a_trusted_hop(render_identity) -> None:
    request = _request("10.1.2.3", {"CF-Connecting-IP": "198.51.100.7"})
    assert security.client_key(request) == "198.51.100.7"
    assert security.identity_is_trusted(request)


def test_the_header_is_ignored_from_an_untrusted_peer(render_identity) -> None:
    request = _request("203.0.113.9", {"CF-Connecting-IP": "198.51.100.7"})
    assert security.client_key(request) == "203.0.113.9"
    assert not security.identity_is_trusted(request)


@pytest.mark.parametrize("headers", [
    {"CF-Connecting-IP": "198.51.100.7, 198.51.100.8"},  # a list
    {"CF-Connecting-IP": "not-an-address"},            # junk
    {},                                                 # missing
    [("CF-Connecting-IP", "198.51.100.7"), ("CF-Connecting-IP", "198.51.100.8")],  # sent twice
])
def test_anything_but_one_valid_address_falls_back_to_the_peer(render_identity, headers) -> None:
    request = _request("10.1.2.3", headers)
    assert security.client_key(request) == "10.1.2.3"
    assert not security.identity_is_trusted(request)


def test_x_forwarded_for_is_never_used_when_a_header_is_named(render_identity) -> None:
    request = _request("10.1.2.3", {"X-Forwarded-For": "198.51.100.9"})
    assert security.client_key(request) == "10.1.2.3"


def test_without_the_setting_the_keys_are_exactly_todays(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLIENT_IP_HEADER", raising=False)
    monkeypatch.delenv("TRUSTED_PROXY_CIDRS", raising=False)
    edge = {"CF-Connecting-IP": "198.51.100.7", "X-Forwarded-For": "198.51.100.9"}
    assert security.client_key(_request("10.1.2.3", edge)) == "10.1.2.3"
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "10.0.0.0/8")
    assert security.client_key(_request("10.1.2.3", edge)) == "198.51.100.9"  # the pre-B8 rule
    assert not security.identity_is_trusted(_request("10.1.2.3", edge))


def test_the_startup_summary_names_the_source_never_an_address(render_identity) -> None:
    summary = security.proxy_trust_summary()
    assert summary["client_identity"] == "header cf-connecting-ip from trusted peers"
    assert "198.51.100" not in str(summary)


# --------------------------------------------------------------------------- #
# AC2 / AC3 — one upload in flight per client, and a capped queue
# --------------------------------------------------------------------------- #


def _gated_app(max_waiting: int = 2):
    """A stand-in /analyze that holds the slot until released, behind the real gate."""
    release, order = asyncio.Event(), []
    inner = FastAPI()

    @inner.post("/analyze")
    async def analyze(request: Request) -> dict:
        tag = request.headers.get("x-tag", "")
        await release.wait()
        order.append(tag)
        return {"tag": tag}

    gate = security.AnalysisMemoryGateMiddleware(inner, wait_seconds=5, max_waiting=max_waiting)
    return gate, release, order


async def _post(gate, tag: str, client_ip: str | None = None) -> httpx.Response:
    headers = {"x-tag": tag}
    if client_ip:
        headers["cf-connecting-ip"] = client_ip
    transport = httpx.ASGITransport(app=gate, client=("10.1.2.3", 1234))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        return await client.post("/analyze", headers=headers)


async def _until(predicate) -> None:
    for _ in range(500):
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition never held")


def test_a_second_upload_from_the_same_client_is_refused_at_once(render_identity) -> None:
    async def scenario():
        gate, release, order = _gated_app()
        first = asyncio.create_task(_post(gate, "a1", "198.51.100.7"))
        await _until(lambda: gate._busy)
        started = time.monotonic()
        second = await _post(gate, "a2", "198.51.100.7")
        refused_in = time.monotonic() - started
        other = asyncio.create_task(_post(gate, "b1", "198.51.100.8"))
        await _until(lambda: len(gate._waiters) == 1)
        release.set()
        return second, refused_in, await first, await other, order

    second, refused_in, first, other, order = asyncio.run(scenario())
    assert second.status_code == 429 and second.json()["error_code"] == "ONE_AT_A_TIME"
    assert second.headers["retry-after"] and refused_in < 1
    assert first.status_code == other.status_code == 200
    assert order == ["a1", "b1"]


def test_without_a_trusted_identity_nobody_is_refused_as_a_repeat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLIENT_IP_HEADER", raising=False)
    monkeypatch.delenv("TRUSTED_PROXY_CIDRS", raising=False)

    async def scenario():
        gate, release, order = _gated_app()
        first = asyncio.create_task(_post(gate, "x1", "198.51.100.7"))
        await _until(lambda: gate._busy)
        second = asyncio.create_task(_post(gate, "x2", "198.51.100.7"))
        await _until(lambda: len(gate._waiters) == 1)
        release.set()
        return await first, await second, order

    first, second, order = asyncio.run(scenario())
    assert first.status_code == second.status_code == 200
    assert order == ["x1", "x2"]


def test_a_third_upload_in_line_is_told_at_once_and_the_line_stays_in_order(monkeypatch) -> None:
    monkeypatch.delenv("CLIENT_IP_HEADER", raising=False)

    async def scenario():
        gate, release, order = _gated_app(max_waiting=2)
        running = asyncio.create_task(_post(gate, "q0"))
        await _until(lambda: gate._busy)
        waiting = [asyncio.create_task(_post(gate, f"q{i}")) for i in (1, 2)]
        await _until(lambda: len(gate._waiters) == 2)
        started = time.monotonic()
        third = await _post(gate, "q3")
        told_in = time.monotonic() - started
        release.set()
        done = [await running] + [await w for w in waiting]
        return third, told_in, done, order

    third, told_in, done, order = asyncio.run(scenario())
    assert third.status_code == 503 and third.json()["error_code"] == "SERVER_BUSY"
    assert third.headers["retry-after"] and told_in < 1
    assert [r.status_code for r in done] == [200, 200, 200]
    assert order == ["q0", "q1", "q2"]


# --------------------------------------------------------------------------- #
# AC4 / AC5 — exit status, and deletion on every path
# --------------------------------------------------------------------------- #


def _fake_pharmcat(tmp_path: Path, body: str) -> Invoker:
    """A stand-in PharmCAT: `body` runs with `vcf` and `out` (Paths) defined."""
    script = tmp_path / "fake_pharmcat.py"
    script.write_text(textwrap.dedent("""
        import json, sys, time
        from pathlib import Path
        vcf = Path(sys.argv[1]); out = Path(sys.argv[sys.argv.index("-o") + 1])
    """) + textwrap.dedent(body))
    return Invoker(kind="wrapper", command_prefix=[sys.executable, str(script)], version_args=[],
                   describe="fake pharmcat")


REPORT = 'out.joinpath("sample.report.json").write_text(json.dumps({"genes": {}}))\n'


def _explode(*_args, **_kwargs):
    raise RuntimeError("injected while building the response")


@pytest.fixture
def temp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "tmproot"
    root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(root))
    return root


def _left(root: Path) -> list[str]:
    return sorted(p.name for p in root.glob("pharmaguard_pharmcat_*"))


def _run(coro):
    return asyncio.run(coro)


def test_a_nonzero_exit_is_not_served_even_with_a_report(tmp_path, temp_root, monkeypatch) -> None:
    monkeypatch.setattr(pharmcat_runner, "resolve_invoker",
                        lambda: _fake_pharmcat(tmp_path, REPORT + "sys.exit(3)\n"))
    with pytest.raises(PharmcatExecutionError) as exc:
        _run(run_pharmcat(DEMO.read_text()))
    assert "status 3" in exc.value.detail
    assert _left(temp_root) == []


def test_the_api_answers_a_nonzero_exit_as_unavailable(tmp_path, temp_root, monkeypatch) -> None:
    monkeypatch.setattr(pharmcat_runner, "resolve_invoker",
                        lambda: _fake_pharmcat(tmp_path, REPORT + "sys.exit(3)\n"))
    response = TestClient(main.app).post(
        "/analyze", files={"file": ("d.vcf", io.BytesIO(DEMO.read_bytes()), "text/plain")},
        data={"drugs": "clopidogrel"})
    assert response.status_code == 503
    assert response.json()["error_code"] == "PHARMCAT_UNAVAILABLE"
    assert _left(temp_root) == []


@pytest.mark.parametrize(("case", "body"), [
    ("no output", "sys.exit(0)\n"),
    ("unreadable report", 'out.joinpath("sample.report.json").write_text("{not json")\n'),
    ("timeout", "time.sleep(30)\n"),
])
def test_a_failed_run_leaves_no_temp_tree(tmp_path, temp_root, monkeypatch, case, body) -> None:
    monkeypatch.setattr(pharmcat_runner, "PHARMCAT_TIMEOUT_SECONDS", 0.5)
    monkeypatch.setattr(pharmcat_runner, "resolve_invoker", lambda: _fake_pharmcat(tmp_path, body))
    with pytest.raises(PharmcatExecutionError):
        _run(run_pharmcat(DEMO.read_text()))
    assert _left(temp_root) == [], case


def test_no_engine_at_all_leaves_no_temp_tree(temp_root, monkeypatch) -> None:
    monkeypatch.setattr(pharmcat_runner, "resolve_invoker", lambda: None)
    with pytest.raises(PharmcatExecutionError):
        _run(run_pharmcat(DEMO.read_text()))
    assert _left(temp_root) == []


def test_a_cancelled_run_leaves_no_temp_tree(tmp_path, temp_root, monkeypatch) -> None:
    monkeypatch.setattr(pharmcat_runner, "resolve_invoker",
                        lambda: _fake_pharmcat(tmp_path, "time.sleep(30)\n"))

    async def scenario():
        task = asyncio.create_task(run_pharmcat(DEMO.read_text()))
        await _until(lambda: _left(temp_root))
        await asyncio.sleep(0.3)  # the child is running
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    _run(scenario())
    assert _left(temp_root) == []


def test_a_failure_after_the_run_leaves_no_temp_tree(temp_root, monkeypatch) -> None:
    if pharmcat_runner.find_jar() is None:  # pragma: no cover
        pytest.skip("PharmCAT jar not found")
    monkeypatch.setattr(main, "build_response", _explode)
    client = TestClient(main.app, raise_server_exceptions=False)
    response = client.post("/analyze", files={"file": ("d.vcf", io.BytesIO(DEMO.read_bytes()), "text/plain")},
                           data={"drugs": "clopidogrel"})
    assert response.status_code == 500
    assert _left(temp_root) == []


def test_a_successful_run_leaves_no_temp_tree(temp_root) -> None:
    if pharmcat_runner.find_jar() is None:  # pragma: no cover
        pytest.skip("PharmCAT jar not found")
    report = _run(run_pharmcat(DEMO.read_text()))
    assert report.genes
    assert _left(temp_root) == []


def test_a_failed_delete_is_retried_then_reported(tmp_path, monkeypatch, caplog) -> None:
    real = pharmcat_runner.shutil.rmtree
    target = tmp_path / "pharmaguard_pharmcat_once"
    target.mkdir()
    (target / "sample.vcf").write_text("x")
    calls = []

    def flaky(path, *args, **kwargs):
        calls.append(path)
        if len(calls) == 1:
            raise PermissionError("busy")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(pharmcat_runner.shutil, "rmtree", flaky)
    with caplog.at_level(logging.WARNING, logger="pharmaguard.pharmcat"):
        assert remove_workdir(target) is True
    assert not target.exists() and len(calls) == 2
    assert "pharmaguard_pharmcat_once" in caplog.text and "sample.vcf" not in caplog.text

    stuck = tmp_path / "pharmaguard_pharmcat_stuck"
    stuck.mkdir()
    monkeypatch.setattr(pharmcat_runner.shutil, "rmtree",
                        lambda *a, **k: (_ for _ in ()).throw(PermissionError("busy")))
    with caplog.at_level(logging.ERROR, logger="pharmaguard.pharmcat"):
        assert remove_workdir(stuck) is False
    assert "could not be removed" in caplog.text


# --------------------------------------------------------------------------- #
# AC6 — logs carry no genotype and no identifier
# --------------------------------------------------------------------------- #

LEAKS = {
    "rsID": re.compile(r"\brs\d{3,}\b"),
    "diplotype": re.compile(r"\*\d+[A-Z]?/\*\d+"),
    "genotype": re.compile(r"(?<![\w.])[01][/|][01](?![\w.])"),
    "sample ID": re.compile(re.escape(SECRET_SAMPLE)),
    "filename": re.compile(re.escape(SECRET_NAME)),
}


def _secret_vcf() -> bytes:
    lines = DEMO.read_text().splitlines()
    out = []
    for line in lines:
        if line.startswith("#CHROM"):
            line = "\t".join(line.split("\t")[:9] + [SECRET_SAMPLE])
        out.append(line)
    return ("\n".join(out) + "\n").encode()


def _leaks(caplog, *outputs: str) -> list[str]:
    """Each record as an operator log shows it (message and any traceback), then any raw output."""
    texts = [(record.name, logging.Formatter().format(record)) for record in caplog.records]
    texts += [("stdout/stderr", output) for output in outputs]
    found = []
    for source, text in texts:
        for name, pattern in LEAKS.items():
            if pattern.search(text):
                found.append(f"{source}: {name} in {text[:120]!r}")
    return found


def test_no_log_line_carries_a_genotype_or_an_identifier(tmp_path, temp_root, monkeypatch, caplog, capfd) -> None:
    """The success path and each AC5 failure path, through the API wherever a request can reach it."""
    caplog.set_level(logging.DEBUG)
    client = TestClient(main.app, raise_server_exceptions=False)

    def post() -> int:
        return client.post("/analyze", files={"file": (SECRET_NAME, io.BytesIO(_secret_vcf()), "text/plain")},
                           data={"drugs": "clopidogrel"}).status_code

    def engine(body: str | None) -> None:
        monkeypatch.setattr(pharmcat_runner, "resolve_invoker",
                            lambda: None if body is None else _fake_pharmcat(tmp_path, body))

    statuses = {}
    if pharmcat_runner.find_jar() is not None:
        statuses["success"] = post()
        with monkeypatch.context() as patch:
            patch.setattr(main, "build_response", _explode)
            statuses["failure while building the response"] = post()
    for case, body in [("no engine", None),
                       ("non-zero exit with a report", REPORT + "sys.exit(3)\n"),
                       ("unreadable report", 'out.joinpath("sample.report.json").write_text("{not json")\n'),
                       ("no output", "sys.exit(0)\n")]:
        engine(body)
        statuses[case] = post()
    engine("time.sleep(30)\n")
    with monkeypatch.context() as patch:
        patch.setattr(pharmcat_runner, "PHARMCAT_TIMEOUT_SECONDS", 0.5)
        statuses["timeout"] = post()

    async def cancelled() -> None:  # TestClient cannot cancel a request; the runner gets what /analyze passes
        task = asyncio.create_task(run_pharmcat(_secret_vcf().decode(), sample_hint=SECRET_SAMPLE))
        await _until(lambda: _left(temp_root))
        await asyncio.sleep(0.3)  # the child is running
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    _run(cancelled())
    out, err = capfd.readouterr()
    failures = {case: status for case, status in statuses.items() if case != "success"}
    assert statuses.get("success", 200) == 200
    assert failures.pop("failure while building the response", 500) == 500
    assert failures == dict.fromkeys(["no engine", "non-zero exit with a report", "unreadable report",
                                      "no output", "timeout"], 503)
    assert caplog.records, "no log record at all: the capture is not seeing the paths under test"
    assert _leaks(caplog, out, err) == []


def test_the_leak_check_would_see_a_leak() -> None:
    """Positive control for the patterns above: in a message, in a traceback, and in raw output."""
    record = logging.LogRecord("x", logging.WARNING, __file__, 1,
                               "rs4244285 *2/*2 0/1 %s %s", (SECRET_SAMPLE, SECRET_NAME), None)
    try:
        raise ValueError(f"no call for {SECRET_SAMPLE}")
    except ValueError:
        traced = logging.LogRecord("x", logging.ERROR, __file__, 1, "analysis failed", None, sys.exc_info())

    class Capture:
        records = [record]

    class Traced:
        records = [traced]

    class Nothing:
        records = []

    assert len(_leaks(Capture())) == 5
    assert len(_leaks(Traced())) == 1
    assert len(_leaks(Nothing(), f"upload {SECRET_NAME}\n")) == 1
