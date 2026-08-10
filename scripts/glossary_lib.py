#!/usr/bin/env python3
"""
Shared machinery for the glossary coverage audit.

WHY THIS EXISTS

The glossary was verified against the schema — every field name the API sends
has a definition. The prose was verified against CPIC — every clinical sentence
traces to a recommendation. Nobody ever checked the glossary against the prose.

Two artifacts, each correct against its own source, never compared to each
other. The demo surfaced it by accident: the shipped explanation for clopidogrel
says "prodrug" and "enzyme", and neither word had a definition.

Fixing that by hand would close the two gaps that happened to be visible and
leave the mechanism intact for the next regeneration. So this module reads the
shipped strings, extracts domain vocabulary mechanically, and the gate in
`glossary_status.py` refuses to pass while any of it is undefined and unsorted.

WHAT IT DOES NOT DO

It does not decide whether a word is biomedical. There is no keyword list and no
model judging meaning — that is precisely the kind of rule this project has
already watched fail. It tags parts of speech, looks up how common a word is in
ordinary English, and hands everything rare to a human.

The rule and its thresholds were recorded in `reports/glossary_precommitment.md`
before this was run over the corpus.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

#: Recorded in the pre-commitment. One occurrence per 10,000 words — the
#: conventional boundary on the Zipf scale between everyday vocabulary and
#: words a general reader may not hold.
ZIPF_THRESHOLD = 4.0

#: Parts of speech kept. Narrowed to nouns because the mechanism vocabulary
#: check measured adjectives and verbs as its largest noise source (57% -> 30%).
KEEP_POS = frozenset({"NOUN", "PROPN"})

DECISIONS_PATH = REPO / "reports" / "glossary_decisions.json"
GLOSSARY_DART = REPO / "app" / "lib" / "glossary" / "glossary.dart"
CONTROL_CORPUS = REPO / "test-data" / "glossary" / "ordinary_english_control.txt"


# --------------------------------------------------------------------------- #
# Where user-facing strings live
# --------------------------------------------------------------------------- #

#: Python modules whose string literals reach a user. Docstrings and comments
#: are excluded by the AST walk — they are written for maintainers.
PY_SOURCES: tuple[str, ...] = (
    "backend/app/explanation/generator_template.py",
    "backend/app/explanation/compose.py",
    "backend/app/coverage.py",
    "backend/app/main.py",
    "backend/app/models.py",
    "backend/app/vcf_validation.py",
    "backend/app/cpic_engine.py",
    "backend/app/pharmcat_runner.py",
)

#: Dart files whose string literals reach a user.
DART_SOURCES: tuple[str, ...] = (
    "app/lib/models/unknown_reason.dart",
    "app/lib/models/enums.dart",
    "app/lib/screens/about_screen.dart",
    "app/lib/screens/home_screen.dart",
    "app/lib/screens/results_screen.dart",
    "app/lib/widgets/coverage_census.dart",
    "app/lib/widgets/coverage_summary.dart",
    "app/lib/widgets/file_readiness.dart",
    "app/lib/widgets/unknown_reason_panel.dart",
    "app/lib/widgets/verdict_card.dart",
    "app/lib/widgets/summary_grid.dart",
    "app/lib/widgets/view_mode.dart",
    "app/lib/widgets/view_toggle.dart",
    "app/lib/widgets/disclosure_row.dart",
    "app/lib/widgets/disclaimer_banner.dart",
    "app/lib/widgets/backend_status_banner.dart",
    "app/lib/print/summary_document.dart",
    "app/lib/config.dart",
    # The definitions are scanned too. A definition that introduces new jargon
    # is the failure mode this whole audit is about, one level down.
    "app/lib/glossary/glossary.dart",
)

#: Functions whose strings reach an OPERATOR and never a user: the startup log,
#: `/ready`, and `PharmcatExecutionError.detail`. Their text names jars, Java
#: runtimes and environment variables on purpose, because the person reading it
#: has a shell and can act on them.
#:
#: This is an exclusion by function, not by file. The pre-commitment forbids
#: narrowing the scan by dropping a source, and dropping `pharmcat_runner.py`
#: would also hide the 503 message a user really does see. Listing the one
#: function keeps the exclusion visible and auditable — and
#: `test_the_operator_detail_was_moved_and_not_deleted` proves the text still
#: exists rather than having been quietly softened.
OPERATOR_ONLY: dict[str, frozenset[str]] = {
    # `unavailable_reason` is the startup log and /ready. `_exec` builds
    # `PharmcatExecutionError.detail`, which reaches the log and never a
    # response body — the user-facing half of that error is
    # UNAVAILABLE_USER_MESSAGE, which IS scanned.
    "backend/app/pharmcat_runner.py": frozenset({"unavailable_reason", "_exec"}),
    # The FastAPI app title and description render in /docs, which is an API
    # reference for a developer. Not the product's voice; not shown to anyone
    # who uploaded a file.
    "backend/app/main.py": frozenset({"_app_metadata"}),
}

EXPLANATIONS_JSON = "backend/app/data/explanations.json"

#: Prose fields of a shipped explanation. Everything a reader sees.
EXPLANATION_FIELDS = ("summary", "mechanism", "variant_rationale", "patient_friendly")


@dataclass
class Snippet:
    """One user-facing string, with where it came from."""

    text: str
    source: str


# --------------------------------------------------------------------------- #
# String-literal collection
# --------------------------------------------------------------------------- #

#: A literal counts as prose at four words and twenty characters. Below that it
#: is a label, a key or an identifier, and it carries no sentence to mine.
MIN_TOKENS = 4
MIN_CHARS = 20


#: Markup and stylesheet blobs. The printable summary embeds a whole CSS sheet
#: as a Dart string; it is long, mostly letters and full of spaces, so it passes
#: every prose heuristic while being read by nobody. Left in, it contributed
#: `consolas`, `menlo`, `monospace`, `tbody`, `thead` and `fff` to the candidate
#: list — noise that would have been sorted by a human for no reason.
#:
#: This is source selection, not threshold tuning: a stylesheet is not a string
#: this project shows a user, so it was never in scope.
_CODEY = (
    re.compile(r"[{;]\s*[a-z-]+\s*:"),      # css declarations
    re.compile(r"</?[a-z]+[ >]"),            # html tags
    re.compile(r"^[a-z]+(?:[A-Z][a-z]+)+$"), # a lone camelCase identifier
)


def _is_prose(value: str) -> bool:
    if len(value) < MIN_CHARS or len(value.split()) < MIN_TOKENS:
        return False
    # Reject things that are structurally code even when they are long: URLs,
    # paths, format-spec soup. Prose in this project contains none of these.
    if "://" in value or value.strip().startswith("/"):
        return False
    if any(rx.search(value) for rx in _CODEY):
        return False
    letters = sum(c.isalpha() or c.isspace() for c in value)
    return letters / len(value) >= 0.75


def _python_literals(path: Path, skip_functions: frozenset[str] = frozenset()) -> list[str]:
    """String literals from a module, minus docstrings and operator-only text."""
    tree = ast.parse(path.read_text())

    skipped: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name in skip_functions:
            for inner in ast.walk(node):
                skipped.add(id(inner))
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and \
                    isinstance(body[0].value, ast.Constant) and \
                    isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))

    out: list[str] = []
    for node in ast.walk(tree):
        if id(node) in skipped:
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docstrings:
            out.append(node.value)
        # f-strings: keep the literal parts, drop the interpolations. A
        # `{gene}` slot carries no vocabulary of its own.
        elif isinstance(node, ast.JoinedStr) and id(node) not in skipped:
            joined = "".join(
                v.value for v in node.values
                if isinstance(v, ast.Constant) and isinstance(v.value, str)
            )
            if joined:
                out.append(joined)
    return out


#: `${expr}` and bare `$identifier`. Both are code, not words on screen.
_DART_INTERP = re.compile(r"\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*")

_DART_COMMENT = re.compile(r"^\s*//.*$", re.M)
_DART_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
#: Single- and double-quoted Dart literals, including the triple-quoted form.
_DART_STRING = re.compile(
    r"'''(.*?)'''|\"\"\"(.*?)\"\"\"|'((?:[^'\\\n]|\\.)*)'|\"((?:[^\"\\\n]|\\.)*)\"",
    re.S,
)


def _dart_literals(path: Path) -> list[str]:
    """
    String literals from a Dart file, minus comments.

    Adjacent literals are joined: this codebase wraps long prose as
    `'first half ' 'second half'`, and treating those as two strings would
    split sentences in the middle and lose the noun phrases that cross the join.
    """
    src = _DART_BLOCK_COMMENT.sub(" ", path.read_text())
    src = _DART_COMMENT.sub("", src)

    pieces: list[tuple[int, int, str]] = []
    for m in _DART_STRING.finditer(src):
        value = next((g for g in m.groups() if g is not None), "")
        pieces.append((m.start(), m.end(), value))

    out: list[str] = []
    buffer, last_end = "", -1
    for start, end, value in pieces:
        gap = src[last_end:start] if last_end >= 0 else "x"
        if last_end >= 0 and gap.strip() == "":
            buffer += value
        else:
            if buffer:
                out.append(buffer)
            buffer = value
        last_end = end
    if buffer:
        out.append(buffer)

    # `\n` and friends survive the regex as escapes; normalise so the tagger
    # sees sentences rather than backslashes.
    #
    # Interpolations are dropped, exactly as f-string slots are on the Python
    # side. `${c.positionsPresent}` is a number by the time anyone reads it —
    # leaving the identifier in made the scanner report `positionsPresent` as
    # vocabulary shown to a user, which it never is. Both languages are now
    # treated the same way, which is what made the asymmetry visible.
    return [_DART_INTERP.sub(" ", b)
            .replace("\\n", " ").replace("\\'", "'").replace('\\"', '"')
            for b in out]


def collect_snippets() -> list[Snippet]:
    """Every user-facing string in the project, with its origin."""
    out: list[Snippet] = []

    data = json.loads((REPO / EXPLANATIONS_JSON).read_text())
    for entry in data.get("explanations", []):
        explanation = entry.get("explanation") or {}
        label = f"explanations.json[{entry.get('drug')}/{entry.get('gene')}]"
        for field_name in EXPLANATION_FIELDS:
            value = explanation.get(field_name)
            if isinstance(value, str) and value.strip():
                out.append(Snippet(value, f"{label}.{field_name}"))
        # The CPIC text is quoted verbatim to the user, so its vocabulary is
        # on screen too — even though its wording is not ours to change.
        quoted = entry.get("cpic_recommendation_used")
        if isinstance(quoted, str) and quoted.strip():
            out.append(Snippet(quoted, f"{label}.cpic_recommendation_used"))

    for rel in PY_SOURCES:
        path = REPO / rel
        if not path.exists():
            continue
        for value in _python_literals(path, OPERATOR_ONLY.get(rel, frozenset())):
            if _is_prose(value):
                out.append(Snippet(value, rel))

    for rel in DART_SOURCES:
        path = REPO / rel
        if not path.exists():
            continue
        for value in _dart_literals(path):
            if _is_prose(value):
                out.append(Snippet(value, rel))

    return out


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #

@lru_cache(maxsize=1)
def _nlp():
    import spacy

    # Parser kept: noun chunks need it, and phrase candidates ("star allele",
    # "position coverage") are the ones a single-token scan would miss.
    return spacy.load("en_core_web_sm", disable=["ner"])


@lru_cache(maxsize=None)
def zipf(word: str) -> float:
    from wordfreq import zipf_frequency

    return zipf_frequency(word, "en")


_WORDLIKE = re.compile(r"^[a-z][a-z\-]*[a-z]$")


def is_candidate_lemma(lemma: str) -> bool:
    """A rare noun. No judgement about meaning is made anywhere in here."""
    return bool(_WORDLIKE.match(lemma)) and zipf(lemma) < ZIPF_THRESHOLD


@dataclass
class Candidate:
    term: str
    count: int = 0
    contexts: list[tuple[str, str]] = field(default_factory=list)  # (source, line)
    #: Every source this term was seen in, not just the first. Needed to tell a
    #: term that appears in the FROZEN explanation prose from one that appears
    #: only in text somebody is still free to rewrite.
    sources: set[str] = field(default_factory=set)
    #: Sentences it appeared in, for the dependency graph.
    sentences: list[str] = field(default_factory=list)

    @property
    def zipf(self) -> float:
        return zipf(self.term)


#: Every term the lemmatiser damaged, and why. Populated by `extract`; read by
#: the report so the drops are visible rather than silent.
DROPPED_ARTIFACTS: dict[str, str] = {}


def _is_artifact(lemma: str, surface: str, corpus_text: str) -> str | None:
    """
    Why this lemma is lemmatiser damage rather than vocabulary, or None.

    Two distinct failures, both of which put non-vocabulary in front of a human
    reviewer:

    **Mangled into a non-word.** `anti-inflammatories` lemmatises to
    `inflammatorie`, and `bcftools` to `bcftool`. Neither is in any dictionary
    and neither appears in the text — nobody can define a word that does not
    exist.

    **Made rare by lemmatising.** `data` becomes `datum`. The lemma is a real
    word and a rare one; the word on screen is `data`, which everybody knows.
    Judging rarity on a form the reader never sees measures the wrong thing.
    """
    if lemma == surface:
        return None

    # "Is it a word?" is answered by the frequency table, not by the system
    # dictionary. `/usr/share/dict/web2` is Webster's 1934: it has no
    # `hepatocyte` and spells `coordinate` with a diaeresis, so using it here
    # dropped two genuine clinical terms as though they were tagger damage.
    # A word with any measured usage at all is a word.
    verbatim = re.search(rf"\b{re.escape(lemma)}\b", corpus_text, re.I) is not None
    if zipf(lemma) == 0.0 and lemma not in reference_vocabulary() and not verbatim:
        return f"not a word: lemmatised from {surface!r}, absent from the text"

    # The reader meets the surface form. If that is ordinary English, the
    # lemma's rarity is an artifact of the tagger, not a fact about the reader.
    if zipf(surface) >= ZIPF_THRESHOLD:
        return (f"surface form {surface!r} is ordinary English "
                f"(zipf {zipf(surface):.2f}); only the lemma is rare")

    return None


def extract(snippets: list[Snippet]) -> dict[str, Candidate]:
    """Rare noun lemmas across every snippet, with one context line each."""
    nlp = _nlp()
    found: dict[str, Candidate] = {}
    corpus_text = "\n".join(s.text for s in snippets)

    for snippet in snippets:
        doc = nlp(snippet.text)
        for token in doc:
            if token.pos_ not in KEEP_POS:
                continue
            lemma = token.lemma_.lower().strip()
            if not is_candidate_lemma(lemma):
                continue
            artifact = _is_artifact(lemma, token.text.lower().strip(), corpus_text)
            if artifact:
                DROPPED_ARTIFACTS.setdefault(lemma, artifact)
                continue
            cand = found.setdefault(lemma, Candidate(lemma))
            cand.count += 1
            cand.sources.add(snippet.source)
            sentence = _context_line(snippet.text, token)
            if sentence not in cand.sentences:
                cand.sentences.append(sentence)
            if len(cand.contexts) < 1:
                cand.contexts.append((snippet.source, sentence))
    return found


def _context_line(text: str, token) -> str:
    """The sentence the term appeared in, trimmed to something quotable."""
    sent = token.sent.text.strip() if token.sent is not None else text
    sent = " ".join(sent.split())
    return sent if len(sent) <= 200 else sent[:197] + "..."


def extract_phrases(snippets: list[Snippet]) -> dict[str, int]:
    """
    Noun chunks containing at least one candidate — "star allele", "poor
    metaboliser". Reported alongside the single words so a reviewer can define
    the phrase a reader actually meets rather than its rarest half.
    """
    nlp = _nlp()
    phrases: dict[str, int] = {}
    for snippet in snippets:
        for chunk in nlp(snippet.text).noun_chunks:
            words = [t for t in chunk if t.pos_ in KEEP_POS or t.pos_ == "ADJ"]
            if not (2 <= len(words) <= 3):
                continue
            if not any(is_candidate_lemma(t.lemma_.lower()) for t in words):
                continue
            text = " ".join(w.text.lower() for w in words)
            phrases[text] = phrases.get(text, 0) + 1
    return phrases


# --------------------------------------------------------------------------- #
# The two decision sources
# --------------------------------------------------------------------------- #

_DART_TERM = re.compile(r"term:\s*'([^']+)'")
_DART_ALIASES = re.compile(r"aliases:\s*<String>\[(.*?)\]", re.S)


def defined_forms() -> set[str]:
    """Every spelling the shipped glossary already answers to."""
    src = GLOSSARY_DART.read_text()
    forms: set[str] = set()
    for block in src.split("GlossaryTerm(")[1:]:
        term = _DART_TERM.search(block)
        if term:
            forms.add(term.group(1).lower())
        aliases = _DART_ALIASES.search(block)
        if aliases:
            forms.update(a.strip().strip("'\"").lower()
                         for a in aliases.group(1).split(",") if a.strip())
    return {f for f in forms if f}


def load_decisions() -> dict:
    if not DECISIONS_PATH.exists():
        return {"decisions": {}}
    return json.loads(DECISIONS_PATH.read_text())


def decided_ordinary() -> set[str]:
    """Terms a human has explicitly marked as ordinary English."""
    decisions = load_decisions().get("decisions", {})
    return {
        term.lower() for term, record in decisions.items()
        if record.get("decision") == "ordinary"
    }


def decided_defined() -> set[str]:
    """Terms a human has written a definition for but that are not yet shipped."""
    decisions = load_decisions().get("decisions", {})
    return {
        term.lower() for term, record in decisions.items()
        if record.get("decision") == "define" and record.get("definition")
    }


def undefined(found: dict[str, Candidate]) -> list[Candidate]:
    """
    Candidates with no definition and no human decision.

    This is what the gate fails on. A term leaves this list one of two ways:
    somebody defines it, or somebody says it needs no definition. Neither is a
    thing this script may do on its own.
    """
    known = defined_forms() | decided_ordinary() | decided_defined()
    return sorted(
        (c for term, c in found.items() if term not in known),
        key=lambda c: (-c.count, c.term),
    )


# --------------------------------------------------------------------------- #
# The rule a definition must satisfy
# --------------------------------------------------------------------------- #

def definition_gaps(term: str, definition: str,
                    extra_known: set[str] | None = None) -> list[str]:
    """
    Candidate terms a definition introduces without defining them.

    This is the failure this whole audit is about, one level down: explaining
    "diplotype" as "your pair of star alleles" is accurate, passes any review
    that checks correctness, and is useless to the only person who would ever
    tap it. A definition may lean on another term only when that term is itself
    answerable.

    The term being defined is allowed to appear — "most variants change
    nothing" after defining `variant` is ordinary English, not circularity.
    """
    known = defined_forms() | decided_ordinary() | decided_defined()
    known |= {term.lower()} | {w.lower() for w in term.split()}
    known |= (extra_known or set())

    found = extract([Snippet(definition, f"definition:{term}")])
    return sorted(t for t in found if t not in known)


def sentence_count(definition: str) -> int:
    return len([s for s in re.split(r"[.!?]+", definition) if s.strip()])


# --------------------------------------------------------------------------- #
# Triage — sorting the candidate list before anyone writes a definition
#
# Roughly half of what the extractor finds is not glossary work at all. Two of
# the categories below are defects in the product rather than gaps in the
# documentation: a user who hits a failure should never be shown `bgzip` or
# `notApplicableReason`. Sorting first means the human review is spent on the
# words a patient actually needs, and the bugs get filed as bugs.
#
# Every rule here is evidence-based and mechanical. Where the evidence does not
# decide, the term is left unclassified for a person — this file never asserts
# that something is a clinical term, because that is the judgement it is not
# allowed to make.
# --------------------------------------------------------------------------- #

CATEGORIES = {
    "A": "candidate glossary term — for a human to confirm and define",
    "A1": "in the FROZEN explanation prose — must be defined, cannot be reworded",
    "A2": "only in editable text — reword the source instead of defining",
    "B": "drug name — already described in the About table",
    "C": "developer string in user-facing text — a BUG",
    "D": "extractor artifact — lemmatiser damage",
    "E": "code identifier in user-facing text — a BUG",
}

SYSTEM_DICT = Path("/usr/share/dict/words")


@lru_cache(maxsize=1)
def known_drugs() -> set[str]:
    """Drugs this build has guidance for, read from the mapping, not typed."""
    text = (REPO / "backend/app/data/label_mapping.yaml").read_text()
    if "drug_primary_gene:" not in text:
        return set()
    block = text.split("drug_primary_gene:")[1]
    return {m.lower() for m in re.findall(r"^\s{2}([a-z0-9_-]+):", block, re.M)}


@lru_cache(maxsize=1)
def reference_vocabulary() -> set[str]:
    """A general English dictionary. Used only to tell words from non-words."""
    if not SYSTEM_DICT.exists():
        return set()
    return {w.strip().lower() for w in SYSTEM_DICT.read_text().splitlines()}


@lru_cache(maxsize=1)
def source_identifiers() -> set[str]:
    """
    Every camelCase and snake_case identifier in the codebase, flattened.

    `notApplicableReason` -> `notapplicablereason`. When a candidate matches one
    of these it is not vocabulary at all — it is a variable name that reached a
    string, which is a bug with a one-line fix.
    """
    out: set[str] = set()
    for rel in list(PY_SOURCES) + list(DART_SOURCES):
        path = REPO / rel
        if not path.exists():
            continue
        for ident in re.findall(r"\b[a-z]+(?:[A-Z][a-z0-9]+)+\b", path.read_text()):
            out.add(ident.lower())
        for ident in re.findall(r"\b[a-z]+(?:_[a-z0-9]+)+\b", path.read_text()):
            out.add(ident.replace("_", ""))
    return out


@lru_cache(maxsize=1)
def tooling_vocabulary() -> set[str]:
    """
    Names of tools, packages and runtimes — gathered from the places that
    declare them as such, never from a list somebody typed.

    Deliberately narrow. An earlier version took every word out of the
    requirements files and the CI workflow, which classified `pharmacogenomic`
    as developer vocabulary because the word appears in a workflow comment.
    That is the failure mode of a keyword rule, arriving on schedule: it is not
    reading what a token *is*, only where it was seen.

    So this reads declarations: package names, dependency keys, and the first
    word of a shell command. A word has to be used as a tool to count as one.
    """
    out: set[str] = set()

    # Declared dependencies: the name before any version specifier.
    for rel in ("backend/requirements.txt", "backend/requirements-dev.txt"):
        path = REPO / rel
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.split("#")[0].strip()
            if line:
                out.add(re.split(r"[<>=!\[]", line)[0].strip().lower())

    # Dart dependencies: the keys under `dependencies:`.
    pubspec = REPO / "app/pubspec.yaml"
    if pubspec.exists():
        for block in re.findall(r"^dependencies:(.*?)^\S", pubspec.read_text(),
                                re.M | re.S):
            out.update(m.lower() for m in re.findall(r"^  ([a-z_][a-z0-9_]*):",
                                                     block, re.M))

    # The first word of a shell command — in CI run-steps and in the fenced
    # blocks of the input requirements, which is where tool names legitimately
    # live.
    commands: list[str] = []
    ci = REPO / ".github/workflows/test.yml"
    if ci.exists():
        for run in re.findall(r"run:\s*\|?\s*\n?((?:.*\n?)*?)(?=\n\s*-|\Z)",
                              ci.read_text()):
            commands.extend(run.splitlines())
    docs = REPO / "docs/input_requirements.md"
    if docs.exists():
        for fence in re.findall(r"```[a-z]*\n(.*?)```", docs.read_text(), re.S):
            commands.extend(fence.splitlines())
    for line in commands:
        line = line.strip()
        m = re.match(r"([a-z][a-z0-9_.-]*)", line)
        if m:
            out.add(m.group(1).lower())

    # An earlier version also scanned `["..."]` list literals in the backend,
    # intending to catch argv[0] of anything executed. It matched every list of
    # strings in the codebase instead, and classified `rationale` as a tool
    # because `["variant_rationale", ...]` exists somewhere. Removed rather
    # than patched: the declarations above are the honest evidence, and a
    # command this project runs is already named in a docs fence or a CI step.
    return {w for w in out if w and not w.startswith("-")}


#: Proper nouns this project shows a user on purpose. PharmCAT is named in the
#: provenance line and on the About screen; PharmaGuard is the product. Seeing
#: them is not a leak — not knowing what they are is a glossary question, so
#: they belong in A rather than being filed as bugs.
DISCLOSED_NAMES = frozenset({"pharmcat", "pharmaguard", "cpic"})


def categorise(term: str, corpus_text: str) -> str | None:
    """
    The category, or None when the evidence does not decide.

    Order matters: a lemma that is not a word at all cannot be a drug name, and
    an identifier is not vocabulary whatever else it looks like.
    """
    lemma = term.lower()

    # D — the lemmatiser mangled a real word. "anti-inflammatories" arrives as
    # `inflammatorie`, which is in no dictionary and appears nowhere in the
    # text. Checked first: a non-word cannot belong to any other category.
    vocab = reference_vocabulary()
    verbatim = re.search(rf"\b{re.escape(lemma)}\b", corpus_text, re.I) is not None
    if vocab and lemma not in vocab and not verbatim and zipf(lemma) == 0.0:
        return "D"

    # E — a variable name that reached a string.
    if lemma in source_identifiers() and lemma not in vocab:
        return "E"

    # B — a drug this build has CPIC guidance for.
    if lemma in known_drugs():
        return "B"

    # C — a tool, format or runtime name, evidenced by its use as one. Names
    # this project deliberately shows a user are excluded: they are vocabulary
    # to explain, not vocabulary that escaped.
    if lemma in tooling_vocabulary() and lemma not in DISCLOSED_NAMES:
        return "C"

    return None


def triage(found: dict[str, Candidate], snippets: list[Snippet]) -> dict[str, list[str]]:
    """Sort candidates into the five buckets. Residual lands in A."""
    corpus_text = "\n".join(s.text for s in snippets)
    buckets: dict[str, list[str]] = {k: [] for k in CATEGORIES}
    for term in found:
        buckets[categorise(term, corpus_text) or "A"].append(term)

    # A splits again by whether the text holding the term can be edited at all.
    a1, a2 = split_editable({t: found[t] for t in buckets["A"]})
    buckets["A1"], buckets["A2"] = a1, a2

    for key in buckets:
        buckets[key].sort()
    return buckets


@lru_cache(maxsize=1)
def about_table_descriptions() -> dict[str, str]:
    """
    The drug blurbs already written on the About screen.

    Offered to the reviewer as the definition for a category-B term so that
    nothing is rewritten. Two descriptions of the same drug, written months
    apart in different files, is the drift this whole audit is about.
    """
    src = (REPO / "app/lib/screens/about_screen.dart").read_text()
    out: dict[str, str] = {}
    # Rows look like: ['clopidogrel', 'preventing clots after a stent', 'a
    # prodrug — it must be switched on by CYP2C19...'].
    for row in re.finditer(r"\[\s*'([a-z][a-z0-9]+)',(.*?)\],", src, re.S):
        drug = row.group(1).lower()
        cells = re.findall(r"'((?:[^'\\]|\\.)*)'", row.group(2))
        if len(cells) < 2:
            continue
        used_for = " ".join(cells[0].split())
        out[drug] = f"A medicine used for {used_for}."
    return out


# --------------------------------------------------------------------------- #
# A1 / A2 — is the text this term lives in editable?
# --------------------------------------------------------------------------- #

def is_frozen_source(source: str) -> bool:
    """
    True for text that cannot be reworded to avoid a term.

    `explanations.json` is the frozen, provenance-verified, individually
    adjudicated store. Rewording a sentence there to dodge a hard word would
    orphan the adjudication decision attached to it — the recorded judgement
    would point at text that no longer exists. So a term appearing there must
    be DEFINED; rewriting is not an option that is actually available.

    Everything else — About copy, error messages, coverage warnings, UI labels,
    the printable summary — is ours to edit, so a hard word there is a choice
    rather than a constraint.
    """
    return source.startswith("explanations.json[")


def split_editable(candidates: dict[str, Candidate]) -> tuple[list[str], list[str]]:
    """
    (A1, A2). A term in both goes to A1: if it must be defined for the frozen
    prose, rewording the editable copy buys nothing.
    """
    a1, a2 = [], []
    for term, cand in candidates.items():
        (a1 if any(is_frozen_source(s) for s in cand.sources) else a2).append(term)
    return sorted(a1), sorted(a2)


# --------------------------------------------------------------------------- #
# Dependency order for the review queue
# --------------------------------------------------------------------------- #

def dependency_graph(terms: list[str],
                     candidates: dict[str, Candidate]) -> dict[str, set[str]]:
    """
    `X -> {Y, ...}`: terms likely to be needed while explaining X.

    Approximated by co-occurrence in the same sentence, which is the only
    evidence available before any definition exists. It is a heuristic and is
    labelled as one — its job is to order a queue so the human hits fewer
    refusals, not to be a semantic claim about the domain.
    """
    wanted = set(terms)
    graph: dict[str, set[str]] = {t: set() for t in terms}
    for term in terms:
        for sentence in candidates[term].sentences:
            lowered = sentence.lower()
            for other in wanted:
                if other != term and re.search(rf"\b{re.escape(other)}\b", lowered):
                    graph[term].add(other)
    return graph


def review_order(terms: list[str],
                 candidates: dict[str, Candidate]) -> tuple[list[str], list[list[str]]]:
    """
    Foundational terms first, plus any cycles found.

    The definition checker refuses a definition that leans on an undefined
    term, so a human working alphabetically hits refusal after refusal. Terms
    that many others depend on are offered first, so that by the time a
    dependent term comes up its prerequisites are already answered.

    Cycles are reported rather than silently broken — two terms that each need
    the other is a real property of the vocabulary, and which one to define
    first in plainer words is a judgement for the person, not for a sort.
    """
    graph = dependency_graph(terms, candidates)

    # How many other terms lean on this one. High = foundational.
    needed_by: dict[str, int] = {t: 0 for t in terms}
    for term, deps in graph.items():
        for dep in deps:
            needed_by[dep] += 1

    cycles = _find_cycles(graph)
    in_cycle = {t for cycle in cycles for t in cycle}

    ordered = sorted(
        terms,
        key=lambda t: (
            # Terms nobody else needs and that need nothing come last.
            -needed_by[t],
            # Fewer prerequisites of its own = safer to define early.
            len(graph[t] - in_cycle),
            -candidates[t].count,
            t,
        ),
    )
    return ordered, cycles


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """
    Mutually-dependent CLUSTERS, not pairs.

    An earlier version reported every mutually-linked pair as a cycle and found
    61 of them. That number was an artifact of the method, not a property of
    the vocabulary: co-occurrence is a symmetric relation, so *every* pair that
    co-occurs is trivially a two-cycle. Reporting them as discovered structure
    would have been a measurement dressed up as a finding.

    What is genuinely useful is the connected components of the mutual graph:
    groups of terms that all talk about each other, which a human should look
    at together and deliberately pick an entry point into. Those are real, and
    there are far fewer of them.
    """
    mutual: dict[str, set[str]] = {
        a: {b for b in deps if a in graph.get(b, set())}
        for a, deps in graph.items()
    }

    seen: set[str] = set()
    clusters: list[list[str]] = []
    for start in mutual:
        if start in seen or not mutual[start]:
            continue
        stack, group = [start], set()
        while stack:
            node = stack.pop()
            if node in group:
                continue
            group.add(node)
            stack.extend(mutual.get(node, set()) - group)
        seen |= group
        if len(group) > 1:
            clusters.append(sorted(group))
    return sorted(clusters, key=lambda c: (-len(c), c))
