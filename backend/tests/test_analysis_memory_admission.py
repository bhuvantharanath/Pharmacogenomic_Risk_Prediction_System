"""Admission must happen before the upload body enters the application."""

from __future__ import annotations

import asyncio
import json

from app.security import AnalysisMemoryGateMiddleware


def test_analysis_admission_serializes_before_body_parsing_and_times_out() -> None:
    async def scenario() -> None:
        entered = asyncio.Event()
        release = asyncio.Event()
        active = 0
        peak = 0

        async def endpoint(scope, receive, send):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            entered.set()
            await release.wait()
            active -= 1
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        app = AnalysisMemoryGateMiddleware(endpoint, wait_seconds=0.04)

        async def request():
            messages = []

            async def send(message):
                messages.append(message)

            async def receive():
                raise AssertionError("the queued request body was read")

            await app({"type": "http", "method": "POST", "path": "/analyze"}, receive, send)
            return messages

        first = asyncio.create_task(request())
        await entered.wait()
        timed_out = await request()
        assert timed_out[0]["status"] == 503
        assert json.loads(timed_out[1]["body"])["error_code"] == "SERVER_BUSY"
        assert active == peak == 1
        release.set()
        assert (await first)[0]["status"] == 200
        assert (await request())[0]["status"] == 200
        assert peak == 1

    asyncio.run(scenario())


def test_non_analysis_path_bypasses_admission() -> None:
    async def endpoint(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"healthy"})

    app = AnalysisMemoryGateMiddleware(endpoint, wait_seconds=0.01)

    async def scenario():
        messages = []
        async def send(message):
            messages.append(message)
        await app({"type": "http", "method": "GET", "path": "/health"},
                  lambda: None, send)
        assert messages[0]["status"] == 200

    asyncio.run(scenario())


def test_coverage_preview_cannot_expand_a_second_upload_during_analysis() -> None:
    async def scenario() -> None:
        entered = asyncio.Event()
        release = asyncio.Event()

        async def endpoint(scope, receive, send):
            if scope["path"] == "/analyze":
                entered.set()
                await release.wait()
            else:
                raise AssertionError("coverage entered while analysis held memory")
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        app = AnalysisMemoryGateMiddleware(endpoint, wait_seconds=0.03)

        async def request(path):
            messages = []

            async def receive():
                raise AssertionError("queued upload body was read")

            async def send(message):
                messages.append(message)

            await app({"type": "http", "method": "POST", "path": path}, receive, send)
            return messages

        first = asyncio.create_task(request("/analyze"))
        await entered.wait()
        waiting_coverage = await request("/coverage")
        assert waiting_coverage[0]["status"] == 503
        assert json.loads(waiting_coverage[1]["body"])["error_code"] == "SERVER_BUSY"
        release.set()
        assert (await first)[0]["status"] == 200

    asyncio.run(scenario())
