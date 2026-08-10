"""
The glossary coverage audit — extractor, definition rule, and gate.

WHY THIS FILE MATTERS

The audit exists because two artifacts were each verified against their own
source and never against each other. A test suite that only checked the
extractor runs would repeat that mistake one level up: the point is not that the
code executes, it is that the gate actually fails when vocabulary goes
undefined.

So the load-bearing tests here are the sabotage ones — a planted undefined term
must fail the gate, and a circular definition must be refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

spacy = pytest.importorskip("spacy")
pytest.importorskip("wordfreq")

import glossary_lib as g  # noqa: E402

if not spacy.util.is_package("en_core_web_sm"):  # pragma: no cover
    pytest.skip("en_core_web_sm not installed", allow_module_level=True)


def snip(text: str) -> list[g.Snippet]:
    return [g.Snippet(text, "test")]


# --------------------------------------------------------------------------- #
# The extractor: catches domain terms, leaves ordinary English alone
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("term, sentence", [
    ("prodrug", "Clopidogrel is a prodrug that the body must switch on."),
    ("enzyme", "The enzyme converts the drug into its active form."),
    ("metabolite", "Active metabolites build up in the blood."),
    ("myelosuppression", "Severe myelosuppression can follow a standard dose."),
    ("pyrimidine", "The pyrimidine pathway clears this medicine."),
])
def test_a_domain_term_is_caught(term: str, sentence: str) -> None:
    """The words that actually appear in the shipped prose."""
    assert term in g.extract(snip(sentence)), f"{term!r} slipped past the scan"


@pytest.mark.parametrize("sentence", [
    "The doctor will start you on a lower dose in the morning.",
    "Take this medicine with food and water every day.",
    "Your result may change what your doctor decides to do next.",
])
def test_ordinary_english_is_left_alone(sentence: str) -> None:
    """
    Not a claim that the extractor is quiet in general — it is measurably not,
    at 41.5% on a control corpus. It is a claim that plain clinical instructions
    in everyday words produce nothing to sort.
    """
    assert g.extract(snip(sentence)) == {}


def test_only_nouns_are_considered() -> None:
    """
    Adjectives and verbs are excluded. The mechanism vocabulary check measured
    them as its largest noise source (57% -> 30% FP when narrowed to nouns), and
    that measurement is why this extractor never looks at them.
    """
    found = g.extract(snip("The genetic result was effectively metabolised."))
    assert "genetic" not in found
    assert "effectively" not in found


def test_the_threshold_is_the_one_that_was_pre_committed() -> None:
    """
    Sabotage check. Raising this silences terms rather than defining them, which
    is exactly what `glossary_precommitment.md` forbids.
    """
    assert g.ZIPF_THRESHOLD == 4.0
    assert g.KEEP_POS == frozenset({"NOUN", "PROPN"})


# --------------------------------------------------------------------------- #
# Source collection
# --------------------------------------------------------------------------- #


def test_the_shipped_explanations_are_actually_scanned() -> None:
    """The corpus that started this. If it stops being read, the audit is a no-op."""
    sources = {s.source for s in g.collect_snippets()}
    assert any(s.startswith("explanations.json[") for s in sources)
    assert any("unknown_reason.dart" in s for s in sources)
    assert any("about_screen.dart" in s for s in sources)
    # The definitions themselves: a definition that introduces new jargon is the
    # same defect one level down.
    assert any("glossary.dart" in s for s in sources)


def test_docstrings_and_comments_are_not_treated_as_user_facing() -> None:
    """
    They are written for maintainers. Scanning them would bury the real gaps
    under this project's own long design commentary.
    """
    texts = [s.text for s in g.collect_snippets()]
    assert not any("WHY THIS LAYER EXISTS" in t for t in texts)
    assert not any("sabotage" in t.lower() for t in texts)


def test_a_stylesheet_is_not_prose() -> None:
    """
    The printable summary embeds a CSS sheet as a Dart string. It is long,
    mostly letters and full of spaces, so it passes every naive prose heuristic
    while being read by nobody — it contributed `consolas`, `menlo` and `tbody`
    before it was excluded.
    """
    css = "body { font: 10.5pt Georgia, serif; color: #000; background: #fff; }"
    assert not g._is_prose(css)
    assert g._is_prose(
        "Your body clears this medicine more slowly than most people do.")


# --------------------------------------------------------------------------- #
# A definition may not lean on an undefined term
# --------------------------------------------------------------------------- #


def test_a_circular_definition_is_refused() -> None:
    """
    "A diplotype is your pair of star alleles" is accurate, passes any review
    that only checks correctness, and is useless to the one person who would
    ever tap it.
    """
    gaps = g.definition_gaps(
        "diplotype", "Your pair of star alleles, one per chromosome.")
    assert "chromosome" in gaps


def test_a_self_standing_definition_is_accepted() -> None:
    assert g.definition_gaps(
        "diplotype",
        "The two versions of a gene you carry, one from each parent.") == []


def test_a_definition_may_use_an_already_defined_term() -> None:
    """
    `poor metaboliser` is defined, so `intermediate metaboliser` may refer to
    it. A defined dependency is one tap away; an undefined one is a dead end.
    """
    assert g.definition_gaps(
        "intermediate metaboliser",
        "Your body clears this medicine more slowly than most people, but not "
        "as slowly as a poor metaboliser.") == []


def test_a_definition_may_use_the_word_it_defines() -> None:
    """Ordinary English, not circularity — the term is defined by then."""
    assert g.definition_gaps(
        "variant",
        "A spot where your DNA differs from the version most people carry. "
        "Most variants change nothing.") == []


def test_sentence_counting_backs_the_length_rule() -> None:
    assert g.sentence_count("One sentence.") == 1
    assert g.sentence_count("One. Two.") == 2


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #


def test_the_gate_fails_on_a_planted_undefined_term(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The sabotage test this file exists for. A regeneration that introduces new
    vocabulary must show up, not pass quietly.
    """
    import glossary_status

    planted = "A rare thiopurine metabolite drives the observed zygosity."
    monkeypatch.setattr(g, "collect_snippets", lambda: snip(planted))
    monkeypatch.setattr(glossary_status.g, "collect_snippets", lambda: snip(planted))
    monkeypatch.setattr(glossary_status.g, "defined_forms", set)
    monkeypatch.setattr(glossary_status.g, "decided_ordinary", set)
    monkeypatch.setattr(glossary_status.g, "decided_defined", set)
    monkeypatch.setattr(glossary_status.g, "load_decisions", lambda: {"decisions": {}})
    monkeypatch.setattr(sys, "argv", ["glossary_status.py", "--gate", "--quiet"])

    assert glossary_status.main() == 1


