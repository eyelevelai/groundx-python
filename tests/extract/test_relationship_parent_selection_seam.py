"""Packet transport and single-matcher relationship selection tests."""

import typing

import pytest

import groundx.extract as extract
import groundx.extract.custom_outputs as custom_outputs
from groundx.extract.custom_outputs import reassemble_custom_outputs_from_xray
from groundx.extract.prompt import utility as prompt_utility

_MATCHER_NAME = "select_relationship_parent"

_ARCADIA_MATCH_ATTRS = ["meter_number", "provider_name", "service_type"]
_ARCADIA_PARENT_PASSTHROUGH = [
    "deregulation_status",
    "pass_through_provider_account_number",
    "pass_through_provider_name",
    "provider_name",
]


def _workflow_extract(
    *,
    relationship_overrides: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    parent_passthrough_attrs: typing.Optional[typing.Sequence[str]] = None,
) -> typing.Dict[str, typing.Any]:
    if parent_passthrough_attrs is None:
        parent_passthrough_attrs = _ARCADIA_PARENT_PASSTHROUGH
    relationship: typing.Dict[str, typing.Any] = {
        "parent_group": "meters",
        "child_group": "charges",
        "parent_output_field": "meter_charges",
        "match_attrs": list(_ARCADIA_MATCH_ATTRS),
        "parent_passthrough_attrs": list(parent_passthrough_attrs),
        "unmatched_child_group": "account_charges",
    }
    if relationship_overrides:
        relationship.update(relationship_overrides)
    fields = ("meter_number", "provider_name", "service_type")
    return {
        "_groundx_persisted_extract": {
            "charges": {"match_attrs": list(_ARCADIA_MATCH_ATTRS)},
            "meters": {"passthrough_attrs": list(parent_passthrough_attrs)},
        },
        "workflow": {
            "custom_steps": [
                {"name": "meter_step", "level": "chunk", "kind": "keys"},
                {"name": "charge_step", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": group,
                    "workflow_field": field,
                    "final_path": f"/{group}/*/{field}",
                    "step_name": step,
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": field,
                }
                for group, step in (("meters", "meter_step"), ("charges", "charge_step"))
                for field in fields
            ],
            "output_relationships": [relationship],
        },
    }


def _reassemble(
    meter_rows: typing.Sequence[typing.Mapping[str, typing.Any]],
    charge_rows: typing.Sequence[typing.Mapping[str, typing.Any]],
    **kwargs: typing.Any,
) -> typing.Any:
    return reassemble_custom_outputs_from_xray(
        {
            "chunks": [
                {
                    "customChunkOutputs": {
                        "meter_step": {"_records": list(meter_rows)},
                        "charge_step": {"_records": list(charge_rows)},
                    }
                }
            ]
        },
        workflow_extract=_workflow_extract(**kwargs),
    )


def test_normalizer_carries_persisted_parent_passthrough_attrs() -> None:
    """design.md:396-402 -- the packet is exactly seven fields, including
    `parent_passthrough_attrs`.  The normalizer must not silently drop it.
    """
    normalized = prompt_utility._normalize_custom_relationship(
        {
            "parent_group": "meters",
            "child_group": "charges",
            "parent_output_field": "meter_charges",
            "match_attrs": list(_ARCADIA_MATCH_ATTRS),
            "parent_passthrough_attrs": list(_ARCADIA_PARENT_PASSTHROUGH),
            "unmatched_child_group": "account_charges",
            "multiple_match_strategy": "first_stable",
        },
        0,
    )

    assert normalized["parent_passthrough_attrs"] == _ARCADIA_PARENT_PASSTHROUGH
    assert normalized["multiple_match_strategy"] == "first_stable"


def test_normalizer_accepts_dispatched_camel_case_parent_passthrough_attrs() -> None:
    """design.md:394-396 -- Cashbot dispatches `parentPassthroughAttrs`."""
    normalized = prompt_utility._normalize_custom_relationship(
        {
            "parentGroup": "meters",
            "childGroup": "charges",
            "parentOutputField": "meter_charges",
            "matchAttrs": list(_ARCADIA_MATCH_ATTRS),
            "parentPassthroughAttrs": list(_ARCADIA_PARENT_PASSTHROUGH),
            "unmatchedChildGroup": "account_charges",
            "multipleMatchStrategy": "first_stable",
        },
        0,
    )

    assert normalized["parent_group"] == "meters"
    assert normalized["match_attrs"] == _ARCADIA_MATCH_ATTRS
    assert normalized["parent_passthrough_attrs"] == _ARCADIA_PARENT_PASSTHROUGH
    assert normalized["multiple_match_strategy"] == "first_stable"


