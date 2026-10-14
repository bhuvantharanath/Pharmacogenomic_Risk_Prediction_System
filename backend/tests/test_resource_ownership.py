"""Phase 6 lifecycle, bounded-input, cleanup, and responsiveness regressions."""

from __future__ import annotations

import asyncio
import io
import os
import sys
import time
from pathlib import Path

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from starlette.requests import Request

from app import main
from app import pharmcat_runner as runner
from app import security
from app.vcf_validation import MAX_UPLOAD_BYTES


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


async def _wait_gone(pids: list[int], timeout: float = 2.0) -> list[int]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        alive = [pid for pid in pids if _alive(pid)]
        if not alive:
            return []
        await asyncio.sleep(0.02)
    return [pid for pid in pids if _alive(pid)]


async def _owned_tree(tmp_path: Path) -> tuple[asyncio.Task, list[int]]:
    pidfile = tmp_path / "owned-pids"
    code = (
        "import os,subprocess,time,pathlib; "
        "p=subprocess.Popen(['sleep','60']); "
        f"pathlib.Path({str(pidfile)!r}).write_text(str(os.getpid())+' '+str(p.pid)); "
        "time.sleep(60)"
    )
    task = asyncio.create_task(
        runner._exec_unguarded([sys.executable, "-c", code], cwd=tmp_path)
    )
    for _ in range(100):
        if pidfile.exists():
            return task, [int(value) for value in pidfile.read_text().split()]
        await asyncio.sleep(0.02)
    task.cancel()
    raise AssertionError("owned process tree did not start")


@pytest.mark.skipif(os.name != "posix", reason="process-group assertion is POSIX-specific")
def test_cancellation_terminates_and_reaps_the_owned_process_group(tmp_path: Path) -> None:
    async def scenario() -> list[int]:
        task, pids = await _owned_tree(tmp_path)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return await _wait_gone(pids)

    assert asyncio.run(scenario()) == []


@pytest.mark.skipif(os.name != "posix", reason="process-group assertion is POSIX-specific")
def test_timeout_terminates_and_reaps_the_owned_process_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "PHARMCAT_TIMEOUT_SECONDS", 0.1)

    async def scenario() -> list[int]:
        pidfile = tmp_path / "timeout-pids"
        code = (
            "import os,subprocess,time,pathlib; "
            "p=subprocess.Popen(['sleep','60']); "
            f"pathlib.Path({str(pidfile)!r}).write_text(str(os.getpid())+' '+str(p.pid)); "
            "time.sleep(60)"
        )
        with pytest.raises(runner.PharmcatExecutionError, match="did not finish"):
            await runner._exec_unguarded([sys.executable, "-c", code], cwd=tmp_path)
        pids = [int(value) for value in pidfile.read_text().split()]
        return await _wait_gone(pids)

    assert asyncio.run(scenario()) == []


def test_normal_child_completion_is_reaped(tmp_path: Path) -> None:
    result = asyncio.run(
        runner._exec_unguarded(
            [sys.executable, "-c", "print('complete')"], cwd=tmp_path
        )
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "complete"


@pytest.mark.skipif(os.name != "posix", reason="process-group assertion is POSIX-specific")
def test_normal_completion_does_not_leave_a_daemonized_descendant(tmp_path: Path) -> None:
    pidfile = tmp_path / "background-pid"
    code = (
        "import subprocess,pathlib; "
        "p=subprocess.Popen(['sleep','60'], stdout=subprocess.DEVNULL, "
        "stderr=subprocess.DEVNULL); "
        f"pathlib.Path({str(pidfile)!r}).write_text(str(p.pid))"
    )
    asyncio.run(runner._exec_unguarded([sys.executable, "-c", code], cwd=tmp_path))
    descendant = int(pidfile.read_text())
    assert asyncio.run(_wait_gone([descendant])) == []


class _Upload:
    def __init__(self, chunks: list[bytes], *, size: int | None = None) -> None:
        self.chunks = list(chunks)
        self.size = size
        self.read_calls = 0
        self.bytes_returned = 0
        self.closed = False

    async def read(self, _size: int = -1) -> bytes:
        self.read_calls += 1
        chunk = self.chunks.pop(0) if self.chunks else b""
        self.bytes_returned += len(chunk)
        return chunk

    async def close(self) -> None:
        self.closed = True


def test_declared_oversize_is_rejected_before_reading() -> None:
    upload = _Upload([b"not-read"], size=MAX_UPLOAD_BYTES + 1)
    with pytest.raises(main.ApiError) as caught:
        asyncio.run(main._read_upload_limited(upload))  # type: ignore[arg-type]
    assert caught.value.status_code == 413
    assert upload.read_calls == 0
    assert upload.closed is True


def test_streaming_upload_stops_at_the_cap() -> None:
    chunk = b"x" * main.UPLOAD_READ_CHUNK_BYTES
    upload = _Upload([chunk] * 100, size=None)
    with pytest.raises(main.ApiError) as caught:
        asyncio.run(main._read_upload_limited(upload))  # type: ignore[arg-type]
    assert caught.value.status_code == 413
    assert upload.bytes_returned <= MAX_UPLOAD_BYTES + main.UPLOAD_READ_CHUNK_BYTES
    assert upload.closed is True


def test_coverage_parsing_does_not_block_the_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = main._read_and_validate

    def slow_validation(contents: bytes, filename: str):
        time.sleep(0.2)
        return original(contents, filename)

    monkeypatch.setattr(main, "_read_and_validate", slow_validation)
    vcf = (
        b"##fileformat=VCFv4.2\n##reference=GRCh38\n"
        b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
        b"chr10\t94842866\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n"
    )

    async def scenario() -> float:
        request = Request({
            "type": "http", "method": "POST", "path": "/coverage",
            "headers": [], "client": ("127.0.0.1", 1234),
        })
        upload = UploadFile(file=io.BytesIO(vcf), filename="sample.vcf", size=len(vcf))
        task = asyncio.create_task(main.coverage_preview(request, upload))
        started = time.monotonic()
        await asyncio.sleep(0.02)
        responsiveness = time.monotonic() - started
        await task
        return responsiveness

    assert asyncio.run(scenario()) < 0.1


def test_pharmcat_log_is_confined_to_and_removed_with_owned_temp_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launch = tmp_path / "launch"
    private = tmp_path / "private"
    launch.mkdir()
    private.mkdir()
    monkeypatch.chdir(launch)
    monkeypatch.setattr(runner.tempfile, "tempdir", str(private))

    class _Invoker:
        def build(self, _vcf_path: Path, _output_dir: Path) -> list[str]:
            return [
                sys.executable,
                "-c",
                "from pathlib import Path; Path('pharmcat.log').write_text('synthetic')",
            ]

    monkeypatch.setattr(runner, "resolve_invoker", lambda: _Invoker())
    with pytest.raises(runner.PharmcatExecutionError, match="did not produce"):
        asyncio.run(runner.run_pharmcat("##fileformat=VCFv4.2\n"))

    assert list(launch.iterdir()) == []
    assert list(private.iterdir()) == []


def test_coverage_uses_the_shared_public_workload_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        security, "limiter", security.InMemoryRateLimiter(max_requests=1, window_seconds=300)
    )
    vcf = (
        b"##fileformat=VCFv4.2\n##reference=GRCh38\n"
        b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
        b"chr10\t94842866\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n"
    )
    with TestClient(main.app) as client:
        first = client.post("/coverage", files={"file": ("sample.vcf", vcf)})
        second = client.post("/coverage", files={"file": ("sample.vcf", vcf)})
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error_code"] == "RATE_LIMITED"
