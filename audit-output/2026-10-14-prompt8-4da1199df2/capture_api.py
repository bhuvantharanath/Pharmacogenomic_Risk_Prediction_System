"""Audit-only passive recorder around the unmodified production ASGI app.

Every ASGI message is forwarded unchanged. For each HTTP request it records the
response status/body bytes and, for multipart uploads, the SHA-256 of the file
part and the submitted form fields, so a browser upload can be bound to an
evidence-table fixture by checksum. Lives outside production code by design.
"""
from __future__ import annotations

import datetime
import email.parser
import email.policy
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.main import app as production_app  # noqa: E402

OUT = Path(os.environ.get("CAPTURE_DIR", str(HERE / "api-captures")))


def _multipart(content_type: str, body: bytes) -> list[dict]:
    if not content_type.startswith("multipart/form-data") or not body:
        return []
    message = email.parser.BytesParser(policy=email.policy.HTTP).parsebytes(
        b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + body
    )
    parts = []
    for part in message.iter_parts():
        payload = part.get_payload(decode=True) or b""
        record = {
            "name": part.get_param("name", header="content-disposition"),
            "filename": part.get_filename(),
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        if part.get_filename() is None and len(payload) < 4096:
            record["value"] = payload.decode("utf-8", "replace")
        parts.append(record)
    return parts


class Capture:
    def __init__(self, inner):
        self.inner = inner
        self.n = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.inner(scope, receive, send)
            return
        self.n += 1
        number = self.n
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        request_chunks: list[bytes] = []
        response_chunks: list[bytes] = []
        status = None
        response_headers = {}

        async def recording_receive():
            message = await receive()
            if message["type"] == "http.request":
                request_chunks.append(message.get("body", b""))
            return message

        async def recording_send(message):
            nonlocal status, response_headers
            if message["type"] == "http.response.start":
                status = message["status"]
                response_headers = {
                    k.decode(): v.decode() for k, v in message.get("headers", [])
                }
            elif message["type"] == "http.response.body":
                response_chunks.append(message.get("body", b""))
            await send(message)

        try:
            await self.inner(scope, recording_receive, recording_send)
        finally:
            headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
            request = b"".join(request_chunks)
            raw = b"".join(response_chunks)
            OUT.mkdir(parents=True, exist_ok=True)
            name = f"{number:04d}-{scope['method'].lower()}-{scope['path'].strip('/') or 'root'}"
            (OUT / f"{name}.body").write_bytes(raw)
            try:
                parts = _multipart(headers.get("content-type", ""), request)
            except Exception as exc:  # recorder must never affect the response
                parts = [{"parse_error": f"{type(exc).__name__}: {exc}"}]
            receipt = {
                "n": number,
                "started": started,
                "finished": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "method": scope["method"],
                "path": scope["path"],
                "query": scope.get("query_string", b"").decode(),
                "client": list(scope.get("client") or []),
                "request_headers": {
                    k: headers[k]
                    for k in ("origin", "user-agent", "content-type", "content-length", "sec-ch-ua")
                    if k in headers
                },
                "request_body_bytes_read": len(request),
                "request_body_sha256": hashlib.sha256(request).hexdigest(),
                "multipart_parts": parts,
                "status": status,
                "response_headers": response_headers,
                "response_bytes": len(raw),
                "response_sha256": hashlib.sha256(raw).hexdigest(),
            }
            (OUT / f"{name}.receipt.json").write_text(json.dumps(receipt, indent=1) + "\n")


app = Capture(production_app)
