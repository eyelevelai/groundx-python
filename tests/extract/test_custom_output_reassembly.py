import json
import pathlib
import typing

import pytest

import groundx.extract as extract
import groundx.extract.custom_outputs as custom_outputs
from groundx.extract import prepare_extraction_yaml, reassemble_custom_outputs
from groundx.extract.custom_outputs import reassemble_custom_outputs_from_xray

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"


def _custom_output_reassembly_cases() -> list[dict]:
    fixture = FIXTURE_DIR / "custom_output_reassembly_cases.json"
    return json.loads(fixture.read_text())["cases"]


def _provenance_dicts(result) -> list[dict]:
    return [
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


def test_reassemble_custom_outputs_public_alias() -> None:
    result = reassemble_custom_outputs({}, workflow_extract={"workflow": {}})

    assert result.final_output == {}
    assert result.relationship_output is None
    assert result.diagnostics == []


def test_pure_legacy_workflow_is_not_applicable_to_custom_output_reassembly() -> None:
    result = reassemble_custom_outputs_from_xray(
        {
            "chunks": [
                {
                    "chunkKeywords": '{"statement": {"account_number": "A-123"}}',
                }
            ]
        },
        workflow_extract={
            "statement": {
                "fields": {
                    "account_number": {
                        "prompt": {
                            "instructions": "Return the account number.",
                            "type": "str",
                        }
                    }
                }
            }
        },
    )

    assert result.final_output == {}
    assert result.relationship_output is None
    assert result.workflow_output == {}
    assert result.diagnostics == []


@pytest.mark.parametrize(
    ("final_path", "kind", "step_value", "expected"),
    [
        ("/field", "instruct", {"value": "root scalar"}, {"field": "root scalar"}),
        (
            "/object/field",
            "instruct",
            {"value": "root nested"},
            {"object": {"field": "root nested"}},
        ),
        (
            "/group/object/field",
            "instruct",
            {"value": "grouped nested"},
            {"group": {"object": {"field": "grouped nested"}}},
        ),
        (
            "/group/*/object/field",
            "keys",
            {"_records": [{"value": "first"}, {"value": "second"}]},
            {
                "group": [
                    {"object": {"field": "first"}},
                    {"object": {"field": "second"}},
                ]
            },
        ),
    ],
)
def test_reassembles_complete_destination_trees_without_depth_inference(
    final_path: str,
    kind: str,
    step_value: dict,
    expected: dict,
) -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "step", "level": "chunk", "kind": kind},
            ],
            "output_routes": [
                {
                    "workflow_group": "source_group",
                    "workflow_field": "field",
                    "final_path": final_path,
                    "step_name": "step",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "value",
                }
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "step": step_value,
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == expected


def test_compiled_final_path_does_not_infer_repetition_from_observed_records() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "step", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "source_group",
                    "workflow_field": "field",
                    "final_path": "/group/object/field",
                    "step_name": "step",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "value",
                }
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "step": {"_records": [{"value": "compiled scalar"}]},
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {
        "group": {"object": {"field": "compiled scalar"}},
    }


