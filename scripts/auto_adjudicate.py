#!/usr/bin/env python3
"""
Automated pre-adjudication: decide the mechanical cases, escalate the rest.

WHAT THIS IS, AND WHAT IT IS NOT

This is **triage under time constraint**, not a substitute for human review. The
distinction is not modesty — it is this project's own measured finding. Evidence
1-3 in `reports/provenance_finding.md` established that automated faithfulness
checking has structural limits: a term-overlap matcher passed a polarity-reversed
claim while rejecting 15 of 16 faithful paraphrases, assertion-marker rules are
blind to fabricated mechanisms, and closed-vocabulary checking ran a 57%
false-positive rate on plain language.

So automation here does only what is genuinely mechanical, and hands everything
requiring judgement to a person.

    AUTO-ACCEPT   the sentence restates an aligned source passage, adding no
                  causal step, quantity, timeline, comparative or scope change,
                  AND a supporting passage can be quoted verbatim.

    ESCALATE      everything else — including every claim of ABSENCE, which is
                  invisible to every check in this project: "not at increased
                  risk" carries no assertion marker and contradicts no directive.

IDENTITY IS NON-NEGOTIABLE

Every record written here is stamped `"adjudicated_by": "automated"`. No human
name is ever written by this script, and it does not touch the placeholder-name
guard in `adjudicate.py`. A false attribution in an academic artifact is worse
than an unadjudicated sentence, because the sentence is visibly outstanding while
the attribution is invisibly wrong.

USAGE

    python scripts/auto_adjudicate.py --dry-run     # show the split, write nothing
    python scripts/auto_adjudicate.py               # write records + escalation list
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(SCRIPTS))

STORE = REPO_ROOT / "backend" / "app" / "data" / "explanations.json"
ESCALATION = REPO_ROOT / "reports" / "escalation_list.md"

#: Stamped into every record this script writes. `adjudicate.py` writes a human
#: name; the two must stay trivially distinguishable by a query.
AUTOMATED_IDENTITY = "automated"
METHOD = "deterministic alignment against the mechanism corpus"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# What makes a sentence require judgement
#
# Each pattern below marks something the sentence may be ASSERTING BEYOND its
# source. None of them is evidence of a defect — they are reasons a human, not a
# regex, should decide.
# --------------------------------------------------------------------------- #

#: A claim that something does NOT happen. The most important category here.
#: An absence carries no assertion marker, contradicts no directive, and reads as
#: reassurance — so it is invisible to every automated check in this project and
#: fails in the one direction that matters. All of these escalate, always.
ABSENCE = re.compile(
    r"\bnot\s+(?:at|associated|linked|expected|likely|known)\b"
    r"|\bno\s+(?:risk|increased|effect|change|impact|need|evidence)\b"
    r"|\bdoes\s+not\b|\bdo\s+not\b|\bwithout\s+(?:risk|any)\b"
    r"|\bunlikely\s+to\b|\bnot\s+affected\b",
    re.IGNORECASE,
)

#: A causal step the source may not make.
CAUSAL = re.compile(
    r"\bbecause\b|\bcauses?\b|\bleads?\s+to\b|\bresults?\s+in\b|\bdue\s+to\b"
    r"|\bso\s+that\b|\btherefore\b|\bconsequently\b|\bwhich\s+means\b"
    r"|\bthis\s+is\s+why\b",
    re.IGNORECASE,
)

#: A number, dose, or measured quantity.
QUANTITY = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%|percent|mg|mcg|g|ml|fold|times|units?)\b"
    r"|\b\d+\s*(?:to|-)\s*\d+\b|\bhalf\b|\bdouble\b|\btwice\b|\bthird\b",
    re.IGNORECASE,
)

#: A timeline the source may not state.
TIMELINE = re.compile(
    r"\b(?:hours?|days?|weeks?|months?|years?)\b"
    r"|\bwithin\b|\bafter\s+\w+\s+(?:dose|treatment)|\bbefore\s+(?:starting|treatment)"
    r"|\bimmediately\b|\bover\s+time\b|\blong[- ]term\b",
    re.IGNORECASE,
)

#: A comparative or graded risk statement.
COMPARATIVE = re.compile(
    r"\b(?:more|less|higher|lower|greater|smaller|stronger|weaker)\s+(?:than|risk|likely)"
    r"|\bincreas\w*\s+(?:the\s+|a\s+)?risk\b"      # "increase THE risk" defeated \bincreased? risk\b
    r"|\breduc\w*\s+(?:the\s+|a\s+)?risk\b|\bhigher\s+chance\b"
    r"|\bmost\s+(?:people|patients)\b|\bcompared\s+(?:to|with)\b",
    re.IGNORECASE,
)

#: A universal or absolute scope.
SCOPE = re.compile(
    r"\b(?:all|every|always|never|none|any)\s+(?:patients?|people|cases?|time)\b"
    r"|\balways\b|\bnever\b|\bin\s+all\s+cases\b",
    re.IGNORECASE,
)

#: Confident phrasing where a source typically hedges.
HEDGE_SHIFT = re.compile(r"\bwill\b|\bdoes\b|\bis\s+going\s+to\b", re.IGNORECASE)
HEDGED = re.compile(r"\bmay\b|\bmight\b|\bcan\b|\bcould\b|\bpossibl", re.IGNORECASE)

#: Wording already flagged in the validation report as awkward but not false.
KNOWN_WORDING = (
    ("azathioprine:NM", "safe risk",
     "the label word `Safe` used as an adjective — awkward English, flagged in "
     "the validation report, never adjudicated"),
)

#: An affirmative statement that something is SAFE. Same asymmetry as an absence
#: claim: it reassures, and this project's findings are unanimous that reassurance
#: is the direction every defect ran in.
SAFETY = re.compile(
    r"\bis\s+(?:likely\s+to\s+be\s+)?safe\b|\bsafe\s+to\s+(?:take|use)\b"
    r"|\bno\s+need\s+to\b|\bshould\s+be\s+fine\b|\bwell\s+tolerated\b",
    re.IGNORECASE,
)

REASONS: tuple[tuple[str, re.Pattern, str], ...] = (
    ("safety-assertion", SAFETY,
     "asserts SAFETY. Reassurance is the direction every defect in this project "
     "ran in, so an affirmative safety claim is never auto-accepted."),
    ("absence", ABSENCE,
     "claims an ABSENCE. Invisible to every automated check here: it carries no "
     "assertion marker and contradicts no directive, and it errs toward "
     "reassurance. Always escalated."),
    ("causal", CAUSAL, "adds a causal step that may not be in the source"),
    ("quantity", QUANTITY, "states a quantity, dose or number"),
    ("timeline", TIMELINE, "states a timeline"),
    ("comparative", COMPARATIVE, "makes a comparative or graded risk claim"),
    ("scope", SCOPE, "asserts a universal or absolute scope"),
)


@dataclass
class Verdict:
    item: dict
    tier: int
    passage: str = ""
    citation: str = ""
    auto: bool = False
    reasons: list[str] = field(default_factory=list)
    detail: list[str] = field(default_factory=list)


def whole_sentences(gene: str | None, drug: str) -> list[str]:
    """
    Corpus sentences, with hard-wrapped lines joined first.

    The worksheet aligner splits per LINE and then per sentence within that line.
    The corpus is markdown wrapped at ~80 columns, so a sentence spanning two
    lines becomes two fragments — measured: median passage 74 chars, max 81, 18
    of 103 under 60. A fragment is fine for RANKING (which is all the worksheet
    needs) but cannot justify ACCEPTING a claim, because the quoted basis would
    be half a sentence. So the basis is rebuilt from unwrapped text.
    """
    from app.retrieval import retrieve_mechanism

    document = retrieve_mechanism(gene, drug)
    if document is None:
        return []
    paragraphs, current = [], []
    for raw in document.body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line.lstrip("-*  ").strip())
    if current:
        paragraphs.append(" ".join(current))

    out: list[str] = []
    for para in paragraphs:
        for sentence in re.split(r"(?<=[.!?])\s+", para):
            sentence = " ".join(sentence.split())
            if len(sentence.split()) >= 5:
                out.append(sentence)
    return out


def best_whole_passage(claim, text: str) -> str:
    """The unwrapped sentence sharing most domain terms with `text`."""
    worksheet = sys.modules.get("build_adjudication_worksheet")
    if worksheet is None or claim is None:
        return ""
    wanted = worksheet.domain_tokens(text)
    if not wanted:
        return ""
    best, score = "", 0.0
    for sentence in whole_sentences(claim.gene, claim.drug):
        hits = wanted & worksheet.expand(sentence)
        if not hits:
            continue
        ratio = len(hits) / len(wanted)
        if ratio > score:
            best, score = sentence, ratio
    # THIS THRESHOLD GOVERNS QUOTABILITY, NOT SAFETY.
    #
    # Its only job is "is there a passage worth quoting as the basis". Whether the
    # claim says MORE than that passage is decided separately, by the semantic
    # detectors above — and those are what actually protect the acceptance.
    #
    # It was first set to 0.5, which escalated 21 items whose best match was
    # near-verbatim (simvastatin:IM scored 0.46 against a source sentence sharing
    # its whole first clause). The score falls when a claim ADDS material, so a
    # high bar here double-counts exactly what the detectors already catch, and
    # rejects perfectly quotable sources.
    #
    # 0.35 is still arbitrary as a number. What is not arbitrary: below it the
    # best match stops being recognisably about the same claim, checked by
    # reading the sub-threshold cases rather than by picking a round figure.
    return best if score >= 0.35 else ""


def classify(item: dict, claim, tier: int) -> Verdict:
    """Decide auto-accept vs escalate. Never auto-rejects — that is a judgement."""
    text = item["text"]
    verdict = Verdict(item=item, tier=tier)

    # The quotable passage. Without one there is nothing to accept AGAINST.
    if claim is not None and claim.support:
        verdict.passage = best_whole_passage(claim, text)
        verdict.citation = claim.citation or claim.corpus_file or ""

    if tier == 1 or not verdict.passage:
        verdict.reasons.append("no-source")
        verdict.detail.append(
            "no corpus passage aligned to this sentence. NOT a finding of "
            "fabrication — the aligner may simply have missed it — but it cannot "
            "be accepted automatically, because there is nothing to accept it against."
        )
        return verdict

    for name, pattern, why in REASONS:
        match = pattern.search(text)
        if match:
            verdict.reasons.append(name)
            verdict.detail.append(f"{why} (“{match.group(0)}”)")

    # Hedging: confident in the claim where the source hedges.
    if HEDGE_SHIFT.search(text) and HEDGED.search(verdict.passage) and not HEDGED.search(text):
        verdict.reasons.append("hedging")
        verdict.detail.append(
            "states confidently what the aligned passage hedges"
        )

    for case, needle, why in KNOWN_WORDING:
        if item["case"] == case and needle.lower() in text.lower():
            verdict.reasons.append("known-wording")
            verdict.detail.append(why)

    verdict.auto = not verdict.reasons
    return verdict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show the split; write nothing.")
    args = parser.parse_args(argv)

    worksheet = _load("build_adjudication_worksheet")
    adjudicate = _load("adjudicate")
    vp = adjudicate._load("verify_provenance")

    store = json.loads(STORE.read_text())
    entries = store["explanations"]
    by_case = {f"{e['drug']}:{e['phenotype']}": e for e in entries}

    # Everything still undecided — including sentences the flagging filter does
    # not surface, so nothing is quietly left out of the count.
    every = adjudicate.collect_flagged(vp, entries, True)
    outstanding = [
        i for i in every
        if i["key"] not in (by_case[i["case"]].get("provenance_adjudications") or {})
    ]

    # Reuse the worksheet's own clustering and alignment rather than
    # reimplementing it — a second aligner would be a second thing to validate,
    # and this project has already documented what unvalidated checks produce.
    claims = worksheet.cluster(outstanding)
    for claim in claims:
        worksheet.align(claim)
    claim_for_key: dict[str, object] = {}
    for claim in claims:
        for occurrence in claim.occurrences:
            claim_for_key[occurrence.key] = claim

    verdicts = []
    for item in outstanding:
        claim = claim_for_key.get(item["key"])
        tier = claim.tier if claim is not None else 1
        verdicts.append(classify(item, claim, tier))

    accepted = [v for v in verdicts if v.auto]
    escalated = [v for v in verdicts if not v.auto]

    print(f"outstanding        {len(outstanding)}")
    print(f"  auto-accepted    {len(accepted)}")
    print(f"  escalated        {len(escalated)}")
    tiers = collections.Counter(v.tier for v in accepted)
    print(f"  accepted by tier {dict(sorted(tiers.items()))}")
    reasons = collections.Counter(r for v in escalated for r in v.reasons)
    print(f"  escalation causes {dict(reasons.most_common())}")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    # --- write the automated records ------------------------------------- #
    now = datetime.now(timezone.utc).isoformat()
    for verdict in accepted:
        item = verdict.item
        entry = by_case[item["case"]]
        block = entry.setdefault("provenance_adjudications", {})
        block[item["key"]] = {
            "version": adjudicate.ADJUDICATION_VERSION,
            "field": item["field"],
            "sentence": item["text"],
            "decision": "accepted",
            "rationale": "restates an aligned corpus passage without adding a "
                         "causal step, quantity, timeline, comparative or scope",
            "adjudicated_by": AUTOMATED_IDENTITY,
            "adjudicated_at": now,
            "method": METHOD,
            "model": None,
            "decided_at": now,
            "basis": verdict.passage,
            "basis_citation": verdict.citation,
            "escalated": False,
            "note": "AUTOMATED provenance adjudication under time constraint; "
                    "not read by a person, and not clinical approval",
        }
    for verdict in escalated:
        item = verdict.item
        entry = by_case[item["case"]]
        block = entry.setdefault("provenance_adjudications", {})
        # Marker only — deliberately NO `decision` key, so the gate cannot count
        # this as decided. It records that automation looked and declined to rule.
        block[item["key"]] = {
            "version": adjudicate.ADJUDICATION_VERSION,
            "field": item["field"],
            "sentence": item["text"],
            "adjudicated_by": AUTOMATED_IDENTITY,
            "method": METHOD,
            "model": None,
            "decided_at": now,
            "basis": verdict.passage,
            "basis_citation": verdict.citation,
            "escalated": True,
            "escalation_reasons": verdict.reasons,
            "escalation_detail": verdict.detail,
            "note": "ESCALATED for human review; automation declined to decide",
        }

    STORE.write_text(json.dumps(store, indent=1, ensure_ascii=False) + "\n")
    print(f"\nwrote {len(accepted)} automated acceptances, "
          f"{len(escalated)} escalation markers")

    write_escalation_list(escalated)
    print(f"escalation list: {ESCALATION.relative_to(REPO_ROOT)}")
    return 0


def write_escalation_list(escalated: list[Verdict]) -> None:
    """
    The human's short pass. Deliberately NO recommended-verdict column: a
    proposed answer invites rubber-stamping, which would convert a real review
    into a signature.
    """
    # Most consequential first: absence claims, then unsourced, then the rest.
    def rank(v: Verdict) -> tuple:
        return (0 if "absence" in v.reasons else
                1 if "no-source" in v.reasons else
                2 if "hedging" in v.reasons else 3,
                v.item["case"])

    ordered = sorted(escalated, key=rank)
    lines = [
        "# Escalation list — sentences automation would not decide",
        "",
        f"**{len(ordered)} items.** Every other outstanding sentence was "
        "auto-accepted against a quoted source passage; these are the ones where "
        "a person has to look.",
        "",
        "Automation never rejects and never guesses. An item is here because it "
        "asserts something the aligned passage does not obviously support, or "
        "because no passage aligned at all.",
        "",
        "There is deliberately **no recommended verdict** — a proposed answer "
        "invites rubber-stamping, and this list exists precisely because these "
        "sentences need judgement rather than a signature.",
        "",
        "Clear them in one pass:",
        "",
        "```bash",
        'python scripts/adjudicate.py --escalated-only --adjudicator "<your real name>"',
        "```",
        "",
        "---",
        "",
    ]
    for n, v in enumerate(ordered, start=1):
        item = v.item
        lines += [
            f"## {n}. {item['case']} · `{item['field']}`",
            "",
            "**Sentence**",
            "",
            f"> {item['text']}",
            "",
        ]
        if v.passage:
            lines += [
                f"**Aligned source passage** — {v.citation or 'mechanism corpus'}",
                "",
                f"> {v.passage}",
                "",
            ]
        else:
            lines += [
                "**Aligned source passage:** :warning: **none found.** The aligner "
                "could not match this sentence to any corpus passage. That is not "
                "a finding of fabrication, but nothing supports it automatically.",
                "",
            ]
        lines += ["**Why this needs your eyes**", ""]
        lines += [f"- {d}" for d in v.detail]
        lines += [
            "",
            "**Decision** (accept / edit / reject) and why:",
            "",
            "```",
            "",
            "```",
            "",
            "---",
            "",
        ]
    ESCALATION.parent.mkdir(parents=True, exist_ok=True)
    ESCALATION.write_text("\n".join(lines))


if __name__ == "__main__":
    raise SystemExit(main())
