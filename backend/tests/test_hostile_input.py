"""
Hostile and malformed input. Specified twice, run neither time until now.

WHAT THIS SUITE ASSERTS

Not "every bad file is rejected" — some of these are legitimately acceptable,
and a suite that demanded 4xx everywhere would be wrong about mixed line endings
and duplicate drug names. What it asserts is the contract that actually matters
on a public upload endpoint:

    never a 5xx           a malformed upload is the user's problem to fix, and
                          a 500 tells them it is ours and gives them nothing
    never a stack trace   a traceback in a response body leaks file paths, the
                          framework version and internal structure
    never a hang          a request that never returns is worse than one that
                          fails, because nothing downstream can time it out
    always actionable     a 4xx that does not say what to do is a dead end

Every case records its real status code so the audit can quote it, and the
assertions are on the invariant rather than on a specific number. Where a status
IS pinned it is because that specific rejection is a documented behaviour.

TEMP-FILE RETENTION

Checked on the same paths. Genomic data is the one thing this project promises
never to persist, and a rejection path that leaves a temp file behind breaks
that promise precisely when something has already gone wrong.
"""

from __future__ import annotations

import gzip
import io
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main

#: A response must never take longer than this. Generous: PharmCAT is stubbed
#: in most of these, and any case that reaches the JVM is rejected before it.
MAX_SECONDS = 60

#: Substrings that betray an internal failure leaking into a response body.
TRACEBACK_MARKERS = (
    "Traceback (most recent call last)", 'File "/', "site-packages",
    "pydantic_core", "raise ", "__init__.py", "asyncio",
)

VALID_HEADER = (
    "##fileformat=VCFv4.2\n"
    "##reference=GRCh38\n"
    "##contig=<ID=chr10,assembly=GRCh38.p14,species=\"Homo sapiens\">\n"
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
)
VALID_ROW = "chr10\t94842866\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, cyp2c19_pm_report):
    """PharmCAT stubbed: these tests are about the door, not the analysis."""

    async def fake(vcf_text: str, *, sample_hint: str = "sample"):
        return cyp2c19_pm_report

    monkeypatch.setattr(main, "run_pharmcat", fake)
    return TestClient(main.app)


def post(client: TestClient, content: bytes, drugs: str = "clopidogrel",
         name: str = "hostile.vcf"):
    return client.post(
        "/analyze",
        files={"file": (name, io.BytesIO(content), "application/octet-stream")},
        data={"drugs": drugs},
    )


def assert_survivable(response, label: str, elapsed: float) -> None:
    """The contract. Applied identically to every case in this file."""
    body = response.text or ""

    assert response.status_code < 500, (
        f"{label}: returned {response.status_code} — a malformed upload must "
        f"never be reported as a server fault.\n{body[:400]}"
    )
    for marker in TRACEBACK_MARKERS:
        assert marker not in body, (
            f"{label}: response body leaks internals ({marker!r}).\n{body[:400]}"
        )
    assert elapsed < MAX_SECONDS, f"{label}: took {elapsed:.1f}s"

    if 400 <= response.status_code < 500:
        try:
            detail = response.json().get("detail", "")
        except ValueError:
            detail = body
        assert isinstance(detail, (str, list)) and detail, (
            f"{label}: {response.status_code} with no explanation"
        )
        if isinstance(detail, str):
            assert len(detail) > 20, (
                f"{label}: {response.status_code} says only {detail!r} — a "
                f"rejection with no remedy is a dead end"
            )


def run_case(client: TestClient, label: str, content: bytes, **kw):
    started = time.perf_counter()
    response = post(client, content, **kw)
    assert_survivable(response, label, time.perf_counter() - started)
    return response


# --------------------------------------------------------------------------- #
# Malformed files
# --------------------------------------------------------------------------- #

def test_truncated_vcf(client: TestClient) -> None:
    """Cut mid-row — the shape a failed download or a full disk produces."""
    truncated = (VALID_HEADER + VALID_ROW * 5)[:-18].encode()
    run_case(client, "truncated", truncated)


def test_a_text_file_renamed_vcf(client: TestClient) -> None:
    body = b"Dear Dr Smith,\n\nPlease find the results attached.\n\nRegards\n"
    r = run_case(client, "text-as-vcf", body)
    assert r.status_code == 400


def test_a_png_renamed_vcf(client: TestClient) -> None:
    """Binary content with a plausible extension."""
    png = (b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + bytes(range(256)) * 8)
    r = run_case(client, "png-as-vcf", png)
    assert r.status_code == 400


def test_gzip_bomb(client: TestClient) -> None:
    """
    A small upload that decompresses enormously. The size cap must apply to the
    DECOMPRESSED stream, or the limit is decorative.
    """
    bomb = gzip.compress(b"\0" * (200 * 1024 * 1024))
    assert len(bomb) < 1024 * 1024, "test premise: the compressed form is small"
    r = run_case(client, "gzip-bomb", bomb, name="bomb.vcf.gz")
    assert r.status_code in (400, 413)