def test_the_gate_passes_when_everything_is_answered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import glossary_status

    clean = "Take this medicine with food and water every day."
    monkeypatch.setattr(glossary_status.g, "collect_snippets", lambda: snip(clean))
    monkeypatch.setattr(glossary_status.g, "load_decisions", lambda: {"decisions": {}})
    monkeypatch.setattr(sys, "argv", ["glossary_status.py", "--gate", "--quiet"])

    assert glossary_status.main() == 0


def test_the_gate_also_fails_a_circular_definition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Editing glossary.dart directly bypasses the review tool's check. The gate
    re-runs it, so the rule cannot be skipped by taking a different route.
    """
    import glossary_status

    monkeypatch.setattr(glossary_status.g, "collect_snippets",
                        lambda: snip("Take this with water."))
    monkeypatch.setattr(glossary_status.g, "load_decisions", lambda: {
        "decisions": {
            "diplotype": {
                "decision": "define",
                "definition": "Your pair of star alleles, one per chromosome.",
                "decided_by": "Test Person",
            }
        }
    })
    monkeypatch.setattr(sys, "argv", ["glossary_status.py", "--gate", "--quiet"])

    assert glossary_status.main() == 1


# --------------------------------------------------------------------------- #
# Decisions are human, attributed, and never written automatically
# --------------------------------------------------------------------------- #


def test_no_decision_may_be_recorded_without_a_real_name() -> None:
    """
    The same guard the adjudication store carries. A false attribution in an
    academic artifact is the one outcome worse than an unsorted term.
    """
    import glossary_review

    for placeholder in ("Claude", "TBD", "automated", "reviewer", "AI"):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sys, "argv",
                       ["glossary_review.py", "--reviewer", placeholder])
            assert glossary_review.main() == 2, placeholder


def test_the_review_tool_offers_no_bulk_accept() -> None:
    """
    Deciding a word needs no explanation is a judgement about a reader. An
    --accept-all would defeat the point rather than speed it up.
    """
    # Match the declared flags, not the prose. The module docstring says
    # "there is no --accept-all", which a substring search reads as one.
    import ast

    source = (REPO / "scripts" / "glossary_review.py").read_text()
    flags: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and \
                getattr(node.func, "attr", "") == "add_argument":
            flags.update(a.value for a in node.args
                         if isinstance(a, ast.Constant) and isinstance(a.value, str))

    assert flags == {"--reviewer", "--drafts", "--limit", "--category"}, flags
    for forbidden in ("--accept-all", "--yes", "--auto", "--all"):
        assert forbidden not in flags


def test_recorded_decisions_carry_who_and_when() -> None:
    """Every decision on disk names a person and a time, or it is not a record."""
    if not g.DECISIONS_PATH.exists():
        pytest.skip("no decisions recorded yet")
    for term, record in json.loads(
            g.DECISIONS_PATH.read_text()).get("decisions", {}).items():
        assert record.get("decided_by"), term
        assert record.get("decided_at"), term
        assert record.get("decision") in {"define", "ordinary"}, term


# --------------------------------------------------------------------------- #
# The pre-commitment is a fact on disk, not a claim in a report
# --------------------------------------------------------------------------- #


def test_the_precommitment_records_the_branch_before_the_number() -> None:
    text = (REPO / "reports" / "glossary_precommitment.md").read_text()
    assert "FP rate < 25%" in text
    assert "FP rate ≥ 25%" in text
    assert "will not be moved to obtain a green result" in text


def test_the_control_corpus_is_vendored_so_the_rate_is_reproducible() -> None:
    """
    A false-positive rate measured against something that has to be downloaded
    is a rate nobody can check. It ships.
    """
    assert g.CONTROL_CORPUS.exists()
    assert len(g.CONTROL_CORPUS.read_text()) > 100_000