def test_empty_parent_passthrough_attrs_normalize_to_empty_list() -> None:
    """design.md:404 -- an empty parent `passthrough_attrs` becomes an empty list."""
    normalized = prompt_utility._normalize_custom_relationship(
        {
            "parent_group": "meters",
            "child_group": "charges",
            "parent_output_field": "meter_charges",
            "match_attrs": list(_ARCADIA_MATCH_ATTRS),
            "parent_passthrough_attrs": [],
            "unmatched_child_group": "account_charges",
        },
        0,
    )

    assert normalized["parent_passthrough_attrs"] == []


def test_derived_relationship_copies_parent_passthrough_attrs() -> None:
    """spec.md:350-352 -- the related parent's existing `passthrough_attrs`
    reaches the relationship; `_relationships_from_final_group_metadata` is the
    SDK-side derivation of that packet.
    """
    derived = prompt_utility._relationships_from_final_group_metadata(
        {
            "meters": {"passthrough_attrs": list(_ARCADIA_PARENT_PASSTHROUGH)},
            "charges": {
                "match_attrs": list(_ARCADIA_MATCH_ATTRS),
                "passthrough": {
                    "from": "meters",
                    "parent_output_field": "meter_charges",
                    "unmatched_child_group": "account_charges",
                    "multiple_match_strategy": "first_stable",
                },
            },
        }
    )

    assert len(derived) == 1
    assert derived[0]["parent_passthrough_attrs"] == _ARCADIA_PARENT_PASSTHROUGH
    assert derived[0]["multiple_match_strategy"] == "first_stable"


def test_apply_relationships_delegates_to_the_exported_primitive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """tasks.md:1356-1358 and spec.md:366-371 -- every production caller
    delegates to the same matching implementation.  The initial X-Ray
    reassembly path must call the exported primitive, not an inline index.
    """
    matcher = getattr(extract, _MATCHER_NAME, None)
    assert matcher is not None, f"groundx.extract must export {_MATCHER_NAME!r} (task 3.2a7b)"
    assert hasattr(custom_outputs, _MATCHER_NAME), (
        f"custom_outputs must resolve {_MATCHER_NAME!r} as a module global so the "
        "single-matcher delegation is observable and monkeypatchable"
    )

    calls: typing.List[typing.Mapping[str, typing.Any]] = []

    def _spy(
        parents: typing.Sequence[typing.Mapping[str, typing.Any]],
        child: typing.Mapping[str, typing.Any],
        relationship: typing.Mapping[str, typing.Any],
    ) -> typing.Any:
        calls.append(dict(child))
        return matcher(parents, child, relationship)

    monkeypatch.setattr(custom_outputs, _MATCHER_NAME, _spy)

    children = [
        {"meter_number": "12", "provider_name": "Test", "service_type": "water"},
        {"meter_number": "99", "provider_name": "Test", "service_type": "water"},
    ]
    _reassemble(
        [{"meter_number": "12", "provider_name": "Test", "service_type": "water"}],
        children,
    )

    # Per-child coverage rather than an exact call count: an implementation that
    # groups or batches children by match key is still correct as long as every
    # child's selection goes through the one exported primitive.
    assert len(calls) >= 1, "relationship placement must route through the one exported primitive"
    for child in children:
        assert any(all(seen.get(key) == value for key, value in child.items()) for seen in calls), (
            f"child {child!r} was not routed through {_MATCHER_NAME!r}"
        )


def test_reassembly_uses_declared_passthrough_fallback() -> None:
    result = _reassemble(
        [{"meter_number": "12", "provider_name": "Test", "service_type": "water"}],
        [{"meter_number": "12", "service_type": "water"}],
    )
    final = result.final_output

    assert final["meters"][0]["meter_charges"] == [{"meter_number": "12", "service_type": "water"}]
    assert final["account_charges"] == []


