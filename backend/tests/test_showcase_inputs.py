"""
The showcase input builder must refuse, not approximate (Phase 10 §3.3).

WHY THESE ARE SABOTAGE TESTS

`scripts/build_showcase_inputs.py` turns a public gVCF into a file that
satisfies this application's input requirement. Every interesting thing it does
is a REFUSAL, and a refusal is the one behaviour that looks identical to a bug
in a broken checker: a tool that always said "conforming" would pass a naive
test on good input, and would then quietly ship a file whose missing positions
read as reference -- the exact failure the coverage gate exists to catch.

So each test here damages a known-good input in ONE specific way and asserts
the builder refuses for that specific reason. The positive control
(`test_undamaged_input_is_accepted`) is what makes the rest meaningful: if the
builder accepted all five inputs, or refused all five, these tests would be
worthless. They must VARY across the class.

The known-good input is synthesised here rather than fetched, so these run with
no network. It covers every required position with reference blocks, which is
the shape a real gVCF has.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "build_showcase_inputs.py"
REQUIREMENTS = REPO_ROOT / "backend" / "app" / "data" / "position_requirements.json"
POSITIONS_VCF = (
    REPO_ROOT / "test-data" / "reference" / "tools" / "pharmcat_positions_3.4.0.vcf.bgz"
)

pytestmark = pytest.mark.skipif(
    shutil.which("bcftools") is None or not POSITIONS_VCF.is_file(),
    reason=(
        "needs bcftools and PharmCAT's positions file; fetch with "
        "`python scripts/fetch_reference_data.py --fetch-tools`"
    ),
)


@pytest.fixture(scope="module")
def builder():
    """The script, imported as a module (it is a CLI, not a package)."""
    spec = importlib.util.spec_from_file_location("build_showcase_inputs", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_showcase_inputs"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def required() -> dict[tuple[str, int], str]:
    spec = json.loads(REQUIREMENTS.read_text())
    return {
        (str(chrom), int(pos)): gene
        for gene, entry in spec["genes"].items()
        for chrom, pos in entry["positions"]
    }


def _write_gvcf(path: Path, blocks: list[tuple[str, int, int, str, str]],
                variants: list[str] = ()) -> None:
    """
    A minimal gVCF: one reference block per span, plus any variant rows.

    `blocks` entries are (chrom, start, end, filter, genotype).
    """
    contigs = sorted({chrom for chrom, *_ in blocks})
    lines = ["##fileformat=VCFv4.2",
             '##FILTER=<ID=PASS,Description="All filters passed">',
             '##FILTER=<ID=LowGQ,Description="Set if true:GQ = 0">',
             '##ALT=<ID=NON_REF,Description="Represents any possible alternative allele">',
             '##INFO=<ID=END,Number=1,Type=Integer,Description="Stop position">',
             '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
             '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Depth">',
             '##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype Quality">',
             '##FORMAT=<ID=MIN_DP,Number=1,Type=Integer,Description="Minimum depth">']
    lines += [f"##contig=<ID={c},length=300000000>" for c in contigs]
    lines.append("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE")
    rows = []
    for chrom, start, end, filter_value, genotype in blocks:
        rows.append(f"{chrom}\t{start}\t.\tA\t<NON_REF>\t.\t{filter_value}\t"
                    f"END={end}\tGT:DP:GQ:MIN_DP\t{genotype}:40:60:38")
    rows += list(variants)
    rows.sort(key=lambda row: (row.split("\t")[0], int(row.split("\t")[1])))
    path.write_bytes(gzip.compress(("\n".join(lines + rows) + "\n").encode()))


def _spans(required: dict[tuple[str, int], str]) -> list[tuple[str, int, int]]:
    """One covering span per contig, padded past the outermost position."""
    by_chrom: dict[str, list[int]] = {}
    for chrom, pos in required:
        by_chrom.setdefault(chrom, []).append(pos)
    return [(chrom, min(ps) - 10, max(ps) + 10) for chrom, ps in sorted(by_chrom.items())]


@pytest.fixture
def good_gvcf(tmp_path: Path, required) -> Path:
    path = tmp_path / "good.g.vcf.gz"
    _write_gvcf(path, [(c, a, b, "PASS", "0/0") for c, a, b in _spans(required)])
    return path


def _build(builder, gvcf: Path, out: Path | None):
    return builder.build("SAMPLE", gvcf, "test://local", out)


# --------------------------------------------------------------------------- #
# The positive control. Without this, every test below is vacuous.
# --------------------------------------------------------------------------- #


def test_undamaged_input_is_accepted(builder, good_gvcf, tmp_path, required) -> None:
    """
    A gVCF covering every required position produces a conforming file.

    This is the control: the damaged variants below must fail where this one
    succeeds, or the checks are not discriminating between good and bad input.
    """
    out = tmp_path / "SAMPLE.vcf"
    meta = _build(builder, good_gvcf, out)
    assert out.is_file(), "a conforming input produced no file"

    emitted = [l for l in out.read_text().splitlines() if not l.startswith("#")]
    assert len(emitted) == len(required), (
        f"expected one row per required position ({len(required)}), got {len(emitted)}"
    )
    for gene in builder.VCF_READABLE_GENES:
        entry = meta["coverage_as_the_application_sees_it"][gene]
        assert entry["sufficient"], f"{gene} was not sufficient on a complete input"


# --------------------------------------------------------------------------- #
# Sabotage: one damaged position must sink the whole file
# --------------------------------------------------------------------------- #


def test_a_position_outside_every_block_is_refused(
    builder, tmp_path, required
) -> None:
    """
    B1. A position no record covers gets no row, and no file is written.

    The failure this prevents is the only one that matters here: writing the
    position as 0/0 because "it is probably reference". At 20% coverage that
    habit produced confidently-wrong calls in up to 47.8% of samples.
    """
    spans = _spans(required)
    # Shorten one span so its last required position falls outside every block.
    chrom, start, end = spans[0]
    uncovered = max(pos for (c, pos) in required if c == chrom)
    damaged = [(chrom, start, uncovered - 1, "PASS", "0/0")] + [
        (c, a, b, "PASS", "0/0") for c, a, b in spans[1:]
    ]
    path = tmp_path / "gap.g.vcf.gz"
    _write_gvcf(path, damaged)

    out = tmp_path / "SAMPLE.vcf"
    with pytest.raises(builder.BuildRefused) as refusal:
        _build(builder, path, out)
    assert not out.exists(), "a file was written despite an uncovered position"
    assert "positions carry an observed" in str(refusal.value)


def test_a_filtered_block_is_not_promoted_to_pass(builder, tmp_path, required) -> None:
    """
    B2. A position the source caller flagged stays flagged.

    This is not hypothetical: in the DRAGEN v4.4.7 reanalysis, SLCO1B1
    chr12:21222355 carries FILTER=LowGQ in most samples, and that single
    position is why most candidates cannot be used. Rewriting it as PASS would
    manufacture a simvastatin recommendation out of a position the caller
    itself declined to call.
    """
    spans = _spans(required)
    damaged = [(c, a, b, "LowGQ" if i == 0 else "PASS", "0/0")
               for i, (c, a, b) in enumerate(spans)]
    path = tmp_path / "filtered.g.vcf.gz"
    _write_gvcf(path, damaged)

    out = tmp_path / "SAMPLE.vcf"
    with pytest.raises(builder.BuildRefused):
        _build(builder, path, out)
    assert not out.exists(), "a file was written from FILTER-failed evidence"


def test_a_no_call_block_is_refused(builder, tmp_path, required) -> None:
    """B2. `./.` is an absence of a call, and never becomes a genotype."""
    spans = _spans(required)
    damaged = [(c, a, b, "PASS", "./." if i == 0 else "0/0")
               for i, (c, a, b) in enumerate(spans)]
    path = tmp_path / "nocall.g.vcf.gz"
    _write_gvcf(path, damaged)

    out = tmp_path / "SAMPLE.vcf"
    with pytest.raises(builder.BuildRefused):
        _build(builder, path, out)
    assert not out.exists(), "a file was written from a no-call"


def test_an_allele_pharmcat_does_not_define_is_refused(
    builder, tmp_path, required
) -> None:
    """
    B3. A called allele that is not one of PharmCAT's is a refusal.

    A genotype is read relative to its REF, so transcribing an allele PharmCAT
    does not list would produce a row that says something other than what the
    source said.
    """
    rows = builder.pharmcat_rows()
    chrom, pos = next(iter(sorted(required)))
    _, ref, _alts, _ = rows[(chrom, pos)]
    invented = "T" * (len(ref) + 3)
    variant = (f"{chrom}\t{pos}\t.\t{ref}\t{invented}\t50\tPASS\t.\t"
               f"GT:DP:GQ\t0/1:40:60")
    path = tmp_path / "alien.g.vcf.gz"
    _write_gvcf(path, [(c, a, b, "PASS", "0/0") for c, a, b in _spans(required)],
                variants=[variant])

    out = tmp_path / "SAMPLE.vcf"
    with pytest.raises(builder.BuildRefused):
        _build(builder, path, out)
    assert not out.exists(), "a file was written from an undefined allele"


def test_an_empty_slice_is_a_failure_not_an_empty_answer(
    builder, tmp_path, required
) -> None:
    """B7. A query that returns nothing is a hard failure."""
    path = tmp_path / "empty.g.vcf.gz"
    _write_gvcf(path, [])
    with pytest.raises(builder.BuildRefused) as refusal:
        _build(builder, path, tmp_path / "SAMPLE.vcf")
    assert "no records" in str(refusal.value)


# --------------------------------------------------------------------------- #
# Properties of what gets written
# --------------------------------------------------------------------------- #


def test_phase_is_not_carried(builder, tmp_path, required) -> None:
    """
    B4. A phased source genotype is written unphased.

    DRAGEN's phase sets do not span a gene; PharmCAT reads `|` as phased across
    one. Carrying the separator would assert phasing the source never claimed.
    """
    rows = builder.pharmcat_rows()
    chrom, pos = next(iter(sorted(required)))
    _, ref, alts, _ = rows[(chrom, pos)]
    variant = (f"{chrom}\t{pos}\t.\t{ref}\t{alts[0]}\t50\tPASS\t.\t"
               f"GT:DP:GQ\t0|1:40:60")
    path = tmp_path / "phased.g.vcf.gz"
    _write_gvcf(path, [(c, a, b, "PASS", "0/0") for c, a, b in _spans(required)],
                variants=[variant])

    out = tmp_path / "SAMPLE.vcf"
    _build(builder, path, out)
    emitted = {
        (line.split("\t")[0], int(line.split("\t")[1])): line.split("\t")[9]
        for line in out.read_text().splitlines() if not line.startswith("#")
    }
    assert emitted[(chrom, pos)] == "0/1", "phase was carried into the output"
    assert "|" not in out.read_text(), "a phased separator reached the output"


def test_output_is_byte_identical_on_a_second_run(
    builder, good_gvcf, tmp_path
) -> None:
    """B8. The recorded checksum means nothing if two runs differ."""
    first, second = tmp_path / "a.vcf", tmp_path / "b.vcf"
    meta_a = _build(builder, good_gvcf, first)
    meta_b = _build(builder, good_gvcf, second)
    assert first.read_bytes() == second.read_bytes()
    assert meta_a["output"]["sha256"] == meta_b["output"]["sha256"]


def test_cyp2d6_never_decides_whether_a_file_is_emitted(
    builder, good_gvcf, tmp_path
) -> None:
    """
    CYP2D6 is excluded from the emission decision on purpose.

    No VCF content makes this application call CYP2D6, so letting its positions
    gate the build would refuse files that are perfectly usable for the seven
    genes that are callable -- and would imply CYP2D6 could be rescued by
    better input, which is the claim the decline exists to avoid.
    """
    from app import coverage as coverage_mod

    assert "CYP2D6" not in builder.VCF_READABLE_GENES
    meta = _build(builder, good_gvcf, tmp_path / "SAMPLE.vcf")
    cyp2d6 = meta["coverage_as_the_application_sees_it"].get("CYP2D6")
    assert cyp2d6 is not None, "CYP2D6 vanished from the coverage report"

    # Coverage is a measurement, and on a synthetic input that carries every
    # position it can legitimately read 100%. The decline lives one layer up,
    # and is a property of the application rather than of any file -- so that
    # is what must still hold.
    assert "CYP2D6" in coverage_mod.NOT_READABLE_FROM_VCF, (
        "the application stopped declining CYP2D6 from a VCF"
    )
    eligibility = coverage_mod.drug_eligibility(
        coverage_mod.assess((tmp_path / "SAMPLE.vcf").read_text()), "codeine"
    )
    assert not eligibility.eligible, (
        "codeine became answerable from a VCF; the CYP2D6 decline is the "
        "project's declared negative control and must survive this tooling"
    )


# --------------------------------------------------------------------------- #
# Source-level conventions this repository enforces on every script
# --------------------------------------------------------------------------- #


def test_every_subprocess_is_checked() -> None:
    """
    B7. `check=True` on every subprocess call, and no silent pipe.

    bcftools exits 255, not 1, and a pipeline hides a non-zero status without
    `pipefail` -- which is how a failed fetch becomes an empty file that reads
    as "no data" rather than "the fetch broke".
    """
    source = SCRIPT.read_text()
    calls = source.count("subprocess.run(")
    checked = source.count("check=True")
    assert calls > 0, "no subprocess calls found; has the script moved?"
    assert checked >= calls, (
        f"{calls} subprocess.run call(s) but only {checked} check=True"
    )
    assert "|| true" not in source
    assert "shell=True" not in source, "a shell pipeline can hide a non-zero status"


# --------------------------------------------------------------------------- #
# Phase 10 §4 — a real codeine result that does not cost the negative control
# --------------------------------------------------------------------------- #


class TestSuppliedCyp2d6:
    """
    CYP2D6 may be SUPPLIED. It is still never CALLED from a VCF.

    The whole value of the decline is that it holds when a right answer is
    available and tempting. NA12273 is the standing example: GeT-RM records it
    as *1/*1 and DRAGEN independently calls it *1/*1, and the file alone must
    still produce Unknown. If that ever stops being true, this project has
    traded its sharpest demonstrated strength for a filled-in cell.
    """

    def test_dragen_is_accepted_and_its_real_notation_parses(self, builder) -> None:
        from app import outside_calls

        assert builder.CYP2D6_CALLER in outside_calls.CALLERS
        # Exactly the diplotypes the source produced for the showcase samples,
        # including a tandem with a copy number, which is the shape a VCF
        # fundamentally cannot express.
        for diplotype in ("*1/*41", "*2/*4", "*2/*2", "*4/*5", "*17/*2",
                          "*10+*36x2/*49", "*1/*1"):
            call = outside_calls.parse(diplotype, builder.CYP2D6_CALLER)
            assert call.gene == "CYP2D6"
            assert call.diplotype == diplotype
            assert "not called by PharmaGuard" in call.provenance

    def test_the_gene_is_pinned_and_never_taken_from_the_supplied_value(
        self, builder
    ) -> None:
        """A supplied call can name a diplotype. It can never name a gene."""
        from app import outside_calls

        for attack in ("CYP2C19\t*1/*2", "*1/*2\nCYP2C19\t*2/*2", "*1/*2; DROP"):
            with pytest.raises(outside_calls.OutsideCallError):
                outside_calls.parse(attack, builder.CYP2D6_CALLER)
        line = outside_calls.parse("*1/*41", builder.CYP2D6_CALLER).file_line()
        assert line == "CYP2D6\t*1/*41\n"
        assert line.count("\n") == 1, "a supplied value added a second line"

    def _targeted(self, builder, monkeypatch, payload) -> dict | None:
        """Run the sidecar emitter against a canned targeted-caller payload."""
        import io

        class _Response:
            status = 200

            def read(self):
                return json.dumps(payload).encode()

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        monkeypatch.setattr(builder.urllib.request, "urlopen",
                            lambda *a, **k: _Response())
        return builder.cyp2d6_call("SAMPLE")

    def test_a_confident_call_is_written_with_its_provenance(
        self, builder, monkeypatch
    ) -> None:
        call = self._targeted(builder, monkeypatch, {
            "softwareVersion": "dragen v13.021.779.4.4.7",
            "cyp2d6": {"genotype": "*4/*5", "genotypeFilter": "PASS",
                       "genotypeQuality": 150, "totalCopyNumber": 3},
        })
        assert call is not None
        assert call["diplotype"] == "*4/*5"
        assert call["caller"] == builder.CYP2D6_CALLER
        assert call["total_copy_number"] == 3
        assert "did not call it" in call["not_called_by_pharmaguard"]

    @pytest.mark.parametrize("payload,why", [
        ({"cyp2d6": {"genotype": "*4/*5", "genotypeFilter": "TargetedLowJVQL"}},
         "the caller flagged its own call"),
        ({"cyp2d6": {"genotype": "", "genotypeFilter": "PASS"}},
         "there is no genotype"),
        ({"cyp2d6": {"genotype": "not a diplotype", "genotypeFilter": "PASS"}},
         "the notation would be refused at upload"),
        ({}, "the source has no CYP2D6 object at all"),
    ])
    def test_anything_short_of_a_confident_call_is_not_written(
        self, builder, monkeypatch, payload, why
    ) -> None:
        """
        Codeine stays Unknown rather than resting on a doubtful call.

        A filled-in cell is worth nothing if the value behind it is one the
        caller would not stand behind -- that is the same trade the coverage
        gate refuses on every other gene.
        """
        assert self._targeted(builder, monkeypatch, payload) is None, why


class TestShippedShowcaseFilesStillDeclineCyp2d6:
    """
    The negative control, asserted on the files that actually ship.

    Dependency-free on purpose: this is a property of the VCFs themselves, so
    it holds with no PharmCAT, no network and no API.
    """

    @staticmethod
    def _shipped() -> list[Path]:
        root = REPO_ROOT / "demo" / "samples"
        return sorted(root.glob("*.vcf")) + sorted(root.glob("*/*.vcf"))

    def test_there_are_shipped_samples(self) -> None:
        assert self._shipped(), "no showcase samples found to check"

    def test_no_shipped_vcf_carries_a_cyp2d6_diplotype(self) -> None:
        """
        The supplied call lives BESIDE the file, never inside it.

        Smuggling a diplotype into the VCF would make the decline depend on
        nobody noticing, rather than on the application's own rule.
        """
        import re

        star = re.compile(r"CYP2D6[^\n]*\*\d")
        for path in self._shipped():
            offending = [l for l in path.read_text().splitlines() if star.search(l)]
            assert not offending, f"{path.name} carries a CYP2D6 diplotype: {offending[:2]}"

    def test_codeine_is_not_answerable_from_any_shipped_file(self) -> None:
        from app import coverage as coverage_mod

        for path in self._shipped():
            report = coverage_mod.assess(path.read_text())
            eligibility = coverage_mod.drug_eligibility(report, "codeine")
            assert not eligibility.eligible, (
                f"{path.name} made codeine answerable from a VCF alone"
            )
            assert "CYP2D6" in eligibility.failed_genes

    def test_the_other_genes_are_answerable_from_the_same_files(self) -> None:
        """
        The control that stops the test above from passing vacuously.

        If every drug were unanswerable these files would be useless, and the
        CYP2D6 assertion would prove nothing about CYP2D6.
        """
        from app import coverage as coverage_mod

        main_flow = [p for p in self._shipped() if p.parent.name == "samples"]
        for path in main_flow:
            report = coverage_mod.assess(path.read_text())
            answerable = [
                drug for drug in ("clopidogrel", "simvastatin", "azathioprine",
                                  "fluorouracil")
                if coverage_mod.drug_eligibility(report, drug).eligible
            ]
            assert len(answerable) == 4, (
                f"{path.name} answers only {answerable}; a showcase file must "
                f"satisfy every gene the application can read"
            )


def test_absent_to_ref_is_never_used() -> None:
    """
    The one flag this project exists to argue against.

    PharmCAT's `--absent-to-ref` fills unobserved positions with reference,
    which is precisely how a reduced-function patient is reported as normal.

    Checked against the EXECUTABLE source only. The prose is allowed to name
    the flag -- explaining why a thing is not done is the point of the comment
    -- so docstrings and comments are stripped before the check, or this test
    would forbid documenting its own rule.
    """
    import ast

    tree = ast.parse(SCRIPT.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and ast.get_docstring(node):
            node.body = node.body[1:]
    code = ast.unparse(tree)
    for forbidden in ("--absent-to-ref", "absent_to_ref", "absentToRef"):
        assert forbidden not in code, f"{forbidden} is used in the builder's code"
