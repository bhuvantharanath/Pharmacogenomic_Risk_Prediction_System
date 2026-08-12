"""
No user ever sees a tool name, a library name, or a variable name.

WHY THIS IS A PERMANENT GUARD AND NOT A ONE-OFF CLEANUP

The strings this catches were written by people trying to be helpful. "Re-create
it with bgzip" is genuinely the right instruction — for a bioinformatician. To
everyone else it is a dead end dressed as advice, arriving at the exact moment
they are already stuck, and it makes the system look like it was built for
somebody else.

The same pressure that produced them the first time is still there, so the rule
has to outlive the cleanup. Every one of these was found by an audit that was
looking for something else entirely; without a guard the next one gets found the
same way, or not at all.

WHERE THE DETAIL WENT

Nowhere. An operator still needs to know that `PHARMCAT_JAR` is unset. That
belongs in the startup log and in `PharmcatExecutionError.detail`, which reach
the person who can act on it — not in a 503 body shown to someone who uploaded a
VCF and can only wait.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

pytest.importorskip("spacy")
pytest.importorskip("wordfreq")

import glossary_lib as g  # noqa: E402

#: Tool, runtime and format names. Small and hand-kept on purpose: this is the
#: one place a list is the right shape, because it encodes "words a patient
#: cannot act on", which is a judgement rather than a measurement.
#:
#: `pharmcat` and `cpic` are absent deliberately — both are named to the user on
#: the About screen and in the provenance line, as disclosure. Naming the source
#: of a result is the opposite of leaking an implementation detail.
FORBIDDEN_TOOLS = (
    "bgzip", "bcftools", "gatk", "picard", "crossmap", "liftovervcf",
    "genotypegvcfs", "tabix", "samtools", "gzip",
    "jvm", "jre", "jdk", "uvicorn", "pytest", "flutter", "gradle",
    "subprocess", "stderr", "stdout", "traceback", "localhost",
    "yaml", "argv", "regex", "runtime error",
)

#: `dosingInformation`, `notApplicableReason`. A variable name that reached a
#: sentence is always a bug — nobody writes camelCase on purpose in prose.
CAMEL_CASE = re.compile(r"\b[a-z]+(?:[A-Z][a-z0-9]+)+\b")

#: Environment variables and CLI flags.
SHOUTY_ENV = re.compile(r"\b[A-Z][A-Z0-9]{3,}(?:_[A-Z0-9]+)+\b")
CLI_FLAG = re.compile(r"(?:^|\s)--[a-z][a-z0-9-]+")


def user_facing() -> list[g.Snippet]:
    return g.collect_snippets()


def test_no_user_facing_string_names_a_tool() -> None:
    """
    The list is small and the rule is absolute. If a new tool genuinely has to
    be named, the right move is to name it in `docs/input_requirements.md` and
    point at that — not to add an exception here.
    """
    offences: list[str] = []
    for snippet in user_facing():
        lowered = snippet.text.lower()
        for tool in FORBIDDEN_TOOLS:
            if re.search(rf"\b{re.escape(tool)}\b", lowered):
                offences.append(f"{snippet.source}: {tool!r} in "
                                f"{' '.join(snippet.text.split())[:110]!r}")
    assert not offences, "\n".join(offences)


def test_no_user_facing_string_contains_a_code_identifier() -> None:
    offences: list[str] = []
    for snippet in user_facing():
        for match in CAMEL_CASE.findall(snippet.text):
            offences.append(f"{snippet.source}: {match!r} in "
                            f"{' '.join(snippet.text.split())[:110]!r}")
    assert not offences, "\n".join(offences)


def test_no_user_facing_string_names_an_environment_variable_or_flag() -> None:
    """
    `PHARMCAT_JAR=/path/to/...` is an instruction to a person with shell access.
    Someone who uploaded a file through a browser has none.
    """
    offences: list[str] = []
    for snippet in user_facing():
        for rx in (SHOUTY_ENV, CLI_FLAG):
            for match in rx.findall(snippet.text):
                # Screaming-case words that are genuinely English are fine:
                # the coverage warning shouts NOT and WRONG on purpose.
                if rx is SHOUTY_ENV and "_" not in match:
                    continue
                offences.append(f"{snippet.source}: {match.strip()!r} in "
                                f"{' '.join(snippet.text.split())[:110]!r}")
    assert not offences, "\n".join(offences)


def test_the_operator_detail_was_moved_and_not_deleted() -> None:
    """
    The counterpart to the rule above. Making the user message plain is only
    correct if the person who can actually fix the deployment still gets told
    what is wrong — otherwise this trades one broken audience for another.
    """
    from app.pharmcat_runner import unavailable_reason

    reason = unavailable_reason()
    assert reason, "unavailable_reason() went silent"
    # It still names something actionable: a jar, a Java runtime, or the
    # environment variables that override discovery.
    assert any(t in reason for t in ("jar", "JAVA", "PHARMCAT_", "Java"))


def test_the_user_message_says_nothing_about_the_deployment() -> None:
    from app.pharmcat_runner import UNAVAILABLE_USER_MESSAGE

    lowered = UNAVAILABLE_USER_MESSAGE.lower()
    for forbidden in ("jar", "jre", "jvm", "java", "path", "pharmcat_"):
        assert forbidden not in lowered, forbidden
    # And it says the one thing that matters to the person reading it.
    assert "nothing was wrong with your upload" in lowered


def test_the_actionable_content_survived_the_rewrite() -> None:
    """
    A message can be made tool-free by making it useless. These are the three
    that carried a real remedy; each must still carry one.
    """
    from app.coverage import variants_only_warning
    from app.vcf_validation import MAX_UPLOAD_BYTES  # noqa: F401

    warning = variants_only_warning().lower()
    assert "every position" in warning
    assert "match the reference" in warning
    # The remedy moved to the docs rather than evaporating.
    assert "input_requirements" in warning


# --------------------------------------------------------------------------- #
# The guard, re-anchored
#
# Audit A could not confirm this guard because its mutation anchor had moved
# during the glossary rewording — it reported ANCHOR-NOT-FOUND rather than a
# result, and the guard was recorded as unverified. These plant one example of
# each category the guard claims to catch, so it is verified against current
# text rather than against a string that may drift again.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("category,text,expect", [
    ("tool name", "Re-create the file with bgzip and try again.", "bgzip"),
    ("camelCase", "CPIC sets dosingInformation for this recommendation.",
     "dosingInformation"),
    ("env var", "Set PHARMCAT_JAR to the full path of the jar file.",
     "PHARMCAT_JAR"),
    ("CLI flag", "Re-run with --include-non-variant-sites enabled.",
     "--include-non-variant-sites"),
])
def test_the_guard_detects_a_planted(category: str, text: str,
                                     expect: str) -> None:
    """
    Each detector, exercised on text of the shape it exists to catch. If one
    stops firing, the guard silently narrows and the next leak ships.
    """
    lowered = text.lower()
    hits: list[str] = []
    hits += [t for t in FORBIDDEN_TOOLS
             if re.search(rf"\b{re.escape(t)}\b", lowered)]
    hits += CAMEL_CASE.findall(text)
    hits += [m for m in SHOUTY_ENV.findall(text) if "_" in m]
    hits += [m.strip() for m in CLI_FLAG.findall(text)]

    assert expect in hits, (
        f"the {category} detector did not fire on {text!r} — it found {hits}")
