import copy
import hashlib
import json
import os
import pathlib
import typing

import pytest

from groundx.extract.custom_outputs import reassemble_custom_outputs_from_xray

UPDATE_GOLDENS_ENV = "UPDATE_GROUNDX_PYTHON_EXTRACT_BOUNDARY_GOLDENS"
ROOT = pathlib.Path(__file__).resolve().parents[2]
EXPECTED_ROOT = ROOT / "tests" / "extract" / "fixtures" / "extraction-boundary"
BOUNDARY_GOLDENS_ROOT = EXPECTED_ROOT / "boundary-goldens"
HANDOFF_ROOT = EXPECTED_ROOT / "boundary-handoffs"
INPUT_ROOT = EXPECTED_ROOT / "inputs"
ADP_EXPECTED_SECTION_COUNT = 11
ADP_EXPECTED_FIELD_COUNT = 159
ADP_MIN_POPULATED_FIELDS = 100
ADP_MAX_POPULATED_FIELDS = 159
ADP_MIN_NULL_FIELDS = 0
ADP_MAX_NULL_FIELDS = 59
ADP_MIN_SECTION_POPULATED_RATIO = 0.6


SURFACES = [
    "arcadia_legacy",
    "arcadia_v1",
    "generic_v1",
    "adp_v1",
]


def test_sdk_reassembly_boundary_packets(tmp_path: pathlib.Path) -> None:
    update_goldens = os.environ.get(UPDATE_GOLDENS_ENV) == "1"
    for surface in SURFACES:
        actual, actual_path, expected_path, diff_path, previous_path, handoff_path = (
            _write_boundary_artifacts(tmp_path, surface)
        )
        expected = _stable_boundary_output(actual)
        if update_goldens:
            _write_json(expected_path, expected)
            _write_json(
                handoff_path,
                _read_json(pathlib.Path(actual["artifacts"]["handoff"]["path"])),
            )

        golden = _read_json(expected_path)
        expected_handoff_sha = _sha256_file(handoff_path)
        actual_handoff_sha = actual["artifacts"]["handoff"]["sha256"]
        handoff = _read_json(pathlib.Path(actual["artifacts"]["handoff"]["path"]))
        _assert_no_synthetic_protected_marker(actual)
        _assert_no_synthetic_protected_marker(handoff)
        diff: typing.Dict[str, typing.Any] = {
            "kind": "machine_readable_json_diff",
            "status": "passed",
        }
        if golden != expected or expected_handoff_sha != actual_handoff_sha:
            diff = {
                "kind": "machine_readable_json_diff",
                "status": "failed",
                "expected": golden,
                "actual": expected,
                "handoff_expected_sha256": expected_handoff_sha,
                "handoff_actual_sha256": actual_handoff_sha,
            }
            _write_json(diff_path, diff)
            pytest.fail(
                "SDK reassembly boundary drifted for "
                f"{surface}; run {UPDATE_GOLDENS_ENV}=1 PYTHONPATH=src pytest "
                "tests/extract/test_extraction_boundary_reassembly.py -q if "
                "this contract change is intended"
            )
        _write_json(diff_path, diff)


def test_boundary_inputs_are_repo_local() -> None:
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    forbidden = [
        "INTERNAL_" + "ARCADIA_" + "ROOT",
        "PLATFORM_" + "ROOT",
    ]
    for token in forbidden:
        assert token not in source, (
            "SDK reassembly boundary tests must consume committed local "
            f"previous-boundary inputs, not sibling repo path {token}"
        )


@pytest.mark.parametrize(
    ("meter_count", "expected"),
    [
        (6, False),
        (7, True),
        (8, True),
        (9, True),
        (10, False),
    ],
)
def test_utility_shape_accepts_reviewed_meter_range(
    meter_count: int,
    expected: bool,
) -> None:
    final_output: typing.Dict[str, typing.Any] = {
        "meters": [{"charges": [{"amount": index}]} for index in range(meter_count)],
        "charges": [{"amount": "account-level"}],
    }
    final_output.update({f"statement_field_{index}": index for index in range(14)})

    assertions = _shape_assertions(
        "arcadia_v1",
        final_output,
        diagnostics=[],
        relationship_output={"charges": []},
    )

    assert assertions["has_expected_parent_count"] is expected


