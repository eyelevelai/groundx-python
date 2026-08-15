#!/usr/bin/env python3
"""Fail closed unless the release-only fixture test set has one valid outcome."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CLASSNAME = "tests.extract.test_extraction_boundary_reassembly"
SURFACES_BY_TEST = {
    "test_boundary_workflow_leaf_repetition_scope_is_api_enum[arcadia_legacy]": "arcadia_legacy",
    "test_boundary_workflow_leaf_repetition_scope_is_api_enum[arcadia_v1]": "arcadia_v1",
    "test_boundary_workflow_leaf_repetition_scope_is_api_enum[generic_v1]": "generic_v1",
    "test_boundary_workflow_leaf_repetition_scope_is_api_enum[adp_v1]": "adp_v1",
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


EXPECTED_FAILURES = {(CLASSNAME, name): _failure_message(surface) for name, surface in SURFACES_BY_TEST.items()}


def _testcase_outcome(testcase: ET.Element) -> tuple[str, str]:
    outcome_children = [child for child in testcase if child.tag in {"failure", "error", "skipped"}]
    if not outcome_children:
        return "passed", ""
    if len(outcome_children) != 1:
        return "invalid", ""
    child = outcome_children[0]
    return child.tag, child.attrib.get("message", "")


def verify_report(path: Path) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        return [f"cannot read JUnit report: {exc}"]

    observed: dict[tuple[str, str], tuple[str, str]] = {}
    errors: list[str] = []
    for testcase in root.iter("testcase"):
        key = (testcase.attrib.get("classname", ""), testcase.attrib.get("name", ""))
        if key in observed:
            errors.append(f"duplicate test: {key[0]}::{key[1]}")
            continue
        observed[key] = _testcase_outcome(testcase)

    expected_keys = set(EXPECTED_FAILURES)
    observed_keys = set(observed)
    for classname, name in sorted(expected_keys - observed_keys):
        errors.append(f"missing test: {classname}::{name}")
    for classname, name in sorted(observed_keys - expected_keys):
        errors.append(f"unexpected test: {classname}::{name}")
    if errors:
        return errors

    outcomes = {outcome for outcome, _message in observed.values()}
    if outcomes == {"passed"}:
        return []
    if outcomes != {"failure"}:
        details = ", ".join(f"{name}={outcome}" for (_classname, name), (outcome, _message) in sorted(observed.items()))
        return [f"mixed outcomes are not allowed: {details}"]

    for key, expected_message in EXPECTED_FAILURES.items():
        observed_message = observed[key][1]
        if observed_message != expected_message:
            errors.append(f"failure message changed for {key[0]}::{key[1]}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("junit_report", type=Path)
    args = parser.parse_args(argv)

    errors = verify_report(args.junit_report)
    if errors:
        for error in errors:
            print(f"release fixture gate failed: {error}", file=sys.stderr)
        return 1

    root = ET.parse(args.junit_report).getroot()
    outcomes = {_testcase_outcome(testcase)[0] for testcase in root.iter("testcase")}
    if outcomes == {"passed"}:
        print(f"release fixture gate passed: all {len(EXPECTED_FAILURES)} protected fixture tests passed")
    else:
        print(
            f"release fixture gate passed: exactly {len(EXPECTED_FAILURES)} approved intentional fixture failures"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