def test_standalone_repeated_group_dedupes_by_explicit_unique_attrs() -> None:
    workflow_extract = {
        "_groundx_persisted_extract": {
            "payload": {"unique_attrs": ["item_id"]},
        },
        "workflow": {
            "custom_steps": [
                {"name": "item_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "source_records",
                    "workflow_field": field,
                    "final_path": f"/payload/items/*/{field}",
                    "step_name": "item_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": field,
                }
                for field in ("item_id", "description", "amount")
            ],
        },
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "item_rows": {
                        "_records": [
                            {"item_id": "A-1", "description": "Service"},
                            {"item_id": "a-1", "amount": 10},
                            {"item_id": "A-2", "description": "Other"},
                        ]
                    }
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.relationship_output is None
    assert result.final_output == {
        "payload": {
            "items": [
                {"item_id": "A-1", "description": "Service", "amount": 10},
                {"item_id": "A-2", "description": "Other"},
            ]
        }
    }


@pytest.mark.parametrize(
    ("first_identity", "second_identity"),
    [
        (["west", "commercial"], ["west", "commercial"]),
        (
            {"region": "west", "category": "commercial"},
            {"category": "commercial", "region": "west"},
        ),
    ],
    ids=["list", "mapping"],
)
def test_standalone_repeated_group_dedupes_structured_identity_values(
    first_identity: object,
    second_identity: object,
) -> None:
    workflow_extract = {
        "_groundx_persisted_extract": {
            "items": {"unique_attrs": ["identity"]},
        },
        "workflow": {
            "custom_steps": [
                {"name": "item_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "source_records",
                    "workflow_field": field,
                    "final_path": f"/items/*/{field}",
                    "step_name": "item_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": field,
                }
                for field in ("identity", "description", "amount")
            ],
        },
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "item_rows": {
                        "_records": [
                            {"identity": first_identity, "description": "Service"},
                            {"identity": second_identity, "amount": 10},
                        ]
                    }
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {
        "items": [
            {
                "identity": first_identity,
                "description": "Service",
                "amount": 10,
            }
        ]
    }


@pytest.mark.parametrize(
    "group_spec",
    [{}, {"unique_attrs": []}],
    ids=["missing", "empty"],
)
def test_standalone_repeated_group_without_identity_preserves_all_records(
    group_spec: dict,
) -> None:
    workflow_extract = {
        "_groundx_persisted_extract": {"payload": group_spec},
        "workflow": {
            "custom_steps": [
                {"name": "item_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "source_records",
                    "workflow_field": "item_id",
                    "final_path": "/payload/items/*/item_id",
                    "step_name": "item_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "item_id",
                }
            ],
        },
    }
    rows = [{"item_id": "A-1"}, {"item_id": "A-1"}]

    result = reassemble_custom_outputs_from_xray(
        {"chunks": [{"customChunkOutputs": {"item_rows": {"_records": rows}}}]},
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {"payload": {"items": rows}}


def test_prepared_pseudo_group_uses_final_group_identity_policy() -> None:
    prepared = prepare_extraction_yaml(
        """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: row_extraction
      level: chunk
      kind: keys

line_items:
  unique_attrs: [item_code]
  fields:
    item_code:
      prompt: {instructions: Return the item code., type: str}
    description_text:
      prompt: {instructions: Return the description., type: str}
    amount_value:
      prompt: {instructions: Return the amount., type: float}

_pseudo_groups:
  row_execution:
    workflow_step: row_extraction
    fields:
      item_code: {path: /line_items/*/item_code}
      description_text: {path: /line_items/*/description_text}
      amount_value: {path: /line_items/*/amount_value}
"""
    )
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "row_extraction": {
                        "_records": [
                            {"item_code": "A-1", "description_text": "Service"},
                            {"item_code": "a-1", "amount_value": 10},
                        ]
                    }
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=prepared.persisted_workflow_extract,
    )

    assert result.final_output == {
        "line_items": [
            {
                "item_code": "A-1",
                "description_text": "Service",
                "amount_value": 10,
            }
        ]
    }


def test_identity_normalization_preserves_large_integer_precision() -> None:
    workflow_extract = {
        "_groundx_persisted_extract": {
            "rows": {"unique_attrs": ["identity_value"]},
        },
        "workflow": {
            "custom_steps": [{"name": "row_step", "level": "chunk", "kind": "keys"}],
            "output_routes": [
                {
                    "workflow_group": "rows",
                    "workflow_field": field,
                    "final_path": f"/rows/*/{field}",
                    "step_name": "row_step",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": field,
                }
                for field in ("identity_value", "label", "detail")
            ],
        },
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "row_step": {
                        "_records": [
                            {"identity_value": 9_007_199_254_740_992, "label": "first"},
                            {"identity_value": 9_007_199_254_740_993, "label": "second"},
                            {"identity_value": 42, "label": "integer"},
                            {"identity_value": 42.0, "detail": "exact float"},
                        ]
                    }
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(xray, workflow_extract=workflow_extract)

    assert result.final_output == {
        "rows": [
            {"identity_value": 9_007_199_254_740_992, "label": "first"},
            {"identity_value": 9_007_199_254_740_993, "label": "second"},
            {"identity_value": 42, "label": "integer", "detail": "exact float"},
        ]
    }


@pytest.mark.parametrize(
    ("unique_attrs", "identity_match", "force_final_comparison"),
    [
        (
            ["fixed_identity", "threshold_identity"],
            {
                "threshold_attrs": ["threshold_identity"],
                "activate_threshold_at": 1,
                "minimum_threshold_matches": 1,
            },
            False,
        ),
        (
            ["threshold_identity"],
            {
                "threshold_attrs": ["threshold_identity"],
                "activate_threshold_at": 1,
                "minimum_threshold_matches": 1,
            },
            False,
        ),
        (
            ["threshold_identity"],
            {
                "threshold_attrs": ["threshold_identity"],
                "activate_threshold_at": 1,
                "minimum_threshold_matches": 1,
            },
            True,
        ),
    ],
    ids=["fixed-partition", "threshold-index", "final-comparison"],
)
def test_missing_exact_attrs_preserves_exact_legacy_identity(
    unique_attrs: list[str],
    identity_match: dict,
    force_final_comparison: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fields = ("fixed_identity", "threshold_identity", "first_value", "second_value")
    rows = [
        {
            "fixed_identity": "GROUP-A",
            "threshold_identity": "VALUE-A",
            "first_value": "first",
        },
        {
            "fixed_identity": "group-a",
            "threshold_identity": "value-a",
            "second_value": "second",
        },
    ]

    def reassemble(exact_attrs: typing.Optional[typing.List[str]]) -> dict:
        configured_identity_match = dict(identity_match)
        if exact_attrs is not None:
            configured_identity_match["exact_attrs"] = exact_attrs
        workflow_extract = {
            "_groundx_persisted_extract": {
                "rows": {
                    "unique_attrs": unique_attrs,
                    "identity_match": configured_identity_match,
                }
            },
            "workflow": {
                "custom_steps": [{"name": "row_step", "level": "chunk", "kind": "keys"}],
                "output_routes": [
                    {
                        "workflow_group": "rows",
                        "workflow_field": field,
                        "final_path": f"/rows/*/{field}",
                        "step_name": "row_step",
                        "level": "chunk",
                        "output_map": "customChunkOutputs",
                        "output_key": field,
                    }
                    for field in fields
                ],
            },
        }
        result = reassemble_custom_outputs_from_xray(
            {"chunks": [{"customChunkOutputs": {"row_step": {"_records": rows}}}]},
            workflow_extract=workflow_extract,
        )
        return result.final_output

    if force_final_comparison:
        monkeypatch.setattr(
            custom_outputs._AdvancedIdentityIndex,
            "_candidate_bits",
            lambda self, record: (1 << len(self.records)) - 1,
        )

    assert reassemble(None) == {"rows": rows}
    assert reassemble([]) == {
        "rows": [
            {
                "fixed_identity": "GROUP-A",
                "threshold_identity": "VALUE-A",
                "first_value": "first",
                "second_value": "second",
            }
        ]
    }


def test_advanced_identity_matching_bounds_candidate_comparisons(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    comparisons = 0
    original = custom_outputs._records_share_identity

    def counted_comparison(*args, **kwargs):
        nonlocal comparisons
        comparisons += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(custom_outputs, "_records_share_identity", counted_comparison)
    fields = ("identity_a", "identity_b", "identity_c")
    workflow_extract = {
        "_groundx_persisted_extract": {
            "rows": {
                "unique_attrs": list(fields),
                "identity_match": {
                    "threshold_attrs": list(fields),
                    "activate_threshold_at": 1,
                    "minimum_threshold_matches": 3,
                },
            }
        },
        "workflow": {
            "custom_steps": [{"name": "row_step", "level": "chunk", "kind": "keys"}],
            "output_routes": [
                {
                    "workflow_group": "rows",
                    "workflow_field": field,
                    "final_path": f"/rows/*/{field}",
                    "step_name": "row_step",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": field,
                }
                for field in fields
            ],
        },
    }
    records = [
        {"identity_a": index, "identity_b": index, "identity_c": index}
        for index in range(2_000)
    ]

    result = reassemble_custom_outputs_from_xray(
        {"chunks": [{"customChunkOutputs": {"row_step": {"_records": records}}}]},
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {"rows": records}
    assert comparisons <= 4_000


def test_renamed_parent_and_child_groups_use_declared_identity_match() -> None:
    parent_fields = (
        "entity_code",
        "period_code",
        "market_state",
        "primary_company",
        "parent_note",
        "parent_amount",
    )
    child_fields = (
        "entity_code",
        "item_code",
        "description_text",
        "amount_value",
        "source_text",
        "child_note",
        "child_detail",
    )
    workflow_extract = {
        "_groundx_persisted_extract": {
            "generic_parents": {
                "unique_attrs": [
                    "entity_code",
                    "period_code",
                    "market_state",
                    "primary_company",
                ],
                "identity_match": {
                    "threshold_attrs": ["market_state", "primary_company"],
                    "activate_threshold_at": 2,
                    "minimum_threshold_matches": 2,
                    "equal_value_shortcuts": {"market_state": ["combined"]},
                    "exact_attrs": [],
                },
            },
            "generic_children": {
                "unique_attrs": [
                    "entity_code",
                    "item_code",
                    "description_text",
                    "amount_value",
                    "source_text",
                ],
                "identity_match": {
                    "threshold_attrs": [
                        "description_text",
                        "amount_value",
                        "source_text",
                    ],
                    "activate_threshold_at": 2,
                    "minimum_threshold_matches": 3,
                    "exact_attrs": [],
                },
                "match_attrs": ["entity_code"],
            },
        },
        "workflow": {
            "custom_steps": [
                {"name": "parent_rows", "level": "chunk", "kind": "keys"},
                {"name": "child_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                *[
                    {
                        "workflow_group": "generic_parents",
                        "workflow_field": field,
                        "final_path": f"/generic_parents/*/{field}",
                        "step_name": "parent_rows",
                        "level": "chunk",
                        "output_map": "customChunkOutputs",
                        "output_key": field,
                    }
                    for field in parent_fields
                ],
                *[
                    {
                        "workflow_group": "generic_children",
                        "workflow_field": field,
                        "final_path": f"/generic_children/*/{field}",
                        "step_name": "child_rows",
                        "level": "chunk",
                        "output_map": "customChunkOutputs",
                        "output_key": field,
                    }
                    for field in child_fields
                ],
            ],
            "output_relationships": [
                {
                    "parent_group": "generic_parents",
                    "child_group": "generic_children",
                    "parent_output_field": "generic_children",
                    "match_attrs": ["entity_code"],
                    "unmatched_child_group": "generic_children",
                }
            ],
        },
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "parent_rows": {
                        "_records": [
                            {
                                "entity_code": "P-1",
                                "period_code": "Q1",
                                "market_state": "combined",
                                "primary_company": "Alpha",
                                "parent_note": "first",
                            },
                            {
                                "entity_code": "p-1",
                                "period_code": "q1",
                                "market_state": "combined",
                                "primary_company": "Beta",
                                "parent_amount": 7,
                            },
                            {
                                "entity_code": "P-2",
                                "period_code": "Q1",
                                "market_state": "open",
                                "primary_company": "Gamma",
                            },
                        ]
                    },
                    "child_rows": {
                        "_records": [
                            {
                                "entity_code": "P-1",
                                "item_code": "L-1",
                                "description_text": "Usage",
                                "amount_value": 10,
                                "source_text": "invoice",
                                "child_note": "first",
                            },
                            {
                                "entity_code": "p-1",
                                "item_code": "l-1",
                                "description_text": "usage",
                                "amount_value": 10.0,
                                "source_text": "INVOICE",
                                "child_detail": "second",
                            },
                            {
                                "entity_code": "P-2",
                                "item_code": "L-2",
                                "description_text": "Demand",
                                "amount_value": 20,
                                "source_text": "invoice",
                            },
                            {
                                "entity_code": "p-2",
                                "item_code": "l-2",
                                "description_text": "demand",
                                "amount_value": 21,
                                "source_text": "INVOICE",
                            },
                        ]
                    },
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(xray, workflow_extract=workflow_extract)

    assert result.diagnostics == []
    assert result.final_output == {
        "generic_parents": [
            {
                "entity_code": "P-1",
                "period_code": "Q1",
                "market_state": "combined",
                "primary_company": "Alpha",
                "parent_note": "first",
                "parent_amount": 7,
                "generic_children": [
                    {
                        "entity_code": "P-1",
                        "item_code": "L-1",
                        "description_text": "Usage",
                        "amount_value": 10,
                        "source_text": "invoice",
                        "child_note": "first",
                        "child_detail": "second",
                    }
                ],
            },
            {
                "entity_code": "P-2",
                "period_code": "Q1",
                "market_state": "open",
                "primary_company": "Gamma",
                "generic_children": [
                    {
                        "entity_code": "P-2",
                        "item_code": "L-2",
                        "description_text": "Demand",
                        "amount_value": 20,
                        "source_text": "invoice",
                    },
                    {
                        "entity_code": "p-2",
                        "item_code": "l-2",
                        "description_text": "demand",
                        "amount_value": 21,
                        "source_text": "INVOICE",
                    },
                ],
            },
        ],
        "generic_children": [],
    }


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            case,
            marks=(pytest.mark.pending_fixture_promotion if case["id"] != "adp-v1" else ()),
        )
        for case in _custom_output_reassembly_cases()
    ],
    ids=lambda case: case["id"],
)
def test_certification_fixture_reassembles_custom_outputs(case: dict) -> None:
    result = reassemble_custom_outputs_from_xray(
        case["xray"],
        workflow_extract=case["workflow_extract"],
    )

    expected = case["expected"]
    assert result.workflow_output == expected["workflow_output"]
    assert result.relationship_output == expected["relationship_output"]
    assert result.final_output == expected["final_output"]
    assert [diagnostic.code for diagnostic in result.diagnostics] == expected["diagnostics"]
    assert _provenance_dicts(result) == expected["source_provenance"]


def test_reassembles_records_wrapper_to_final_relationship_output() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "account_rows", "level": "chunk", "kind": "summary"},
                {"name": "transaction_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "accounts",
                    "workflow_field": "account_id",
                    "final_path": "/accounts/*/account_id",
                    "step_name": "account_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_id",
                },
                {
                    "workflow_group": "transactions",
                    "workflow_field": "account_id",
                    "final_path": "/transactions/*/account_id",
                    "step_name": "transaction_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_id",
                },
                {
                    "workflow_group": "transactions",
                    "workflow_field": "amount",
                    "final_path": "/transactions/*/amount",
                    "step_name": "transaction_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "amount",
                },
            ],
            "output_relationships": [
                {
                    "parent_group": "accounts",
                    "child_group": "transactions",
                    "parent_output_field": "transactions",
                    "match_attrs": ["account_id"],
                    "unmatched_child_group": "transactions",
                }
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "account_rows": {
                        "_records": [
                            {"account_id": "A-1"},
                            {"account_id": "A-2"},
                        ]
                    },
                    "transaction_rows": {
                        "_records": [
                            {"account_id": "a-1", "amount": 10},
                            {"account_id": "A-3", "amount": 99},
                        ]
                    },
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.diagnostics == []
    assert result.final_output == {
        "accounts": [
            {
                "account_id": "A-1",
                "transactions": [{"account_id": "a-1", "amount": 10}],
            },
            {"account_id": "A-2", "transactions": []},
        ],
        "transactions": [{"account_id": "A-3", "amount": 99}],
    }
    assert result.relationship_output == result.final_output
    assert result.workflow_output == {
        "accounts": [{"account_id": "A-1"}, {"account_id": "A-2"}],
        "transactions": [
            {"account_id": "a-1", "amount": 10},
            {"account_id": "A-3", "amount": 99},
        ],
    }


def test_relationship_places_rows_deduped_by_explicit_unique_attrs() -> None:
    workflow_extract = {
        "_groundx_persisted_extract": {
            "charges": {
                "match_attrs": ["meter_number"],
                "unique_attrs": ["description", "amount"],
            }
        },
        "workflow": {
            "custom_steps": [
                {"name": "meter_rows", "level": "chunk", "kind": "summary"},
                {"name": "charge_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "meters",
                    "workflow_field": "meter_number",
                    "final_path": "/meters/*/meter_number",
                    "step_name": "meter_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "meter_number",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "meter_number",
                    "final_path": "/charges/*/meter_number",
                    "step_name": "charge_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "meter_number",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "description",
                    "final_path": "/charges/*/description",
                    "step_name": "charge_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "description",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "amount",
                    "final_path": "/charges/*/amount",
                    "step_name": "charge_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "amount",
                },
            ],
            "output_relationships": [
                {
                    "parent_group": "meters",
                    "child_group": "charges",
                    "parent_output_field": "charges",
                    "match_attrs": ["meter_number"],
                    "unmatched_child_group": "charges",
                }
            ],
        },
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "meter_rows": {"_records": [{"meter_number": "M-1"}]},
                    "charge_rows": {
                        "_records": [
                            {
                                "meter_number": "M-1",
                                "description": "Energy",
                                "amount": 10,
                            },
                            {
                                "meter_number": "M-1",
                                "description": "Energy",
                                "amount": 10,
                            },
                            {
                                "meter_number": "M-1",
                                "description": "Demand",
                                "amount": 20,
                            },
                            {
                                "description": "Account fee",
                                "amount": 3,
                            },
                            {
                                "description": "Account fee",
                                "amount": 3,
                            },
                        ]
                    },
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.diagnostics == []
    assert result.final_output == {
        "meters": [
            {
                "meter_number": "M-1",
                "charges": [
                    {
                        "meter_number": "M-1",
                        "description": "Energy",
                        "amount": 10,
                    },
                    {
                        "meter_number": "M-1",
                        "description": "Demand",
                        "amount": 20,
                    },
                ],
            }
        ],
        "charges": [{"description": "Account fee", "amount": 3}],
    }
    assert result.relationship_output == result.final_output


def test_relationship_roles_support_the_same_declared_value_types() -> None:
    parent_group = "generic_parent_records"
    child_group = "generic_child_records"
    parent_step = "generic_parent_step"
    child_step = "generic_child_step"
    child_field = "generic_children"
    values = {
        "generic_identity": {
            "region": "north",
            "parts": [1, True, {"code": "A"}],
        },
        "generic_scalar": "source value",
        "generic_list": ["one", 2, False],
        "generic_null": None,
        "generic_number": 12.5,
        "generic_boolean": False,
        "generic_object": {"nested": {"enabled": True}},
        "generic_conflict": {
            "value": "primary",
            "confidence": 0.8,
            "conflicts": ["alternate"],
        },
        "generic_passthrough": {"source": "workflow"},
    }
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": parent_step, "level": "chunk", "kind": "summary"},
                {"name": child_step, "level": "chunk", "kind": "keys"},
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
                for group, step in (
                    (parent_group, parent_step),
                    (child_group, child_step),
                )
                for field in values
            ],
            "output_relationships": [
                {
                    "parent_group": parent_group,
                    "child_group": child_group,
                    "parent_output_field": child_field,
                    "match_attrs": ["generic_identity"],
                    "unmatched_child_group": child_group,
                }
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    parent_step: {"_records": [values]},
                    child_step: {"_records": [values]},
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    expected = {key: value for key, value in values.items() if value is not None}
    parent = result.final_output[parent_group][0]
    child = parent[child_field][0]
    assert result.diagnostics == []
    assert {
        key: value for key, value in parent.items() if key != child_field
    } == expected
    assert child == expected
    assert result.workflow_output == {
        parent_group: [expected],
        child_group: [expected],
    }
    assert json.loads(json.dumps(result.final_output)) == result.final_output


def test_relationship_match_keeps_booleans_distinct_from_numbers() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "generic_parent_step", "level": "chunk", "kind": "summary"},
                {"name": "generic_child_step", "level": "chunk", "kind": "keys"},
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
                for group, step in (
                    ("generic_parents", "generic_parent_step"),
                    ("generic_children", "generic_child_step"),
                )
                for field in ("generic_identity", "generic_label")
            ],
            "output_relationships": [
                {
                    "parent_group": "generic_parents",
                    "child_group": "generic_children",
                    "parent_output_field": "generic_children",
                    "match_attrs": ["generic_identity"],
                    "unmatched_child_group": "generic_children",
                }
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "generic_parent_step": {
                        "_records": [
                            {"generic_identity": True, "generic_label": "boolean"},
                            {"generic_identity": 1, "generic_label": "number"},
                        ]
                    },
                    "generic_child_step": {
                        "_records": [
                            {"generic_identity": True, "generic_label": "boolean"},
                            {"generic_identity": 1, "generic_label": "number"},
                        ]
                    },
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.diagnostics == []
    assert result.final_output == {
        "generic_parents": [
            {
                "generic_identity": True,
                "generic_label": "boolean",
                "generic_children": [
                    {"generic_identity": True, "generic_label": "boolean"}
                ],
            },
            {
                "generic_identity": 1,
                "generic_label": "number",
                "generic_children": [
                    {"generic_identity": 1, "generic_label": "number"}
                ],
            },
        ],
        "generic_children": [],
    }


@pytest.mark.parametrize("incomplete_value", [None, "", "   "])
def test_relationship_compares_available_match_keys(
    incomplete_value: object,
) -> None:
    fields = ("key_a", "key_b", "label")
    parent_rows = [
        {"key_a": "shared", "key_b": incomplete_value, "label": "incomplete parent"},
        {"key_a": "shared", "key_b": "COMPLETE", "label": "complete parent"},
    ]
    child_rows = [
        {"key_a": "SHARED", "key_b": incomplete_value, "label": "incomplete child"},
        {"key_a": "SHARED", "key_b": "complete", "label": "complete child"},
    ]
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "parent_step", "level": "chunk", "kind": "keys"},
                {"name": "child_step", "level": "chunk", "kind": "keys"},
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
                for group, step in (("parents", "parent_step"), ("children", "child_step"))
                for field in fields
            ],
            "output_relationships": [
                {
                    "parent_group": "parents",
                    "child_group": "children",
                    "parent_output_field": "children",
                    "match_attrs": ["key_a", "key_b"],
                    "unmatched_child_group": "children",
                }
            ],
        }
    }

    result = reassemble_custom_outputs_from_xray(
        {
            "chunks": [
                {
                    "customChunkOutputs": {
                        "parent_step": {"_records": parent_rows},
                        "child_step": {"_records": child_rows},
                    }
                }
            ]
        },
        workflow_extract=workflow_extract,
    )

    expected_incomplete_child: typing.Dict[str, object] = {
        "key_a": "SHARED",
        "label": "incomplete child",
    }
    if incomplete_value not in (None, ""):
        expected_incomplete_child["key_b"] = incomplete_value
    assert result.final_output["parents"][0]["children"] == [
        expected_incomplete_child
    ]
    assert result.final_output["parents"][1]["children"] == [
        {"key_a": "SHARED", "key_b": "complete", "label": "complete child"}
    ]
    assert result.final_output["children"] == []


