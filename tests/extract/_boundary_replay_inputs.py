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
    xray_path = input_root / surface / "groundx_python_xray_reassembly.xray.json"
    expected_path = goldens_root / surface / "groundx_python_xray_reassembly.expected.json"
    if not all(path.is_file() for path in (handoff_path, xray_path, expected_path)):
        return False

    try:
        handoff = _read_json(handoff_path)
        xray_sidecar = _read_json(xray_path)
        expected = _read_json(expected_path)
        artifacts = expected["artifacts"]
        return (
            handoff["surface"] == surface
            and handoff["stage"] == "internal_arcadia_download_workflow_load"
            and isinstance(handoff["request"], dict)
            and isinstance(handoff["workflow_extract"], dict)
            and xray_sidecar["surface"] == surface
            and xray_sidecar["schema_version"] == "groundx_python_xray_reassembly_sidecar_v1"
            and xray_sidecar["input_for"] == "groundx_python_xray_reassembly"
            and xray_sidecar["source_handoff"] == "internal_arcadia_download_workflow_load.handoff.json"
            and isinstance(xray_sidecar["xray"], dict)
            and expected["surface"] == surface
            and expected["input_sha256"] == _sha256(handoff_path)
            and artifacts["previous_download_workflow_load"]["sha256"] == _sha256(handoff_path)
            and artifacts["xray_sidecar"]["sha256"] == _sha256(xray_path)
        )
    except (KeyError, TypeError, json.JSONDecodeError):
        return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
