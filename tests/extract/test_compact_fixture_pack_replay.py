from __future__ import annotations

import base64
import copy
import dataclasses
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from groundx.extract.custom_outputs import reassemble_custom_outputs_from_xray


def _read_blob(root: Path, reference: dict[str, Any]) -> bytes:
    digest = reference["sha256"]
    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    relative = Path(reference["blob"])
    assert relative == Path("blobs") / "sha256" / digest
    path = root / relative
    assert path.is_file() and not path.is_symlink()
    stored = path.read_bytes()
    assert reference["encoding"] == "gzip"
    assert len(stored) == reference["stored_bytes"]
    assert hashlib.sha256(stored).hexdigest() == reference["stored_sha256"]
    body = gzip.decompress(stored)
    assert len(body) == reference["bytes"]
    assert hashlib.sha256(body).hexdigest() == digest
    return body


def _artifact(case: dict[str, Any], role: str) -> dict[str, Any]:
    references = case["artifacts"].get(role, [])
    assert len(references) == 1
    return references[0]


def _workflow_extract_from_arcadia_request(
    request_packet: dict[str, Any],
) -> dict[str, Any]:
    metadata = request_packet["request"]["extraction_workflow_metadata_v1"]
    workflow = {
        "custom_steps": copy.deepcopy(metadata["custom_steps"]),
        "output_routes": copy.deepcopy(metadata["custom_output_routes"]),
    }
    output_relationships = metadata.get("output_relationships")
    if isinstance(output_relationships, list):
        workflow["output_relationships"] = copy.deepcopy(output_relationships)
    prepared_final_groups = metadata.get("prepared_final_groups")
    return {
        "workflow": workflow,
        "groups": copy.deepcopy(prepared_final_groups if isinstance(prepared_final_groups, dict) else {}),
    }


EXPECTED_OUTPUT_MEMBERS = {
    "workflow_output",
    "relationship_output",
    "final_output",
    "diagnostics",
    "source_provenance",
}


def _assert_xray_predecessor(envelope: dict[str, Any]) -> None:
    assert envelope.get("kind") == "xray_predecessor"
    source = envelope.get("source")
    assert isinstance(source, dict)
    assert source.get("source_kind") == "live_capture"
    for field in ("run_id", "process_id", "document_id"):
        assert isinstance(source.get(field), str) and source[field]
    raw = base64.b64decode(envelope["raw_xray_model_base64"], validate=True)
    assert hashlib.sha256(raw).hexdigest() == envelope["raw_xray_model_sha256"]
    assert len(raw) == envelope["raw_xray_model_bytes"]
    parsed = json.loads(raw)
    canonical = json.dumps(
        parsed, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    assert raw == canonical, "X-Ray predecessor uses an unknown serializer"
    assert parsed == envelope["value"]


def test_protected_reassembly_replays_compact_fixture_pack() -> None:
    root = Path(
        os.environ.get(
            "EXTRACTION_FIXTURE_PACK_ROOT",
            Path("tests") / "extract" / "fixtures" / "extraction-fixture-pack",
        )
    ).resolve()
    manifest = json.loads((root / "fixture-pack.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "extraction_fixture_pack_v1"
    assert manifest["state"] == "promoted"
    assert manifest["review"]["decision"] == "approved"
    assert sorted(
        case["case_id"] for case in manifest["cases"].values()
    ) == sorted(manifest["configured_set"]["case_ids"])

    for case in manifest["cases"].values():
        xray = json.loads(_read_blob(root, _artifact(case, "arcadia.xray_input")))
        _assert_xray_predecessor(xray)
        request_packet = json.loads(_read_blob(root, _artifact(case, "arcadia.request")))
        expected = json.loads(_read_blob(root, _artifact(case, "groundx_python.reassembly_output")))
        assert set(expected) == EXPECTED_OUTPUT_MEMBERS
        assert isinstance(expected["diagnostics"], list)
        assert isinstance(expected["source_provenance"], list)

        result = reassemble_custom_outputs_from_xray(
            xray["value"],
            workflow_extract=_workflow_extract_from_arcadia_request(request_packet),
        )

        assert result.workflow_output == expected["workflow_output"]
        assert result.relationship_output == expected["relationship_output"]
        assert result.final_output == expected["final_output"]
        assert [dataclasses.asdict(diagnostic) for diagnostic in result.diagnostics] == expected["diagnostics"]
        assert [
            {
                "final_path": source.final_path,
                "output_source": source.output_source,
                "page_numbers": list(source.page_numbers),
                "record_index": source.record_index,
                "workflow_field": source.workflow_field,
                "workflow_group": source.workflow_group,
            }
            for source in result.source_provenance
        ] == expected["source_provenance"]
