"""
Every shipped sample VCF must actually demo something.

WHAT WENT WRONG
    `test-data/sample1.vcf` and `sample2.vcf` survived from Phase 1, when the
    analyzer was a stub that ignored the file. Once PharmCAT became real they
    were worse than useless: with only 5 and 4 positions they do not carry a
    single gene's full definition set, so PharmCAT cannot call anything and
    exits without writing a report at all. `/analyze` then returns
    **503 PHARMCAT_UNAVAILABLE** — a server error, not a degraded result.

    A demo where someone picks the first file in the list and gets a 503 is the
    worst possible first impression, and nothing in the suite noticed.

THE ASSERTION THAT WOULD HAVE CAUGHT IT
    Position coverage. A callable VCF carries every defining position for the
    gene in question (306 for our six-gene panel); the relics carried 5.
    `test_has_enough_positions_to_be_callable` is the specific guard.

DEPENDENCY-FREE BY DESIGN
    These checks are structural, so they run in the normal suite with no
    PharmCAT, Java or Docker. `TestAgainstRealPharmcat` at the bottom performs
    the true end-to-end assertion and is skipped unless a pipeline is on PATH.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.vcf_validation import ReferenceBuild, validate_vcf

TEST_DATA = Path(__file__).resolve().parents[2] / "test-data"

#: The contract for every shipped sample: which drug it is meant to demonstrate,
#: which gene drives that result, and what a demo audience should see.
#:
#: Adding a VCF to test-data/ without adding a row here fails
#: `test_every_shipped_vcf_is_declared` — a sample nobody has stated an
#: expectation for is exactly how the Phase 1 relics survived.
SAMPLE_EXPECTATIONS: dict[str, dict[str, object]] = {
    "cyp2c19_poor_metabolizer.vcf": {
        "drug": "clopidogrel",
        "gene": "CYP2C19",
        "expected_label": "Ineffective",
        "note": "*2/*2 poor metaboliser — the prodrug is never activated",
    },
    "dpyd_variant_carrier.vcf": {
        "drug": "fluorouracil",
        "gene": "DPYD",
        "expected_label": "Adjust Dosage",
        "note": "c.1905+1G>A heterozygote — reduced clearance",
    },
    "normal_metabolizer_control.vcf": {
        "drug": "clopidogrel",
        "gene": "CYP2C19",
        "expected_label": "Safe",
        "note": "all-reference control — the negative case",
    },
}

#: Minimum data rows for a VCF to be callable. Our panel needs 306; the Phase 1
#: relics had 5 and 4. 50 is comfortably above the broken files and far below a
#: legitimate one, so it catches the failure without being brittle.
MIN_CALLABLE_POSITIONS = 50


def shipped_vcfs() -> list[Path]:
    return sorted(TEST_DATA.glob("*.vcf"))


def _data_rows(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln and not ln.startswith("#")]


def _is_non_reference(row: str) -> bool:
    """
    True when the sample's genotype carries at least one ALT allele.

    Deliberately order-agnostic. The synthetic generator emits alleles as
    (haplotype1, haplotype2), so a variant sitting on the first haplotype
    produces `1/0`, not `0/1` — an earlier version of this check only looked
    for `0/1` and wrongly flagged a valid DPYD carrier as all-reference.
    Phased separators are handled for the same reason.
    """
    genotype = row.rsplit("\t", 1)[-1].split(":")[0]
    alleles = re.split(r"[/|]", genotype)
    return any(a.isdigit() and int(a) > 0 for a in alleles)


class TestShippedSamplesAreUsable:
    def test_at_least_one_sample_is_shipped(self) -> None:
        assert shipped_vcfs(), "no sample VCFs — the README tells users to try one"

    def test_every_shipped_vcf_is_declared(self) -> None:
        """A sample with no stated expectation is how the relics survived."""
        undeclared = [p.name for p in shipped_vcfs() if p.name not in SAMPLE_EXPECTATIONS]
        assert not undeclared, (
            f"{undeclared} ship in test-data/ but declare no expected result. "
            f"Add a row to SAMPLE_EXPECTATIONS stating the drug and label it "
            f"demonstrates, or delete the file."
        )

    def test_every_declared_vcf_exists(self) -> None:
        missing = [n for n in SAMPLE_EXPECTATIONS if not (TEST_DATA / n).is_file()]
        assert not missing, f"declared but absent: {missing}"

    @pytest.mark.parametrize("name", sorted(SAMPLE_EXPECTATIONS))
    def test_passes_validation(self, name: str) -> None:
        """It must survive our own front door before PharmCAT ever sees it."""
        meta = validate_vcf((TEST_DATA / name).read_bytes(), name)
        assert meta.sample_ids, "no sample column"
        assert meta.variant_count > 0

    @pytest.mark.parametrize("name", sorted(SAMPLE_EXPECTATIONS))
    def test_is_grch38(self, name: str) -> None:
        """GRCh37 would be rejected at upload; shipping one would be a trap."""
        meta = validate_vcf((TEST_DATA / name).read_bytes(), name)
        assert meta.reference_build is ReferenceBuild.GRCH38, (
            f"{name} is {meta.reference_build.value}; PharmCAT requires GRCh38"
        )

    @pytest.mark.parametrize("name", sorted(SAMPLE_EXPECTATIONS))
    def test_has_enough_positions_to_be_callable(self, name: str) -> None:
        """
        THE regression assertion.

        `sample1.vcf` had 5 rows and `sample2.vcf` had 4. A named allele is
        defined by a combination of positions, so a sparse file matches no
        haplotype — PharmCAT writes no report and the API 503s.
        """
        rows = _data_rows((TEST_DATA / name).read_text())
        assert len(rows) >= MIN_CALLABLE_POSITIONS, (
            f"{name} has only {len(rows)} data rows. PharmCAT needs a gene's "
            f"full definition set to call a diplotype; a file this sparse "
            f"produces no report at all and /analyze returns 503."
        )

    @pytest.mark.parametrize("name", sorted(SAMPLE_EXPECTATIONS))
    def test_covers_its_target_gene(self, name: str) -> None:
        """The gene the sample is meant to demonstrate must be present."""
        gene = SAMPLE_EXPECTATIONS[name]["gene"]
        text = (TEST_DATA / name).read_text()
        hits = [ln for ln in _data_rows(text) if f"PX={gene}" in ln]
        assert len(hits) >= 20, (
            f"{name} carries only {len(hits)} {gene} positions; not enough for "
            f"a diplotype call"
        )

    @pytest.mark.parametrize(
        "name",
        [n for n, e in SAMPLE_EXPECTATIONS.items() if e["expected_label"] != "Safe"],
    )
    def test_non_control_samples_carry_non_reference_calls(self, name: str) -> None:
        """
        A sample meant to show an abnormal result must actually contain a
        variant. An all-reference file would silently demo as `Safe`.
        """
        gene = SAMPLE_EXPECTATIONS[name]["gene"]
        variants = [
            ln
            for ln in _data_rows((TEST_DATA / name).read_text())
            if f"PX={gene}" in ln and _is_non_reference(ln)
        ]
        assert variants, (
            f"{name} is meant to demonstrate "
            f"{SAMPLE_EXPECTATIONS[name]['expected_label']!r} but every {gene} "
            f"genotype is reference — it would demo as Safe"
        )

    def test_control_sample_is_all_reference(self) -> None:
        """The control's whole job is to be the negative case."""
        text = (TEST_DATA / "normal_metabolizer_control.vcf").read_text()
        non_ref = [ln for ln in _data_rows(text) if _is_non_reference(ln)]
        assert not non_ref, (
            f"control carries {len(non_ref)} non-reference calls; it would not "
            f"demonstrate the Safe path"
        )

    def test_docs_never_tell_a_user_to_open_a_missing_file(self) -> None:
        """
        Docs must not point a user at a VCF we do not ship.

        Scoped to the places a reader actually *acts* on — fenced command
        blocks and the file table — rather than all prose. A paragraph
        explaining that a file was removed is useful history and must not fail
        this test; a `curl -F file=@…` line naming a deleted file must.
        """
        shipped = {p.name for p in shipped_vcfs()}
        # Generic placeholders that stand for "your file", not a shipped one.
        placeholders = {
            "my_sample.vcf", "input.vcf", "sample.vcf", "file.vcf",
            "pgx_only.vcf", "my_file.vcf", "your_sample.vcf",
        }

        for doc in ("README.md", "test-data/README.md"):
            path = Path(__file__).resolve().parents[2] / doc
            if not path.is_file():
                continue
            text = path.read_text()

            actionable: list[str] = []
            actionable += re.findall(r"```.*?```", text, re.DOTALL)  # command blocks
            actionable += [ln for ln in text.splitlines() if ln.startswith("|")]  # tables

            referenced = {
                name
                for chunk in actionable
                for name in re.findall(r"\b([a-z0-9_]+\.vcf)\b", chunk)
            } - placeholders

            dangling = referenced - shipped
            assert not dangling, (
                f"{doc} tells a user to open {sorted(dangling)}, which is not "
                f"shipped. Shipped: {sorted(shipped)}"
            )


