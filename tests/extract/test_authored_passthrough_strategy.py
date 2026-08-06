"""Authored v1 YAML declares `passthrough.multiple_match_strategy` (task 3.2a7b, fix round 2).

Cross-repo contract crosswalk defect: `_PASSTHROUGH_KEYS`
(`src/groundx/extract/prompt/utility.py`) omitted `multiple_match_strategy`, so
`_validate_object_array_metadata` rejected authored YAML declaring
`passthrough.multiple_match_strategy: first_stable` with "unsupported
passthrough keys" -- while Cashbot accepts the identical authored source
(`pkg/workflowyaml/validate_source.go:858-866`, task 3.2a7a: "The generic
source declares `passthrough.multiple_match_strategy: first_stable`") and the
SDK's own derivation (`_relationships_from_final_group_metadata`) consumes the
key.  No prior test authored the key through `prepare_extraction_yaml`; every
existing test supplied it via the persisted path or internal helpers.

These tests pin the authored path end to end on a renamed generic v1 source:
compile, packet transport, matcher tie-break, and the only-`first_stable`
contract (spec.md:348-349, design.md:392-394).
"""

import pytest

from groundx.extract import prepare_extraction_yaml
from groundx.extract.custom_outputs import reassemble_custom_outputs_from_xray

_AUTHORED_RENAMED_GENERIC_V1 = """
extraction_policy_version: v1
workflow:
  custom_steps:
    - {name: parent_rows, level: chunk, kind: keys}
    - {name: child_rows, level: chunk, kind: keys}
generic_group_b:
  workflow_step: parent_rows
  fields:
    generic_attr_18:
      workflow_output_key: generic_attr_18
      prompt: {instructions: Return the key, type: str}
generic_group_c:
  workflow_step: child_rows
  match_attrs: [generic_attr_18]
  passthrough:
    from: generic_group_b
    parent_output_field: generic_group_c
    unmatched_child_group: generic_group_c
    multiple_match_strategy: __STRATEGY__
  fields:
    generic_attr_18:
      workflow_output_key: generic_attr_18
      prompt: {instructions: Return the key, type: str}
"""


def _authored_source(strategy: str) -> str:
    return _AUTHORED_RENAMED_GENERIC_V1.replace("__STRATEGY__", strategy)


def test_authored_first_stable_strategy_compiles_into_the_relationship_packet() -> None:
    prepared = prepare_extraction_yaml(_authored_source("first_stable"))

    assert prepared.persisted_workflow_extract["workflow"]["output_relationships"] == [
        {
            "parent_group": "generic_group_b",
            "child_group": "generic_group_c",
            "parent_output_field": "generic_group_c",
            "match_attrs": ["generic_attr_18"],
            "unmatched_child_group": "generic_group_c",
            "multiple_match_strategy": "first_stable",
        }
    ]


def test_authored_first_stable_strategy_reaches_the_matcher_tie_break() -> None:
    """Two exact candidates: the authored `first_stable` declaration must reach
    `select_relationship_parent`, selecting the first parent in input order
    instead of reporting the undeclared-strategy ambiguity (behavior-table rows
    R15/R16)."""
    prepared = prepare_extraction_yaml(_authored_source("first_stable"))
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "parent_rows": {
                        "_records": [
                            {"generic_attr_18": "K-1"},
                            {"generic_attr_18": "k-1"},
                        ]
                    },
                    "child_rows": {"_records": [{"generic_attr_18": "K-1"}]},
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=prepared.persisted_workflow_extract,
    )

    assert result.diagnostics == []
    final = result.final_output
    assert final["generic_group_b"][0]["generic_group_c"] == [
        {"generic_attr_18": "K-1"}
    ]
    assert final["generic_group_b"][1]["generic_group_c"] == []
    assert final.get("generic_group_c", []) == []


@pytest.mark.parametrize(
    "rejected",
    ["first_match", "first", "last_stable", "FIRST_STABLE"],
)
def test_authored_non_first_stable_strategy_is_rejected(rejected: str) -> None:
    """spec.md:348-349 / design.md:392-394 -- `first_stable` is the only
    accepted ambiguity value on the authored path too."""
    with pytest.raises(ValueError, match="first_stable"):
        prepare_extraction_yaml(_authored_source(rejected))


def test_authored_passthrough_without_strategy_still_compiles() -> None:
    """Guard: allowlisting the key must not make it required."""
    source = "\n".join(
        line
        for line in _authored_source("first_stable").splitlines()
        if "multiple_match_strategy" not in line
    )
    prepared = prepare_extraction_yaml(source)
    relationship = prepared.persisted_workflow_extract["workflow"][
        "output_relationships"
    ][0]

    assert "multiple_match_strategy" not in relationship
    assert relationship["match_attrs"] == ["generic_attr_18"]
