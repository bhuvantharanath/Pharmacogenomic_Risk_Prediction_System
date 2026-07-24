"""
The guard and the provenance verifier, exercised against **real captured output**.

WHY THIS FILE EXISTS

Every other guard test in this suite feeds the guard text this codebase composed
itself — templates, or strings hand-written to trip a specific rule. Those prove
the logic. They cannot prove the guard survives contact with a language model,
because a model writes in ways nobody anticipated when writing the assertions.

The fixture here is a verbatim capture of the 2026-07-23 run:

    tests/fixtures/captured/gemini_3_6_flash_2026-07-23.json

Nothing in it is hand-written. It holds prose the model actually produced, the
guard's verdict on that prose, and — deliberately — the run's failures. That run
mostly did not work: of 12 experiment calls, 5 returned truncated JSON, 4 hit the
free-tier quota, and 3 produced usable text. Keeping the failures as fixtures is
the point. They are what a real free-tier run looks like, and two of these tests
exist only because of them.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.explanation.context import Explanation
from app.explanation.guard import check as guard_check

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
CAPTURED = (
    Path(__file__).parent / "fixtures" / "captured" / "gemini_3_6_flash_2026-07-23.json"
)

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def captured() -> dict:
    assert CAPTURED.is_file(), f"missing capture fixture: {CAPTURED}"
    return json.loads(CAPTURED.read_text())


# --------------------------------------------------------------------------- #
# Provenance of the fixture itself
# --------------------------------------------------------------------------- #


class TestTheFixtureIsReal:
    """
    A fixture claiming to be captured model output has to prove it.

    Hand-written "model output" is the exact failure this file exists to avoid:
    it would let the guard be validated against text written by someone who
    already knew what the guard checks.
    """

    def test_it_records_the_model_and_capture_date(self, captured: dict) -> None:
        assert captured["model"] == "gemini-3.6-flash"
        assert captured["captured_at"].startswith("2026-07-23")
        assert "guard_events.jsonl" in captured["capture_source"]["guard_events"]

    def test_it_preserves_the_run_failures(self, captured: dict) -> None:
        """
        The run mostly failed and the fixture says so.

        A capture that kept only the successes would misrepresent what a
        free-tier run does, and would have hidden the token-ceiling bug.
        """
        assert captured["api_failures"], "a capture with no failures is not this run"
        assert "truncated" in captured["run_notes"]
        assert "429" in captured["run_notes"]


# --------------------------------------------------------------------------- #
# Faithful output that PASSES
# --------------------------------------------------------------------------- #


class TestRealPassingGenerationsStillPass:
    def test_there_is_at_least_one(self, captured: dict) -> None:
        assert captured["passing_generations"], "no captured passing generation"

    def test_they_are_prose_not_stubs(self, captured: dict) -> None:
        for row in captured["passing_generations"]:
            text = row["text"]
            assert set(text) == {
                "summary", "mechanism", "variant_rationale", "patient_friendly"
            }
            for name, value in text.items():
                assert len(value.split()) >= 5, f"{row['arm']}/{name}: too short to be prose"

    def test_the_guard_still_accepts_them(self, captured: dict) -> None:
        """
        Re-derived, not trusted.

        A recorded `passed: true` proves what the guard said on the day. Running
        it now proves the text is still acceptable under the *current* guard —
        so a regression in matching surfaces here rather than in production.
        """
        pregen = _load_script("pregenerate_explanations")
        for row in captured["passing_generations"]:
            case = pregen.Case(row["drug"], row["gene"], row["phenotype"])
            context, _ = pregen.build_context(case)
            report = guard_check(Explanation(**row["text"]), context, generator="recheck")
            assert report.passed, (
                f"{row['arm']}/{case.key} passed at capture time but fails now: "
                + ", ".join(str(v) for v in report.violations)
            )


# --------------------------------------------------------------------------- #
# Real fabrication that FAILS
# --------------------------------------------------------------------------- #


class TestRealFabricationWasCaught:
    """
    The guard's whole claim, evidenced by a real catch.

    Sourced from `logs/guard_events.jsonl` rather than the experiment's raw
    JSON. The log is append-only and spans every run; the raw JSON holds only
    the most recent one, and a later partial run overwrote the run that produced
    this catch. Reading the durable record instead of the overwritable one is
    also simply the more honest choice of evidence.
    """

    def test_the_guard_caught_a_real_fabrication(self, captured: dict) -> None:
        caught = captured["guard_caught"]
        assert caught, (
            "no captured guard rejection — the guard has never been shown to "
            "reject real model output, and cannot be cited as validated"
        )

    def test_the_catch_names_concrete_invented_tokens(self, captured: dict) -> None:
        """A rejection with no token is unreviewable, and cannot drive the retry."""
        valid = {"dose", "number", "rsid", "star_allele", "gene", "drug", "slot"}
        for event in captured["guard_caught"]:
            assert event["violations"], f"rejection with no violations: {event}"
            for violation in event["violations"]:
                assert violation["kind"] in valid, violation
                assert violation["token"].strip(), violation
                assert violation["field"].strip(), violation

    def test_the_corrupted_arm_is_what_got_caught(self, captured: dict) -> None:
        """
        The catch came from the arm fed deliberately fabricated CPIC text, and
        the tokens caught are the ones that were planted. That rules out a
        coincidental rejection of something unrelated.
        """
        corrupted = [e for e in captured["guard_caught"] if e.get("arm") == "corrupted"]
        assert corrupted, "the corrupted arm produced no rejection"
        tokens = {v["token"] for e in corrupted for v in e["violations"]}
        planted = _load_script("guard_experiment").CORRUPT_TEXT
        assert tokens, "no tokens recorded"
        for token in tokens:
            assert token in planted, (
                f"{token!r} was flagged but is not in the planted corrupt text — "
                "the catch may be incidental rather than the fabrication"
            )


# --------------------------------------------------------------------------- #
# The token-ceiling bug this run exposed
# --------------------------------------------------------------------------- #


class TestTruncationIsDiagnosedNotMisreported:
    """
    A regression test for the defect that cost the run.

    `max_output_tokens=2048` was shared with the model's thinking budget, so
    responses were cut off mid-JSON. Every failure surfaced as
    `Invalid JSON: EOF while parsing a string at line 4 column 84` — true, and
    pointing at the parser rather than the ceiling that caused it. The
    misdiagnosis is what made it expensive.
    """

    def test_the_captured_failures_are_the_truncation_signature(self, captured: dict) -> None:
        truncated = [f for f in captured["api_failures"] if "EOF while parsing" in f["error"]]
        assert truncated, "expected the captured truncation failures"

    def test_thinking_is_disabled_and_the_ceiling_is_generous(self) -> None:
        from app.explanation import generator_llm

        assert generator_llm.THINKING_BUDGET == 0, (
            "thinking tokens compete with the answer under a finite ceiling"
        )
        assert generator_llm.MAX_OUTPUT_TOKENS >= 4096

    def test_a_truncated_response_names_the_real_cause(self) -> None:
        from app.explanation.generator_llm import (
            LlmUnavailableError,
            _reject_if_truncated,
        )

        response = SimpleNamespace(
            candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="MAX_TOKENS"))],
            usage_metadata=SimpleNamespace(
                thoughts_token_count=1988, candidates_token_count=60
            ),
        )
        with pytest.raises(LlmUnavailableError) as excinfo:
            _reject_if_truncated(response)

        message = str(excinfo.value)
        assert "ceiling" in message and "cut off" in message
        assert "1988 thinking tokens" in message, "the diagnostic number must be shown"
        assert "JSON" not in message.replace("mid-JSON", ""), (
            "must not read as a parsing problem — that is the misdiagnosis"
        )

    def test_a_normal_response_is_untouched(self) -> None:
        from app.explanation.generator_llm import _reject_if_truncated

        _reject_if_truncated(
            SimpleNamespace(
                candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))],
                usage_metadata=SimpleNamespace(
                    thoughts_token_count=0, candidates_token_count=420
                ),
            )
        )
        _reject_if_truncated(SimpleNamespace(candidates=[]))


# --------------------------------------------------------------------------- #
# Failure degrades, never fabricates
# --------------------------------------------------------------------------- #


class TestApiFailureDegradesToTemplate:
    """
    What the pipeline did when the model failed 9 times out of 12.

    The requirement is not that generation succeeds — free tiers fail. It is
    that failure produces honest template text, marked as such, rather than a
    gap or an invention.
    """

    def test_the_failed_case_fell_back_and_says_so(self, captured: dict) -> None:
        entries = captured["template_fallback_entries"]
        assert entries, "the failed generation left no fallback record"
        for entry in entries:
            assert entry["fallback"] is True
            assert entry["generator"] == "template", "a fallback must not claim to be LLM output"
            assert entry["fallback_reason"], "a fallback with no reason is unauditable"
            assert entry["attempts"] >= 2, "must have retried before giving up"

    def test_the_fallback_reason_records_the_real_error(self, captured: dict) -> None:
        for entry in captured["template_fallback_entries"]:
            assert "API error" in entry["fallback_reason"]

    def test_no_fallback_reason_leaks_the_api_key(self, captured: dict) -> None:
        """These strings are committed, so a leaked key here would be published."""
        blob = json.dumps(captured)
        assert "AQ.Ab8" not in blob
        assert not re.search(r"AIza[0-9A-Za-z_\-]{35}", blob)


# --------------------------------------------------------------------------- #
# Provenance verification against captured prose
# --------------------------------------------------------------------------- #


class TestProvenanceVerifierOnCapturedText:
    @pytest.fixture(scope="class")
    def verifier(self):
        return _load_script("verify_provenance")

    def test_a_planted_unsourced_clinical_sentence_fails(self, verifier) -> None:
        """
        The release gate's reason for existing.

        A dose that appears in no source must fail, whatever else is true of the
        entry. If this ever passes, the gate is decorative.
        """
        entry = {
            "drug": "clopidogrel", "gene": "CYP2C19", "phenotype": "PM",
            "derived_risk_label": "Ineffective",
            "cpic_recommendation_used": "Avoid clopidogrel if possible.",
            "explanation": {
                "summary": "Reduce the starting dose to 25 mg twice daily.",
                "mechanism": "", "variant_rationale": "", "patient_friendly": "",
            },
        }
        result = verifier.verify_entry(entry, *verifier.load_paraphrases())
        assert not result.clinical_ok
        # The verifier now reports the unsupported *assertion*, not a bare word:
        # the field-level policy flags "quantity:'25 mg'" because that dose
        # appears nowhere in the source with that unit.
        unsupported = {w for s in result.failures for w in s.untraced}
        assert any("25 mg" in w for w in unsupported), unsupported

    def test_a_planted_invented_risk_claim_fails(self, verifier) -> None:
        entry = {
            "drug": "simvastatin", "gene": "SLCO1B1", "phenotype": "PM",
            "derived_risk_label": "Toxic",
            "cpic_recommendation_used": "Consider a lower dose or an alternative statin.",
            "explanation": {
                "summary": "This drug causes fatal rhabdomyolysis in most patients.",
                "mechanism": "", "variant_rationale": "", "patient_friendly": "",
            },
        }
        result = verifier.verify_entry(entry, *verifier.load_paraphrases())
        assert not result.clinical_ok

    def test_a_paraphrase_on_the_wrong_label_fails(self, verifier) -> None:
        """
        The subtle one. The sentence is declared — just not for this result.
        Telling a patient with a Toxic result that nothing needs to change is
        the most dangerous thing this system could do, and it would sail through
        any check that only asked "is this string approved somewhere?".
        """
        labels, phenotypes = verifier.load_paraphrases()
        safe_wording = next(s for s, label in labels.items() if label == "Safe")
        entry = {
            "drug": "azathioprine", "gene": "TPMT", "phenotype": "PM",
            "derived_risk_label": "Toxic",
            "cpic_recommendation_used": "Consider an alternative agent.",
            "explanation": {
                "summary": "", "mechanism": "", "variant_rationale": "",
                "patient_friendly": safe_wording,
            },
        }
        result = verifier.verify_entry(entry, labels, phenotypes)
        assert not result.clinical_ok
        assert any("label=Safe" in w for s in result.failures for w in s.untraced)

    def test_captured_model_prose_is_classified_not_crashed(
        self, verifier, captured: dict
    ) -> None:
        """
        Robustness against real prose.

        The classifier was written against template text. Model output has
        different rhythm, and a sentence splitter that chokes on it would make
        the gate unreliable exactly when it starts mattering.
        """
        labels, phenotypes = verifier.load_paraphrases()
        classified = 0
        for row in captured["passing_generations"]:
            for text in row["text"].values():
                for sentence in verifier.split_sentences(text):
                    kind = verifier.classify(sentence, labels, phenotypes)
                    assert kind in {
                        verifier.CLINICAL, verifier.LABEL_PARAPHRASE,
                        verifier.PHENOTYPE_PARAPHRASE, verifier.MECHANISM,
                        verifier.PROCESS, verifier.FRAMING,
                    }
                    classified += 1
        assert classified >= 10, "too little captured prose to be a real check"

    def test_the_shipped_store_passes_the_gate(self, verifier) -> None:
        """The release gate, run against what would actually ship."""
        store = json.loads(
            (REPO_ROOT / "backend" / "app" / "data" / "explanations.json").read_text()
        )
        results = verifier.verify_all(store["explanations"])
        failures = [
            f"{r.key}: {s.text[:60]}" for r in results for s in r.failures
        ]
        assert not failures, "unverified clinical content would ship:\n  " + "\n  ".join(failures)
