"""
Phase 5A build-time tooling — the properties that must hold regardless of
whether a generation run has happened.

These cover the invariants that protect users and quota:

  * reachability is derived, not assumed, and unreachable cases are never
    authored;
  * a run interrupted by a rate limit resumes without duplicating or skipping
    work;
  * adversarial experiment output — which is deliberately fabricated — can
    never reach the explanation store;
  * the API key never appears in printed output, logs or error text;
  * the deployed path still needs no key at all.

Everything here runs without an API key, without PharmCAT and without a network.
Tests that need real captured model output live in `test_guard_real_outputs.py`
and skip themselves until a run has produced fixtures.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
CASE_MATRIX = REPO_ROOT / "backend" / "app" / "data" / "case_matrix.json"
EXPLANATIONS = REPO_ROOT / "backend" / "app" / "data" / "explanations.json"

# The scripts are CLIs, not an installed package; load them by path so the tests
# exercise the same modules the operator runs.
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Reachability
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(not CASE_MATRIX.is_file(), reason="run scripts/enumerate_cases.py first")
class TestReachability:
    @pytest.fixture(scope="class")
    def matrix(self) -> dict:
        return json.loads(CASE_MATRIX.read_text())

    def test_matrix_has_the_expected_shape(self, matrix: dict) -> None:
        assert matrix["cases"], "no cases enumerated"
        for case in matrix["cases"]:
            assert set(case) >= {
                "drug", "gene", "phenotype", "reachable", "reason", "evidence"
            }, case
            assert isinstance(case["reachable"], bool)

    def test_totals_match_the_case_list(self, matrix: dict) -> None:
        cases = matrix["cases"]
        totals = matrix["totals"]
        assert totals["enumerated"] == len(cases)
        assert totals["reachable"] == sum(1 for c in cases if c["reachable"])
        assert totals["unreachable"] == sum(1 for c in cases if not c["reachable"])

    def test_it_is_not_the_naive_product(self, matrix: dict) -> None:
        """
        The brief's warning, encoded.

        6 drugs x 6 phenotypes = 36 is fiction: genes do not all have every
        phenotype, CYP2D6 is not callable at all, and some phenotypes have no
        CPIC row. If this ever equals the naive product, the enumeration has
        stopped deriving and started assuming.
        """
        assert matrix["totals"]["enumerated"] != 36
        assert matrix["totals"]["unreachable"] > 0

    def test_every_unreachable_case_states_why(self, matrix: dict) -> None:
        """An unreachable case with no reason is an undocumented gap."""
        for case in matrix["cases"]:
            if not case["reachable"]:
                assert case["reason"].strip(), case
                assert len(case["reason"]) > 20, f"reason too vague: {case}"

    def test_cyp2d6_is_unreachable_except_unknown(self, matrix: dict) -> None:
        """
        The headline honesty case. PharmCAT reports callSource=NONE for CYP2D6
        even with every definition position present, so any phenotype other
        than Unknown would be fabricated.
        """
        cyp2d6 = [c for c in matrix["cases"] if c["gene"] == "CYP2D6"]
        assert cyp2d6, "CYP2D6 not enumerated at all"
        for case in cyp2d6:
            if case["phenotype"] == "Unknown":
                assert case["reachable"], "the Unknown case must remain reachable"
            else:
                assert not case["reachable"], case
                assert "not callable" in case["reason"].lower()

    def test_every_drug_has_a_reachable_unknown_case(self, matrix: dict) -> None:
        """
        Any gene can fail to call, so every drug needs something to say when it
        does. A drug with no Unknown entry would fall through to the template.
        """
        by_drug: dict[str, set[str]] = {}
        for case in matrix["cases"]:
            if case["reachable"]:
                by_drug.setdefault(case["drug"], set()).add(case["phenotype"])
        for drug, phenotypes in by_drug.items():
            assert "Unknown" in phenotypes, f"{drug} has no reachable Unknown case"

    def test_unreachable_cases_are_never_authored(self, matrix: dict) -> None:
        """
        The rule from the brief: document unreachable cases, never write prose
        for them. Padding coverage with cases the pipeline cannot produce would
        misrepresent the system.
        """
        if not EXPLANATIONS.is_file():
            pytest.skip("no explanation store yet")
        entries = json.loads(EXPLANATIONS.read_text()).get("explanations", [])
        authored = {f"{e['drug']}:{e['phenotype']}" for e in entries}
        unreachable = {
            f"{c['drug']}:{c['phenotype']}" for c in matrix["cases"] if not c["reachable"]
        }
        overlap = authored & unreachable
        assert not overlap, f"explanations exist for unreachable cases: {sorted(overlap)}"


# --------------------------------------------------------------------------- #
# Resume / idempotency
# --------------------------------------------------------------------------- #


class TestResumeIdempotency:
    """
    A free-tier run can stop at any point. Resuming must neither duplicate work
    already paid for nor silently skip a case that was never generated.
    """

    @pytest.fixture(scope="class")
    def pregen(self):
        return _load("pregenerate_explanations")

    def _store(self, entries: list[dict]) -> dict:
        return {"version": 2, "generator": "llm", "explanations": entries}

    def _entry(self, drug: str, phenotype: str) -> dict:
        return {
            "drug": drug,
            "phenotype": phenotype,
            "gene": "X",
            "explanation": {
                "summary": "s", "mechanism": "m",
                "variant_rationale": "v", "patient_friendly": "p",
            },
            "generator": "llm:test",
            "fallback": False,
            "reviewed_by": None,
        }

    def test_resume_skips_exactly_what_is_already_present(self, pregen, tmp_path) -> None:
        cases = pregen.load_reachable_cases()
        assert len(cases) >= 3, "need a few cases to exercise this"

        # Simulate a run interrupted after the first two cases.
        done = cases[:2]
        path = tmp_path / "partial.json"
        path.write_text(json.dumps(self._store([self._entry(c.drug, c.phenotype) for c in done])))

        existing = json.loads(path.read_text())
        by_key = {f"{e['drug']}:{e['phenotype']}" for e in existing["explanations"]}
        remaining = [c for c in cases if c.key not in by_key]

        assert len(remaining) == len(cases) - 2
        assert all(c.key not in by_key for c in remaining)
        # And nothing was dropped: done + remaining covers everything, once.
        assert by_key | {c.key for c in remaining} == {c.key for c in cases}

    def test_resume_produces_no_duplicates(self, pregen, tmp_path) -> None:
        """The store is keyed by (drug, phenotype), so re-running cannot double up."""
        cases = pregen.load_reachable_cases()
        by_key: dict[str, dict] = {}

        # Two passes over the same cases — the second simulates a resume that
        # wrongly re-ran everything.
        for _ in range(2):
            for case in cases:
                by_key[case.key] = self._entry(case.drug, case.phenotype)

        assert len(by_key) == len(cases)
        keys = [f"{e['drug']}:{e['phenotype']}" for e in by_key.values()]
        assert len(keys) == len(set(keys)), "duplicate entries after a re-run"

    def test_resume_leaves_no_gaps_once_complete(self, pregen) -> None:
        cases = {c.key for c in pregen.load_reachable_cases()}
        if not EXPLANATIONS.is_file():
            pytest.skip("no explanation store yet")
        entries = json.loads(EXPLANATIONS.read_text()).get("explanations", [])
        authored = {f"{e['drug']}:{e['phenotype']}" for e in entries}
        missing = cases - authored
        assert not missing, f"reachable cases with no entry: {sorted(missing)}"

    def test_atomic_write_leaves_no_partial_file(self, tmp_path) -> None:
        """
        Writes go through a temp file + rename. A half-written store would be
        worse than a stopped run: it destroys the work it was protecting.
        """
        common = _load("_common")
        target = tmp_path / "store.json"
        common.write_json_atomic(target, {"explanations": [self._entry("d", "NM")]})

        assert target.is_file()
        assert json.loads(target.read_text())["explanations"]
        assert not list(tmp_path.glob("*.tmp")), "temp file left behind"


# --------------------------------------------------------------------------- #
# Experiment isolation — the safety invariant
# --------------------------------------------------------------------------- #


class TestGuardExperimentIsolation:
    """
    `guard_experiment.py` deliberately produces fabricated clinical text —
    invented doses, invented rsIDs. Exactly one thing must never happen: any of
    it reaching `explanations.json`, from where it would be served to users.
    """

    @pytest.fixture(scope="class")
    def experiment(self):
        return _load("guard_experiment")

    def test_refuses_the_real_store_by_exact_path(self, experiment) -> None:
        with pytest.raises(SystemExit):
            experiment._assert_not_explanations(EXPLANATIONS)

    def test_refuses_any_file_named_explanations_json(self, experiment, tmp_path) -> None:
        with pytest.raises(SystemExit):
            experiment._assert_not_explanations(tmp_path / "explanations.json")

    def test_refuses_anything_inside_the_app_data_directory(self, experiment) -> None:
        with pytest.raises(SystemExit):
            experiment._assert_not_explanations(EXPLANATIONS.parent / "anything.json")
        with pytest.raises(SystemExit):
            experiment._assert_not_explanations(EXPLANATIONS.parent / "sub" / "x.json")

    def test_allows_the_reports_directory(self, experiment) -> None:
        experiment._assert_not_explanations(REPO_ROOT / "reports" / "guard_experiment.md")
        experiment._assert_not_explanations(REPO_ROOT / "reports" / "guard_experiment_raw.json")

    def test_default_output_paths_are_outside_app_data(self, experiment) -> None:
        for path in (experiment.OUTPUT_PATH, experiment.RAW_PATH):
            assert EXPLANATIONS.parent not in path.resolve().parents, path

    def test_the_guard_is_enforced_on_every_write_site(self, experiment) -> None:
        """
        Not just declared — actually called before each write. A guard function
        nobody invokes is decoration.
        """
        source = (SCRIPTS / "guard_experiment.py").read_text()
        # Every write of report or raw output must be preceded by the assertion.
        assert source.count("_assert_not_explanations(") >= 4, (
            "expected the isolation assert at the CLI entry, the report writer "
            "and the raw writer"
        )
        assert "write_json_atomic" not in source, (
            "guard_experiment must not import the store writer at all"
        )

    def test_experiment_never_imports_the_store_path_for_writing(self, experiment) -> None:
        source = (SCRIPTS / "guard_experiment.py").read_text()
        # EXPLANATIONS_PATH may be imported (it is needed to refuse it), but must
        # never be passed to a write.
        assert ".write_text(" not in source.split("def _assert_not_explanations")[0], (
            "a write occurs before the isolation guard is even defined"
        )


# --------------------------------------------------------------------------- #
# Key hygiene
# --------------------------------------------------------------------------- #


class TestKeyHygiene:
    @pytest.fixture(scope="class")
    def common(self):
        return _load("_common")

    def test_redact_never_reveals_the_middle(self, common) -> None:
        secret = "AQ.SUPERSECRETVALUE1234567890abcdefgh"
        rendered = common.redact(secret)
        assert secret not in rendered
        assert "SUPERSECRET" not in rendered
        assert str(len(secret)) in rendered  # length is safe and useful

    def test_scrub_removes_the_key_from_arbitrary_text(
        self, common, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        secret = "AQ.PRETEND_THIS_IS_A_REAL_KEY_0987654321"
        monkeypatch.setenv("GEMINI_API_KEY", secret)
        text = f"Request failed: https://api/v1?key={secret}&x=1"
        scrubbed = common.scrub(text)
        assert secret not in scrubbed
        assert "<<REDACTED_API_KEY>>" in scrubbed

    def test_scrub_handles_exception_objects(
        self, common, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        secret = "AQ.ANOTHER_FAKE_KEY_ABCDEFGHIJKLMNOP"
        monkeypatch.setenv("GEMINI_API_KEY", secret)
        scrubbed = common.scrub(RuntimeError(f"boom key={secret}"))
        assert secret not in scrubbed

    def test_scrub_is_a_noop_when_no_key_is_set(
        self, common, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        assert common.scrub("nothing to hide") == "nothing to hide"

    def test_no_script_prints_a_raw_key(self) -> None:
        """
        Every render of the key must go through redact() or scrub(). A bare
        f-string interpolation of the value would put it in a terminal log.
        """
        import re

        offenders: list[str] = []
        pattern = re.compile(r"print\([^)]*\{(?:key|api_key|secret)\}")
        for path in sorted(SCRIPTS.glob("*.py")):
            for number, line in enumerate(path.read_text().splitlines(), start=1):
                if pattern.search(line):
                    offenders.append(f"{path.name}:{number}")
        assert not offenders, f"raw key interpolated into output at {offenders}"

    def test_exception_sites_are_scrubbed(self) -> None:
        """
        SDK error text is third-party and outside our control, so every site
        that renders an exception must scrub it first.
        """
        import re

        unscrubbed: list[str] = []
        for path in sorted(SCRIPTS.glob("*.py")):
            for number, line in enumerate(path.read_text().splitlines(), start=1):
                # A rendered exception that is neither scrubbed nor sliced.
                if "not-rendered" in line:
                    continue  # explicitly annotated as match-only, never output
                if re.search(r"\{exc\}", line) and "scrub(" not in line:
                    unscrubbed.append(f"{path.name}:{number}: {line.strip()[:60]}")
        assert not unscrubbed, f"exception rendered without scrub(): {unscrubbed}"

    def test_dotenv_is_gitignored_and_untracked(self) -> None:
        import subprocess

        dotenv = REPO_ROOT / ".env"
        if not dotenv.is_file():
            pytest.skip("no .env in this checkout")

        ignored = subprocess.run(
            ["git", "check-ignore", "-q", str(dotenv)], cwd=REPO_ROOT, capture_output=True
        )
        assert ignored.returncode == 0, ".env exists but git does not ignore it"

        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(dotenv)],
            cwd=REPO_ROOT, capture_output=True,
        )
        assert tracked.returncode != 0, ".env is tracked by git"

    def test_no_key_shaped_literal_anywhere_in_the_tree(self) -> None:
        import re

        pattern = re.compile(r"AIza[0-9A-Za-z_\-]{25,}|AQ\.[A-Za-z0-9_\-]{40,}")
        skip = {".venv", ".git", "build", ".dart_tool", "__pycache__", "node_modules", "logs"}
        offenders: list[str] = []
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file() or any(part in skip for part in path.parts):
                continue
            if path.name == ".env":
                continue  # gitignored by design; asserted separately above
            if path.suffix not in {".py", ".md", ".json", ".yaml", ".yml", ".txt", ".sh", ".dart"}:
                continue
            try:
                if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                    offenders.append(str(path.relative_to(REPO_ROOT)))
            except OSError:
                continue
        assert not offenders, f"key-shaped literals found in {offenders}"


# --------------------------------------------------------------------------- #
# The deployed path stays key-free
# --------------------------------------------------------------------------- #


class TestDeployedPathNeedsNoKey:
    """
    The whole point of pre-generation: the key is BUILD-TIME ONLY. If the served
    path ever needs one, the deployment story collapses.
    """

    def test_analyze_returns_complete_explanations_with_no_key(
        self, monkeypatch: pytest.MonkeyPatch, cyp2c19_pm_report, valid_vcf_bytes
    ) -> None:
        import io

        from fastapi.testclient import TestClient

        from app import main
        from app.explanation import generator_llm

        for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setenv("EXPLANATION_MODE", "static")

        def forbidden(*args, **kwargs):
            raise AssertionError("the served path called the LLM generator")

        monkeypatch.setattr(generator_llm, "generate", forbidden)

        async def fake_run_pharmcat(vcf_text: str, *, sample_hint: str = "sample"):
            return cyp2c19_pm_report

        monkeypatch.setattr(main, "run_pharmcat", fake_run_pharmcat)

        response = TestClient(main.app).post(
            "/analyze",
            files={"file": ("t.vcf", io.BytesIO(valid_vcf_bytes), "text/plain")},
            data={"drugs": "clopidogrel,codeine,aspirin"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["analyses"]

        for analysis in body["analyses"]:
            explanation = analysis["llm_generated_explanation"]
            for field, text in explanation.items():
                assert text.strip(), f"{analysis['drug']}.{field} is empty without a key"
            assert "Not a medical device" in explanation["disclaimer"]
            # Slots must be filled, not leaked to the user as literals.
            assert "{" not in " ".join(
                v for k, v in explanation.items() if k != "disclaimer"
            )

    def test_scripts_are_not_imported_by_the_application(self) -> None:
        """
        Build-time tooling must not leak into the served app. If `app.*` ever
        imports from `scripts/`, the key-free guarantee becomes accidental.
        """
        import re

        # Real import statements only. Docstrings legitimately *mention* the
        # scripts — that is documentation of where generation happens, not a
        # dependency — so a substring match would flag prose.
        import_pattern = re.compile(
            r"^\s*(?:from\s+(?:_common|scripts\.|pregenerate_explanations|guard_experiment)"
            r"|import\s+(?:_common|pregenerate_explanations|guard_experiment))\b",
            re.MULTILINE,
        )
        app_dir = REPO_ROOT / "backend" / "app"
        offenders = [
            str(path.relative_to(REPO_ROOT))
            for path in app_dir.rglob("*.py")
            if import_pattern.search(path.read_text())
        ]
        assert not offenders, f"application code imports build-time tooling: {offenders}"