def test_relationship_preserves_exact_child_rows_without_unique_attrs() -> None:
    workflow_extract = {
        "_groundx_persisted_extract": {
            "charges": {
                "match_attrs": ["meter_number"],
            }
        },
        "workflow": {
            "custom_steps": [
                {"name": "meter_rows", "level": "chunk", "kind": "summary"},
                {"name": "charge_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "meters",
                    "workflow_field": "meter_number",
                    "final_path": "/meters/*/meter_number",
                    "step_name": "meter_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "meter_number",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "meter_number",
                    "final_path": "/charges/*/meter_number",
                    "step_name": "charge_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "meter_number",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "amount",
                    "final_path": "/charges/*/amount",
                    "step_name": "charge_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "amount",
                },
            ],
            "output_relationships": [
                {
                    "parent_group": "meters",
                    "child_group": "charges",
                    "parent_output_field": "charges",
                    "match_attrs": ["meter_number"],
                    "unmatched_child_group": "charges",
                }
            ],
        },
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "meter_rows": {"_records": [{"meter_number": "M-1"}]},
                    "charge_rows": {
                        "_records": [
                            {"meter_number": "M-1", "amount": 10},
                            {"meter_number": "M-1", "amount": 10},
                            {"meter_number": "M-1", "amount": 20},
                        ]
                    },
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.diagnostics == []
    assert result.final_output == {
        "meters": [
            {
                "meter_number": "M-1",
                "charges": [
                    {"meter_number": "M-1", "amount": 10},
                    {"meter_number": "M-1", "amount": 10},
                    {"meter_number": "M-1", "amount": 20},
                ],
            }
        ],
        "charges": [],
    }
    assert result.relationship_output == result.final_output


def test_explicit_status_identity_preserves_values_and_blank_rows() -> None:
    workflow_extract = {
        "_groundx_persisted_extract": {
            "parents": {"unique_attrs": ["parent_id"]},
            "children": {
                "match_attrs": ["parent_id"],
                "unique_attrs": ["parent_id", "status"],
            },
        },
        "workflow": {
            "custom_steps": [
                {"name": "parent_rows", "level": "chunk", "kind": "keys"},
                {"name": "child_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "parents",
                    "workflow_field": "parent_id",
                    "final_path": "/parents/*/parent_id",
                    "step_name": "parent_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "parent_id",
                },
                {
                    "workflow_group": "children",
                    "workflow_field": "parent_id",
                    "final_path": "/children/*/parent_id",
                    "step_name": "child_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "parent_id",
                },
                {
                    "workflow_group": "children",
                    "workflow_field": "status",
                    "final_path": "/children/*/status",
                    "step_name": "child_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "status",
                },
            ],
            "output_relationships": [
                {
                    "parent_group": "parents",
                    "child_group": "children",
                    "parent_output_field": "children",
                    "match_attrs": ["parent_id"],
                    "unmatched_child_group": "children",
                }
            ],
        },
    }
    child_rows = [
        {"parent_id": "P-1", "status": "supply"},
        {"parent_id": "P-1", "status": "supply"},
        {"parent_id": "P-1", "status": "delivery"},
        {"parent_id": "P-1", "status": "full_service"},
        {"parent_id": "P-1", "status": " "},
        {"parent_id": "P-1", "status": " "},
        {"parent_id": "P-1"},
        {"parent_id": "P-1"},
    ]
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "parent_rows": {"_records": [{"parent_id": "P-1"}]},
                    "child_rows": {"_records": child_rows},
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.diagnostics == []
    assert result.final_output == {
        "parents": [
            {
                "parent_id": "P-1",
                "children": [
                    {"parent_id": "P-1", "status": "supply"},
                    {"parent_id": "P-1", "status": "delivery"},
                    {"parent_id": "P-1", "status": "full_service"},
                    {"parent_id": "P-1", "status": " "},
                    {"parent_id": "P-1", "status": " "},
                    {"parent_id": "P-1"},
                    {"parent_id": "P-1"},
                ],
            }
        ],
        "children": [],
    }


def test_chained_relationships_are_order_independent() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "account_rows", "level": "chunk", "kind": "keys"},
                {"name": "charge_rows", "level": "chunk", "kind": "keys"},
                {"name": "tax_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "accounts",
                    "workflow_field": "account_id",
                    "final_path": "/accounts/*/account_id",
                    "step_name": "account_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_id",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "account_id",
                    "final_path": "/charges/*/account_id",
                    "step_name": "charge_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_id",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "charge_id",
                    "final_path": "/charges/*/charge_id",
                    "step_name": "charge_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "charge_id",
                },
                {
                    "workflow_group": "taxes",
                    "workflow_field": "charge_id",
                    "final_path": "/taxes/*/charge_id",
                    "step_name": "tax_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "charge_id",
                },
                {
                    "workflow_group": "taxes",
                    "workflow_field": "tax_amount",
                    "final_path": "/taxes/*/tax_amount",
                    "step_name": "tax_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "tax_amount",
                },
            ],
            "output_relationships": [
                {
                    "parent_group": "accounts",
                    "child_group": "charges",
                    "parent_output_field": "charges",
                    "match_attrs": ["account_id"],
                    "unmatched_child_group": "charges",
                },
                {
                    "parent_group": "charges",
                    "child_group": "taxes",
                    "parent_output_field": "taxes",
                    "match_attrs": ["charge_id"],
                    "unmatched_child_group": "taxes",
                },
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "account_rows": {"_records": [{"account_id": "A-1"}]},
                    "charge_rows": {"_records": [{"account_id": "A-1", "charge_id": "C-1"}]},
                    "tax_rows": {"_records": [{"charge_id": "C-1", "tax_amount": "1.23"}]},
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.diagnostics == []
    assert result.final_output == {
        "accounts": [
            {
                "account_id": "A-1",
                "charges": [
                    {
                        "account_id": "A-1",
                        "charge_id": "C-1",
                        "taxes": [{"charge_id": "C-1", "tax_amount": "1.23"}],
                    }
                ],
            }
        ],
        "charges": [],
        "taxes": [],
    }
    assert result.relationship_output == {
        "accounts": [
            {
                "account_id": "A-1",
                "charges": [
                    {
                        "account_id": "A-1",
                        "charge_id": "C-1",
                        "taxes": [{"charge_id": "C-1", "tax_amount": "1.23"}],
                    }
                ],
            }
        ],
        "charges": [],
        "taxes": [],
    }


def test_exposes_workflow_output_before_final_routing() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "employer_fields", "level": "chunk", "kind": "instruct"},
            ],
            "output_routes": [
                {
                    "workflow_group": "adp_f1_employer_information",
                    "workflow_field": "f001_employer_name",
                    "final_path": "/employer_information/employer_name",
                    "step_name": "employer_fields",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "employer_name",
                },
            ],
        }
    }
    xray = {"chunks": [{"customChunkOutputs": {"employer_fields": {"employer_name": "Acme Inc."}}}]}

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {"employer_information": {"employer_name": "Acme Inc."}}
    assert result.workflow_output == {"adp_f1_employer_information": {"f001_employer_name": "Acme Inc."}}


