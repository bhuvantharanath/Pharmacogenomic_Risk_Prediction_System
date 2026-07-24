"""
Field-level provenance policy.

WHY THIS REPLACES THE OLD GLOBAL CHECK

The first provenance gate required every content word of a sentence to appear in
the source. `reports/provenance_diagnosis.md` records what that actually
measured: three probes showed a faithful paraphrase FAILS while a sentence that
*contradicts* the source PASSES as long as it reuses the vocabulary. Of 16 real
failures on captured model output, 15 were false positives and none was a
fabricated claim. It was a copying metric, and the template's 100% was true by
construction rather than by merit.

WHAT THIS DOES INSTEAD

Different fields carry different obligations, so they get different rules:

    clinical_recommendation   VERBATIM. Never model-authored. Byte-identical to
                              what PharmCAT emitted. Exact match, no tolerance.

    summary                   CLAIM-LEVEL. Wording may differ from the source;
    mechanism                 every clinical ASSERTION must trace. `mechanism`
    variant_rationale         traces to the mechanism corpus as well as CPIC.

    patient_friendly          NO NEW CLAIMS. Paraphrase is explicitly permitted
                              and expected — translating "leukopenia" into "low
                              white blood cell count" is the entire point of the
                              field. What it may not do is introduce a dose, a
                              timeline, a probability, a comparative risk, or a
                              mechanism the source does not support.

HOW A "CLAIM" IS DETECTED WITHOUT AN LLM

Rule-based, and deliberately so: using a model to judge a model is circular, and
it would spend quota to answer a question a few hundred lines of rules answer
more predictably. A sentence is scanned for ASSERTION MARKERS. Each marker
becomes an `Assertion` that must be satisfied by the source. A sentence with no
assertion markers asserts nothing clinical — it is procedural or advisory
framing ("talk to your doctor") — and passes.

Two kinds of assertion, matched two different ways:

  * LITERAL  (quantity, time) — a dose, a percentage, a duration. These are
    specific facts and must appear in the source as the same number/unit. "50%"
    is not interchangeable with "40%", and a timeline the source never gave is
    an invention regardless of phrasing.

  * CONCEPTUAL (direction, harm, severity, mechanism) — "lower the dose" and
    "dose reduction" are the same claim in different words, so these match on a
    documented concept set rather than on spelling. This is what lets a faithful
    paraphrase pass while still catching a claim the source never made.

WHAT THIS STILL CANNOT DO

It cannot detect a reversed claim built from sourced concepts — "increased
activity" where the source says decreased would match the DIRECTION concept
family. Negation and direction-of-effect need a reader. That is exactly why the
automated layer only flags candidates and `scripts/adjudicate.py` is the actual
release gate: a person decides, once, for twenty entries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# Field policies
# --------------------------------------------------------------------------- #

VERBATIM = "verbatim"
CLAIM_LEVEL = "claim_level"
NO_NEW_CLAIMS = "no_new_claims"

#: Which rule applies to which field of the explanation contract.
FIELD_POLICY: dict[str, str] = {
    "clinical_recommendation": VERBATIM,
    "summary": CLAIM_LEVEL,
    "mechanism": CLAIM_LEVEL,
    "variant_rationale": CLAIM_LEVEL,
    "patient_friendly": NO_NEW_CLAIMS,
}

#: Fields whose assertions may also be satisfied by the mechanism corpus, not
#: only by the CPIC recommendation text.
CORPUS_BACKED = frozenset({"mechanism", "variant_rationale", "summary"})


# --------------------------------------------------------------------------- #
# Concept families — the documented synonym sets
# --------------------------------------------------------------------------- #
#
# Every entry here is a claim this domain actually makes. They are deliberately
# narrow: a family that swallowed too much would let an unsourced claim through
# by matching something unrelated in the source.

CONCEPTS: dict[str, frozenset[str]] = {
    # A dose/exposure/activity going DOWN.
    "direction_down": frozenset({
        "reduce", "reduced", "reduces", "reduction", "lower", "lowered", "lowering",
        "decrease", "decreased", "decreases", "less", "lessen", "smaller", "minimal",
        "low", "deficient", "deficiency", "absent", "loss", "impaired", "poor",
        "slower", "slows", "slow", "inactive", "nonfunctional", "diminished",
    }),
    # A dose/exposure/activity going UP.
    "direction_up": frozenset({
        "increase", "increased", "increases", "higher", "high", "greater", "greatly",
        "more", "elevated", "excess", "excessive", "accumulate", "accumulation",
        "accumulates", "rapid", "ultrarapid", "faster", "enhanced", "exposure",
    }),
    # Choosing something else / not using this drug.
    "switch": frozenset({
        "alternative", "alternate", "different", "substitute", "switch", "avoid",
        "nonthiopurine", "replace", "another", "other",
    }),
    # Harm of any kind.
    "harm": frozenset({
        "toxicity", "toxic", "adverse", "harm", "harmful", "side", "effects",
        "myelosuppression", "myelotoxicity", "leukopenia", "neutropenia",
        "thrombocytopenia", "suppression", "bone-marrow", "marrow", "cytopenia",
        "myopathy", "rhabdomyolysis", "reaction", "risk", "danger",
    }),
    # How bad.
    "severity": frozenset({
        "severe", "serious", "fatal", "life-threatening", "major", "profound",
        "significant", "grave",
    }),
    # Biological action.
    "mechanism": frozenset({
        "metabolise", "metabolize", "metabolism", "metabolises", "metabolizes",
        "metabolite", "metabolites", "metabolizer", "activate", "activates",
        "activation", "inactivate", "inactivates", "inactivation", "convert",
        "converts", "converted", "conversion", "enzyme", "prodrug", "substrate",
        "methylate", "methylates", "methylating", "catabolism", "clearance",
        "transporter", "uptake", "breakdown", "break", "down", "processes",
        "process", "function", "activity",
    }),
}

#: Reverse index: word -> the family it belongs to.
_WORD_TO_CONCEPT: dict[str, str] = {
    word: family for family, words in CONCEPTS.items() for word in words
}

#: Time nouns. A duration is a LITERAL claim — the source either gave one or it
#: did not.
_TIME_NOUNS = frozenset({
    "second", "seconds", "minute", "minutes", "hour", "hours", "day", "days",
    "week", "weeks", "month", "months", "year", "years", "dose", "doses",
})

#: Units that make a bare number a clinical quantity.
_UNITS = r"(?:mg/kg/day|mg/kg|mg/m2|mcg|µg|mg|g|ml|units?|iu|%|percent)"

#: A number with a unit, or a percentage, or a numeric range.
_QUANTITY = re.compile(
    rf"\b\d+(?:\.\d+)?\s*(?:-|–|to)\s*\d+(?:\.\d+)?\s*{_UNITS}"
    rf"|\b\d+(?:\.\d+)?\s*{_UNITS}"
    rf"|\b\d+(?:\.\d+)?\s*(?=%)",
    re.IGNORECASE,
)

#: A duration: an optional number (or vague quantifier) plus a time noun.
_TIME = re.compile(
    r"\b(?:\d+(?:\.\d+)?(?:\s*(?:-|–|to)\s*\d+(?:\.\d+)?)?|a few|several|couple of)?\s*"
    r"\b(second|minute|hour|day|week|month|year)s?\b",
    re.IGNORECASE,
)

#: Worded multipliers and comparative ratios. "twice as likely" is a
#: quantitative claim even though it contains no digit — the sensitivity check
#: caught this hole: an invented "twice as likely to have a reaction" passed
#: every numeric check because it spells its number.
_WORDED_COMPARATIVE = re.compile(
    r"\b(?:twice|double|triple|thrice|half|tenfold|ten-fold|[a-z]+-fold)\b"
    r"|\b(?:two|three|four|five|ten)\s+times\b"
    r"|\bas\s+likely\s+as\b|\bmore\s+likely\s+than\b|\bless\s+likely\s+than\b",
    re.IGNORECASE,
)

#: Runtime slot placeholders — not claims; their values come from PharmCAT and
#: are checked separately by the runtime slot verifier.
_SLOT = re.compile(r"\{[a-z_]+\}")


# --------------------------------------------------------------------------- #
# Assertions
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Assertion:
    """One checkable claim inside a sentence."""

    kind: str          # quantity | time | direction | harm | severity | mechanism
    surface: str       # what the sentence actually said
    key: str           # normalised matching key (a number, or a concept family)
    literal: bool      # True -> must match the same number/unit in the source

    def __str__(self) -> str:
        return f"{self.kind}:{self.surface!r}"


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def _normalise_unit(unit: str) -> str:
    unit = unit.lower().replace(" ", "")
    return {"percent": "%", "µg": "mcg", "unit": "units"}.get(unit, unit)


def _quantity_pairs(text: str) -> set[tuple[str, str]]:
    """
    Every (number, unit) pair in `text`.

    Unit-aware on purpose. Matching a bare number against any digit in the
    source is a false-negative waiting to happen: an invented "15% chance"
    traced successfully because some unrelated "15" appeared in a citation in
    the mechanism corpus. A dose or a probability is only sourced if the source
    states that number *with that unit*.
    """
    pairs: set[tuple[str, str]] = set()
    for match in re.finditer(rf"(\d+(?:\.\d+)?)\s*({_UNITS})", text, re.IGNORECASE):
        pairs.add((match.group(1), _normalise_unit(match.group(2))))
    # Ranges: "30-80% of standard" sources both endpoints with the trailing unit.
    for match in re.finditer(
        rf"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*({_UNITS})", text, re.IGNORECASE
    ):
        unit = _normalise_unit(match.group(3))
        pairs.add((match.group(1), unit))
        pairs.add((match.group(2), unit))
    return pairs


def extract_assertions(sentence: str) -> list[Assertion]:
    """
    Pull every checkable claim out of a sentence.

    A sentence yielding no assertions makes no clinical claim — it is framing,
    and framing is not something provenance can or should police.
    """
    bare = _SLOT.sub(" ", sentence)
    lowered = bare.lower()
    out: list[Assertion] = []

    for match in _QUANTITY.finditer(bare):
        surface = match.group(0).strip()
        out.append(Assertion("quantity", surface, surface.lower(), literal=True))

    for match in _WORDED_COMPARATIVE.finditer(bare):
        surface = match.group(0).strip()
        out.append(Assertion("comparative", surface, surface.lower(), literal=True))

    for match in _TIME.finditer(bare):
        surface = match.group(0).strip()
        noun = match.group(1).lower()
        if noun in ("dose",):  # "dose" alone is not a duration
            continue
        digits = _numbers(surface)
        # Key on the time noun plus any number; "a few weeks" keys on "week".
        out.append(Assertion("time", surface, f"{noun}|{','.join(sorted(digits))}", literal=True))

    seen_concepts: set[str] = set()
    for word in re.findall(r"[a-z][a-z\-]+", lowered):
        family = _WORD_TO_CONCEPT.get(word)
        if family and family not in seen_concepts:
            seen_concepts.add(family)
            out.append(Assertion(family.split("_")[0] if family.startswith("direction") else family,
                                 word, family, literal=False))
    return out


def _source_concepts(source: str) -> set[str]:
    lowered = source.lower()
    found = set()
    for word in re.findall(r"[a-z][a-z\-]+", lowered):
        family = _WORD_TO_CONCEPT.get(word)
        if family:
            found.add(family)
    return found


def assertion_traces(assertion: Assertion, source: str) -> bool:
    """Is this claim supported by the source text?"""
    if assertion.literal:
        lowered = source.lower()
        if assertion.kind == "time":
            noun = assertion.key.split("|")[0]
            digits = [d for d in assertion.key.split("|")[-1].split(",") if d]
            # The source must mention the same time unit (singular or plural).
            if not re.search(rf"\b{noun}s?\b", lowered):
                return False
            # If the sentence named specific numbers, the source must have them.
            return all(d in _numbers(source) for d in digits)
        if assertion.kind == "comparative":
            # A worded ratio must appear in the source as the same phrase.
            return assertion.key in source.lower()
        # quantity: the number must appear in the source WITH the same unit.
        claimed = _quantity_pairs(assertion.surface)
        if not claimed:
            return False
        return claimed <= _quantity_pairs(source)
    return assertion.key in _source_concepts(source)


# --------------------------------------------------------------------------- #
# Field checks
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Polarity
# --------------------------------------------------------------------------- #
#
# The concept check matches "reduction" against "lower" regardless of whether
# either is negated, so "Do NOT consider dose reduction" scored identically to
# "Consider dose reduction". That was demonstrated, not hypothesised — it is the
# negation probe in reports/provenance_diagnosis.md. Polarity closes it.

#: Words that flip the sense of a claim.
_NEGATORS = frozenset({
    "not", "no", "never", "none", "neither", "nor", "without", "cannot",
    "unless", "except",
    "n't", "dont", "doesnt", "didnt", "shouldnt", "cant", "wont",
})
#
# Deliberately NOT negators: "avoid", "instead", "rather", "discontinue".
# Those are switch-concept words in their own right, so treating them as
# negators made a sentence negate its own concept — "use a different medicine
# to avoid side effects" was scored as negating `switch`, which is the opposite
# of what it says. Prohibition is handled by its own rule below, where it can
# be reasoned about explicitly rather than as a side effect of tokenisation.

#: Clause AND sentence boundaries. Negation does not reach across them.
#:
#: Sentence terminators are included, and that omission was a real bug: CPIC
#: text like "Avoid clopidogrel if possible. Use prasugrel ... if no
#: contraindication." was treated as one clause, so the "no" in the second
#: sentence negated the "avoid" in the first. Four verbatim-faithful sentences
#: were flagged on the first real run because of it.
_CLAUSE_SPLIT = re.compile(
    r"[.!?,;:]|\b(?:but|however|although|whereas|while|and then)\b"
)


def _clauses(text: str) -> list[str]:
    return [c for c in _CLAUSE_SPLIT.split(text.lower()) if c and c.strip()]


def polarity_of(text: str, concept: str) -> bool | None:
    """
    Is `concept` negated in `text`?

    Returns True (negated), False (asserted positively), or None (the concept
    does not appear at all). Scoped to the clause containing the concept, so
    "Avoid azathioprine, consider an alternative" does not mark the alternative
    as negated.
    """
    words_in_family = CONCEPTS.get(concept, frozenset())
    seen = None
    for clause in _clauses(text):
        tokens = re.findall(r"[a-z][a-z\-']*", clause)
        if not any(t in words_in_family for t in tokens):
            continue
        negated = any(t in _NEGATORS for t in tokens)
        # A clause asserting the concept positively wins: if any clause states
        # it plainly, the text as a whole asserts it.
        if not negated:
            return False
        seen = True
    return seen


#: Source wording that prohibits a drug outright.
_PROHIBITION = re.compile(
    r"\b(?:avoid|contraindicated|do not use|should not be used|discontinue|"
    r"not recommended)\b",
    re.IGNORECASE,
)

#: Candidate wording that affirmatively directs use of the drug.
_AFFIRMATIVE_USE = re.compile(
    r"\b(?:use|uses|using|take|takes|taking|start|starts|starting|initiate|"
    r"initiates|continue|continues|continuing|proceed)\b",
    re.IGNORECASE,
)


def prohibition_conflict(sentence: str, source: str) -> str | None:
    """
    The source prohibits the drug; the sentence tells the reader to use it.

    A separate rule from `polarity_of` because the candidate need not mention
    the prohibition concept at all — "Use azathioprine at the standard dose"
    contradicts "Avoid azathioprine" by omission, so there is no shared concept
    whose polarity could be compared. This is the highest-consequence
    contradiction the checker can face, so it gets its own rule.
    """
    if not _PROHIBITION.search(source):
        return None
    for clause in _clauses(sentence):
        tokens = re.findall(r"[a-z][a-z\-']*", clause)
        if not _AFFIRMATIVE_USE.search(clause):
            continue
        # An affirmative directive that is itself negated is fine
        # ("do not start therapy"), as is one that defers to a clinician.
        if any(t in _NEGATORS for t in tokens):
            continue
        # "Avoid use of X" restates the prohibition — the verb "use" is the
        # object of the prohibition, not a directive. Without this the sentence
        # would be flagged for agreeing with its source.
        if _PROHIBITION.search(clause):
            continue
        return (
            "prohibition: source prohibits the drug "
            f"({_PROHIBITION.search(source).group(0)!r}) but the sentence directs use "
            f"({_AFFIRMATIVE_USE.search(clause).group(0)!r})"
        )
    return None


#: Concept families where negation inverts a clinical INSTRUCTION, and is
#: therefore worth flagging.
#:
#: `mechanism` is deliberately excluded. Describing reduced enzyme function
#: negates mechanism words as a matter of ordinary English — "your body cannot
#: break this down" is the correct rendering of "reduced function", not a
#: contradiction of it. Including it produced 6 false positives on the first
#: real generation run. `harm`/`severity` are excluded for the same reason: a
#: normal-metaboliser explanation correctly says "you are NOT at higher risk",
#: which conflicts with the general risk language elsewhere in the source.
POLARITY_FAMILIES = ("direction_down", "direction_up", "switch")


def polarity_conflicts(sentence: str, source: str) -> list[str]:
    """
    Concepts whose polarity differs between the sentence and the directive.

    Checked in BOTH directions: asserting something the source negates is as
    wrong as negating something the source asserts.

    **`source` must be the CPIC recommendation alone, not the concatenated
    corpus.** Polarity is a property of an instruction, and the mechanism corpus
    describes every phenotype — so checking against it let a clause about a
    different patient decide the polarity of this one. That produced 4 further
    false positives before being narrowed.
    """
    conflicts: list[str] = []
    for concept in POLARITY_FAMILIES:
        candidate_polarity = polarity_of(sentence, concept)
        if candidate_polarity is None:
            continue
        source_polarity = polarity_of(source, concept)
        if source_polarity is None:
            continue
        if candidate_polarity != source_polarity:
            conflicts.append(
                f"{concept}: sentence={'negated' if candidate_polarity else 'asserted'}, "
                f"source={'negated' if source_polarity else 'asserted'}"
            )
    prohibition = prohibition_conflict(sentence, source)
    if prohibition:
        conflicts.append(prohibition)
    return conflicts


# --------------------------------------------------------------------------- #
# Mechanism closed-vocabulary check
# --------------------------------------------------------------------------- #
#
# The sensitivity check named a miss this closes: "The enzyme is inhibited by
# grapefruit juice, which raises plasma levels." contains no number, no
# duration, and no unknown concept word, so every assertion rule passed it. A
# fabricated causal mechanism can be built entirely from ordinary words.
#
# For MECHANISM only, the vocabulary is therefore closed: a biomedical or causal
# content term must appear in the cited corpus for that gene-drug pair.
#
# Deliberately NOT applied to `patient_friendly`. Lexical checking on plain
# language is exactly what the provenance diagnosis proved unsound — rendering
# "leukopenia" as "low white blood cell count" introduces words no clinical
# source contains, and that is the field working correctly, not failing.

#: Abstract nouns that are grammatically nouns but carry no biomedical content.
#: A POS tagger keeps "ability", "result" and "process" because they ARE nouns;
#: they are excluded here because being outside the corpus tells us nothing.
_ABSTRACT_NOUNS = frozenset("""
ability abilities result results effect effects way ways level levels amount
amounts rate rates process processes function functions response responses
type types kind kinds form forms case cases term terms part parts point points
reason reasons factor factors change changes difference differences
person persons patient patients people body bodies someone individual individuals
doctor doctors pharmacist pharmacists provider providers
drug drugs medicine medicines medication medications dose doses therapy therapies
treatment treatments gene genes result analysis test tests
information detail details example examples number numbers time times
condition conditions situation situations problem problems issue issues
""".split())

#: Minimum length for a checkable noun. Short nouns are overwhelmingly generic.
_MECHANISM_MIN_LEN = 4

#: Does the vocabulary check gate a release? **No.**
#:
#: A decision rule was recorded BEFORE tuning: keep it in the gate below a 15%
#: false-positive rate on real mechanism text, retire it at or above. Narrowing
#: to concrete nouns took it from 57% to 30% while preserving 5/5 planted
#: catches — a real improvement, and still above the line. It is retired from
#: the gate rather than tuned further, because the first detector was tuned
#: 12 -> 4 -> 0 and ended up blunted; honouring a pre-committed threshold is the
#: safeguard against repeating that.
#:
#: It remains a measured capability: it still runs, still reports, and its
#: output is shown to the adjudicator as a hint. What replaces it as the
#: safeguard is MANDATORY individual adjudication of every mechanism sentence.
MECHANISM_VOCAB_GATES = False

#: Because the vocabulary check does not gate, mechanism sentences cannot be
#: bulk-accepted — each is read individually.
MECHANISM_REQUIRES_INDIVIDUAL_ADJUDICATION = True

_NLP = None
_NLP_TRIED = False


def _tagger():
    """
    Load the POS tagger once, lazily, and tolerate its absence.

    Lazy and optional on purpose: this check is BUILD-TIME only. The deployed
    service never calls it, so spaCy must never become a runtime dependency of
    the served path — importing it at module scope would make the API refuse to
    start without a package it does not use.
    """
    global _NLP, _NLP_TRIED
    if _NLP_TRIED:
        return _NLP
    _NLP_TRIED = True
    try:
        import spacy

        _NLP = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])
    except Exception:  # noqa: BLE001 — absent package or model
        _NLP = None
    return _NLP


def _inflections(word: str) -> set[str]:
    """
    Surface forms to treat as the same term.

    Crude on purpose: a real stemmer is another dependency, and the failure mode
    here is a visible false positive rather than a silent pass.
    """
    forms = {word}
    for suffix, stem in (("ies", "y"), ("es", ""), ("s", ""), ("ed", ""),
                         ("ing", ""), ("d", ""), ("ly", "")):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            forms.add(word[: -len(suffix)] + stem)
    forms |= {word + "s", word + "es", word + "e"}
    return forms


def _mechanism_terms(text: str) -> set[str]:
    """
    Concrete nouns worth checking against the corpus.

    NOUN/PROPN only. The first implementation checked every content word and
    produced a **57% false-positive rate** on real mechanism prose, flagging
    `genetic`, `well`, `properly`, `ability`, `effectively` — adjectives,
    adverbs and abstract nouns. A fabricated mechanism is a fabricated *thing*
    ("grapefruit juice"), so restricting to nouns targets the actual failure
    mode instead of penalising ordinary explanatory English.

    With no tagger available the check degrades to returning nothing, so it
    cannot silently fall back to the noisy behaviour it replaced.
    """
    nlp = _tagger()
    if nlp is None:
        return set()
    doc = nlp(_SLOT.sub(" ", text))
    out = set()
    for token in doc:
        if token.pos_ not in ("NOUN", "PROPN"):
            continue
        word = token.text.lower().strip("-")
        if len(word) < _MECHANISM_MIN_LEN or word in _ABSTRACT_NOUNS:
            continue
        if not word.isalpha() and "-" not in word:
            continue
        out.add(word)
    return out


def mechanism_vocabulary_violations(sentence: str, corpus: str) -> list[str]:
    """
    Concrete nouns in a mechanism sentence that the cited corpus never uses.

    Singular/plural and simple inflections are tolerated, so "metabolites"
    matches a corpus saying "metabolite". Anything genuinely foreign — a drug, a
    food, an organ the corpus never mentions — is reported.
    """
    if not corpus.strip():
        return []
    known = set()
    for word in re.findall(r"[a-z][a-z\-]{2,}", corpus.lower()):
        known |= _inflections(word)
    return sorted(
        term for term in _mechanism_terms(sentence) if not (_inflections(term) & known)
    )


@dataclass
class SentenceVerdict:
    field_name: str
    text: str
    policy: str
    verified: bool
    assertions: list[Assertion] = field(default_factory=list)
    unsupported: list[Assertion] = field(default_factory=list)
    #: Concepts whose negation does not match the source's, in either direction.
    polarity: list[str] = field(default_factory=list)
    #: Mechanism-field concrete nouns absent from the cited corpus. REPORTED,
    #: not gating: measured at a 30% false-positive rate, above the 15%
    #: threshold pre-committed before tuning. See MECHANISM_VOCAB_GATES.
    foreign_terms: list[str] = field(default_factory=list)

    @property
    def is_framing(self) -> bool:
        return not self.assertions

    @property
    def reason(self) -> str:
        if self.verified:
            return "framing (no clinical assertion)" if self.is_framing else "all assertions trace"
        parts = []
        if self.unsupported:
            parts.append("unsupported: " + ", ".join(str(a) for a in self.unsupported))
        if self.polarity:
            parts.append("POLARITY: " + "; ".join(self.polarity))
        if self.foreign_terms:
            parts.append("NOT IN CORPUS: " + ", ".join(self.foreign_terms))
        return " | ".join(parts)


def check_sentence(
    field_name: str,
    sentence: str,
    source: str,
    directive: str | None = None,
    corpus: str | None = None,
) -> SentenceVerdict:
    """
    Apply the field's policy to one sentence.

    `source` is everything the claim may draw on (CPIC text + corpus).
    `directive` is the CPIC recommendation alone — polarity is checked against
    it, because an instruction's polarity cannot be judged against background
    prose describing other patients. Defaults to `source` for callers that have
    only one.
    """
    policy = FIELD_POLICY.get(field_name, CLAIM_LEVEL)
    assertions = extract_assertions(sentence)
    unsupported = [a for a in assertions if not assertion_traces(a, source)]
    # Polarity is checked even when every assertion traces: a negated claim
    # reuses exactly the source's vocabulary, which is why the old checker
    # passed it.
    polarity = polarity_conflicts(sentence, directive if directive is not None else source)
    # Closed vocabulary, mechanism only. See the block comment above
    # `mechanism_vocabulary_violations` for why this is not applied elsewhere.
    foreign = (
        mechanism_vocabulary_violations(sentence, corpus)
        if field_name == "mechanism" and corpus
        else []
    )
    return SentenceVerdict(
        field_name=field_name,
        text=sentence,
        policy=policy,
        # `foreign` deliberately does NOT gate — see MECHANISM_VOCAB_GATES.
        verified=not unsupported and not polarity,
        assertions=assertions,
        unsupported=unsupported,
        polarity=polarity,
        foreign_terms=foreign,
    )


def check_verbatim(served: str, pharmcat_text: str) -> bool:
    """
    The recommendation must be byte-identical to PharmCAT's own output.

    Whitespace is normalised because JSON round-tripping can reflow it; nothing
    else is tolerated. This field is never model-authored, so any difference is
    a defect, not a paraphrase.
    """
    return " ".join(served.split()) == " ".join(pharmcat_text.split())
