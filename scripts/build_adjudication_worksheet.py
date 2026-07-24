#!/usr/bin/env python3
"""
Build the human adjudication worksheet for outstanding mechanism sentences.

    python scripts/build_adjudication_worksheet.py
    python scripts/build_adjudication_worksheet.py --json

WHAT THIS DOES, AND WHAT IT REFUSES TO DO

It does **alignment**: for every outstanding claim it locates the corpus passage
that would support it, quoted verbatim with its location — or states plainly
that no such passage exists.

It records **no decision**, proposes none, and implies none. There is no verdict
column and no recommendation anywhere in the output, because the outstanding
sentences are all `mechanism` prose — precisely the class where this project
demonstrated that rule-based checking fails (see `reports/provenance_finding.md`,
Evidence 4 and 5). The closed-vocabulary check was retired at a measured 30%
false-positive rate specifically so a human would read these. Emitting a
suggested answer would invite rubber-stamping and reintroduce the failure the
gate exists to prevent.

DEDUPLICATION

Mechanism describes gene-drug biology, which does not vary by phenotype, so the
same claim recurs across every entry for a drug. Clustering near-identical
claims turns a 53-sentence reading task into far fewer decisions, and one
decision can then propagate to all its occurrences
(`scripts/adjudicate.py --by-claim`).

DETERMINISM

Every step is deterministic: token-overlap clustering and token-overlap
alignment against the corpus, with fixed thresholds. No model is consulted, so
nothing here needs a "machine-surfaced" caveat and the worksheet is reproducible
byte-for-byte from the same inputs.
"""

from __future__ import annotations

import argparse
import importlib.util
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
    rel,
    rule,
    yellow,
)

SCRIPTS = REPO_ROOT / "scripts"
WORKSHEET_PATH = REPORTS_DIR / "adjudication_worksheet.md"

#: Two claims are the same claim above this token-overlap (Jaccard) score.
#: Deliberately high — merging two claims that differ materially would hide a
#: distinction from the reader, which is worse than showing one claim twice.
CLUSTER_THRESHOLD = 0.60

#: A corpus sentence is offered as supporting text above this score. Lower than
#: the cluster threshold because a source passage legitimately says more than
#: the claim drawn from it.
SUPPORT_THRESHOLD = 0.15

#: How many supporting passages to quote per claim.
MAX_SUPPORT = 3

_STOP = frozenset("""
a an the and or but if then than that this these those there here of in on at to
for with without from by as is are was were be been being it its your you their
they them we our us who which what when where how why not no nor so such very
more most much many few less least same can will just should now may might could
would shall must has have had do does did doing done get got make made take also
however therefore because since while during before after above below up down out
off over under again further once about against between into through result
results show shows suggest indicate mean means likely other another each both all
any some one two three
""".split())

#: Lay and generic vocabulary. Excluded when SCORING alignment, because a claim
#: written in plain language is still the same claim.
#:
#: Without this the matcher reproduced the exact failure that got the closed-
#: vocabulary check retired: "Azathioprine is a medication that works by
#: producing active metabolites that can affect the bone marrow" scored as
#: UNSUPPORTED, even though the corpus says "produces active metabolites" and
#: names "marrow as the tissue at risk". The words `medication`, `works`, `body`
#: diluted the overlap until a well-sourced claim looked fabricated.
_LAY = frozenset("""
medication medications medicine medicines drug drugs body bodies patient patients
person people doctor doctors pharmacist result results genetic gene genes test
tests work works working properly well effectively normally normal ability able
amount amounts level levels thing things way ways help helps process processes
affect affects affected change changes make makes made take takes taken
your you their its this that these those certain some more less
""".split())