def test_reads_sdk_typed_snake_case_custom_output_maps() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "statement_fields", "level": "chunk", "kind": "instruct"},
            ],
            "output_routes": [
                {
                    "workflow_group": "statement",
                    "workflow_field": "account_number",
                    "final_path": "/statement/account_number",
                    "step_name": "statement_fields",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_number",
                },
            ],
        }
    }
    xray = {
        "chunks": [
            {
                # SDK DocumentXray objects dump aliases as snake_case.
                "custom_chunk_outputs": {"statement_fields": {"account_number": "A-123"}},
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.diagnostics == []
    assert result.final_output == {"statement": {"account_number": "A-123"}}
    assert result.workflow_output == {"statement": {"account_number": "A-123"}}


def test_missing_relationship_list_groups_are_empty_lists() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "statement_fields", "level": "chunk", "kind": "instruct"},
                {"name": "meter_fields", "level": "chunk", "kind": "summary"},
                {"name": "charge_fields", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "statement",
                    "workflow_field": "account_number",
                    "final_path": "/statement/account_number",
                    "step_name": "statement_fields",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_number",
                },
                {
                    "workflow_group": "meters",
                    "workflow_field": "meter_number",
                    "final_path": "/meters/*/meter_number",
                    "step_name": "meter_fields",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "meter_number",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "charge_amount",
                    "final_path": "/charges/*/charge_amount",
                    "step_name": "charge_fields",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "charge_amount",
                },
            ],
            "output_relationships": [
                {
                    "parent_group": "meters",
                    "child_group": "charges",
                    "parent_output_field": "charges",
                    "match_attrs": ["meter_number"],
                    "unmatched_child_group": "charges",
                }
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "statement_fields": {"account_number": "A-123"},
                    "meter_fields": {"meter_number": ""},
                    "charge_fields": {"charge_amount": ""},
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.diagnostics == []
    assert result.final_output == {
        "statement": {"account_number": "A-123"},
        "meters": [],
        "charges": [],
    }
    assert result.relationship_output == result.final_output


def test_utility_routes_without_relationships_emit_diagnostic() -> None:
    workflow_extract = {
        "_groundx_persisted_extract": {
            "charges": {
                "match_attrs": ["meter_number"],
                "passthrough": {"from": "meters"},
            },
            "meters": {"fields": {"meter_number": {}}},
        },
        "workflow": {
            "custom_steps": [
                {"name": "meter_fields", "level": "chunk", "kind": "summary"},
                {"name": "charge_fields", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "meters",
                    "workflow_field": "meter_number",
                    "final_path": "/meters/*/meter_number",
                    "step_name": "meter_fields",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "meter_number",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "meter_number",
                    "final_path": "/charges/*/meter_number",
                    "step_name": "charge_fields",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "meter_number",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "charge_amount",
                    "final_path": "/charges/*/charge_amount",
                    "step_name": "charge_fields",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "charge_amount",
                },
            ],
        },
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "meter_fields": {"_records": [{"meter_number": "M-1"}]},
                    "charge_fields": {"_records": [{"meter_number": "M-1", "charge_amount": "12.34"}]},
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.relationship_output is None
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["missing_output_relationships"]
    assert result.diagnostics[0].workflow_group == "charges"


def test_records_wrapper_preserves_direct_outputs_next_to_records() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "mixed_outputs", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "statement",
                    "workflow_field": "account_number",
                    "final_path": "/statement/account_number",
                    "step_name": "mixed_outputs",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_number",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "description",
                    "final_path": "/charges/*/description",
                    "step_name": "mixed_outputs",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "description",
                },
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "mixed_outputs": {
                        "account_number": "A-123",
                        "_records": [{"description": "Admin fee"}],
                    }
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {
        "statement": {"account_number": "A-123"},
        "charges": [{"description": "Admin fee"}],
    }


def test_section_outputs_copied_to_multiple_chunks_are_processed_once() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "section_rows", "level": "section", "kind": "summary"},
            ],
            "output_routes": [
                {
                    "workflow_group": "sections",
                    "workflow_field": "section_id",
                    "final_path": "/sections/*/section_id",
                    "step_name": "section_rows",
                    "level": "section",
                    "output_map": "customSectionOutputs",
                    "output_key": "section_id",
                },
                {
                    "workflow_group": "sections",
                    "workflow_field": "total",
                    "final_path": "/sections/*/total",
                    "step_name": "section_rows",
                    "level": "section",
                    "output_map": "customSectionOutputs",
                    "output_key": "total",
                },
            ],
        }
    }
    copied_section_outputs = {
        "section_rows": {
            "_records": [
                {"section_id": "S-1", "total": 10},
            ]
        }
    }
    xray = {
        "chunks": [
            {
                "chunkId": "chunk-1",
                "customSectionOutputs": copied_section_outputs,
            },
            {
                "chunkId": "chunk-2",
                "customSectionOutputs": copied_section_outputs,
            },
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {
        "sections": [{"section_id": "S-1", "total": 10}],
    }


def test_document_outputs_copied_to_chunks_are_processed_once() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "document_rows", "level": "document", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "documents",
                    "workflow_field": "document_id",
                    "final_path": "/documents/*/document_id",
                    "step_name": "document_rows",
                    "level": "document",
                    "output_map": "customDocumentOutputs",
                    "output_key": "document_id",
                },
            ],
        }
    }
    copied_document_outputs = {
        "document_rows": {
            "_records": [
                {"document_id": "D-1"},
            ]
        }
    }
    xray = {
        "chunks": [
            {
                "chunkId": "chunk-1",
                "pageNumbers": [1],
                "customDocumentOutputs": copied_document_outputs,
            },
            {
                "chunkId": "chunk-2",
                "pageNumbers": [2],
                "customDocumentOutputs": copied_document_outputs,
            },
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {
        "documents": [{"document_id": "D-1"}],
    }
    assert [provenance.page_numbers for provenance in result.source_provenance] == [()]


def test_identical_section_payloads_on_different_pages_are_not_collapsed() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "section_rows", "level": "section", "kind": "summary"},
            ],
            "output_routes": [
                {
                    "workflow_group": "sections",
                    "workflow_field": "section_type",
                    "final_path": "/sections/*/section_type",
                    "step_name": "section_rows",
                    "level": "section",
                    "output_map": "customSectionOutputs",
                    "output_key": "section_type",
                },
            ],
        }
    }
    section_outputs = {
        "section_rows": {
            "_records": [
                {"section_type": "charge_summary"},
            ]
        }
    }
    xray = {
        "chunks": [
            {
                "chunkId": "chunk-1",
                "pageNumbers": [1],
                "customSectionOutputs": section_outputs,
            },
            {
                "chunkId": "chunk-2",
                "pageNumbers": [2],
                "customSectionOutputs": section_outputs,
            },
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {
        "sections": [
            {"section_type": "charge_summary"},
            {"section_type": "charge_summary"},
        ],
    }
    assert [provenance.page_numbers for provenance in result.source_provenance] == [(1,), (2,)]


def test_reassembly_reports_source_provenance_for_routed_outputs() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "statement_labels", "level": "chunk", "kind": "instruct"},
                {"name": "charge_lines", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "statement_identity",
                    "workflow_field": "acct",
                    "final_path": "/statement/account_number",
                    "step_name": "statement_labels",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_number_label",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "amount",
                    "final_path": "/charges/amount",
                    "step_name": "charge_lines",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "amount",
                },
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "chunkId": "chunk-1",
                "pageNumbers": [2],
                "customChunkOutputs": {
                    "statement_labels": {"account_number_label": "A-123"},
                    "charge_lines": {
                        "_records": [
                            {"amount": 10},
                            {"amount": 4},
                        ]
                    },
                },
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert [provenance.__dict__ for provenance in result.source_provenance] == [
        {
            "output_source": "customChunkOutputs",
            "workflow_group": "statement_identity",
            "workflow_field": "acct",
            "final_path": "/statement/account_number",
            "record_index": None,
            "page_numbers": (2,),
        },
        {
            "output_source": "customChunkOutputs",
            "workflow_group": "charges",
            "workflow_field": "amount",
            "final_path": "/charges/amount",
            "record_index": 0,
            "page_numbers": (2,),
        },
        {
            "output_source": "customChunkOutputs",
            "workflow_group": "charges",
            "workflow_field": "amount",
            "final_path": "/charges/amount",
            "record_index": 1,
            "page_numbers": (2,),
        },
    ]


def test_adp_scalar_reducer_prefers_source_backed_positive_over_later_default() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {
                    "name": "adp_f2_eligibility_requirements",
                    "level": "section",
                    "kind": "instruct",
                },
            ],
            "output_routes": [
                {
                    "workflow_group": "adp_f2_eligibility_requirements",
                    "workflow_field": "predecessor_service",
                    "final_path": "/eligibility_requirements/predecessor_service",
                    "step_name": "adp_f2_eligibility_requirements",
                    "level": "section",
                    "output_map": "customSectionOutputs",
                    "output_key": "predecessor_service",
                },
                {
                    "workflow_group": "adp_f2_eligibility_requirements",
                    "workflow_field": "entry_date",
                    "final_path": "/eligibility_requirements/entry_date",
                    "step_name": "adp_f2_eligibility_requirements",
                    "level": "section",
                    "output_map": "customSectionOutputs",
                    "output_key": "entry_date",
                },
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "chunkId": "source-backed",
                "pageNumbers": [12],
                "customSectionOutputs": {
                    "adp_f2_eligibility_requirements": {
                        "predecessor_service": "Service with predecessor employer counts",
                        "entry_date": "2026-01-01",
                    }
                },
            },
            {
                "chunkId": "irrelevant-default",
                "pageNumbers": [99],
                "customSectionOutputs": {
                    "adp_f2_eligibility_requirements": {
                        "predecessor_service": "Not specified",
                        "entry_date": "2026-02-01",
                    }
                },
            },
            {
                "chunkId": "irrelevant-not-indicated",
                "pageNumbers": [100],
                "customSectionOutputs": {
                    "adp_f2_eligibility_requirements": {
                        "predecessor_service": {
                            "value": "Not Indicated",
                            "_raw_text": "No predecessor-service section visible.",
                        },
                    }
                },
            },
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {
        "eligibility_requirements": {
            "predecessor_service": "Service with predecessor employer counts",
            "entry_date": "2026-01-01",
        }
    }
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["conflicting_output_candidates"]
    assert result.diagnostics[0].severity == "warning"
    assert result.diagnostics[0].final_path == "/eligibility_requirements/entry_date"