@pytest.mark.parametrize(
    ("meter_charge_count", "expected"),
    [
        (21, False),
        (22, True),
        (23, True),
        (28, True),
        (32, True),
        (33, False),
        (50, False),
    ],
)
def test_utility_shape_accepts_reviewed_meter_charge_range(
    meter_charge_count: int,
    expected: bool,
) -> None:
    final_output: typing.Dict[str, typing.Any] = {
        "meters": [{"charges": []} for _unused in range(8)],
        "charges": [],
    }
    for index in range(meter_charge_count):
        final_output["meters"][index % 8]["charges"].append(
            {"charge_amount": index}
        )
    final_output.update({f"statement_field_{index}": index for index in range(14)})

    assertions = _shape_assertions(
        "arcadia_v1",
        final_output,
        diagnostics=[],
        relationship_output={"meters": final_output["meters"]},
    )

    assert assertions["has_expected_meter_charge_count"] is expected


@pytest.mark.parametrize(
    ("account_charge_count", "expected"),
    [
        (0, True),
        (1, True),
        (3, True),
        (4, False),
    ],
)
def test_utility_shape_accepts_reviewed_account_charge_range(
    account_charge_count: int,
    expected: bool,
) -> None:
    final_output: typing.Dict[str, typing.Any] = {
        "meters": [
            {"charges": [{"charge_amount": meter_index}]}
            for meter_index in range(8)
        ],
        "charges": [
            {"charge_amount": charge_index}
            for charge_index in range(account_charge_count)
        ],
    }
    final_output.update({f"statement_field_{index}": index for index in range(14)})

    assertions = _shape_assertions(
        "arcadia_v1",
        final_output,
        diagnostics=[],
        relationship_output={"meters": final_output["meters"]},
    )

    assert assertions["has_expected_account_child_count"] is expected


