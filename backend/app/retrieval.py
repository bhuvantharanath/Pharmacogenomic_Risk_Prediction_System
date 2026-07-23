"""
PharmaGuard — mechanism retrieval.

WHY THERE IS NO VECTOR DATABASE HERE
------------------------------------
The retrieval space is six documents, keyed by a pair of controlled vocabulary
terms (an HGNC gene symbol and a drug name that PharmCAT already normalised).
That is a dictionary lookup, not a search problem.

Embeddings would buy nothing and cost several things that matter to this
project:

  * **Correctness.** Nearest-neighbour search can return the *wrong* document
    with high confidence. With six clinically distinct pairs — where CYP2C19
    means "prodrug not activated" and DPYD means "drug not cleared" — a
    near-miss is not a slightly worse answer, it is a mechanism explanation
    attached to the wrong drug.
  * **Auditability.** "Row (CYP2C19, clopidogrel) of a table" is reviewable by a
    faculty guide. "Cosine similarity 0.83 in a 768-dimensional space" is not.
  * **Cost and dependencies.** Embedding models, a vector store, and an index
    build step, all to replace a `dict.get()`.

If the corpus ever grows past a few dozen documents *and* free-text queries
become a requirement, revisit. Until then, exact lookup is the correct
engineering choice, not a shortcut.

A miss returns None. Callers degrade — the template generator produces a
mechanism-free explanation rather than failing.
"""

from __future__ import annotations

import functools
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


def _resolve_corpus_dir() -> Path:
    """
    Locate `rag-corpus/mechanisms`, in the repo and in the container.

    The two layouts differ, and a hard-coded relative path silently breaks one
    of them. In the repo the module is `backend/app/retrieval.py`, so the corpus
    is two levels up. In the Docker image `app/` is copied to
    `/opt/pharmaguard/app`, dropping the `backend/` level, so the same
    expression resolves to `/opt/rag-corpus` — which does not exist.

    That failure mode is quiet and bad: every lookup returns None, every
    explanation loses its mechanism section, and nothing errors. So we check
    candidates and let the environment override.
    """
    override = os.environ.get("PHARMAGUARD_CORPUS_DIR")
    if override:
        return Path(override)

    here = Path(__file__).resolve()
    candidates = (
        here.parents[2] / "rag-corpus" / "mechanisms",  # repo: backend/app/..
        here.parents[1] / "rag-corpus" / "mechanisms",  # container: app/..
        Path("/opt/pharmaguard/rag-corpus/mechanisms"),  # container, absolute
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    # Nothing found: return the repo-relative path so error messages point
    # somewhere meaningful, and let callers degrade.
    return candidates[0]


CORPUS_DIR = _resolve_corpus_dir()

# Front matter is a small, fixed YAML block. Parsed with PyYAML (already a
# dependency for label_mapping.yaml).
_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)

# Markdown emphasis around a word, e.g. *CYP2C19*. The leading-letter
# requirement keeps star alleles (*2, *3A, *2xN) safe.
_MARKDOWN_EMPHASIS = re.compile(r"\*([A-Za-z][A-Za-z0-9\-]*)\*")


