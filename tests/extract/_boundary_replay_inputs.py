import base64
import hashlib
import json
from pathlib import Path
from typing import Any


def replay_inputs_are_locally_coherent(
    *,
    surface: str,
    input_root: Path,
    goldens_root: Path,
) -> bool:
    handoff_path = input_root / surface / "internal_arcadia_download_workflow_load.handoff.json"
    xray_path = input_root / surface / "internal_arcadia_agent_load_xray.xray.json"
    expected_path = goldens_root / surface / "groundx_python_xray_reassembly.expected.json"
    if not all(path.is_file() for path in (handoff_path, xray_path, expected_path)):
        return False

    try:
        handoff = _read_json(handoff_path)
        xray_envelope, _xray = read_exact_xray_predecessor(xray_path)
        expected = _read_json(expected_path)
        artifacts = expected["artifacts"]
        return (
            handoff["surface"] == surface
            and handoff["stage"] == "internal_arcadia_download_workflow_load"
            and isinstance(handoff["request"], dict)
            and isinstance(handoff["workflow_extract"], dict)
            and xray_envelope["source"]["run_id"] == handoff["request"]["workflow_capture"]["run_id"]
            and xray_envelope["source"]["process_id"] == handoff["request"]["task_id"]
            and xray_envelope["source"]["document_id"] == handoff["request"]["document_id"]
            and expected["surface"] == surface
            and expected["input_sha256"] == _sha256(handoff_path)
            and artifacts["previous_download_workflow_load"]["sha256"] == _sha256(handoff_path)
            and artifacts["xray_predecessor"]["sha256"] == _sha256(xray_path)
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def read_exact_xray_predecessor(
    path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    envelope = _read_json(path)
    if envelope.get("kind") != "xray_predecessor":
        raise ValueError("X-Ray predecessor kind is invalid")
    value = envelope.get("value")
    source = envelope.get("source")
    encoded = envelope.get("raw_xray_model_base64")
    digest = envelope.get("raw_xray_model_sha256")
    byte_count = envelope.get("raw_xray_model_bytes")
    if not isinstance(value, dict) or not isinstance(source, dict):
        raise ValueError("X-Ray predecessor value and source are required")
    if source.get("source_kind") != "live_capture":
        raise ValueError("X-Ray predecessor is not a live capture")
    for field in ("run_id", "process_id", "document_id"):
        if not isinstance(source.get(field), str) or not source[field]:
            raise ValueError(f"X-Ray predecessor source.{field} is required")
    if not isinstance(encoded, str) or not isinstance(digest, str):
        raise ValueError("X-Ray predecessor raw model bytes are required")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except ValueError as error:
        raise ValueError("X-Ray predecessor raw model base64 is invalid") from error
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("X-Ray predecessor raw model digest changed")
    if byte_count != len(raw):
        raise ValueError("X-Ray predecessor raw model byte count changed")
    try:
        parsed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("X-Ray predecessor raw model is not JSON") from error
    canonical = json.dumps(
        parsed,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if raw != canonical:
        raise ValueError("X-Ray predecessor uses an unknown serializer")
    if parsed != value:
        raise ValueError("X-Ray predecessor value differs from captured bytes")
    return envelope, value


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