def _write_boundary_artifacts(
    tmp_path: pathlib.Path,
    surface: str,
) -> typing.Tuple[
    typing.Dict[str, typing.Any],
    pathlib.Path,
    pathlib.Path,
    pathlib.Path,
    pathlib.Path,
    pathlib.Path,
]:
    out_dir = tmp_path / surface
    previous_path = (
        INPUT_ROOT
        / surface
        / "internal_arcadia_extract_chain.handoff.json"
    )
    previous = _read_json(previous_path)
    result = reassemble_custom_outputs_from_xray(
        previous["xray"],
        workflow_extract=previous["workflow_extract"],
    )
    diagnostics = [
        {
            "code": diagnostic.code,
            "message": diagnostic.message,
            "severity": diagnostic.severity,
            "workflow_group": diagnostic.workflow_group,
            "workflow_field": diagnostic.workflow_field,
            "final_path": diagnostic.final_path,
            "relationship": diagnostic.relationship,
            "child_record_index": diagnostic.child_record_index,
        }
        for diagnostic in result.diagnostics
    ]
    source_provenance = [
        {
            "output_source": provenance.output_source,
            "workflow_group": provenance.workflow_group,
            "workflow_field": provenance.workflow_field,
            "final_path": provenance.final_path,
            "record_index": provenance.record_index,
            "page_numbers": list(provenance.page_numbers),
        }
        for provenance in result.source_provenance
    ]
    final_output = copy.deepcopy(result.final_output)
    assertions = _shape_assertions(
        surface,
        final_output,
        diagnostics,
        result.relationship_output,
        workflow_extract=previous["workflow_extract"],
    )
    inherited_evidence = _inherited_evidence(previous)

    handoff = {
        "schema_version": "groundx-python-sdk-reassembly-handoff-v1",
        "surface": surface,
        "stage": "groundx_python_sdk_reassembly",
        "input_from": "internal_arcadia_extract_chain",
        "output_for": "internal_arcadia_save_callback",
        "workflow_schema_hash": previous["workflow_schema_hash"],
        "request": previous["request"],
        "input_sha256": _sha256_file(previous_path),
        "workflow_output": result.workflow_output,
        "relationship_output": result.relationship_output,
        "final_output": final_output,
        "diagnostics": diagnostics,
        "source_provenance": source_provenance,
    }
    handoff.update(inherited_evidence)
    handoff_actual_path = out_dir / "groundx_python_sdk_reassembly.handoff.json"
    _write_json(handoff_actual_path, handoff)

    actual = {
        "surface": surface,
        "stage": "groundx_python_sdk_reassembly",
        "input_from": "internal_arcadia_extract_chain",
        "output_for": "internal_arcadia_save_callback",
        "workflow_schema_hash": previous["workflow_schema_hash"],
        "request": previous["request"],
        "input_sha256": _sha256_file(previous_path),
        "output": {
            "workflow_output_sha256": _sha256_json(result.workflow_output),
            "relationship_output_sha256": _sha256_json(result.relationship_output),
            "final_output_sha256": _sha256_json(final_output),
            "diagnostic_count": len(diagnostics),
            "source_provenance_count": len(source_provenance),
        },
        "shape_assertions": assertions,
        "artifacts": {
            "previous_extract_chain": {
                "path": str(previous_path),
                "sha256": _sha256_file(previous_path),
            },
            "handoff": {
                "path": str(handoff_actual_path),
                "sha256": _sha256_file(handoff_actual_path),
            },
        },
        "assertions": {
            "consumes_internal_extract_chain_handoff": previous["stage"]
            == "internal_arcadia_extract_chain",
            "has_no_error_diagnostics": assertions["has_no_error_diagnostics"],
            "shape_contract_passed": all(assertions.values()),
            "handoff_written_for_save_callback": handoff_actual_path.exists(),
        },
    }
    actual.update(inherited_evidence)
    assert actual["assertions"]["consumes_internal_extract_chain_handoff"]
    assert actual["assertions"]["has_no_error_diagnostics"]
    assert actual["assertions"]["shape_contract_passed"]
    assert actual["assertions"]["handoff_written_for_save_callback"]
    if previous.get("evidence_level") == "plumbing_only_synthetic":
        assert actual["evidence_level"] == "plumbing_only_synthetic"
        assert actual["certification_eligible"] is False

    actual_path = out_dir / "groundx_python_sdk_reassembly.actual.json"
    expected_path = (
        BOUNDARY_GOLDENS_ROOT / surface / "groundx_python_sdk_reassembly.expected.json"
    )
    diff_path = out_dir / "groundx_python_sdk_reassembly.diff.json"
    handoff_path = (
        HANDOFF_ROOT / surface / "groundx_python_sdk_reassembly.handoff.json"
    )
    _write_json(actual_path, actual)
    return actual, actual_path, expected_path, diff_path, previous_path, handoff_path


