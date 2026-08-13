"""
Concurrent /analyze must not run two JVMs, hang, or die ambiguously.

WHY THIS EXISTS

`reports/memory_measurement.md` (2026-08-13) measured peak resident memory of
the whole process tree while N analyses were in flight at the tightest heap
setting that does not OOM:

    1 request   322 MB      2 requests   594 MB      3 requests   910 MB

The deployment target is a 512 MB Render instance. Two concurrent analyses
exceed it. On a small host the second request does not return an error — the
kernel OOM-kills the container and every in-flight request dies with it,
including the one that had nearly finished.

One uvicorn worker never bounded this. A worker is an event loop, and
`asyncio.create_subprocess_exec` yields to the loop while the JVM runs, so a
single worker holds N subprocesses quite happily. The bound is the semaphore in
`pharmcat_runner`, and these tests are what stop it being removed by someone who
reads "one worker" and concludes it is redundant.

WHAT IS ASSERTED, AND WHY IT IS NOT THE OBVIOUS THING

Not "the response is 200". A gate that rejected every second request would pass
that, and so would a gate that silently ran both. The observable properties are:

  * never more than MAX_CONCURRENT_PHARMCAT invocations overlap in time;
  * every request terminates — with a result, or a clean 503 carrying
    Retry-After and error_code SERVER_BUSY, never a hang;
  * busy is distinguishable from broken, at the wire level, by a client.
"""

from __future__ import annotations

import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from app import main as main_mod
from app import pharmcat_runner as runner


@pytest.fixture(autouse=True)
def _reset_slots():
    """Each test gets a fresh gate; a leaked permit must not cross tests."""
    runner._pharmcat_slots = None
    runner._slots_loop = None
    yield
    runner._pharmcat_slots = None
    runner._slots_loop = None


class Overlap:
    """Records how many fake invocations were in flight at once."""

    def __init__(self) -> None:
        self.current = 0
        self.peak = 0
        self.started = 0

    async def invoke(self, _command, hold: float = 0.15):
        self.started += 1
        self.current += 1
        self.peak = max(self.peak, self.current)
        try:
            await asyncio.sleep(hold)
            return runner.PharmcatInvocation(
                command=["fake"], returncode=0, stdout="", stderr="")
        finally:
            self.current -= 1


async def _drive(n: int, hold: float, monkeypatch) -> Overlap:
    tracker = Overlap()

    async def fake_unguarded(command):
        return await tracker.invoke(command, hold=hold)

    monkeypatch.setattr(runner, "_exec_unguarded", fake_unguarded)
    await asyncio.gather(*[runner._exec(["fake"]) for _ in range(n)])
    return tracker


# --------------------------------------------------------------------------- #
# The gate itself
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("n", [2, 3, 8])
def test_never_more_than_the_limit_run_at_once(monkeypatch, n: int) -> None:
    """
    THE MEMORY PROPERTY. Peak RSS is a function of this number and nothing else,
    so this is the assertion that stands between the deployment and an OOM kill.
    """
    tracker = asyncio.run(_drive(n, hold=0.05, monkeypatch=monkeypatch))
    assert tracker.started == n, "some invocation never ran at all"
    assert tracker.peak <= runner.MAX_CONCURRENT_PHARMCAT, (
        f"{tracker.peak} JVMs overlapped with "
        f"MAX_CONCURRENT_PHARMCAT={runner.MAX_CONCURRENT_PHARMCAT}; two "
        f"measured 594 MB against a 512 MB instance")


def test_queued_requests_still_complete(monkeypatch) -> None:
    """Serialised, not dropped. A gate that sheds load is a different product."""
    tracker = asyncio.run(_drive(4, hold=0.05, monkeypatch=monkeypatch))
    assert tracker.started == 4


def test_the_wait_is_bounded_and_reports_busy(monkeypatch) -> None:
    """
    The refinement that matters most at the client: a bounded wait. An
    indefinite one is indistinguishable from a crash to whoever is watching a
    spinner, so exhaustion has to produce a *message*, not silence.
    """
    monkeypatch.setattr(runner, "PHARMCAT_QUEUE_TIMEOUT_SECONDS", 0.2)

    async def scenario():
        async def slow(_command):
            await asyncio.sleep(5)

        monkeypatch.setattr(runner, "_exec_unguarded", slow)
        holder = asyncio.create_task(runner._exec(["fake"]))
        await asyncio.sleep(0.05)  # let it take the only permit

        started = time.monotonic()
        with pytest.raises(runner.PharmcatBusyError) as caught:
            await runner._exec(["fake"])
        waited = time.monotonic() - started

        holder.cancel()
        return caught.value, waited

    error, waited = asyncio.run(scenario())
    assert waited < 2.0, f"waited {waited:.1f}s — the bound did not apply"
    assert error.retry_after > 0
    # It says nothing is wrong with the upload, because nothing is.
    assert "nothing is wrong with your file" in str(error).lower()