@pytest.mark.skipif(
    __import__("shutil").which(
        __import__("os").environ.get("PHARMCAT_PIPELINE", "pharmcat_pipeline")
    )
    is None,
    reason="PharmCAT not on PATH; structural checks above cover the regression",
)
class TestAgainstRealPharmcat:
    """
    The true end-to-end assertion, when a pipeline is available.

    Opt-in rather than always-on: requiring PharmCAT would make the whole suite
    undeployable in CI. The structural tests above are what actually guard the
    regression day to day.
    """

    @pytest.mark.parametrize("name", sorted(SAMPLE_EXPECTATIONS))
    def test_produces_the_expected_label(self, name: str) -> None:
        import asyncio

        from app.main import build_response
        from app.pharmcat_runner import run_pharmcat

        expectation = SAMPLE_EXPECTATIONS[name]
        meta = validate_vcf((TEST_DATA / name).read_bytes(), name)

        report = asyncio.run(
            run_pharmcat(meta.text, sample_hint=meta.sample_ids[0])
        )
        response = build_response(report, [expectation["drug"]], meta, 0)
        analysis = response.analyses[0]

        assert analysis.risk_assessment.risk_label.value != "Unknown", (
            f"{name} + {expectation['drug']} returned Unknown — this sample "
            f"would demo as broken"
        )
        assert analysis.risk_assessment.risk_label.value == expectation["expected_label"]
        assert analysis.pharmacogenomic_profile.primary_gene == expectation["gene"]