def _inherited_evidence(previous: typing.Mapping[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    inherited: typing.Dict[str, typing.Any] = {}
    if "evidence_level" in previous:
        inherited["evidence_level"] = previous["evidence_level"]
    if "certification_eligible" in previous:
        inherited["certification_eligible"] = previous["certification_eligible"]
    if "model_fixture" in previous:
        inherited["model_fixture"] = previous["model_fixture"]
    return inherited


def _assert_no_synthetic_protected_marker(
    value: typing.Any,
    path: typing.Tuple[str, ...] = (),
) -> None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_synthetic_protected_marker(item, path + (str(index),))
        return

    if isinstance(value, dict):
        for key, item in value.items():
            child_path = path + (str(key),)
            assert key != "fake_agent_data", ".".join(child_path)
            assert not (key == "certification_eligible" and item is False), ".".join(
                child_path
            )
            _assert_no_synthetic_protected_marker(item, child_path)
        return

    if isinstance(value, str):
        for marker in (
            "arcadia_legacy_",
            "arcadia_v1_",
            "generic_v1_",
            "adp_v1_",
            "_parent_",
            "_account_level",
            "deterministic_from_cashbot_deployed_output_routes",
            "plumbing_only_synthetic",
            "_fake_xray_for_workflow",
            "boundary://",
        ):
            assert marker not in value, ".".join(path)


def _shape_assertions(
    surface: str,
    final_output: typing.Mapping[str, typing.Any],
    diagnostics: typing.Sequence[typing.Mapping[str, typing.Any]],
    relationship_output: typing.Any,
    *,
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]] = None,
) -> typing.Dict[str, bool]:
    assertions = {
        "has_no_error_diagnostics": not any(
            diagnostic.get("severity") == "error" for diagnostic in diagnostics
        )
    }
    if surface == "adp_v1":
        assertions.update(_adp_shape_assertions(final_output, workflow_extract or {}))
        return assertions

    parent_group, child_group, child_field = _utility_groups(surface)
    parent_records = final_output.get(parent_group)
    account_children = final_output.get(child_group)
    assertions.update(
        {
            "has_expected_parent_count": isinstance(parent_records, list)
            and 7 <= len(parent_records) <= 9,
            "every_parent_has_child_rows": isinstance(parent_records, list)
            and all(
                isinstance(parent, dict)
                and isinstance(parent.get(child_field), list)
                and len(parent[child_field]) >= 1
                for parent in parent_records
            ),
            "has_expected_account_child_count": isinstance(account_children, list)
            and 0 <= len(account_children) <= 3,
            "has_expected_meter_charge_count": isinstance(parent_records, list)
            and 22
            <= _nested_child_count(parent_records, child_field)
            <= 32,
            "has_statement_fields": _statement_field_count(surface, final_output) >= 14,
            "has_relationship_output": bool(relationship_output),
        }
    )
    return assertions


def _adp_shape_assertions(
    final_output: typing.Mapping[str, typing.Any],
    workflow_extract: typing.Mapping[str, typing.Any],
) -> typing.Dict[str, bool]:
    expected_sections = _adp_expected_sections(workflow_extract)
    actual_sections = {
        str(section_name)
        for section_name, section_value in final_output.items()
        if isinstance(section_value, typing.Mapping)
    }
    actual_fields = {
        f"{section_name}.{field_name}"
        for section_name, section_value in final_output.items()
        if isinstance(section_value, typing.Mapping)
        for field_name in section_value
        if not str(field_name).startswith("_")
    }
    expected_fields = {
        f"{section_name}.{field_name}"
        for section_name, fields in expected_sections.items()
        for field_name in fields
    }

    populated_field_count = 0
    populated_by_section: typing.Dict[str, int] = {}
    ratio_failures: typing.List[str] = []
    for section_name, fields in expected_sections.items():
        section_value = final_output.get(section_name)
        if not isinstance(section_value, typing.Mapping):
            populated_by_section[section_name] = 0
            ratio_failures.append(section_name)
            continue
        section_populated = 0
        ratio_fields = _adp_section_ratio_fields(fields)
        ratio_populated = 0
        for field_name in fields:
            if _has_extracted_value(section_value.get(field_name)):
                populated_field_count += 1
                section_populated += 1
                if field_name in ratio_fields:
                    ratio_populated += 1
        populated_by_section[section_name] = section_populated
        ratio = ratio_populated / len(ratio_fields) if ratio_fields else 1.0
        if ratio < ADP_MIN_SECTION_POPULATED_RATIO:
            ratio_failures.append(section_name)

    null_or_blank_count = len(expected_fields) - populated_field_count
    return {
        "has_expected_adp_section_count": len(expected_sections)
        == ADP_EXPECTED_SECTION_COUNT
        and actual_sections == set(expected_sections),
        "has_expected_adp_field_count": len(expected_fields) == ADP_EXPECTED_FIELD_COUNT
        and actual_fields == expected_fields,
        "has_adp_populated_fields_in_range": ADP_MIN_POPULATED_FIELDS
        <= populated_field_count
        <= ADP_MAX_POPULATED_FIELDS,
        "has_adp_null_fields_in_range": ADP_MIN_NULL_FIELDS
        <= null_or_blank_count
        <= ADP_MAX_NULL_FIELDS,
        "has_adp_core_fields_populated_by_section": not ratio_failures,
    }