@dataclass(frozen=True)
class MechanismDocument:
    """One mechanism file: its provenance metadata and its prose."""

    gene: str
    drug: str
    body: str
    source_guideline: str = ""
    source_url: str = ""
    primary_citation: str = ""
    retrieved: str = ""
    contains_dosing: bool = False
    reviewed_by: str | None = None
    aliases: tuple[str, ...] = ()
    path: Path | None = None

    @property
    def citation_line(self) -> str:
        """One-line provenance, for the `source` field of a response."""
        parts = [p for p in (self.source_guideline, self.primary_citation) if p]
        return " — ".join(parts) if parts else "PharmaGuard mechanism corpus"

    def snippet(self, max_chars: int = 2000) -> str:
        """
        The prose handed to the LLM (or template) as grounding context.

        Front matter is stripped: the model should see the mechanism, not the
        citation metadata, which it might otherwise copy into its output and
        trip the guard's numeric checks on a PMID.
        """
        text = self.body.strip()
        if len(text) <= max_chars:
            return text
        # Cut at a paragraph boundary so the snippet never ends mid-sentence.
        cut = text.rfind("\n\n", 0, max_chars)
        return text[: cut if cut > max_chars // 2 else max_chars].rstrip()

    def prose(self, max_chars: int = 2000) -> str:
        """
        `snippet()` reflowed for display in a UI.

        The corpus files are hard-wrapped at ~76 columns for reviewable diffs,
        but those newlines are an artifact of the source format, not of the
        sentence. Rendered verbatim in the app they produce ragged, prematurely
        broken lines. Markdown emphasis is stripped for the same reason —
        `*CYP2C19*` reaches the client as literal asterisks.

        The emphasis pattern requires a leading letter, so star alleles (`*2`,
        `*3A`) are never touched.
        """
        text = _MARKDOWN_EMPHASIS.sub(r"\1", self.snippet(max_chars))
        # Collapse single newlines inside a paragraph; keep blank-line breaks.
        return "\n\n".join(
            " ".join(part.split()) for part in text.split("\n\n") if part.strip()
        )


def _parse_document(path: Path) -> MechanismDocument | None:
    """Parse one corpus file. Returns None (not an exception) if unusable."""
    import yaml

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None

    match = _FRONT_MATTER.match(raw)
    if match is None:
        # A file with no front matter has no provenance, so it is not usable as
        # a grounding source. Skipping is safer than guessing its gene/drug.
        return None

    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(meta, dict):
        return None

    gene = str(meta.get("gene") or "").strip()
    drug = str(meta.get("drug") or "").strip()
    if not gene or not drug:
        return None

    aliases = meta.get("aliases") or []
    if not isinstance(aliases, list):
        aliases = []

    return MechanismDocument(
        gene=gene.upper(),
        drug=drug.lower(),
        body=match.group(2),
        source_guideline=str(meta.get("source_guideline") or ""),
        source_url=str(meta.get("source_url") or ""),
        primary_citation=" ".join(str(meta.get("primary_citation") or "").split()),
        retrieved=str(meta.get("retrieved") or ""),
        contains_dosing=bool(meta.get("contains_dosing")),
        reviewed_by=meta.get("reviewed_by"),
        aliases=tuple(str(a).strip().lower() for a in aliases if str(a).strip()),
        path=path,
    )


@dataclass
class _Index:
    by_pair: dict[tuple[str, str], MechanismDocument] = field(default_factory=dict)
    by_drug: dict[str, MechanismDocument] = field(default_factory=dict)
    # Alias -> canonical drug name, e.g. "5-fu" -> "fluorouracil".
    drug_aliases: dict[str, str] = field(default_factory=dict)

    @property
    def documents(self) -> list[MechanismDocument]:
        return list(self.by_pair.values())


@functools.lru_cache(maxsize=1)
def _load_index(corpus_dir: Path | None = None) -> _Index:
    """Load and index the corpus once. Call `.cache_clear()` in tests."""
    index = _Index()
    directory = corpus_dir or CORPUS_DIR
    if not directory.is_dir():
        return index

    for path in sorted(directory.glob("*.md")):
        document = _parse_document(path)
        if document is None:
            continue
        index.by_pair[(document.gene, document.drug)] = document
        # Each drug in this corpus maps to exactly one primary gene; if that
        # ever stops being true, the pair lookup still disambiguates.
        index.by_drug.setdefault(document.drug, document)
        index.drug_aliases[document.drug] = document.drug
        for alias in document.aliases:
            index.drug_aliases.setdefault(_normalise(alias), document.drug)
    return index


def _normalise(value: str) -> str:
    """
    Loose key for alias matching.

    Lower-cases and strips punctuation/whitespace so "5-FU", "5 FU" and "5fu"
    all collapse to the same key. Deliberately conservative: it never edits the
    stem, so "fluorouracil" and "fluoruracil" stay different.
    """
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def canonical_drug(name: str) -> str | None:
    """Resolve a drug name or alias to its canonical corpus name."""
    index = _load_index()
    key = _normalise(name)
    for candidate, canonical in index.drug_aliases.items():
        if _normalise(candidate) == key:
            return canonical
    return None


def retrieve_mechanism(gene: str | None, drug: str) -> MechanismDocument | None:
    """
    Look up the mechanism document for a (gene, drug) pair.

    Exact pair match first. If the gene is unknown or does not match — which
    happens legitimately, e.g. CYP2D6 could not be called, or azathioprine was
    attributed to NUDT15 rather than TPMT — fall back to the drug alone, then to
    an alias. Returns None on a miss; callers degrade gracefully.
    """
    index = _load_index()
    drug_key = (drug or "").strip().lower()

    if gene:
        document = index.by_pair.get((gene.strip().upper(), drug_key))
        if document is not None:
            return document

    document = index.by_drug.get(drug_key)
    if document is not None:
        return document

    canonical = canonical_drug(drug_key)
    if canonical:
        return index.by_drug.get(canonical)
    return None


def all_documents() -> list[MechanismDocument]:
    """Every parsed document. Used by the pre-generation script and tests."""
    return _load_index().documents


def known_genes() -> set[str]:
    """
    Gene symbols the corpus covers.

    The guard uses this (unioned with PharmCAT's target genes) to decide which
    gene-shaped tokens in generated text need to be justified by the context.
    """
    index = _load_index()
    genes = {gene for gene, _ in index.by_pair}
    for document in index.documents:
        genes.add(document.gene)
    return genes