def test_thousands_of_sample_columns(client: TestClient) -> None:
    header = (
        "##fileformat=VCFv4.2\n##reference=GRCh38\n#CHROM\tPOS\tID\tREF\tALT\t"
        "QUAL\tFILTER\tINFO\tFORMAT\t" + "\t".join(f"S{i}" for i in range(5000))
        + "\n"
    )
    row = "chr10\t94842866\t.\tA\tG\t.\tPASS\t.\tGT\t" + "\t".join(
        ["0/1"] * 5000) + "\n"
    run_case(client, "5000-samples", (header + row).encode())


def test_non_utf8_bytes(client: TestClient) -> None:
    """Latin-1 accents in a header. Must not raise a decode error."""
    body = VALID_HEADER.encode() + "##note=caf\xe9 r\xe9sum\xe9\n".encode("latin-1") \
        + VALID_ROW.encode()
    run_case(client, "non-utf8", body)


def test_nul_bytes(client: TestClient) -> None:
    body = VALID_HEADER.encode() + b"chr10\t100\t.\tA\x00\tG\t.\tPASS\t.\tGT\t0/1\n"
    run_case(client, "nul-bytes", body)


@pytest.mark.parametrize("ending,label", [
    ("\r\n", "crlf"), ("\r", "cr-only"), ("\n", "lf"),
])
def test_mixed_line_endings(client: TestClient, ending: str, label: str) -> None:
    """
    Not required to be rejected — a CRLF VCF from Windows is a real file that
    should work. Required only not to explode.
    """
    body = (VALID_HEADER + VALID_ROW * 3).replace("\n", ending).encode()
    run_case(client, f"line-endings-{label}", body)


def test_wrong_species(client: TestClient) -> None:
    mouse = (
        "##fileformat=VCFv4.2\n##reference=GRCm39\n"
        '##contig=<ID=chr10,assembly=GRCm39,species="Mus musculus">\n'
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
        "chr10\t94842866\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n"
    ).encode()
    run_case(client, "wrong-species", mouse)


def test_wrong_contig_naming(client: TestClient) -> None:
    """`10` vs `chr10` — a real and common difference between pipelines."""
    body = (VALID_HEADER + VALID_ROW.replace("chr10", "10")).encode()
    run_case(client, "contig-naming", body)


def test_empty_file(client: TestClient) -> None:
    r = run_case(client, "empty", b"")
    assert r.status_code == 400


def test_whitespace_only_file(client: TestClient) -> None:
    r = run_case(client, "whitespace", b"   \n\t\n   \n")
    assert r.status_code == 400


def test_extremely_long_line(client: TestClient) -> None:
    """One 5 MB INFO field. Line-based parsers fall over here."""
    long_row = ("chr10\t94842866\t.\tA\tG\t.\tPASS\t"
                + "X" * (5 * 1024 * 1024) + "\tGT\t0/1\n")
    run_case(client, "5mb-line", (VALID_HEADER + long_row).encode())


# --------------------------------------------------------------------------- #
# Hostile parameters
# --------------------------------------------------------------------------- #

def test_900_drug_list(client: TestClient) -> None:
    drugs = ",".join(f"drug{i}" for i in range(900))
    r = run_case(client, "900-drugs", (VALID_HEADER + VALID_ROW).encode(),
                 drugs=drugs)
    assert r.status_code == 422, "the documented per-request drug cap"


@pytest.mark.parametrize("drugs,label", [
    ("clopidogrel'; DROP TABLE users;--", "sql"),
    ("clopidogrel; rm -rf /", "shell"),
    ("clopidogrel && cat /etc/passwd", "shell-and"),
    ("clopidogrel$(whoami)", "shell-subst"),
    ("клопидогрель,クロピドグレル,🧬", "unicode"),
    ("../../../../etc/passwd", "traversal"),
    ("<script>alert(1)</script>", "xss"),
])
def test_metacharacters_in_drug_names(client: TestClient, drugs: str,
                                      label: str) -> None:
    """
    None of these should be treated as anything but an unknown drug name. The
    assertion is the survivability contract plus: nothing is echoed back in a
    way that suggests it was interpreted.
    """
    r = run_case(client, f"metachar-{label}", (VALID_HEADER + VALID_ROW).encode(),
                 drugs=drugs)
    assert "root:" not in r.text, "looks like /etc/passwd was read"


def test_duplicate_drug_entries(client: TestClient) -> None:
    r = run_case(client, "duplicates", (VALID_HEADER + VALID_ROW).encode(),
                 drugs="clopidogrel,clopidogrel,clopidogrel")
    if r.status_code == 200:
        drugs = [a["drug"] for a in r.json()["analyses"]]
        assert len(drugs) == len(set(drugs)), (
            f"duplicates were not collapsed: {drugs} — the same result rendered "
            f"three times reads as three separate findings")


def test_empty_and_blank_drug_entries(client: TestClient) -> None:
    run_case(client, "empty-entries", (VALID_HEADER + VALID_ROW).encode(),
             drugs="clopidogrel,,  ,,codeine")


