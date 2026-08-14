"""
Numbers in prose must match what the code actually does. Re-derived here.

WHY THIS EXISTS — THREE STALE VALUES, NOT ONE

  1. PROJECT_STATUS said NA12273 was "2/2 exact". CYP2C9 is not: we decline
     where consensus asserts `*1/*2`.
  2. README repeated it twice — once in the results table, once in the External
     concordance paragraph.
  3. README said "DPYD passes at 37.3% coverage with 0% error". After the
     position-identity requirement it is gated at 8 of 28 critical positions.

All three went stale the same way: a number was measured once, typed into prose,
and then the behaviour behind it changed. Nothing connected the sentence to the
thing it described, so nothing could go red.

**So this gates the class, not the instances.** Every value below is re-derived
from the live pipeline at test time and compared against what the documentation
asserts. Adding a new claim of this kind without a check here is the failure
mode; the tests are written so that a doc edit contradicting behaviour fails.

WHAT IS AND IS NOT IN SCOPE

In scope: numbers a reader would take as a statement about how the system
behaves — per-gene coverage, gate outcomes, external concordance, test counts.

Not in scope: numbers inside GENERATED reports
(`decision_critical_positions.md`, `glossary_candidates.md`,
`adjudication_worksheet.md`). Those are re-emitted by their scripts and cannot
drift from the code independently — checking them here would test the generator
twice and add nothing.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from app import coverage

REPO = Path(__file__).resolve().parents[2]
NA12273 = REPO / "test-data/demo/demo_na12273_1000g.vcf"

DOCS = ("README.md", "PROJECT_STATUS.md", "docs/input_requirements.md",
        "reports/validation_report.md")


def _text(name: str) -> str:
    path = REPO / name
    return path.read_text() if path.exists() else ""


def _all_docs() -> str:
    return "\n".join(_text(name) for name in DOCS)


#: Words that mark a sentence as RETRACTING a claim rather than making one.
#:
#: A plain substring check cannot tell "DPYD passes at 37.3%" from "the old
#: reading, that DPYD passes at 37.3%, is wrong" — and this project deliberately
#: keeps its corrections visible rather than deleting the mistake, so the
#: forbidden phrase legitimately appears inside the sentence that retracts it.
#: Without this the guard would forbid documenting the fix.
_RETRACTION = ("earlier", "previously", "overstated", "old reading", "went stale",
               "no longer", "was wrong", "is corrected", "used to", "before the")


def _asserts(phrase: str) -> list[str]:
    """
    Sentences that state `phrase` as fact, ignoring ones that retract it.
    """
    hits = []
    for name in DOCS:
        for sentence in re.split(r"(?<=[.!?])\s+|\n", _text(name)):
            if phrase not in sentence:
                continue
            if any(marker in sentence.lower() for marker in _RETRACTION):
                continue
            hits.append(f"{name}: {sentence.strip()[:140]}")
    return hits


def _asserts_matching(pattern: str) -> list[str]:
    """
    `_asserts` by regex. Needed because the stale claims were not one phrase
    repeated — they were the same statement in three different wordings, and a
    literal list only ever covers the spellings already found.
    """
    rx = re.compile(pattern, re.I)
    hits = []
    for name in DOCS:
        for sentence in re.split(r"(?<=[.!?])\s+|\n", _text(name)):
            if not rx.search(sentence):
                continue
            if any(marker in sentence.lower() for marker in _RETRACTION):
                continue
            hits.append(f"{name}: {sentence.strip()[:140]}")
    return hits


@pytest.fixture(scope="module")
def na12273():
    if not NA12273.exists():  # pragma: no cover
        pytest.skip("NA12273 demo file absent")
    return coverage.assess(NA12273.read_text())


# --------------------------------------------------------------------------- #
# NA12273 — the sample whose documented result went stale
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("gene,present,required", [
    ("SLCO1B1", 20, 35),
    ("CYP2C19", 16, 35),
    ("DPYD", 31, 83),
    ("CYP2C9", 17, 88),
    ("TPMT", 9, 45),
    ("NUDT15", 5, 20),
])
def test_the_documented_per_gene_coverage_is_what_the_code_produces(
    na12273, gene: str, present: int, required: int
) -> None:
    """
    The figures printed in `input_requirements.md` and `validation_report.md`,
    re-derived. If the slice, the requirements table or the parser changes,
    these numbers change and the documentation has to change with them.
    """
    actual = na12273.genes[gene]
    assert (actual.present, actual.required) == (present, required), (
        f"{gene}: code says {actual.present}/{actual.required}, this test (and "
        f"the docs) say {present}/{required}")

    documented = f"{present}/{required}"
    percent = round(actual.percent, 1)

    # PER FILE, not against the concatenation. Checking the join let a wrong
    # percentage in one document pass because another document still carried
    # the right pairing — found by planting `31/83 (99.9%)` and watching the
    # guard stay green.
    for name in DOCS:
        text = _text(name)
        if documented not in text:
            continue
        assert re.search(rf"{re.escape(documented)}\s*\(\s*{percent}\s*%\s*\)",
                         text), (
            f"{name} quotes {gene} as {documented} but not with {percent}% — "
            f"the pair went out of step in this file")


def test_every_gene_is_gated_on_this_sample_and_the_docs_do_not_claim_otherwise(
    na12273,
) -> None:
    """
    THE THIRD STALE VALUE. README said "DPYD passes at 37.3% coverage"; after
    the position-identity requirement DPYD is gated at 8 of 28 critical
    positions, and every other gene was already gated.
    """
    passing = [g for g, c in na12273.genes.items() if c.sufficient]
    assert not passing, f"{passing} now pass on NA12273 — the docs say gated"

    # BY PATTERN, not by literal phrase. The first version listed the two
    # exact spellings it had seen; a third, "Only DPYD clears its bar", sat in
    # docs/input_requirements.md and sailed past both. Any sentence asserting
    # that DPYD passes has to fail, however it is worded.
    claims = _asserts_matching(
        r"(?:only\s+)?DPYD\b[^.\n]{0,60}\b(?:passes|passing|clears|clearing|"
        r"meets its|above the|exceeds)\b"
        r"|\bonly\s+DPYD\b"
        r"|DPYD\s*\|[^|\n]*\|[^|\n]*\|\s*passes")
    assert not claims, (
        "a document still asserts that DPYD passes the gate. On NA12273 it "
        "carries 8 of 28 decision-critical positions and is gated:\n  "
        + "\n  ".join(claims))


def test_dpyd_decision_critical_coverage_is_as_documented(na12273) -> None:
    """`8 of 28` appears in the validation report and the findings document."""
    dpyd = na12273.genes["DPYD"]
    assert (dpyd.critical_present, dpyd.critical_required) == (8, 28)

    docs = _all_docs()
    if "decision-critical" in docs:
        assert re.search(r"\b8\s*(?:of|/)\s*28\b", docs), (
            "the DPYD decision-critical figure is quoted differently from "
            f"{dpyd.critical_present} of {dpyd.critical_required}")


def test_no_document_claims_na12273_is_fully_concordant() -> None:
    """
    The original stale claim, in every spelling it appeared in. CYP2C19 is
    concordant; CYP2C9 is a REFUSAL — we report `Undetermined` where consensus
    asserts `*1/*2`. It is neither a match nor an error.
    """
    for phrase in ("2/2 exact", "2 / 2 exact", "2/2 concordant",
                   "CYP2C9 `*1/*2` exact"):
        stated = _asserts(phrase)
        assert not stated, (
            f"{phrase!r} is stated as fact. NA12273 CYP2C9 is a conservative "
            f"refusal, not a match — see reports/predeploy_audit_a.md:\n  "
            + "\n  ".join(stated))


def test_the_guard_distinguishes_a_claim_from_a_retraction() -> None:
    """
    The guard's own premise. Its first version forbade the phrase anywhere,
    which failed on this project's own corrections — the fix is documented by
    quoting the mistake, so a blunt substring check would forbid writing the
    fix down. Pinned so nobody re-blunts it.
    """
    assert _RETRACTION, "the retraction markers are gone"
    # A retraction present in the real docs must not register as a claim.
    assert not _asserts("2/2 exact"), (
        "a retraction is being read as an assertion")
    # And the docs really do still contain the phrase, inside a retraction —
    # otherwise this test proves nothing.
    assert "2/2 exact" in _all_docs(), (
        "the correction that quotes the old claim has been deleted; this guard "
        "is now vacuous")


def test_the_conservative_direction_is_stated_not_just_the_divergence() -> None:
    """
    A bare "CYP2C9 diverges" would read as an error. The direction is the whole
    point: declining is the safe failure, and saying so is what stops a reader
    counting it as a wrong call.
    """
    # SENTENCE level. Asking only whether the word appears somewhere in the
    # file passed even after the direction was struck from the claim itself,
    # because "conservative" survived elsewhere in the document — found by
    # deleting it from the External-concordance passage and watching this stay
    # green. The direction has to travel with the claim it qualifies.
    for name in ("README.md", "PROJECT_STATUS.md"):
        # Only sentences that ASSERT divergence need the qualifier. One that
        # already says "we decline" has stated the direction by saying it.
        claims = [s for s in re.split(r"(?<=[.!?])\s+|\n", _text(name))
                  if "CYP2C9" in s and "diverg" in s.lower()]
        assert claims, f"{name} no longer states the CYP2C9 divergence at all"
        for sentence in claims:
            lowered = sentence.lower()
            assert any(marker in lowered for marker in
                       ("conservativ", "refusal", "undetermined", "declin")), (
                f"{name} states the CYP2C9 divergence without its direction — "
                f"a bare 'diverges' reads as a wrong call:\n  "
                f"{sentence.strip()[:160]}")


# --------------------------------------------------------------------------- #
# Other derived numbers
# --------------------------------------------------------------------------- #

def test_the_documented_test_counts_match_the_suite() -> None:
    """
    README quotes both suites. These drift every time anyone adds a test, which
    is exactly why they need a check rather than a habit.
    """
    documented = re.search(r"\|\s*Backend tests\s*\|\s*\*?\*?(\d+)",
                           _text("README.md"))
    if documented is None:
        pytest.skip("README no longer quotes a backend test count")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         "-p", "no:warnings"],
        cwd=REPO / "backend", capture_output=True, text=True, timeout=900)

    # `--collect-only -q` prints "path: N" per file and NO total line. An
    # earlier version regexed for "N tests collected", never matched, and
    # skipped — so a stale count of 560 against an actual 739 went unnoticed.
    # A guard that skips on a parse failure is a guard that reports success
    # when it has checked nothing.
    counts = [int(n) for n in re.findall(r":\s*(\d+)\s*$", result.stdout, re.M)]
    assert counts, (
        f"could not parse pytest collection output — this check must fail "
        f"loudly rather than skip:\n{result.stdout[-400:]}")
    actual = sum(counts)
    claimed = int(documented.group(1))
    # Collection counts every test including skips, so allow the small gap
    # between collected and passed rather than pinning an exact equality that
    # would fail on an environment-dependent skip.
    assert abs(claimed - actual) <= 10, (
        f"README says {claimed} backend tests; the suite collects {actual}")


def test_the_label_mapping_figures_match_the_validator() -> None:
    """`92/105` and `13 divergences` appear in README and PROJECT_STATUS."""
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/validate_label_mapping.py"), "--json"],
        cwd=REPO, capture_output=True, text=True, timeout=900)
    if result.returncode not in (0, 1) or not result.stdout.strip():
        pytest.skip("validator unavailable (needs the PharmCAT jar)")

    import json
    data = json.loads(result.stdout)
    agree, total = data["agreements"], data["combinations"]
    diverge = data["disagreements"]

    docs = _all_docs()
    for spelling in (f"{agree}/{total}", f"{agree} / {total}"):
        if spelling in docs:
            break
    else:
        pytest.fail(f"no document quotes the current {agree}/{total}")

    assert re.search(rf"\b{diverge}\b\s*(?:accepted\s+|documented\s+)?diverg",
                     docs), f"the divergence count is not documented as {diverge}"


def test_generated_reports_are_excluded_and_that_is_deliberate() -> None:
    """
    Documents the scope boundary so the next person does not "helpfully" add
    them. A generated report cannot drift from the code independently — it is
    re-emitted by the code.
    """
    generated = ("decision_critical_positions.md", "glossary_candidates.md",
                 "adjudication_worksheet.md", "escalation_list.md")
    for name in generated:
        assert not any(name in doc for doc in DOCS), (
            f"{name} is generated; checking it here tests the generator twice")


# --------------------------------------------------------------------------- #
# About-screen copy — the only behaviour-derived numbers a PATIENT reads
#
# These were outside the guard until the sweep that produced it. They are the
# highest-consequence instance of the class: every other number here is read by
# a developer or an examiner who can go and check it.
# --------------------------------------------------------------------------- #

ABOUT = REPO / "app/lib/screens/about_screen.dart"


def _about() -> str:
    return ABOUT.read_text() if ABOUT.exists() else ""


def test_the_about_screen_wrong_call_rate_matches_the_sweep() -> None:
    """
    "at 60% position coverage, up to 28.6% of calls came back confidently
    wrong" — re-derived as the worst per-gene rate at that coverage level. If
    the sweep is re-run and the maximum moves, this sentence has to move.
    """
    import json
    data = json.loads((REPO / "reports/coverage_sensitivity.json").read_text())
    at_60 = {k.split("|")[0]: v
             for k, v in data["confidently_wrong_rate"].items()
             if k.endswith("|60")}
    assert at_60, "the sweep no longer reports a 60% coverage level"

    worst = max(at_60.values())
    quoted = re.search(r"up to (\d+\.?\d*)% of calls came back", _about())
    assert quoted, "the About screen no longer quotes a wrong-call rate"
    assert abs(float(quoted.group(1)) - worst * 100) < 0.1, (
        f"About says up to {quoted.group(1)}% confidently wrong at 60% "
        f"coverage; the sweep's worst gene is {worst * 100:.1f}% "
        f"({max(at_60, key=at_60.get)})")


def test_the_about_screen_cyp2d6_claim_matches_the_negative_control() -> None:
    """
    "Across 400 test samples it declined every single time." A single
    fabricated CYP2D6 call makes this sentence false, and it is the strongest
    safety claim the app makes to a patient.
    """
    quoted = re.search(r"Across (\d+) test samples", _about())
    assert quoted, "the About screen no longer quotes the CYP2D6 control"
    claimed = int(quoted.group(1))

    import json
    # SUBSCRIPT, not .get(key, default). The first version read
    # `fidelity.get("samples", n)` — the key is `samples_with_report`, so the
    # default won and the assertion reduced to `n <= n`. Planting 9999 left it
    # green. A missing key must raise, not quietly satisfy the check.
    fidelity = json.loads((REPO / "reports/integration_fidelity.json").read_text())
    assert claimed == fidelity["samples_with_report"], (
        f"About tells the user {claimed} samples; the cohort run covers "
        f"{fidelity['samples_with_report']}")

    # And "declined every single time" is a property of the CODE, not just of
    # that one run: PharmCAT reports CYP2D6 with callSource NONE from an
    # unphased VCF, which the runner maps to NOT_ATTEMPTED and attaches the
    # caveat to. A cohort figure alone would go stale the moment the cohort did.
    from app.pharmcat_runner import CYP2D6_WARNING
    runner = (REPO / "backend/app/pharmcat_runner.py").read_text()
    assert 'symbol == "CYP2D6" and status is CallStatus.NOT_ATTEMPTED' in runner, (
        "the CYP2D6 no-call path moved; the About screen promises the user it "
        "declines every time")
    assert "cannot be resolved" in CYP2D6_WARNING


# --------------------------------------------------------------------------- #
# The adjudication gate — the fourth stale derived value found
#
# README said "55 outstanding" long after it was 19. Same shape as the other
# three: measured once, typed into prose, left behind when the work moved.
#
# This one matters more than a test count. The number quantifies how much
# unreviewed clinical prose ships, so a stale one understates or overstates the
# single most consequential open item in the project.
# --------------------------------------------------------------------------- #

def _adjudication_status() -> str:
    """
    The gate's own output.

    The exit code is DELIBERATELY not asserted: this gate exits non-zero by
    design while sentences remain escalated, so a non-zero status is the
    expected state, not a failure. What must be checked is that it produced a
    summary at all — an earlier version returned `result.stdout` unconditionally
    and the caller skipped when the text was missing, so a crashed script made
    the guard silently not run. That is the same "skip on parse failure"
    defect this file already fixed once for the test-count check.
    """
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/adjudication_status.py")],
        cwd=REPO, capture_output=True, text=True, timeout=300)
    if "outstanding" not in result.stdout:
        raise AssertionError(
            "adjudication_status.py produced no summary — this check must fail "
            "loudly rather than skip, or a broken gate reads as a passing one.\n"
            f"exit={result.returncode}\nstdout={result.stdout[-400:]!r}\n"
            f"stderr={result.stderr[-400:]!r}")
    return result.stdout


def test_the_documented_adjudication_counts_are_current() -> None:
    """Re-derived from the gate itself, not from memory of a past run."""
    output = _adjudication_status()
    outstanding = re.search(r"outstanding\s+(\d+)", output)
    sentences = re.search(r"claim sentences\s+(\d+)", output)
    assert outstanding and sentences

    docs = _all_docs()
    n_out, n_sent = outstanding.group(1), sentences.group(1)

    # ADJACENT, not merely nearby. A 60-character window reached across
    # clauses and reported "124 adjudicated by a person" as an outstanding
    # count, because the sentence went on to mention escalation. At most two
    # words may sit between the number and the word it qualifies.
    pattern = re.compile(
        r"\b(\d+)\b(?:\s+\*{0,2}\w+\*{0,2}){0,2}\s+"
        r"(?:escalat|outstanding|undecided)", re.I)

    # Present at least once…
    claimed = {m.group(1) for name in DOCS for m in pattern.finditer(_text(name))}
    assert n_out in claimed, (
        f"the gate reports {n_out} outstanding; no document says so. A stale "
        f"count here misstates how much unreviewed clinical prose ships")

    # …AND nowhere contradicted. Asserting only presence let a wrong number
    # sit beside a right one and pass — the same weakness as checking the
    # concatenation of all docs instead of each file. A guard that tolerates a
    # contradiction is not checking the number, only that it appears.
    wrong = claimed - {n_out}
    assert not wrong, (
        f"the gate reports {n_out} outstanding, but the documentation also "
        f"claims {sorted(wrong)}. One of them is stale")

    assert n_sent in docs, f"{n_sent} claim sentences is not documented"


def test_no_document_claims_the_gate_is_green_or_the_review_complete() -> None:
    """
    The gate is red BY DECISION: there is no qualified clinical reviewer on the
    project, so clearing it would assert a review that did not happen. Prose
    must not quietly promote "escalated" into "done".
    """
    for phrase in ("adjudication complete", "fully adjudicated",
                   "all sentences decided", "clinically reviewed",
                   "reviewed by a clinician"):
        stated = _asserts(phrase)
        assert not stated, (
            f"{phrase!r} is stated as fact. 19 sentences are escalated and "
            f"undecided, and the gate records clinical expert NOT_OBTAINED:\n  "
            + "\n  ".join(stated))


def test_the_gate_still_reports_no_clinical_reviewer() -> None:
    """
    If this ever stops being true, the framing above needs rewriting rather
    than the assertion deleting — a reviewer arriving is the good outcome, and
    the docs should then say so.
    """
    assert "NOT_OBTAINED" in _adjudication_status(), (
        "the gate no longer reports clinical expert NOT_OBTAINED — if a "
        "reviewer has been obtained, update README's adjudication section")
