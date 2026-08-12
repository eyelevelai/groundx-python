from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIER = REPO_ROOT / "scripts" / "verify_release_intentional_red.py"
CLASSNAME = "tests.extract.test_extraction_boundary_reassembly"
EXPECTED_FAILURES = {
    "test_sdk_xray_reassembly_real_boundary_packets[arcadia_legacy]": "arcadia_legacy",
    "test_sdk_xray_reassembly_real_boundary_packets[arcadia_v1]": "arcadia_v1",
    "test_sdk_xray_reassembly_real_boundary_packets[generic_v1]": "generic_v1",
    "test_sdk_xray_reassembly_real_boundary_packets[adp_v1]": "adp_v1",
    "test_adp_boundary_reassembly_detects_corrupted_real_input": "adp_v1",
    "test_adp_boundary_reassembly_detects_corrupted_expected_output": "adp_v1",
    "test_adp_boundary_reassembly_rejects_invalid_identity_threshold_metadata": "adp_v1",
}


def _failure_message(surface: str) -> str:
    return (
        "Failed: INTENTIONAL RED: protected extraction boundary fixture is missing: "
        "tests/extract/fixtures/extraction-boundary/inputs/"
        f"{surface}/internal_arcadia_download_workflow_load.handoff.json. "
        "Remove this protected case only from the canonical Harness certification registry, "
        "then regenerate the owner projections. Never add a skip."
    )


def _write_report(
    path: Path,
    outcomes: dict[str, tuple[str, str | None]],
) -> None:
    suite = ET.Element("testsuite", name="pytest tests")
    for name, (outcome, message) in outcomes.items():
        case = ET.SubElement(suite, "testcase", classname=CLASSNAME, name=name)
        if outcome != "passed":
            child = ET.SubElement(case, outcome)
            if message is not None:
                child.set("message", message)
    suite.set("tests", str(len(outcomes)))
    suite.set("failures", str(sum(outcome == "failure" for outcome, _ in outcomes.values())))
    suite.set("errors", str(sum(outcome == "error" for outcome, _ in outcomes.values())))
    suite.set("skipped", str(sum(outcome == "skipped" for outcome, _ in outcomes.values())))
    ET.ElementTree(ET.Element("testsuites")).write(path, encoding="utf-8", xml_declaration=True)
    root = ET.parse(path).getroot()
    root.append(suite)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def _run_verifier(report: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFIER), str(report)],
        check=False,
        capture_output=True,
        text=True,
    )


def _expected_failures() -> dict[str, tuple[str, str | None]]:
    return {name: ("failure", _failure_message(surface)) for name, surface in EXPECTED_FAILURES.items()}


def _expected_passes() -> dict[str, tuple[str, str | None]]:
    return {name: ("passed", None) for name in EXPECTED_FAILURES}


def test_release_gate_accepts_exact_intentional_fixture_failures(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    _write_report(report, _expected_failures())

    result = _run_verifier(report)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "exactly seven approved intentional fixture failures" in result.stdout


def test_release_gate_accepts_all_seven_tests_after_fixture_promotion(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    _write_report(report, _expected_passes())

    result = _run_verifier(report)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "all seven protected fixture tests passed" in result.stdout


def test_release_gate_rejects_missing_test(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    outcomes = _expected_failures()
    outcomes.pop(next(iter(outcomes)))
    _write_report(report, outcomes)

    result = _run_verifier(report)

    assert result.returncode == 1
    assert "missing test" in result.stderr


def test_release_gate_rejects_extra_test(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    outcomes = _expected_failures()
    outcomes["test_unexpected_failure"] = ("failure", "unexpected")
    _write_report(report, outcomes)

    result = _run_verifier(report)

    assert result.returncode == 1
    assert "unexpected test" in result.stderr


def test_release_gate_rejects_changed_failure_reason(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    outcomes = _expected_failures()
    name = next(iter(outcomes))
    outcomes[name] = ("failure", "Failed: different reason")
    _write_report(report, outcomes)

    result = _run_verifier(report)

    assert result.returncode == 1
    assert "failure message changed" in result.stderr


def test_release_gate_rejects_mixed_pass_and_failure(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    outcomes = _expected_failures()
    outcomes[next(iter(outcomes))] = ("passed", None)
    _write_report(report, outcomes)

    result = _run_verifier(report)

    assert result.returncode == 1
    assert "mixed outcomes" in result.stderr


def test_release_gate_rejects_skip_or_error(tmp_path: Path) -> None:
    for outcome in ("skipped", "error"):
        report = tmp_path / f"{outcome}.xml"
        outcomes = _expected_failures()
        outcomes[next(iter(outcomes))] = (outcome, "changed outcome")
        _write_report(report, outcomes)

        result = _run_verifier(report)

        assert result.returncode == 1
        assert outcome in result.stderr
