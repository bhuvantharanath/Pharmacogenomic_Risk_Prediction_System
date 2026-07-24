"""
The faithfulness guard, exercised against **real captured model output**.

WHY THIS FILE IS SEPARATE

Every other guard test in this suite feeds the guard text that this codebase
composed itself — deterministic templates, or hand-written strings designed to
trip a specific rule. Those tests prove the guard's logic. They cannot prove the
guard survives contact with a language model, because a model writes in ways we
did not anticipate when writing the assertions.

These tests close that gap. They read the artifacts a real generation run leaves
behind and re-derive the verdict rather than trusting the one that was recorded:

    backend/app/data/explanations.json    the prose actually shipped to users
    reports/guard_experiment_raw.json     all four adversarial arms, verbatim
    logs/guard_events.jsonl               every evaluation, pass or fail

Re-deriving matters. A recorded `"passed": true` proves only what the guard said
on the day of the run. Re-running the guard now proves the shipped text is still
faithful under the *current* guard, corpus and CPIC fixtures — so a regression in
any of the three surfaces here rather than in production.

UNTIL A RUN HAS HAPPENED

Every class skips with the exact command that produces its input. That is
deliberate: a test that silently passes with no data would report the guard as
validated against real output when it has never seen any. Skipped and loud beats
green and hollow.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

from app.explanation.context import Explanation
from app.explanation.guard import check as guard_check

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"

EXPLANATIONS = REPO_ROOT / "backend" / "app" / "data" / "explanations.json"
EXPERIMENT_RAW = REPO_ROOT / "reports" / "guard_experiment_raw.json"
GUARD_EVENTS = REPO_ROOT / "logs" / "guard_events.jsonl"

RUN_GENERATION = "python scripts/pregenerate_explanations.py --resume"
RUN_EXPERIMENT = "python scripts/guard_experiment.py"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _pregen():
    """Load the generation CLI by path — it is a script, not an installed module."""
    spec = importlib.util.spec_from_file_location(
        "pregenerate_explanations", SCRIPTS / "pregenerate_explanations.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["pregenerate_explanations"] = module
    spec.loader.exec_module(module)
    return module


def _llm_entries() -> list[dict]:
    """Shipped entries that came from a model, not from the template fallback."""
    if not EXPLANATIONS.is_file():
        return []
    entries = json.loads(EXPLANATIONS.read_text()).get("explanations", [])
    return [
        e
        for e in entries
        if str(e.get("generator", "")).startswith("llm") and not e.get("fallback")
    ]


def _experiment_rows() -> list[dict]:
    if not EXPERIMENT_RAW.is_file():
        return []
    return json.loads(EXPERIMENT_RAW.read_text()).get("results", [])


def _guard_events() -> list[dict]:
    if not GUARD_EVENTS.is_file():
        return []
    rows = []
    for line in GUARD_EVENTS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


needs_generation = pytest.mark.skipif(
    not _llm_entries(),
    reason=f"no real model output in the store yet — run: {RUN_GENERATION}",
)
needs_experiment = pytest.mark.skipif(
    not _experiment_rows(),
    reason=f"no captured experiment output yet — run: {RUN_EXPERIMENT}",
)
needs_events = pytest.mark.skipif(
    not _guard_events(),
    reason=f"no guard event log yet — run: {RUN_GENERATION}",
)


# --------------------------------------------------------------------------- #
# The shipped prose
# --------------------------------------------------------------------------- #


@needs_generation
class TestShippedExplanationsAreStillFaithful:
    """
    The load-bearing test of the whole project.

    Every sentence a user reads was written by a model and must contain nothing
    the CPIC context did not supply. Generation-time approval is not enough:
    the guard, the mechanism corpus and the CPIC fixtures all keep changing, and
    prose that was faithful against last month's context may not be against
    this one.
    """

    @pytest.fixture(scope="class")
    def pregen(self):
        return _pregen()

    def test_every_shipped_entry_passes_the_current_guard(self, pregen) -> None:
        failures: list[str] = []
        for entry in _llm_entries():
            case = pregen.Case(entry["drug"], entry["gene"], entry["phenotype"])
            context, _ = pregen.build_context(case)
            report = guard_check(
                Explanation(**entry["explanation"]), context, generator="recheck"
            )
            if not report.passed:
                failures.append(
                    f"{case.key}: " + ", ".join(str(v) for v in report.violations)
                )
        assert not failures, (
            "shipped explanations no longer pass the guard — either the prose or "
            "the context it was grounded on has drifted:\n  " + "\n  ".join(failures)
        )

    def test_the_recorded_verdict_matches_a_fresh_one(self, pregen) -> None:
        """
        Guard determinism.

        Same text plus same context must give the same verdict every time. If it
        does not, the guard depends on something it should not — ordering, a
        mutable default, or the corpus loading differently between runs.
        """
        mismatches: list[str] = []
        for entry in _llm_entries():
            recorded = (entry.get("guard_report") or {}).get("passed")
            if recorded is None:
                continue
            case = pregen.Case(entry["drug"], entry["gene"], entry["phenotype"])
            context, _ = pregen.build_context(case)
            fresh = guard_check(Explanation(**entry["explanation"]), context).passed
            if fresh is not recorded:
                mismatches.append(f"{case.key}: recorded={recorded} fresh={fresh}")
        assert not mismatches, f"guard is not deterministic: {mismatches}"

    def test_shipped_prose_is_not_the_template(self, pregen) -> None:
        """
        Guards against the failure this phase existed to fix.

        Before Phase 5A the field named `llm_generated_explanation` held template
        text, so the guard had only ever validated strings we composed ourselves.
        An entry marked `llm` whose prose is byte-identical to the template would
        be that same misnomer returning.
        """
        from app.explanation import generator_template

        identical: list[str] = []
        for entry in _llm_entries():
            case = pregen.Case(entry["drug"], entry["gene"], entry["phenotype"])
            context, _ = pregen.build_context(case)
            if entry["explanation"] == generator_template.generate(context).fields():
                identical.append(case.key)
        assert not identical, f"entries marked llm are template text: {identical}"

    def test_slot_placeholders_survived_generation(self) -> None:
        """
        One reviewed sentence is reused for every patient sharing a phenotype, so
        patient-specific values must remain placeholders. A model that helpfully
        substituted a concrete diplotype would have baked one patient's genotype
        into everyone's explanation.
        """
        offenders: list[str] = []
        for entry in _llm_entries():
            joined = " ".join(entry["explanation"].values())
            # A literal star-allele diplotype where a placeholder belongs.
            if re.search(r"\*\d+\s*/\s*\*\d+", joined):
                offenders.append(f"{entry['drug']}:{entry['phenotype']}")
        assert not offenders, (
            f"concrete diplotypes baked into reusable prose: {offenders}"
        )

    def test_every_entry_records_what_produced_it(self) -> None:
        """Provenance for the human reviewer: model, prompt fingerprint, verdict."""
        for entry in _llm_entries():
            key = f"{entry['drug']}:{entry['phenotype']}"
            assert entry.get("model"), f"{key} has no model id"
            assert entry.get("prompt_hash"), f"{key} has no prompt hash"
            assert entry.get("generated_at"), f"{key} has no timestamp"
            assert entry.get("guard_report"), f"{key} has no guard report"


# --------------------------------------------------------------------------- #
# The adversarial experiment
# --------------------------------------------------------------------------- #


@needs_experiment
class TestAdversarialArmsCaughtRealFabrication:
    """
    The experiment's claim, re-derived from its own raw output.

    A guard that accepts everything would sail through the grounded arm. Only
    the arms given stripped, corrupted or coaxing context prove it is doing
    anything at all.
    """

    @pytest.fixture(scope="class")
    def rows(self) -> list[dict]:
        return _experiment_rows()

    def test_all_four_arms_produced_output(self, rows: list[dict]) -> None:
        arms = {row["arm"] for row in rows}
        assert arms >= {"grounded", "stripped", "corrupted", "coaxed"}, (
            f"experiment is missing arms: {arms}"
        )

    def test_captured_text_is_real_prose(self, rows: list[dict]) -> None:
        """Cheap sanity check that these are model outputs, not empty stubs."""
        for row in rows:
            if row.get("error"):
                continue
            text = row.get("text") or {}
            assert set(text) == {
                "summary", "mechanism", "variant_rationale", "patient_friendly"
            }, row
            for name, value in text.items():
                if row["arm"] == "grounded":
                    assert value.strip(), f"{row['arm']}/{row['drug']}: {name} is empty"
                    continue
                # Adversarial arms may legitimately yield an empty field. In the
                # 2026-07-24 llama-3.1-8b run the `stripped` arm returned an
                # empty mechanism — given almost no context the model declined
                # to write one rather than inventing biology. That is the
                # behaviour we want; asserting non-empty here would have made
                # correct refusal look like a defect.
                assert isinstance(value, str)

    def test_the_adversarial_arms_were_caught(self) -> None:
        """
        The headline result — read from the durable log, not the raw JSON.

        `guard_experiment_raw.json` holds only the most recent run and is
        overwritten each time; `guard_events.jsonl` is append-only and spans
        every run. On 2026-07-23 that distinction mattered: a partial re-run
        (mostly truncated responses and 429s) overwrote the raw file, leaving no
        rejection in it, while the log still held the real catch. Asserting
        against the overwritable artifact would have reported "the guard never
        caught anything" about a guard that demonstrably did.

        The strict per-run version of this assertion lives in
        `test_captured_outputs.py`, against the captured fixture.
        """
        caught = [e for e in _guard_events() if e.get("passed") is False]
        assert caught, (
            "no guard rejection in logs/guard_events.jsonl — the guard has never "
            "been shown to reject real model output, so the experiment cannot be "
            "cited as validation. Re-run: python scripts/guard_experiment.py"
        )
        for event in caught:
            assert event["violations"], f"a rejection with no violations: {event}"

    def test_violations_name_a_concrete_token(self, rows: list[dict]) -> None:
        """
        A violation must be actionable. `kind` alone tells a reviewer nothing;
        the offending token is what makes a rejection reviewable — and it is what
        the retry prompt feeds back to the model.
        """
        valid_kinds = {"dose", "number", "rsid", "star_allele", "gene", "drug", "slot"}
        for row in rows:
            for violation in row.get("violations") or []:
                assert violation["kind"] in valid_kinds, violation
                assert violation["token"].strip(), violation
                assert violation["field"].strip(), violation

    def test_experiment_output_never_entered_the_store(self, rows: list[dict]) -> None:
        """
        The safety invariant, verified against the artifact rather than the code
        that was supposed to enforce it. Deliberately fabricated clinical text
        exists on disk; the one thing that must never happen is it being served.
        """
        shipped = {
            json.dumps(e["explanation"], sort_keys=True)
            for e in json.loads(EXPLANATIONS.read_text()).get("explanations", [])
        } if EXPLANATIONS.is_file() else set()
        for row in rows:
            if not row.get("text"):
                continue
            fingerprint = json.dumps(row["text"], sort_keys=True)
            assert fingerprint not in shipped, (
                f"experiment output from the {row['arm']!r} arm is in "
                f"explanations.json — this is the worst possible outcome"
            )


# --------------------------------------------------------------------------- #
# The boundary-aware regression, against real text
# --------------------------------------------------------------------------- #


@needs_experiment
class TestBoundaryFixHoldsOnRealText:
    """
    The specific bug that made the guard worthless, re-checked against prose a
    model actually wrote.

    Naive substring matching accepted an invented "50 mg" because the mechanism
    background contains "cytochrome P450", and "P450" contains "50". The unit
    tests cover this with hand-built strings; this covers it with the real thing,
    where "cytochrome P450" appears constantly and entirely legitimately.
    """

    def test_p450_in_real_prose_does_not_whitelist_a_bare_number(self) -> None:
        from app.explanation.guard import _contains

        # Take the mechanism text as it was actually captured, not a fixture.
        haystacks = [
            (row.get("text") or {}).get("mechanism", "") for row in _experiment_rows()
        ]
        relevant = [h for h in haystacks if "P450" in h]
        if not relevant:
            pytest.skip("no captured mechanism text mentions P450")

        for haystack in relevant:
            assert not _contains(haystack, "50", "number"), (
                "boundary matching regressed: 'P450' is again whitelisting a "
                "bare '50', which is how an invented dose got through before"
            )
            assert not _contains(haystack, "50 mg", "dose")

    def test_a_genuinely_present_number_still_matches(self) -> None:
        """
        The other half of the fix. Tightening the match must not make the guard
        reject faithful text — that would push every case to the template and
        quietly undo the phase.
        """
        from app.explanation.guard import _contains

        for row in _experiment_rows():
            if row.get("arm") != "grounded" or row.get("passed") is not True:
                continue
            for value in (row.get("text") or {}).values():
                for number in re.findall(r"(?<![\w.])\d{1,3}(?![\w.])", value):
                    assert _contains(value, number, "number"), (
                        f"guard cannot find {number!r} in text that contains it"
                    )
            return


# --------------------------------------------------------------------------- #
# The event log
# --------------------------------------------------------------------------- #


@needs_events
class TestGuardEventLog:
    """
    The audit trail. Every evaluation is logged, pass or fail — a log that
    recorded only rejections would make the guard look busier than it is, and one
    that recorded only acceptances would hide the failures entirely.
    """

    @pytest.fixture(scope="class")
    def events(self) -> list[dict]:
        return _guard_events()

    def test_events_are_well_formed(self, events: list[dict]) -> None:
        for event in events:
            assert set(event) >= {"timestamp", "source", "case", "model", "passed"}, event
            assert event["source"] in {"pregenerate", "guard_experiment"}, event
            assert isinstance(event["passed"], bool), event

    def test_failed_events_explain_themselves(self, events: list[dict]) -> None:
        for event in events:
            if event["passed"] is False:
                assert event["violations"], (
                    f"a rejection with no violations is unreviewable: {event}"
                )

    def test_the_log_covers_every_shipped_entry(self, events: list[dict]) -> None:
        """No entry may reach the store without having been evaluated."""
        generated = {e["case"] for e in events if e["source"] == "pregenerate"}
        if not generated:
            pytest.skip("no generation events logged yet")
        for entry in _llm_entries():
            key = f"{entry['drug']}:{entry['phenotype']}"
            assert key in generated, f"{key} shipped with no guard event logged"

    def test_no_event_leaks_the_api_key(self, events: list[dict]) -> None:
        """
        The log is committed and quoted in the report. A key that reached it
        would be published.
        """
        raw = GUARD_EVENTS.read_text()
        assert "AQ.Ab8" not in raw, "an API-key-shaped literal is in the guard log"
        assert not re.search(r"AIza[0-9A-Za-z_\-]{35}", raw), "Google API key in log"