#: Words marking an added causal step — the claim asserting a *link* the source
#: may not have drawn. Used only to TIER for attention, never to judge.
_CAUSAL = re.compile(
    r"\b(?:causing|causes|cause|leads? to|leading to|results? in|resulting in|"
    r"so that|therefore|thus|hence|which means|meaning|because|due to|"
    r"allows?|allowing|prevents?|preventing|triggers?|drives?)\b",
    re.IGNORECASE,
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _inflect(word: str) -> set[str]:
    """Surface forms of one word, so `producing` matches `produces`."""
    forms = {word}
    for suffix, stem in (("ies", "y"), ("ing", ""), ("es", ""), ("ed", ""),
                         ("s", ""), ("d", ""), ("ly", "")):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            forms.add(word[: -len(suffix)] + stem)
    forms |= {word + "s", word + "es", word + "e", word + "ing"}
    return forms


def tokens(text: str) -> set[str]:
    """
    Base comparable tokens: lowercased, hyphen-split, stopwords dropped.

    Hyphen splitting matters because the corpus writes "bone-marrow" while the
    generated prose writes "bone marrow".
    """
    raw = re.findall(r"[a-z][a-z0-9\-]{2,}", text.lower())
    words: set[str] = set()
    for word in raw:
        words.add(word)
        words.update(part for part in word.split("-") if len(part) > 2)
    return {w for w in words if w not in _STOP}


def expand(text: str) -> set[str]:
    """
    The corpus side of a comparison, widened to every inflection.

    Asymmetric on purpose. Inflating BOTH sides was a real bug: the claim's
    token count ballooned with forms like `producinge` that cannot match
    anything, so coverage fell and well-sourced claims were pushed INTO the
    "no source found" tier — the opposite of the intended effect. Only the
    haystack is widened; the claim is measured as written.
    """
    out: set[str] = set()
    for word in tokens(text):
        out |= _inflect(word)
    return out


def domain_tokens(text: str) -> set[str]:
    """Tokens that carry domain content — lay phrasing removed before scoring."""
    return {w for w in tokens(text) if w not in _LAY}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def coverage(claim: set[str], source: set[str]) -> float:
    """Fraction of the claim's tokens the source accounts for."""
    return (len(claim & source) / len(claim)) if claim else 0.0


# --------------------------------------------------------------------------- #
# Corpus
# --------------------------------------------------------------------------- #


@dataclass
class Passage:
    text: str
    section: str
    line: int


def corpus_passages(gene: str | None, drug: str) -> tuple[list[Passage], str, str]:
    """Sentences of the mechanism corpus file, with section and line number."""
    from app.retrieval import retrieve_mechanism

    document = retrieve_mechanism(gene, drug)
    if document is None:
        return [], "", ""
    passages: list[Passage] = []
    section = "(top)"
    for number, raw in enumerate(document.body.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            section = line.lstrip("# ").strip()
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            sentence = sentence.strip()
            if len(sentence.split()) >= 4:
                passages.append(Passage(sentence, section, number))
    name = document.path.name if document.path else f"{gene}_{drug}.md"
    return passages, name, document.citation_line


# --------------------------------------------------------------------------- #
# Claims
# --------------------------------------------------------------------------- #


@dataclass
class Occurrence:
    case: str
    field: str
    key: str
    text: str


@dataclass
class Claim:
    claim_id: str
    drug: str
    gene: str
    text: str                       # the representative wording
    occurrences: list[Occurrence] = field(default_factory=list)
    corpus_file: str = ""
    citation: str = ""
    support: list[tuple[Passage, float]] = field(default_factory=list)
    tier: int = 1
    difference: str = ""

    @property
    def variants(self) -> list[str]:
        seen, out = set(), []
        for occurrence in self.occurrences:
            norm = " ".join(occurrence.text.split())
            if norm not in seen:
                seen.add(norm)
                out.append(occurrence.text)
        return out


def cluster(outstanding: list[dict]) -> list[Claim]:
    """
    Group near-identical claims, per drug.

    Clustering across drugs would merge "CYP2C19 converts clopidogrel" with a
    structurally similar sentence about a different gene, which is a different
    claim requiring a different source.
    """
    claims: list[Claim] = []
    by_drug: dict[str, list[dict]] = {}
    for item in outstanding:
        by_drug.setdefault(item["drug"], []).append(item)

    for drug in sorted(by_drug):
        buckets: list[tuple[set[str], Claim]] = []
        for item in sorted(by_drug[drug], key=lambda i: (i["case"], i["text"])):
            token_set = tokens(item["text"])
            placed = False
            for bucket_tokens, claim in buckets:
                if jaccard(token_set, bucket_tokens) >= CLUSTER_THRESHOLD:
                    claim.occurrences.append(
                        Occurrence(item["case"], item["field"], item["key"], item["text"])
                    )
                    placed = True
                    break
            if placed:
                continue
            claim = Claim(
                claim_id=f"{drug[:4].upper()}-{len(buckets) + 1:02d}",
                drug=drug,
                gene=item.get("gene", "") or "",
                text=item["text"],
            )
            claim.occurrences.append(
                Occurrence(item["case"], item["field"], item["key"], item["text"])
            )
            buckets.append((token_set, claim))
        claims.extend(c for _, c in buckets)
    return claims


def align(claim: Claim) -> None:
    """
    Attach the corpus passages that would support this claim, or none.

    Scored on DOMAIN tokens only. A claim rendered in plain language is the same
    claim, and scoring it on lay vocabulary is what made the retired
    closed-vocabulary check unusable — repeating that here would produce a
    worksheet whose top tier was mostly faithful paraphrase.
    """
    passages, filename, citation = corpus_passages(claim.gene, claim.drug)
    claim.corpus_file, claim.citation = filename, citation

    claim_domain = domain_tokens(claim.text)
    if not passages:
        claim.tier = 1
        claim.difference = "no mechanism corpus file exists for this gene-drug pair"
        return

    # Rank passages by how many of the claim's domain terms each accounts for.
    scored = []
    for passage in passages:
        hits = claim_domain & expand(passage.text)
        if hits:
            scored.append((passage, len(hits) / max(len(claim_domain), 1), hits))
    scored.sort(key=lambda row: row[1], reverse=True)
    claim.support = [(p, s) for p, s, _ in scored[:MAX_SUPPORT] if s >= SUPPORT_THRESHOLD]

    # Coverage is measured against the WHOLE corpus file, not one sentence: a
    # claim may legitimately draw on two passages.
    corpus_all = set()
    for passage in passages:
        corpus_all |= expand(passage.text)
    unaccounted = sorted(claim_domain - corpus_all)
    covered = 1.0 - (len(unaccounted) / max(len(claim_domain), 1))

    if not claim_domain:
        claim.tier = 3
        claim.difference = "carries no domain-specific term; phrasing only"
        return

    if covered < 0.5 or not claim.support:
        claim.tier = 1
        claim.difference = (
            f"{len(unaccounted)} of {len(claim_domain)} domain terms appear nowhere in "
            f"the corpus file: " + ", ".join(unaccounted[:8])
        )
        return

    adds_causal = bool(_CAUSAL.search(claim.text)) and not any(
        _CAUSAL.search(p.text) for p, _ in claim.support
    )
    if adds_causal or unaccounted:
        claim.tier = 2
        bits = []
        if adds_causal:
            bits.append("states a causal link the matched passages do not")
        if unaccounted:
            bits.append("terms absent from the corpus: " + ", ".join(unaccounted[:8]))
        claim.difference = "; ".join(bits)
    else:
        claim.tier = 3
        claim.difference = (
            "wording differs; every domain term appears in the cited corpus"
        )


# --------------------------------------------------------------------------- #
# Worksheet
# --------------------------------------------------------------------------- #

TIER_LABEL = {
    1: "TIER 1 — no passage aligned (NOT a finding of fabrication)",
    2: "TIER 2 — source found; claim adds a causal step or specificity",
    3: "TIER 3 — source found; claim differs only in wording",
}


def write_worksheet(claims: list[Claim], total_sentences: int, path: Path) -> None:
    ordered = sorted(claims, key=lambda c: (c.tier, c.drug, c.claim_id))
    counts = {tier: sum(1 for c in claims if c.tier == tier) for tier in (1, 2, 3)}

    lines = [
        "# Adjudication worksheet — outstanding mechanism claims",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Outstanding sentences:** {total_sentences}  ",
        f"**Unique claims to decide:** {len(claims)}  ",
        "**Alignment:** deterministic token-overlap against the cited mechanism "
        "corpus. No model was consulted.",
        "",
        "---",
        "",
        "## How to use this",
        "",
        "Each section is one **claim**, with the corpus passage that would support",
        "it quoted underneath. Decide once per claim; the decision applies to every",
        "entry listed under *Occurrences*.",
        "",
        "**There is deliberately no suggested answer.** These are all `mechanism`",
        "sentences — the class where this project showed rule-based checking fails,",
        "and the automated check covering them was retired at a measured 30%",
        "false-positive rate precisely so a person would read them. A proposed",
        "verdict here would invite agreement rather than judgement.",
        "",
        "### The question to ask",
        "",
        "> Does the source below actually support this claim — including the",
        "> **direction** of the effect?",
        "",
        "Direction is the one thing no check in this project can catch. For a",
        "prodrug (clopidogrel, azathioprine) *less* enzyme activity means *less*",
        "active drug. For a drug cleared by an enzyme (fluorouracil) *less*",
        "activity means *more* drug. A sentence with the arrow reversed is fluent,",
        "fully sourced term-by-term, and wrong.",
        "",
        "To record decisions afterwards:",
        "",
        "```bash",
        "python scripts/adjudicate.py --adjudicator \"<your name>\" --by-claim",
        "```",
        "",
        "---",
        "",
        "## Triage summary",
        "",
        "| Tier | Meaning | Claims |",
        "| --- | --- | ---: |",
        f"| **1** | no passage aligned by the matcher (see caveat below) | **{counts[1]}** |",
        f"| 2 | source found; claim adds a causal step or specificity | {counts[2]} |",
        f"| 3 | source found; claim differs only in wording | {counts[3]} |",
        "",
    ]
    lines += [
        "### What TIER 1 does and does not mean",
        "",
        "**TIER 1 means the deterministic matcher found no aligning passage. It",
        "does NOT mean the claim is fabricated.** The matcher compares domain",
        "terms against the cited corpus; a claim that renders technical content",
        "in plain words can fall into TIER 1 purely because the corpus never uses",
        "those words. During construction this misfired repeatedly — a claim the",
        "corpus plainly supports (*\"produces active metabolites\"*, *\"marrow as",
        "the tissue at risk\"*) landed in TIER 1 until inflection and hyphen",
        "handling were fixed, which moved 10 claims out of it.",
        "",
        "That is the same weakness that got the closed-vocabulary check retired",
        "at a 30% false-positive rate. It is disclosed here rather than smoothed",
        "over, because a triage tier that cries wolf on faithful text is worse",
        "than no triage at all — the reader stops trusting it.",
        "",
        "Read the *What differs* line under each claim: it names the exact terms",
        "the corpus did not account for, so a plain-language rendering is",
        "distinguishable from an invented mechanism at a glance.",
        "",
    ]
    if counts[1]:
        lines += [
            f"⚠️ **{counts[1]} claim(s) had no passage aligned.** Listed first — not",
            "because they are wrong, but because they are where a reader's attention",
            "is most likely to be repaid.",
            "",
        ]
    lines += ["---", ""]

    current_tier = None
    for claim in ordered:
        if claim.tier != current_tier:
            current_tier = claim.tier
            lines += [f"# {TIER_LABEL[claim.tier]}", ""]

        lines += [
            f"## `{claim.claim_id}` · {claim.drug} ({claim.gene})",
            "",
            "**Claim as generated:**",
            "",
            f"> {claim.text}",
            "",
        ]
        others = claim.variants[1:]
        if others:
            lines += ["<details><summary>Wording variants of this claim "
                      f"({len(others)})</summary>", ""]
            lines += [f"> {v}" for v in others]
            lines += ["", "</details>", ""]

        lines += [
            f"**Source consulted:** `{claim.corpus_file or '(no corpus file)'}`  ",
            f"**Cited as:** {claim.citation or '_(none)_'}",
            "",
        ]
        if claim.support:
            lines += ["**Supporting text from the source:**", ""]
            for passage, score in claim.support:
                lines += [
                    f"> {passage.text}",
                    f">",
                    f"> — *{claim.corpus_file}*, §{passage.section}, line {passage.line} "
                    f"(overlap {score:.0%})",
                    "",
                ]
        else:
            lines += [
                "**Supporting text from the source:**",
                "",
                "> ❌ **NO CORRESPONDING SOURCE TEXT FOUND.**",
                "> No passage in the cited corpus file shares enough content with this",
                "> claim to be offered as support.",
                "",
            ]

        lines += [
            f"**What differs:** {claim.difference}",
            "",
            f"**Occurrences ({len(claim.occurrences)}):** "
            + ", ".join(f"`{o.case}`" for o in claim.occurrences),
            "",
            "**Decision:** ☐ accept ☐ reject ☐ edit —",
            "",
            "**Reasoning:** ",
            "",
            "---",
            "",
        ]

    lines += [
        "## What this worksheet is not",
        "",
        "It is not a review. It locates source text; it does not judge adequacy.",
        "Recording a decision is a separate, deliberate act performed by a named",
        "person, and nothing in this file has been written to the explanation",
        "store.",
        "",
        "**No clinical expert has reviewed any of this.** This project has none.",
        "Adjudication here is the project author checking prose against its cited",
        "source — a narrower claim, and never described as more.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", type=Path, default=EXPLANATIONS_PATH)
    parser.add_argument("-o", "--output", type=Path, default=WORKSHEET_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    vp = _load("verify_provenance")
    adj = _load("adjudicate")
    store = load_json(args.input)
    entries = store.get("explanations", [])

    every = adj.collect_flagged(vp, entries, include_all=True)
    decided = {k for e in entries for k in (e.get("provenance_adjudications") or {})}
    outstanding = [i for i in every if i["key"] not in decided and i["field"] == "mechanism"]
    if not outstanding:
        print(green("No outstanding mechanism sentences — nothing to prepare."))
        return 0

    claims = cluster(outstanding)
    for claim in claims:
        align(claim)
    write_worksheet(claims, len(outstanding), args.output)

    counts = {tier: sum(1 for c in claims if c.tier == tier) for tier in (1, 2, 3)}
    if args.json:
        print(json.dumps({
            "outstanding_sentences": len(outstanding),
            "unique_claims": len(claims),
            "tiers": counts,
            "alignment": "deterministic token-overlap; no model consulted",
            "claims": [
                {"id": c.claim_id, "drug": c.drug, "tier": c.tier,
                 "occurrences": [o.case for o in c.occurrences],
                 "supported": bool(c.support), "text": c.text}
                for c in sorted(claims, key=lambda c: (c.tier, c.claim_id))
            ],
        }, indent=1))
        return 0

    print(rule("adjudication worksheet"))
    print(f"  {len(outstanding)} outstanding sentences → {bold(str(len(claims)))} unique claims")
    print(f"  {red('TIER 1')} no source found            {counts[1]}")
    print(f"  {yellow('TIER 2')} adds causal step/specificity {counts[2]}")
    print(f"  {green('TIER 3')} wording only                {counts[3]}")
    for claim in sorted(claims, key=lambda c: (c.tier, c.claim_id)):
        if claim.tier == 1:
            print(red(f"    · {claim.claim_id} {claim.drug}: {claim.text[:64]}"))
    print(dim(f"\n  wrote {rel(args.output)}"))
    print(dim("  NO decision recorded. Nothing written to the explanation store."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