def _adp_expected_sections(
    workflow_extract: typing.Mapping[str, typing.Any],
) -> typing.Dict[str, typing.List[str]]:
    workflow = workflow_extract.get("workflow")
    routes = workflow.get("output_routes") if isinstance(workflow, dict) else None
    expected: typing.Dict[str, typing.List[str]] = {}
    if not isinstance(routes, list):
        return expected
    for route in routes:
        if not isinstance(route, typing.Mapping):
            continue
        final_path = route.get("final_path")
        if not isinstance(final_path, str):
            continue
        parts = _pointer_parts(final_path)
        if len(parts) != 2:
            continue
        section_name, field_name = parts
        if section_name in {"meters", "charges"}:
            continue
        fields = expected.setdefault(section_name, [])
        if field_name not in fields:
            fields.append(field_name)
    return expected


def _adp_section_ratio_fields(fields: typing.Sequence[str]) -> typing.Tuple[str, ...]:
    return tuple(
        field_name
        for field_name in fields
        if not field_name.endswith("_other_specify")
    )


def _has_extracted_value(value: typing.Any) -> bool:
    if isinstance(value, typing.Mapping) and "value" in value:
        return _has_extracted_value(value.get("value"))
    if value in (None, "", [], {}):
        return False
    return True


def _pointer_parts(pointer: str) -> typing.Tuple[str, ...]:
    if not pointer.startswith("/"):
        return ()
    return tuple(
        part.replace("~1", "/").replace("~0", "~")
        for part in pointer.split("/")[1:]
        if part
    )


def _utility_groups(surface: str) -> typing.Tuple[str, str, str]:
    if surface == "generic_v1":
        return "generic_group_b", "generic_group_c", "generic_group_c"
    return "meters", "charges", "charges"


def _statement_field_count(
    surface: str,
    final_output: typing.Mapping[str, typing.Any],
) -> int:
    if surface == "arcadia_legacy":
        statement = final_output.get("statement")
        return len(statement) if isinstance(statement, dict) else 0
    if surface == "generic_v1":
        return sum(
            1
            for key in final_output
            if isinstance(key, str) and key.startswith("generic_attr_")
        )
    excluded = {"meters", "charges"}
    return sum(1 for key in final_output if key not in excluded)


def _nested_child_count(
    parent_records: typing.Sequence[typing.Mapping[str, typing.Any]],
    child_field: str,
) -> int:
    child_count = 0
    for parent in parent_records:
        children = parent.get(child_field)
        if isinstance(children, list):
            child_count += len(children)
    return child_count


def _leaf_count(value: typing.Any) -> int:
    if isinstance(value, dict):
        return sum(_leaf_count(child) for child in value.values())
    if isinstance(value, list):
        return sum(_leaf_count(child) for child in value)
    return 1


def _stable_boundary_output(
    actual: typing.Mapping[str, typing.Any],
) -> typing.Dict[str, typing.Any]:
    stable = copy.deepcopy(dict(actual))
    artifacts = stable.get("artifacts")
    if isinstance(artifacts, dict):
        for value in artifacts.values():
            if isinstance(value, dict):
                value.pop("path", None)
    return typing.cast(typing.Dict[str, typing.Any], _json_round_trip(stable))


def _read_json(path: pathlib.Path) -> typing.Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: pathlib.Path, data: typing.Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _json_round_trip(data: typing.Any) -> typing.Any:
    return json.loads(json.dumps(data, sort_keys=True))


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(data: typing.Any) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