def test_reassembly_keeps_child_unmatched_when_ignored_field_conflicts() -> None:
    """Behavior-table rows R11/R12: a conflicting ignored field rejects the
    parent from the fallback.  Conflict state is read from the generic
    `<field>__conflicts` record sibling (design.md:408-409, tasks.md:1368-1369).
    """
    result = _reassemble(
        [
            {
                "meter_number": "12",
                "provider_name": "Test",
                "service_type": "water",
                "provider_name__conflicts": ["Other"],
            }
        ],
        [{"meter_number": "12", "provider_name": "Unknown", "service_type": "water"}],
    )
    final = result.final_output

    assert final["meters"][0]["meter_charges"] == []
    assert final["account_charges"] == [{"meter_number": "12", "provider_name": "Unknown", "service_type": "water"}]


def test_reassembly_keeps_empty_value_conflict_sibling_for_fallback_selection() -> None:
    """An empty routed value must not discard its non-empty conflict sibling.

    The sibling is the same retained conflict evidence the selector consumes
    when supplied directly, so fallback selection must reject this parent.
    """
    result = _reassemble(
        [
            {
                "meter_number": "12",
                "provider_name": "",
                "provider_name__conflicts": ["Other"],
                "service_type": "water",
            }
        ],
        [{"meter_number": "12", "provider_name": "Unknown", "service_type": "water"}],
    )
    final = result.final_output

    assert final["meters"][0]["provider_name__conflicts"] == ["Other"]
    assert final["meters"][0]["meter_charges"] == []
    assert final["account_charges"] == [{"meter_number": "12", "provider_name": "Unknown", "service_type": "water"}]


def test_reassembly_keeps_omitted_value_conflict_sibling_from_records() -> None:
    result = _reassemble(
        [
            {
                "meter_number": "12",
                "provider_name__conflicts": ["Other"],
                "service_type": "water",
            },
            {"meter_number": "99", "service_type": "water"},
        ],
        [{"meter_number": "12", "provider_name": "Unknown", "service_type": "water"}],
    )
    final = result.final_output

    assert final["meters"][0]["provider_name__conflicts"] == ["Other"]
    assert "provider_name" not in final["meters"][0]
    assert "provider_name" not in final["meters"][1]
    assert "provider_name__conflicts" not in final["meters"][1]
    assert final["meters"][0]["meter_charges"] == []
    assert final["account_charges"] == [{"meter_number": "12", "provider_name": "Unknown", "service_type": "water"}]


def test_reassembly_keeps_omitted_value_conflict_sibling_from_list_output() -> None:
    result = reassemble_custom_outputs_from_xray(
        {
            "chunks": [
                {
                    "customChunkOutputs": {
                        "meter_step": [
                            {
                                "meter_number": "12",
                                "provider_name__conflicts": ["Other"],
                                "service_type": "water",
                            },
                            {"meter_number": "99", "service_type": "water"},
                        ],
                        "charge_step": {
                            "_records": [
                                {
                                    "meter_number": "12",
                                    "provider_name": "Unknown",
                                    "service_type": "water",
                                }
                            ]
                        },
                    }
                }
            ]
        },
        workflow_extract=_workflow_extract(),
    )
    final = result.final_output

    assert final["meters"][0]["provider_name__conflicts"] == ["Other"]
    assert "provider_name" not in final["meters"][0]
    assert "provider_name" not in final["meters"][1]
    assert "provider_name__conflicts" not in final["meters"][1]
    assert final["meters"][0]["meter_charges"] == []
    assert final["account_charges"] == [{"meter_number": "12", "provider_name": "Unknown", "service_type": "water"}]


def test_reassembly_requires_a_unique_fallback_parent() -> None:
    """Behavior-table row R13: two parents sharing the stable identity are not
    a unique fallback candidate (`classes/statement.py@2797b5e:3843-3850`).
    """
    result = _reassemble(
        [
            {"meter_number": "12", "provider_name": "Test", "service_type": "water"},
            {"meter_number": "12", "provider_name": "Other", "service_type": "water"},
        ],
        [{"meter_number": "12", "provider_name": "Unknown", "service_type": "water"}],
    )
    final = result.final_output

    assert final["meters"][0]["meter_charges"] == []
    assert final["meters"][1]["meter_charges"] == []
    assert len(final["account_charges"]) == 1