def test_no_drugs_at_all(client: TestClient) -> None:
    r = run_case(client, "no-drugs", (VALID_HEADER + VALID_ROW).encode(), drugs="")
    assert r.status_code in (400, 422)


# --------------------------------------------------------------------------- #
# Concurrency
# --------------------------------------------------------------------------- #

def test_ten_concurrent_uploads(client: TestClient) -> None:
    """
    Ten at once. A shared temp directory, a module-level parser or a
    non-reentrant cache shows up here and nowhere else.
    """
    payload = (VALID_HEADER + VALID_ROW * 20).encode()

    def one(i: int):
        started = time.perf_counter()
        r = post(client, payload, drugs="clopidogrel", name=f"c{i}.vcf")
        return r, time.perf_counter() - started

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(one, range(10)))

    for i, (r, elapsed) in enumerate(results):
        # 429 is a correct answer here, not a failure: the rate limiter doing
        # its job is the opposite of a defect.
        assert r.status_code < 500 or r.status_code == 429, (
            f"concurrent[{i}]: {r.status_code}\n{r.text[:300]}")
        assert elapsed < MAX_SECONDS, f"concurrent[{i}] took {elapsed:.1f}s"


# --------------------------------------------------------------------------- #
# Retention on every one of these paths
# --------------------------------------------------------------------------- #

def test_no_temp_files_survive_any_rejection(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """
    The retention promise has to hold on the FAILURE paths especially — those
    are the ones where an early return can skip a cleanup block.
    """
    private = tmp_path / "tmproot"
    private.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(private))

    cases = [
        b"", b"   \n", b"not a vcf at all, just prose\n",
        b"\x89PNG\r\n\x1a\n" + bytes(range(256)),
        gzip.compress(b"\0" * (50 * 1024 * 1024)),
        (VALID_HEADER + VALID_ROW).encode(),
    ]
    for i, payload in enumerate(cases):
        post(client, payload, name=f"r{i}.vcf")

    leftover = list(private.iterdir())
    assert leftover == [], f"temp files survived: {leftover}"


def test_coverage_preview_survives_the_same_inputs(client: TestClient) -> None:
    """`/coverage` takes the same uploads and must hold the same contract."""
    for label, payload in (
        ("empty", b""),
        ("png", b"\x89PNG\r\n\x1a\n" + bytes(range(256))),
        ("bomb", gzip.compress(b"\0" * (200 * 1024 * 1024))),
        ("long-line", (VALID_HEADER + "chr10\t1\t.\tA\tG\t.\tPASS\t"
                       + "X" * (2 * 1024 * 1024) + "\tGT\t0/1\n").encode()),
    ):
        started = time.perf_counter()
        r = client.post("/coverage",
                        files={"file": (f"{label}.vcf", io.BytesIO(payload),
                                        "application/octet-stream")})
        assert_survivable(r, f"coverage-{label}", time.perf_counter() - started)


# --------------------------------------------------------------------------- #
# Two gaps this suite found on its first run. Encoded as explicit assertions of
# CURRENT behaviour so they are visible in the suite rather than passing
# silently under the survivability contract. Neither is a 5xx, a stack trace or
# a hang — the core contract holds — but both accept a file that should
# arguably be refused. Reported for a decision, not fixed here.
# --------------------------------------------------------------------------- #

def test_GAP_a_mouse_genome_is_currently_accepted(client: TestClient) -> None:
    """
    FINDING: a GRCm39 / `Mus musculus` VCF returns 200, not 4xx.

    Build detection looks for GRCh37-vs-GRCh38 signals; anything else falls to
    UNKNOWN, which is a warning rather than a rejection. A mouse genome cannot
    carry human star alleles, so every position lookup misses and the result is
    a confident set of Unknowns — the failure mode is wasted work rather than a
    wrong call, which is why it has survived.

    Pinned so that if someone adds species validation this test fails and gets
    updated deliberately.
    """
    mouse = (
        "##fileformat=VCFv4.2\n##reference=GRCm39\n"
        '##contig=<ID=chr10,assembly=GRCm39,species="Mus musculus">\n'
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
        "chr10\t94842866\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n"
    ).encode()
    assert post(client, mouse).status_code == 200, (
        "species validation was added — good; update this test to assert the "
        "rejection and remove it from the audit's open-findings list"
    )


def test_GAP_nul_bytes_in_a_data_row_are_currently_accepted(
    client: TestClient,
) -> None:
    """
    FINDING: a NUL byte inside a data row returns 200.

    The binary-content check samples the header region, so a NUL further into
    the file is not seen. Harmless in practice — the row fails to parse as a
    genotype and is ignored — but it means "is this a text file?" is answered
    from a prefix rather than from the whole upload.
    """
    body = (VALID_HEADER.encode()
            + b"chr10\t100\t.\tA\x00\tG\t.\tPASS\t.\tGT\t0/1\n")
    assert post(client, body).status_code == 200