def test_the_permit_is_returned_when_the_invocation_raises(monkeypatch) -> None:
    """
    A leaked permit is permanent: every later request waits the full queue
    timeout and then reports a busy server that is in fact completely idle.
    Release therefore lives in `finally`, and this is what pins it there.
    """
    async def scenario():
        calls = {"n": 0}

        async def boom(_command):
            calls["n"] += 1
            raise RuntimeError("PharmCAT fell over")

        monkeypatch.setattr(runner, "_exec_unguarded", boom)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await runner._exec(["fake"])

        # If the permit leaked, this acquire times out instead of succeeding.
        await asyncio.wait_for(runner._slots().acquire(), timeout=1.0)
        runner._slots().release()
        return calls["n"]

    assert asyncio.run(scenario()) == 3


def test_busy_is_a_subclass_so_ordering_of_except_clauses_matters() -> None:
    """
    `PharmcatBusyError` extends `PharmcatExecutionError`, so a handler that
    catches the parent first swallows the child and reports every queue wait as
    a dead analysis backend. main.py orders them child-first; this records why
    that ordering is load-bearing rather than stylistic.
    """
    assert issubclass(runner.PharmcatBusyError, runner.PharmcatExecutionError)

    source = (main_mod.__file__ and open(main_mod.__file__).read()) or ""
    busy = source.find("except PharmcatBusyError")
    generic = source.find("except PharmcatExecutionError")
    assert busy != -1 and generic != -1
    assert busy < generic, (
        "main.py catches PharmcatExecutionError before PharmcatBusyError — "
        "every busy response will read as PHARMCAT_UNAVAILABLE")


# --------------------------------------------------------------------------- #
# The wire contract a client branches on
# --------------------------------------------------------------------------- #

def test_the_busy_response_carries_retry_after_and_its_own_code(monkeypatch) -> None:
    """
    Three different waits — cold start, rate limit, server busy — must be three
    different things on the wire, or the client cannot tell the user which one
    they are in.
    """
    async def busy(*_args, **_kwargs):
        raise runner.PharmcatBusyError("The server is busy. Nothing is wrong "
                                       "with your file.", retry_after=30)

    monkeypatch.setattr(main_mod, "run_pharmcat", busy)

    vcf = (main_mod.Path(__file__).resolve().parents[2]
           / "test-data/demo/demo_confident.vcf")
    with TestClient(main_mod.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/analyze",
            files={"file": ("demo.vcf", vcf.read_bytes(), "text/plain")},
            data={"drugs": ["clopidogrel"]},
        )

    assert response.status_code == 503
    assert response.json()["error_code"] == "SERVER_BUSY", (
        "busy must not be reported as PHARMCAT_UNAVAILABLE — one means try "
        "again shortly, the other means this deployment is broken")
    assert response.headers.get("Retry-After") == "30"


def test_a_real_backend_failure_still_reports_unavailable(monkeypatch) -> None:
    """The other side of the branch, so the codes cannot collapse into one."""
    async def broken(*_args, **_kwargs):
        raise runner.PharmcatExecutionError("PharmCAT could not be run.")

    monkeypatch.setattr(main_mod, "run_pharmcat", broken)

    vcf = (main_mod.Path(__file__).resolve().parents[2]
           / "test-data/demo/demo_confident.vcf")
    with TestClient(main_mod.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/analyze",
            files={"file": ("demo.vcf", vcf.read_bytes(), "text/plain")},
            data={"drugs": ["clopidogrel"]},
        )

    assert response.status_code == 503
    assert response.json()["error_code"] == "PHARMCAT_UNAVAILABLE"
    assert "Retry-After" not in response.headers


# --------------------------------------------------------------------------- #
# The single-worker assertion
# --------------------------------------------------------------------------- #

def test_multiple_workers_are_refused(monkeypatch) -> None:
    """
    An asyncio.Semaphore is per process. Four workers means four gates, each
    allowing one JVM — the exact state the gate exists to prevent, while looking
    correct in the source.
    """
    monkeypatch.setattr(main_mod.sys, "argv",
                        ["uvicorn", "app.main:app", "--workers", "4"])
    with pytest.raises(RuntimeError, match="PER PROCESS"):
        main_mod._assert_single_worker()


@pytest.mark.parametrize("argv,env,expected", [
    (["uvicorn", "app.main:app", "--workers", "3"], {}, 3),
    (["uvicorn", "app.main:app", "--workers=2"], {}, 2),
    (["uvicorn", "app.main:app", "-w", "5"], {}, 5),
    (["uvicorn", "app.main:app"], {"WEB_CONCURRENCY": "4"}, 4),
    (["uvicorn", "app.main:app"], {}, None),
])
def test_the_worker_count_is_read_from_every_place_it_can_come_from(
    monkeypatch, argv, env, expected
) -> None:
    """
    Render sets WEB_CONCURRENCY; a Dockerfile CMD passes --workers. Reading only
    one of them would leave the gate defeated by the other, silently.
    """
    monkeypatch.setattr(main_mod.sys, "argv", argv)
    for var in ("WEB_CONCURRENCY", "UVICORN_WORKERS", "GUNICORN_WORKERS"):
        monkeypatch.delenv(var, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert main_mod._configured_workers() == expected


def test_one_worker_is_accepted(monkeypatch) -> None:
    monkeypatch.setattr(main_mod.sys, "argv",
                        ["uvicorn", "app.main:app", "--workers", "1"])
    main_mod._assert_single_worker()  # must not raise
