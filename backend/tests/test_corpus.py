"""
Corpus provenance rule, enforced as a build gate.

`rag-corpus/README.md` promises this file exists and that it fails the build on
dosing language in the mechanism corpus. Keeping the promise checkable is the
point: a rule nobody enforces is a comment.

The substantive assertions live in `test_explanation.py::TestCorpus`; this
module re-exports them under the name the README advertises so that
`pytest tests/test_corpus.py` does what a reader expects.
"""

from __future__ import annotations

from test_explanation import TestCorpus  # noqa: F401  (re-exported for pytest)
