#!/usr/bin/env python3
"""
Field-level provenance verification — flags candidates for human adjudication.

    python scripts/verify_provenance.py              # table + report, exit code
    python scripts/verify_provenance.py --json
    python scripts/verify_provenance.py --only clopidogrel -v

WHAT CHANGED, AND WHY

This script used to require every content word of a sentence to appear in the
source. `reports/provenance_diagnosis.md` records what that actually measured:
a faithful paraphrase FAILED, while a sentence that *contradicted* the source
PASSED because it reused the vocabulary. Of 16 failures on real model output,
15 were false positives and none was a fabricated claim. It scored copying, and
the template's 100% was true by construction rather than by merit.

It now applies `app.explanation.provenance`, which gives each field the rule it
actually needs:

    clinical_recommendation   VERBATIM — byte-identical to PharmCAT's output.
                              Never model-authored.
    summary / mechanism /     CLAIM-LEVEL — wording may differ; every clinical
    variant_rationale         ASSERTION must trace. mechanism also traces to the
                              cited mechanism corpus.
    patient_friendly          NO NEW CLAIMS — paraphrase is expected (rendering
                              "leukopenia" as "low white blood cell count" is the
                              point of the field); it may not introduce a dose,
                              timeline, probability, comparative risk or
                              mechanism the source does not support.

Declared paraphrases in `label_paraphrases.yaml` keep their exact-match rule and
must match THIS entry's own label/phenotype, so the "Safe" wording on a Toxic
result still fails.

WHAT THIS IS AND IS NOT

It is a **filter**, not a verdict. It flags sentences whose claims it cannot
source. It cannot detect a reversed claim assembled from sourced concepts —
"increased activity" where the source says decreased still matches the direction
family. Negation and direction-of-effect need a reader.

That is why the release gate is now `scripts/adjudication_status.py`: this script
narrows twenty entries down to the handful of sentences a person must actually
look at, and the person decides. With a pre-generated set that is tractable —
which is the whole payoff of pre-generating rather than generating per request.

No LLM is used as a judge anywhere here. Using a model to certify a model is
circular, and it would spend quota to answer a question that documented rules
answer more predictably.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from _common import (
    EXPLANATIONS_PATH,
    REPO_ROOT,
    REPORTS_DIR,
    bold,
    dim,
    green,
    load_json,
    red,
    rule,
    write_json_atomic,
    yellow,
)

from app.explanation.provenance import (
    CLAIM_LEVEL,
    CORPUS_BACKED,
    FIELD_POLICY,
    check_sentence,
)
from app.retrieval import retrieve_mechanism

#: Bumped when classification or tracing changes, so a recorded
#: `verified_by` string identifies the logic that produced it.
VERIFIER_VERSION = "1.0.0"
VERIFIER_NAME = f"verify_provenance.py v{VERIFIER_VERSION}"

REPORT_PATH = REPORTS_DIR / "provenance_report.md"
PARAPHRASE_PATH = REPO_ROOT / "backend" / "app" / "data" / "label_paraphrases.yaml"


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #

#: Prescribing actions and recommendation verbs.
_ACTION = re.compile(
    r"\b(?:avoid|use|using|consider|select|choose|prescrib\w*|administer\w*|"
    r"start\w*|initiat\w*|switch\w*|substitut\w*|replac\w*|discontinu\w*|"
    r"stop|withhold|reduce\w*|decreas\w*|increas\w*|adjust\w*|titrat\w*|"
    r"monitor\w*|test\w*|screen\w*|dose|dosing|therapy|treat\w*|"
    r"alternative|alternate)\b",
    re.IGNORECASE,
)

#: Risk, severity and effectiveness statements.
_RISK = re.compile(
    r"\b(?:toxic\w*|adverse|harm\w*|danger\w*|fatal|death|sever\w*|serious|"
    r"contraindicat\w*|ineffective|effective\w*|efficacy|fail\w*|"
    r"myopathy|myalgia|rhabdomyolysis|neutropenia|myelosuppression|"
    r"thrombo\w*|bleed\w*|stroke|infarct\w*|risk|hazard\w*|"
    r"not work|may not work|works? (?:less|poorly))\b",
    re.IGNORECASE,
)

#: Biological and pharmacological background.
_MECHANISM = re.compile(
    r"\b(?:enzyme|protein|transporter|receptor|gene|allele|variant|"
    r"metabolis\w*|metaboli[sz]\w*|activat\w*|inactivat\w*|convert\w*|"
    r"substrate|prodrug|oxidis\w*|oxidiz\w*|hydroly\w*|catalys\w*|catalyz\w*|"
    r"express\w*|encode\w*|liver|hepatic|plasma|uptake|clearance|"
    r"pathway|function\w*|activity|abolish\w*|reduce[sd]? (?:enzyme|activity)|"
    r"polymorph\w*|genotype|phenotype|diplotype|pharmacokinetic\w*)\b",
    re.IGNORECASE,
)

#: Words carrying no claim. Removed before coverage is computed, because
#: requiring "the" to appear in a CPIC recommendation would be theatre.
_STOPWORDS = frozenset("""
a an the and or but if then than that this these those there here of in on at to
for with without from by as is are was were be been being it its it's your you
their his her they them we our us i me my he she who whom which what when where
how why not no nor so such very more most much many few less least own same s t
can will just don should now may might could would shall must has have had do
does did doing done get gets got make makes made take takes taken give gives
also however therefore because since while during before after above below up
down out off over under again further once about against between into through
result results resulting shows show shown suggest suggests indicate indicates
means meaning likely unlikely other others another each both all any some one two
""".split())

#: Sentence terminator that tolerates abbreviations and citation trailers.
_ABBREV = re.compile(
    r"\b(?:e\.g|i\.e|etc|cf|vs|approx|no|fig|al|dr|prof|st|mr|ms|mrs|"
    r"ther|pharmacol|clin|med|j|vol|pp|ed|eds|inc|ltd)\.$",
    re.IGNORECASE,
)

#: Runtime slot placeholders. Not claims — their values come straight from
#: PharmCAT and are separately checked by the runtime slot verifier.
_SLOT = re.compile(r"\{[a-z_]+\}")

#: Statements about what the pipeline did, not about biology or treatment.
#: "No genotype was called" is a fact about this analysis; it traces to the
#: PharmCAT result, and demanding it appear in a CPIC guideline would be a
#: category error.
_PROCESS = re.compile(
    r"\b(?:pharmcat|this tool|this analysis|this system|was (?:not )?called|"
    r"could not be called|no (?:genotype|result|call|recommendation) was|"
    r"no variant-level|not (?:be )?(?:determined|available|reported)|"
    r"supplied context|insufficient to explain)\b",
    re.IGNORECASE,
)

#: Strong, unambiguous clinical triggers: a quantity with a unit, or a dosing
#: phrase with a qualifying adjective. These classify CLINICAL outright.
_DOSE_STRONG = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mg|g|mcg|µg|units?|iu|mg/kg|mg/m2|ml)\b"
    r"|\b\d+(?:\.\d+)?\s*%"
    r"|\b(?:standard|starting|initial|maximum|reduced?|full|half|alternative)\s+"
    r"(?:dose|dosing|therapy|agent)\b",
    re.IGNORECASE,
)

CLINICAL = "CLINICAL"
LABEL_PARAPHRASE = "LABEL_PARAPHRASE"
PHENOTYPE_PARAPHRASE = "PHENOTYPE_PARAPHRASE"
MECHANISM = "MECHANISM"
PROCESS = "PROCESS"
FRAMING = "FRAMING"

#: Classes that make a claim about the patient, and therefore gate a release.
GATED = (CLINICAL, LABEL_PARAPHRASE, PHENOTYPE_PARAPHRASE, "CLAIM_LEVEL", "NO_NEW_CLAIMS", "VERBATIM")


def split_sentences(text: str) -> list[str]:
    """
    Split prose into sentences.

    Abbreviation-aware, because the corpus is full of citations
    ("Clin Pharmacol Ther (2022).") that a naive split on `.` would shred into
    fragments — and a fragment classifies differently from the sentence it came
    from, which would corrupt the counts this script exists to report.
    """
    # The "Source: ..." trailer is provenance metadata, not prose.
    text = re.split(r"\n\s*Source:", text)[0]

    out: list[str] = []
    buffer = ""
    for chunk in re.split(r"(?<=[.!?])\s+", text.strip()):
        buffer = f"{buffer} {chunk}".strip() if buffer else chunk
        if _ABBREV.search(buffer):
            continue  # abbreviation, not a terminator — keep accumulating
        if buffer:
            out.append(buffer)
        buffer = ""
    if buffer:
        out.append(buffer)
    return [s for s in (x.strip() for x in out) if s]


def classify(
    sentence: str,
    paraphrases: dict[str, str] | None = None,
    phenotype_paraphrases: dict[str, str] | None = None,
) -> str:
    """
    Label one sentence.

    Order is load-bearing, and was corrected against real output:

      1. A **declared label paraphrase** is recognised first, by exact text. It
         is a clinical claim, but one traced to the risk label rather than to a
         source document, so it needs its own class.
      2. A **process** statement ("no genotype was called") describes this
         analysis, not treatment. Demanding it appear in a CPIC guideline would
         be a category error.
      3. A **strong** clinical trigger — a quantity with a unit, or a qualified
         dosing phrase — classifies CLINICAL outright.
      4. **Mechanism** is checked before the weak action-verb rule. This matters:
         the corpus sentence "DPD is ... responsible for breaking down the great
         majority of an administered fluoropyrimidine dose" was being called
         CLINICAL by the action rule, because "administered" is a verb and
         "dose" is a noun. It is descriptive biology, it is verbatim from the
         corpus, and calling it an unsourced prescribing instruction was simply
         wrong — 4 of the first run's 18 failures were this one sentence.
      5. Only then does an action verb plus a treatment noun imply CLINICAL.
    """
    bare = _SLOT.sub(" ", sentence)
    normalised = _normalise_sentence(sentence)

    if paraphrases and normalised in paraphrases:
        return LABEL_PARAPHRASE
    if phenotype_paraphrases and normalised in phenotype_paraphrases:
        return PHENOTYPE_PARAPHRASE
    if _PROCESS.search(bare):
        return PROCESS
    if _DOSE_STRONG.search(bare) or _RISK.search(bare):
        return CLINICAL
    if _MECHANISM.search(bare):
        return MECHANISM
    if _ACTION.search(bare) and re.search(
        r"\b(?:dose|dosing|therapy|treat\w*|drug|medicine|medication|agent|"
        r"alternative|prescrib\w*|regimen)\b",
        bare,
        re.IGNORECASE,
    ):
        return CLINICAL
    return FRAMING


def _normalise_sentence(text: str) -> str:
    """Whitespace- and case-insensitive form, for matching declared paraphrases."""
    return re.sub(r"\s+", " ", text.strip().lower())


def load_paraphrases() -> tuple[dict[str, str], dict[str, str]]:
    """
    Declared paraphrases: (sentence -> risk label, sentence -> phenotype).

    Loaded from `backend/app/data/label_paraphrases.yaml` rather than hardcoded,
    for the same reason the risk labels themselves live in a YAML file: a
    clinical string that a person can be asked to check must be readable
    without reading code.
    """
    import yaml

    if not PARAPHRASE_PATH.is_file():
        return {}, {}
    payload = yaml.safe_load(PARAPHRASE_PATH.read_text(encoding="utf-8")) or {}
    labels = {
        _normalise_sentence(item["sentence"]): item["label"]
        for item in payload.get("paraphrases", [])
        if item.get("sentence") and item.get("label")
    }
    phenotypes = {
        _normalise_sentence(item["sentence"]): item["phenotype"]
        for item in payload.get("phenotype_paraphrases", [])
        if item.get("sentence") and item.get("phenotype")
    }
    return labels, phenotypes


def content_words(text: str) -> set[str]:
    """Claim-bearing words: lowercased, destemmed of plurals, stopwords removed."""
    bare = _SLOT.sub(" ", text.lower())
    words = re.findall(r"[a-z][a-z0-9\-]*|\d+(?:\.\d+)?", bare)
    out = set()
    for word in words:
        if word in _STOPWORDS or len(word) < 3:
            continue
        out.add(word)
    return out


def _normalise(word: str) -> set[str]:
    """
    Surface forms to accept for one word.

    Crude stemming on purpose: a full stemmer would be another dependency and
    another thing to justify, and the failure mode here is a *false* failure,
    which is visible and cheap. A false pass would not be.
    """
    forms = {word}
    for suffix, stem in (
        ("ies", "y"), ("es", ""), ("s", ""), ("ed", ""), ("ing", ""),
        ("d", ""), ("ly", ""),
    ):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            forms.add(word[: -len(suffix)] + stem)
    forms.add(word + "s")
    forms.add(word + "e")
    return forms


def traces_to(sentence: str, *sources: str) -> tuple[bool, set[str]]:
    """
    Does every content word of `sentence` appear in some source?

    Returns (verified, untraced_words).
    """
    haystack = " ".join(s or "" for s in sources).lower()
    present = set(re.findall(r"[a-z][a-z0-9\-]*|\d+(?:\.\d+)?", haystack))
    # Include stems of source words too, so "avoiding" in prose matches "avoid"
    # in the source and vice versa.
    for word in list(present):
        present |= _normalise(word)

    untraced = {
        word for word in content_words(sentence) if not (_normalise(word) & present)
    }
    return (not untraced), untraced


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #


@dataclass
class SentenceResult:
    field_name: str
    text: str
    kind: str
    verified: bool
    untraced: set[str] = field(default_factory=set)
    source: str = ""


@dataclass
class EntryResult:
    drug: str
    gene: str
    phenotype: str
    sentences: list[SentenceResult] = field(default_factory=list)
    note: str = ""

    @property
    def key(self) -> str:
        return f"{self.drug}:{self.phenotype}"

    def of(self, kind: str) -> list[SentenceResult]:
        return [s for s in self.sentences if s.kind == kind]

    @property
    def failures(self) -> list[SentenceResult]:
        """Sentences needing human adjudication: a claim whose source we cannot find."""
        exempt = (FRAMING, PROCESS)
        return [s for s in self.sentences if s.kind not in exempt and not s.verified]

    @property
    def clinical_ok(self) -> bool:
        """The release gate: every claim-bearing sentence must be traced."""
        return all(s.verified for kind in GATED for s in self.of(kind))


def verify_entry(
    entry: dict,
    paraphrases: dict[str, str] | None = None,
    phenotype_paraphrases: dict[str, str] | None = None,
) -> EntryResult:
    drug = entry.get("drug", "")
    gene = entry.get("gene", "")
    result = EntryResult(drug=drug, gene=gene, phenotype=entry.get("phenotype", ""))

    cpic = entry.get("cpic_recommendation_used", "") or ""
    implications = " ".join(entry.get("cpic_implications", []) or [])
    # The derived risk label is itself CPIC-derived: label_mapping.yaml classifies
    # CPIC's own wording by a named, reviewable rule. Prose that restates the
    # label therefore has a real provenance chain, and is accepted as such — but
    # the report counts it separately, because it is one inference removed from
    # the source text.
    label = entry.get("derived_risk_label", "") or ""

    document = retrieve_mechanism(gene, drug)
    corpus = document.body if document else ""
    if not document:
        result.note = f"no mechanism corpus file for {gene}/{drug}"

    if not cpic:
        result.note = (result.note + "; " if result.note else "") + (
            "no CPIC recommendation text for this case"
        )

    corpus_text = document.body if document else ""
    clinical_source = " ".join([cpic, implications])
    full_source = clinical_source + " " + corpus_text

    for field_name, text in (entry.get("explanation") or {}).items():
        for sentence in split_sentences(text):
            normalised = _normalise_sentence(sentence)

            # Declared paraphrases keep their own exact-match rule: they restate
            # a derived value, and the check is that the wording is the declared
            # one FOR THIS ENTRY (the Safe wording on a Toxic result must fail).
            if paraphrases and normalised in paraphrases:
                declared = paraphrases.get(normalised, "")
                verified = declared == label
                result.sentences.append(SentenceResult(
                    field_name, sentence, LABEL_PARAPHRASE, verified,
                    set() if verified else {f"label={declared or 'undeclared'}"},
                    f"label_paraphrases.yaml -> {label}"))
                continue
            if phenotype_paraphrases and normalised in phenotype_paraphrases:
                declared = phenotype_paraphrases.get(normalised, "")
                verified = declared == result.phenotype
                result.sentences.append(SentenceResult(
                    field_name, sentence, PHENOTYPE_PARAPHRASE, verified,
                    set() if verified else {f"phenotype={declared or 'undeclared'}"},
                    f"label_paraphrases.yaml -> {result.phenotype}"))
                continue

            # Everything else goes through the field-level policy: assertions
            # must trace, wording may differ, framing is exempt.
            source = full_source if field_name in CORPUS_BACKED else clinical_source + " " + corpus_text
            verdict = check_sentence(field_name, sentence, source, directive=cpic, corpus=corpus_text)
            kind = FRAMING if verdict.is_framing else FIELD_POLICY.get(field_name, CLAIM_LEVEL).upper()
            result.sentences.append(SentenceResult(
                field_name, sentence, kind, verdict.verified,
                {str(a) for a in verdict.unsupported} | set(verdict.polarity)
                | {f'not-in-corpus:{w}' for w in verdict.foreign_terms},
                f"{verdict.policy} against {'CPIC+corpus' if field_name in CORPUS_BACKED else 'CPIC'}",
            ))

    return result


def verify_all(entries: list[dict]) -> list[EntryResult]:
    labels, phenotypes = load_paraphrases()
    return [verify_entry(e, labels, phenotypes) for e in entries]


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def _tally(results: list[EntryResult], kind: str) -> tuple[int, int]:
    sentences = [s for r in results for s in r.of(kind)]
    return sum(1 for s in sentences if s.verified), len(sentences)


def _tally_gated(results: list[EntryResult]) -> tuple[int, int]:
    """CLINICAL + LABEL_PARAPHRASE — every sentence that makes a clinical claim."""
    sentences = [s for r in results for kind in GATED for s in r.of(kind)]
    return sum(1 for s in sentences if s.verified), len(sentences)


def write_report(results: list[EntryResult], path: Path) -> None:
    clin_ok, clin_total = _tally_gated(results)
    direct_ok, direct_total = _tally(results, CLINICAL)
    para_ok, para_total = _tally(results, LABEL_PARAPHRASE)
    mech_ok, mech_total = _tally(results, MECHANISM)
    framing = [s for r in results for s in r.of(FRAMING)]
    process = [s for r in results for s in r.of(PROCESS)]
    pct = (100.0 * clin_ok / clin_total) if clin_total else 100.0

    lines: list[str] = [
        "# Provenance verification",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}  ",
        f"**Verifier:** `{VERIFIER_NAME}`  ",
        f"**Store:** `{EXPLANATIONS_PATH.relative_to(REPO_ROOT)}`  ",
        f"**Entries:** {len(results)}",
        "",
        "## What this number means",
        "",
        "This project has **no qualified clinical reviewer**, so it makes a",
        "different and narrower claim than expert approval: *the system asserts",
        "no clinical content of its own.* Every sentence carrying a clinical",
        "claim is traced, word by word, to text this project did not write.",
        "",
        "| | |",
        "| --- | --- |",
        "| ✅ **verified means** | every clinical word in the sentence appears in a cited source |",
        "| ❌ **verified does NOT mean** | a clinician has agreed the sentence is correct |",
        "",
        "Lexical tracing cannot detect a sentence that is assembled from source",
        "words and still wrong — reversed causality, a hedge dropped, a",
        "recommendation attached to the wrong phenotype. That needs a clinician.",
        "**Do not quote the percentage below without this paragraph.**",
        "",
        "## Headline",
        "",
        f"- **{clin_ok} of {clin_total} clinical-claim sentences have verified "
        f"provenance ({pct:.1f}%)** — target 100%",
        "",
        "| Class | Verified | Traces to | Gates release |",
        "| --- | ---: | --- | :---: |",
        f"| `CLINICAL` | {direct_ok}/{direct_total} | CPIC recommendation text, verbatim from PharmCAT | ✅ |",
        f"| `LABEL_PARAPHRASE` | {para_ok}/{para_total} | `label_paraphrases.yaml` → the label a named `label_mapping.yaml` rule derived from CPIC text | ✅ |",
        f"| `MECHANISM` | {mech_ok}/{mech_total} | the corpus file for that gene-drug pair (cited, dated) | ➖ reported |",
        f"| `PROCESS` | {len(process)} | describes this analysis, not a clinical claim | ➖ exempt |",
        f"| `FRAMING` | {len(framing)} | carries no clinical claim | ➖ exempt, listed below |",
        "",
        "### Why `LABEL_PARAPHRASE` is a separate class",
        "",
        "Patient-facing prose cannot quote CPIC verbatim and stay readable —",
        "\"Avoid standard dose (75 mg) clopidogrel if possible\" is exactly what a",
        "worried patient cannot parse. One sentence per result therefore restates",
        "the derived risk label in plain words.",
        "",
        "That sentence is a clinical claim whose words appear in no source. Left",
        "implicit it would be the system asserting clinical content on its own",
        "authority. Declaring each paraphrase in `label_paraphrases.yaml` makes",
        "the chain explicit and checkable, and the verifier additionally requires",
        "that a paraphrase match **this entry's** label — so the `Safe` wording",
        "attached to a `Toxic` result fails rather than passing as \"declared\".",
        "",
    ]

    failures = [(r, s) for r in results for s in r.failures]
    if failures:
        lines += ["## ❌ Unverified", "", "| Case | Field | Kind | Untraced words | Sentence |", "| --- | --- | --- | --- | --- |"]
        for entry, sentence in failures:
            words = ", ".join(f"`{w}`" for w in sorted(sentence.untraced)[:6])
            text = sentence.text.replace("|", "\\|")[:150]
            lines.append(
                f"| `{entry.key}` | {sentence.field_name} | **{sentence.kind}** | {words} | {text} |"
            )
        lines.append("")
    else:
        lines += ["## ✅ No unverified clinical or mechanism sentences", ""]

    lines += ["## Per-entry", "", "| Case | Clinical | Mechanism | Framing | Status |", "| --- | ---: | ---: | ---: | --- |"]
    for entry in sorted(results, key=lambda r: r.key):
        gated = [s for k in GATED for s in entry.of(k)]
        c_ok, c_n = sum(1 for s in gated if s.verified), len(gated)
        m_ok, m_n = sum(1 for s in entry.of(MECHANISM) if s.verified), len(entry.of(MECHANISM))
        status = "✅" if not entry.failures else f"❌ {len(entry.failures)} unverified"
        if entry.note:
            status += f" _{entry.note}_"
        lines.append(
            f"| `{entry.key}` | {c_ok}/{c_n} | {m_ok}/{m_n} | {len(entry.of(FRAMING))} | {status} |"
        )

    lines += [
        "",
        "## FRAMING sentences (exempt — read them anyway)",
        "",
        "These carry no clinical claim, so nothing traces them. That makes this",
        "the list where an unnoticed clinical assertion would hide, which is why",
        "it is printed in full rather than counted.",
        "",
    ]
    seen: set[str] = set()
    for entry in sorted(results, key=lambda r: r.key):
        for sentence in entry.of(FRAMING):
            if sentence.text in seen:
                continue
            seen.add(sentence.text)
            lines.append(f"- `{entry.key}` · *{sentence.field_name}* — {sentence.text}")

    lines += [
        "",
        "## Method",
        "",
        "1. Prose is split into sentences (abbreviation-aware, so citations survive).",
        "2. Each sentence is classified CLINICAL / MECHANISM / FRAMING by pattern.",
        "   CLINICAL wins ties, so a dosing instruction cannot escape the strict",
        "   check by also mentioning an enzyme.",
        "3. Content words are extracted (stopwords and runtime slots removed).",
        "4. Every content word must appear in the source, allowing for plural and",
        "   tense variation. CLINICAL traces to the CPIC recommendation, its",
        "   implications, and the derived risk label; MECHANISM traces to the",
        "   corpus file for that gene-drug pair.",
        "",
        "Stricter than the faithfulness guard, which checks only entities (doses,",
        "numbers, rsIDs, star alleles, genes, drugs). A sentence can pass the guard",
        "while making a claim the source never made, because its numbers all appear",
        "somewhere. Here the whole claim must be present.",
        "",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def stamp_review_blocks(store: dict, results: list[EntryResult], path: Path) -> int:
    """
    Record each entry's verdict in its `review` block, and write the store back.

    Replaces the old `reviewed_by` / `reviewed_at` pair, which had exactly one
    state worth recording and implied the wrong one. The block distinguishes
    what a machine checked, what the author read, and the clinical review that
    **was never obtained** — named outright, so it cannot be mistaken for
    merely pending.

    `read_by_author` is preserved across runs: re-verifying is not un-reading.
    """
    by_key = {r.key: r for r in results}
    now = datetime.now(timezone.utc).isoformat()
    stamped = 0

    for entry in store.get("explanations", []):
        result = by_key.get(f"{entry.get('drug')}:{entry.get('phenotype')}")
        if result is None:
            continue
        previous = entry.get("review") or {}
        entry["review"] = {
            "provenance_verified": result.clinical_ok,
            "verified_by": VERIFIER_NAME,
            "verified_at": now,
            # Carried over. A legacy `reviewed_by` name meant someone read it,
            # never that a clinician approved it, so it maps here and nowhere else.
            "read_by_author": previous.get("read_by_author") or entry.get("reviewed_by"),
            "clinical_expert_review": None,
            "clinical_expert_review_status": "NOT_OBTAINED",
        }
        entry.pop("reviewed_by", None)
        entry.pop("reviewed_at", None)
        stamped += 1

    write_json_atomic(path, store)
    return stamped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--only", default="", help="Verify one drug only.")
    parser.add_argument("-i", "--input", type=Path, default=EXPLANATIONS_PATH)
    parser.add_argument("-o", "--output", type=Path, default=REPORT_PATH)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print every sentence.")
    parser.add_argument(
        "--no-report", action="store_true", help="Skip writing the Markdown report."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Stamp the verdict into each entry's `review` block in the store.",
    )
    args = parser.parse_args(argv)

    store = load_json(args.input)
    entries = store.get("explanations", [])
    if args.only:
        entries = [e for e in entries if e.get("drug") == args.only]
    if not entries:
        print(red(f"No entries to verify in {args.input}."), file=sys.stderr)
        return 2

    results = verify_all(entries)
    clin_ok, clin_total = _tally_gated(results)
    mech_ok, mech_total = _tally(results, MECHANISM)
    pct = (100.0 * clin_ok / clin_total) if clin_total else 100.0
    failures = [(r, s) for r in results for s in r.failures]

    if not args.no_report:
        write_report(results, args.output)

    if args.write:
        stamped = stamp_review_blocks(store, results, args.input)
        print(dim(f"Stamped `review` on {stamped} entr{'y' if stamped == 1 else 'ies'}."))

    if args.json:
        print(json.dumps({
            "verifier": VERIFIER_NAME,
            "entries": len(results),
            "clinical": {"verified": clin_ok, "total": clin_total, "percent": round(pct, 2)},
            "by_class": {
                k: {"verified": _tally(results, k)[0], "total": _tally(results, k)[1]}
                for k in (CLINICAL, LABEL_PARAPHRASE, PHENOTYPE_PARAPHRASE,
                          MECHANISM, PROCESS, FRAMING)
            },
            "mechanism": {"verified": mech_ok, "total": mech_total},
            "framing": sum(len(r.of(FRAMING)) for r in results),
            "passed": all(r.clinical_ok for r in results),
            "failures": [
                {"case": r.key, "field": s.field_name, "kind": s.kind,
                 "untraced": sorted(s.untraced), "sentence": s.text}
                for r, s in failures
            ],
        }, indent=1))
        return 0 if all(r.clinical_ok for r in results) else 1

    print(rule("provenance verification"))
    for entry in sorted(results, key=lambda r: r.key):
        gated = [s for k in GATED for s in entry.of(k)]
        c_ok, c_n = sum(1 for s in gated if s.verified), len(gated)
        marker = green("PASS") if entry.clinical_ok else red("FAIL")
        detail = (f"clinical {c_ok}/{c_n}  mechanism {len(entry.of(MECHANISM))}  "
                  f"process {len(entry.of(PROCESS))}  framing {len(entry.of(FRAMING))}")
        print(f"  {marker}  {entry.key.ljust(26)} {dim(detail)}")
        if args.verbose:
            for sentence in entry.sentences:
                tick = green("·") if sentence.verified else red("✗")
                print(f"      {tick} {dim(sentence.kind.ljust(9))} {sentence.text[:96]}")
    print(rule())

    if failures:
        print(red(f"\n{len(failures)} unverified sentence(s):\n"))
        for entry, sentence in failures:
            print(red(f"  {entry.key} · {sentence.field_name} · {sentence.kind}"))
            print(f"    {sentence.text[:160]}")
            print(yellow(f"    untraced: {', '.join(sorted(sentence.untraced))}\n"))

    print(f"\nClinical-claim provenance: {bold(f'{clin_ok}/{clin_total} ({pct:.1f}%)')}  target 100%")
    print(dim(f"MECHANISM: {mech_ok}/{mech_total}   FRAMING (exempt): {sum(len(r.of(FRAMING)) for r in results)}"))
    if not args.no_report:
        print(dim(f"Report: {args.output.relative_to(REPO_ROOT)}"))

    passed = all(r.clinical_ok for r in results)
    print(green("\nAll clinical assertions trace to a cited source.") if passed
          else red("\nUnverified clinical content present — this is a release gate failure."))
    print(dim("Verified means every clinical ASSERTION traces to a cited source."))
    print(dim("Wording may differ — paraphrase is allowed; invented claims are not."))
    print(dim("It does NOT mean a clinician has agreed the sentence is correct."))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