def test_scalar_candidate_sidecar_preserves_equal_quality_conflicts_and_pages() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "eligibility", "level": "section", "kind": "instruct"},
            ],
            "output_routes": [
                {
                    "workflow_group": "eligibility_requirements",
                    "workflow_field": "entry_date",
                    "final_path": "/eligibility_requirements/entry_date",
                    "step_name": "eligibility",
                    "level": "section",
                    "output_map": "customSectionOutputs",
                    "output_key": "entry_date",
                },
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "chunkId": "first",
                "pageNumbers": [12, 12],
                "customSectionOutputs": {"eligibility": {"entry_date": "January 1"}},
            },
            {
                "chunkId": "duplicate",
                "pageNumbers": [14, 12],
                "customSectionOutputs": {"eligibility": {"entry_date": " january   1 "}},
            },
            {
                "chunkId": "conflict",
                "pageNumbers": [9],
                "customSectionOutputs": {"eligibility": {"entry_date": "April 8"}},
            },
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {"eligibility_requirements": {"entry_date": "January 1"}}
    assert len(result.scalar_candidate_sets) == 1
    candidate_set = result.scalar_candidate_sets[0]
    assert candidate_set.output_source == "customSectionOutputs"
    assert candidate_set.workflow_group == "eligibility_requirements"
    assert candidate_set.workflow_field == "entry_date"
    assert candidate_set.final_path == "/eligibility_requirements/entry_date"
    assert candidate_set.selected.value == "January 1"
    assert candidate_set.selected.page_numbers == (12, 14)
    assert [(candidate.value, candidate.page_numbers) for candidate in candidate_set.alternatives] == [
        ("April 8", (9,)),
    ]