def test_reassembly_without_parent_passthrough_attrs_has_no_fallback() -> None:
    """`classes/statement.py@2797b5e:3826-3827` -- with no declared parent
    passthrough attr there is no fallback pass, so the same child stays
    unmatched.  Guard against over-applying the fallback.
    """
    result = _reassemble(
        [{"meter_number": "12", "provider_name": "Test", "service_type": "water"}],
        [{"meter_number": "12", "service_type": "water"}],
        parent_passthrough_attrs=[],
    )
    final = result.final_output

    assert final["meters"][0]["meter_charges"] == []
    assert final["account_charges"] == [{"meter_number": "12", "service_type": "water"}]


@pytest.mark.parametrize(
    "rejected",
    ["first_match", "first", "last_stable", "any", "", "FIRST_STABLE", True, 1],
    ids=[
        "first_match",
        "first",
        "last_stable",
        "any",
        "empty",
        "wrong_case",
        "bool",
        "int",
    ],
)
def test_normalizer_rejects_every_other_ambiguity_value(rejected: typing.Any) -> None:
    """spec.md:348-349 and design.md:392-394 -- `first_stable` is the only
    accepted ambiguity value; "no other ambiguity value is accepted".

    Guard: the current normalizer already enforces this at
    `prompt/utility.py:1582-1588`.  Nothing pinned it, so a 3.2a7b refactor of
    that function could silently drop the check.
    """
    with pytest.raises(ValueError):
        prompt_utility._normalize_custom_relationship(
            {
                "parent_group": "meters",
                "child_group": "charges",
                "parent_output_field": "meter_charges",
                "match_attrs": list(_ARCADIA_MATCH_ATTRS),
                "parent_passthrough_attrs": list(_ARCADIA_PARENT_PASSTHROUGH),
                "unmatched_child_group": "account_charges",
                "multiple_match_strategy": rejected,
            },
            0,
        )


@pytest.mark.parametrize(
    "omitted",
    ["parent_output_field", "unmatched_child_group"],
)
def test_output_names_default_to_the_child_group_name(omitted: str) -> None:
    """design.md:384-388 -- `passthrough.parent_output_field` and
    `passthrough.unmatched_child_group` "both default to the child group name".

    The current normalizer instead *requires* `parent_output_field`
    (`prompt/utility.py:1560-1564`), so the documented default is unimplemented.
    """
    relationship = {
        "parent_group": "meters",
        "child_group": "charges",
        "parent_output_field": "meter_charges",
        "match_attrs": list(_ARCADIA_MATCH_ATTRS),
        "parent_passthrough_attrs": list(_ARCADIA_PARENT_PASSTHROUGH),
        "unmatched_child_group": "account_charges",
    }
    relationship.pop(omitted)

    normalized = prompt_utility._normalize_custom_relationship(relationship, 0)

    assert normalized[omitted] == "charges", f"design.md:384-388 -- {omitted} defaults to the child group name"


def test_reassembly_reports_ambiguity_only_per_declared_strategy() -> None:
    """Encodes behavior-table row R16 under the 2026-08-17 ruling (supersedes
    RULING 7b): an undeclared `multiple_match_strategy` defaults to
    `first_stable`, matching the legacy Arcadia matcher.  Two exact candidates
    with no declared strategy attach the child to the first parent in stable
    input order with no ambiguity diagnostic.  (Behavior-table rows R15/R16.)
    """
    meters = [
        {"meter_number": "M-1", "provider_name": "Utility", "service_type": "water"},
        {"meter_number": "m-1", "provider_name": "utility", "service_type": "WATER"},
    ]
    charge = {"meter_number": "M-1", "provider_name": "Utility", "service_type": "water"}

    undeclared = _reassemble(meters, [charge])
    assert undeclared.final_output["meters"][0]["meter_charges"] == [charge]
    assert undeclared.final_output["meters"][1]["meter_charges"] == []
    assert undeclared.final_output["account_charges"] == []
    assert undeclared.diagnostics == []

    stable = _reassemble(
        meters,
        [charge],
        relationship_overrides={"multiple_match_strategy": "first_stable"},
    )
    assert stable.final_output["meters"][0]["meter_charges"] == [charge]
    assert stable.final_output["meters"][1]["meter_charges"] == []
    assert stable.final_output.get("account_charges", []) == []
    assert stable.diagnostics == []
