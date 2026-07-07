from groundx.extract import reassemble_custom_outputs
from groundx.extract.custom_outputs import reassemble_custom_outputs_from_xray


def test_reassemble_custom_outputs_public_alias() -> None:
    result = reassemble_custom_outputs({}, workflow_extract={"workflow": {}})

    assert result.final_output == {}
    assert result.relationship_output is None
    assert result.diagnostics == []


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
                    "final_path": "/accounts/account_id",
                    "step_name": "account_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_id",
                },
                {
                    "workflow_group": "transactions",
                    "workflow_field": "account_id",
                    "final_path": "/transactions/account_id",
                    "step_name": "transaction_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_id",
                },
                {
                    "workflow_group": "transactions",
                    "workflow_field": "amount",
                    "final_path": "/transactions/amount",
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
                    "final_path": "/accounts/account_id",
                    "step_name": "account_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_id",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "account_id",
                    "final_path": "/charges/account_id",
                    "step_name": "charge_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "account_id",
                },
                {
                    "workflow_group": "charges",
                    "workflow_field": "charge_id",
                    "final_path": "/charges/charge_id",
                    "step_name": "charge_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "charge_id",
                },
                {
                    "workflow_group": "taxes",
                    "workflow_field": "charge_id",
                    "final_path": "/taxes/charge_id",
                    "step_name": "tax_rows",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "charge_id",
                },
                {
                    "workflow_group": "taxes",
                    "workflow_field": "tax_amount",
                    "final_path": "/taxes/tax_amount",
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
                    "charge_rows": {
                        "_records": [{"account_id": "A-1", "charge_id": "C-1"}]
                    },
                    "tax_rows": {
                        "_records": [{"charge_id": "C-1", "tax_amount": "1.23"}]
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
    xray = {
        "chunks": [
            {
                "customChunkOutputs": {
                    "employer_fields": {"employer_name": "Acme Inc."}
                }
            }
        ]
    }

    result = reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )

    assert result.final_output == {
        "employer_information": {"employer_name": "Acme Inc."}
    }
    assert result.workflow_output == {
        "adp_f1_employer_information": {"f001_employer_name": "Acme Inc."}
    }


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
                    "final_path": "/charges/description",
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
                    "final_path": "/sections/section_id",
                    "step_name": "section_rows",
                    "level": "section",
                    "output_map": "customSectionOutputs",
                    "output_key": "section_id",
                },
                {
                    "workflow_group": "sections",
                    "workflow_field": "total",
                    "final_path": "/sections/total",
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
                    "final_path": "/documents/document_id",
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
    assert [
        provenance.page_numbers
        for provenance in result.source_provenance
    ] == [()]


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
                    "final_path": "/sections/section_type",
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
    assert [
        provenance.page_numbers
        for provenance in result.source_provenance
    ] == [(1,), (2,)]


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