def test_scalar_candidate_sidecar_clears_inferior_candidates_after_replacement() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {"name": "eligibility", "level": "section", "kind": "instruct"},
            ],
            "output_routes": [
                {
                    "workflow_group": "eligibility_requirements",
                    "workflow_field": "entry_date",
                    "final_path": "/eligibility_requirements/entry_date",
                    "step_name": "eligibility",
                    "level": "section",
                    "output_map": "customSectionOutputs",
                    "output_key": "entry_date",
                },
            ],
        }
    }
    xray = {
        "chunks": [
            {
                "chunkId": "low-confidence-selected",
                "pageNumbers": [1],
                "customSectionOutputs": {
                    "eligibility": {"entry_date": {"value": "January 1", "confidence": 0.4}}
                },
            },
            {
                "chunkId": "low-confidence-conflict",
                "pageNumbers": [2],
                "customSectionOutputs": {
                    "eligibility": {"entry_date": {"value": "April 8", "confidence": 0.4}}
                },
            },
            {
                "chunkId": "high-confidence-selected",
                "pageNumbers": [3],
                "customSectionOutputs": {
                    "eligibility": {"entry_date": {"value": "July 1", "confidence": 0.9}}
                },
            },
            {
                "chunkId": "high-confidence-conflict",
                "pageNumbers": [4],
                "customSectionOutputs": {
                    "eligibility": {"entry_date": {"value": "October 1", "confidence": 0.9}}
                },
            },
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    candidate_set = result.scalar_candidate_sets[0]
    assert candidate_set.selected.value == {"value": "July 1", "confidence": 0.9}
    assert candidate_set.selected.page_numbers == (3,)
    assert [(candidate.value, candidate.page_numbers) for candidate in candidate_set.alternatives] == [
        ({"value": "October 1", "confidence": 0.9}, (4,)),
    ]
    assert result.final_output == {
        "eligibility_requirements": {
            "entry_date": {"value": "July 1", "confidence": 0.9},
        }
    }


def test_scalar_candidate_sidecar_types_are_public_exports() -> None:
    assert "CustomOutputScalarCandidate" in extract.__all__
    assert "CustomOutputScalarCandidateSet" in extract.__all__
    assert (
        extract.CustomOutputScalarCandidate
        is custom_outputs.CustomOutputScalarCandidate
    )
    assert (
        extract.CustomOutputScalarCandidateSet
        is custom_outputs.CustomOutputScalarCandidateSet
    )


def test_non_repeated_section_list_value_remains_scalar_field() -> None:
    workflow_extract = {
        "workflow": {
            "custom_steps": [
                {
                    "name": "adp_f3_vesting_compensation",
                    "level": "section",
                    "kind": "instruct",
                },
            ],
            "output_routes": [
                {
                    "workflow_group": "adp_f3_vesting_compensation",
                    "workflow_field": "compensation_definition",
                    "final_path": "/compensation/compensation_definition",
                    "step_name": "adp_f3_vesting_compensation",
                    "level": "section",
                    "output_map": "customSectionOutputs",
                    "output_key": "compensation_definition",
                },
                {
                    "workflow_group": "adp_f3_vesting_compensation",
                    "workflow_field": "compensation_excluded_all",
                    "final_path": "/compensation/compensation_excluded_all",
                    "step_name": "adp_f3_vesting_compensation",
                    "level": "section",
                    "output_map": "customSectionOutputs",
                    "output_key": "compensation_excluded_all",
                },
            ],
        }
    }
    excluded_all = [
        {
            "value": "N/A",
            "_raw_text": "No selected exclusion shown in the compensation section.",
        }
    ]
    xray = {
        "chunks": [
            {
                "chunkId": "compensation-page",
                "pageNumbers": [9],
                "customSectionOutputs": {
                    "adp_f3_vesting_compensation": {
                        "compensation_definition": {
                            "value": "W2 Compensation",
                            "_raw_text": "Selected compensation definition.",
                        },
                        "compensation_excluded_all": excluded_all,
                    }
                },
            },
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {
        "compensation": {
            "compensation_definition": {
                "value": "W2 Compensation",
                "_raw_text": "Selected compensation definition.",
            },
            "compensation_excluded_all": excluded_all,
        }
    }
    assert result.workflow_output["adp_f3_vesting_compensation"]["compensation_excluded_all"] == excluded_all
    assert [
        provenance.record_index
        for provenance in result.source_provenance
        if provenance.workflow_field == "compensation_excluded_all"
    ] == [None]


def test_duplicate_parents_without_unique_attrs_are_not_collapsed() -> None:
    workflow_extract = {
        "_groundx_persisted_extract": {
            "accounts": {},
            "transactions": {},
        },
        "workflow": {
            "custom_steps": [
                {"name": "account_rows", "level": "chunk", "kind": "keys"},
                {"name": "transaction_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                {
                    "workflow_group": "accounts",
                    "workflow_field": "account_id",
                    "final_path": "/accounts/*/account_id",
                    "step_name": "account_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_id",
                },
                {
                    "workflow_group": "transactions",
                    "workflow_field": "account_id",
                    "final_path": "/transactions/*/account_id",
                    "step_name": "transaction_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_id",
                },
                {
                    "workflow_group": "transactions",
                    "workflow_field": "amount",
                    "final_path": "/transactions/*/amount",
                    "step_name": "transaction_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "amount",
                },
            ],
            "output_relationships": [
                {
                    "parent_group": "accounts",
                    "child_group": "transactions",
                    "parent_output_field": "transactions",
                    "match_attrs": ["account_id"],
                    "unmatched_child_group": "transactions",
                }
            ],
        },
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "account_rows": {
                        "_records": [
                            {"account_id": "A-1"},
                            {"account_id": "A-1"},
                        ]
                    },
                    "transaction_rows": {"_records": [{"account_id": "a-1", "amount": 10}]},
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(xray, workflow_extract=workflow_extract)

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["ambiguous_relationship_match"]
    assert result.final_output == {
        "accounts": [
            {
                "account_id": "A-1",
                "transactions": [],
            },
            {
                "account_id": "A-1",
                "transactions": [],
            },
        ],
        "transactions": [{"account_id": "a-1", "amount": 10}],
    }


def test_compiled_relationship_can_attach_ambiguous_child_to_first_parent() -> None:
    identity_attrs = (
        "record_key",
        "period_start",
        "period_end",
        "category",
        "market_state",
        "alternate_account",
        "alternate_provider",
        "primary_provider",
    )
    workflow_extract = {
        "_groundx_persisted_extract": {
            "parents": {
                "unique_attrs": list(identity_attrs),
                "identity_match": {
                    "threshold_attrs": [
                        "market_state",
                        "alternate_account",
                        "alternate_provider",
                        "primary_provider",
                    ],
                    "activate_threshold_at": 2,
                    "minimum_threshold_matches": 3,
                    "group_attrs": ["record_key", "category", "market_state"],
                    "sort_attrs": ["record_key"],
                    "equal_value_shortcuts": {"market_state": ["combined"]},
                    "exact_attrs": list(identity_attrs),
                },
            },
            "children": {},
        },
        "workflow": {
            "custom_steps": [
                {"name": "parent_rows", "level": "chunk", "kind": "keys"},
                {"name": "child_rows", "level": "chunk", "kind": "keys"},
            ],
            "output_routes": [
                *[
                    {
                        "workflow_group": "parents",
                        "workflow_field": field,
                        "final_path": f"/parents/*/{field}",
                        "step_name": "parent_rows",
                        "level": "chunk",
                        "output_map": "customChunkOutputs",
                        "output_key": field,
                    }
                    for field in (*identity_attrs, "label")
                ],
                *[
                    {
                        "workflow_group": "children",
                        "workflow_field": field,
                        "final_path": f"/children/*/{field}",
                        "step_name": "child_rows",
                        "level": "chunk",
                        "output_map": "customChunkOutputs",
                        "output_key": field,
                    }
                    for field in ("record_key", "category", "primary_provider", "value")
                ],
            ],
            "output_relationships": [
                {
                    "parent_group": "parents",
                    "child_group": "children",
                    "parent_output_field": "children",
                    "match_attrs": ["record_key", "category", "primary_provider"],
                    "unmatched_child_group": "children",
                    "multiple_match_strategy": "first_stable",
                }
            ],
        },
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "parent_rows": {
                        "_records": [
                            {
                                "record_key": "P-1",
                                "period_start": "2026-01-01",
                                "period_end": "2026-01-31",
                                "category": "primary",
                                "market_state": "combined",
                                "alternate_account": "A-1",
                                "alternate_provider": "Provider A",
                                "primary_provider": "Provider B",
                                "label": "first",
                            },
                            {
                                "record_key": "p-1",
                                "period_start": "2026-01-01",
                                "period_end": "2026-01-31",
                                "category": "primary",
                                "market_state": "combined",
                                "alternate_account": "A-1",
                                "alternate_provider": "Provider A",
                                "primary_provider": "Provider B",
                                "label": "second",
                            },
                        ]
                    },
                    "child_rows": {
                        "_records": [
                            {
                                "record_key": "P-1",
                                "category": "PRIMARY",
                                "primary_provider": "provider b",
                                "value": 42,
                            }
                        ]
                    },
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.diagnostics == []
    assert result.final_output == {
        "parents": [
            {
                "record_key": "P-1",
                "period_start": "2026-01-01",
                "period_end": "2026-01-31",
                "category": "primary",
                "market_state": "combined",
                "alternate_account": "A-1",
                "alternate_provider": "Provider A",
                "primary_provider": "Provider B",
                "label": "first",
                "children": [
                    {
                        "record_key": "P-1",
                        "category": "PRIMARY",
                        "primary_provider": "provider b",
                        "value": 42,
                    }
                ],
            },
            {
                "record_key": "p-1",
                "period_start": "2026-01-01",
                "period_end": "2026-01-31",
                "category": "primary",
                "market_state": "combined",
                "alternate_account": "A-1",
                "alternate_provider": "Provider A",
                "primary_provider": "Provider B",
                "label": "second",
                "children": [],
            },
        ],
        "children": [],
    }


@pytest.mark.parametrize(
    "multiple_match_strategy",
    ["first_stable", None],
    ids=["first-stable", "strict-ambiguity"],
)
def test_relationship_matching_at_scale_follows_declared_strategy(
    multiple_match_strategy: str | None,
) -> None:
    """Large parent/child sets follow only the declared ambiguity strategy.

    This test previously monkeypatched the `_match_key` index helper and
    bounded its call count to O(parents + children).  Task 3.2a7b replaced
    that index with the exported `select_relationship_parent` primitive,
    whose per-child parent scan is legacy-faithful (the legacy matcher scans
    every meter per charge, `internal-arcadia classes/statement.py@2797b5e:
    3803-3817`), so `_match_key` was deleted and the key-computation bound
    with it; no comparable budget exists on the primitive path to re-point
    the guard at.  The behavioral half of the original test is retained:
    at scale, multiple exact candidates follow a declared `first_stable`
    strategy, and with no declared strategy every such child is reported
    ambiguous and stays unmatched.
    """
    relationship = {
        "parent_group": "parents",
        "child_group": "children",
        "parent_output_field": "children",
        "match_attrs": ["record_key"],
        "unmatched_child_group": "children",
    }
    if multiple_match_strategy is not None:
        relationship["multiple_match_strategy"] = multiple_match_strategy
    workflow_extract = {
        "_groundx_persisted_extract": {"parents": {}, "children": {}},
        "workflow": {
            "custom_steps": [
                {"name": "parent_rows", "level": "chunk", "kind": "keys"},
                {"name": "child_rows", "level": "chunk", "kind": "keys"},
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
                for group, step, fields in (
                    ("parents", "parent_rows", ("record_key", "label")),
                    ("children", "child_rows", ("record_key", "value")),
                )
                for field in fields
            ],
            "output_relationships": [relationship],
        },
    }
    record_count = 300
    parents = [
        {"record_key": key, "label": label}
        for index in range(record_count)
        for key, label in ((f"P-{index}", "first"), (f"p-{index}", "second"))
    ]
    children = [{"record_key": f"P-{index}", "value": index} for index in range(record_count)]

    result = reassemble_custom_outputs_from_xray(
        {
            "chunks": [
                {
                    "customChunkOutputs": {
                        "parent_rows": {"_records": parents},
                        "child_rows": {"_records": children},
                    }
                }
            ]
        },
        workflow_extract=workflow_extract,
    )

    if multiple_match_strategy == "first_stable":
        assert result.diagnostics == []
        assert result.final_output["parents"][0]["children"] == [children[0]]
        assert result.final_output["parents"][1]["children"] == []
        assert result.final_output["children"] == []
    else:
        assert len(result.diagnostics) == record_count
        assert all(diagnostic.code == "ambiguous_relationship_match" for diagnostic in result.diagnostics)
        assert result.final_output["children"] == children


def test_indexed_relationship_matching_preserves_structured_keys() -> None:
    workflow_extract = {
        "_groundx_persisted_extract": {"parents": {}, "children": {}},
        "workflow": {
            "custom_steps": [
                {"name": "parent_rows", "level": "chunk", "kind": "keys"},
                {"name": "child_rows", "level": "chunk", "kind": "keys"},
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
                for group, step, fields in (
                    ("parents", "parent_rows", ("record_key", "label")),
                    ("children", "child_rows", ("record_key", "value")),
                )
                for field in fields
            ],
            "output_relationships": [
                {
                    "parent_group": "parents",
                    "child_group": "children",
                    "parent_output_field": "children",
                    "match_attrs": ["record_key"],
                    "unmatched_child_group": "children",
                }
            ],
        },
    }
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "parent_rows": {
                        "_records": [
                            {
                                "record_key": {"region": "west", "codes": ["A", "B"]},
                                "label": "first",
                            }
                        ]
                    },
                    "child_rows": {
                        "_records": [
                            {
                                "record_key": {"codes": ["A", "B"], "region": "west"},
                                "value": 42,
                            }
                        ]
                    },
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.diagnostics == []
    assert result.final_output["parents"][0]["children"] == [
        {
            "record_key": {"codes": ["A", "B"], "region": "west"},
            "value": 42,
        }
    ]
    assert result.final_output["children"] == []
