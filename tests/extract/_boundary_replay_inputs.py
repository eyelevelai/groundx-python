import base64
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit

COMPLETE_OUTPUT_MEMBERS = (
    "workflow_output",
    "relationship_output",
    "final_output",
    "diagnostics",
    "source_provenance",
)
_COMPONENT_HASH_FIELDS = (
    ("workflow_output", "workflow_output_sha256"),
    ("relationship_output", "relationship_output_sha256"),
    ("final_output", "final_output_sha256"),
)


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


def resolve_reviewed_complete_output(
    expected: Mapping[str, Any] | bytes,
    *,
    downloader: Callable[[str], bytes],
) -> dict[str, Any]:
    complete, _raw = _resolve_reviewed_complete_output_bytes(expected, downloader=downloader)
    return complete


def _resolve_reviewed_complete_output_bytes(
    expected: Mapping[str, Any] | bytes,
    *,
    downloader: Callable[[str], bytes],
) -> tuple[dict[str, Any], bytes]:
    if isinstance(expected, bytes):
        complete = _parse_complete_output(expected)
        return complete, expected

    evidence = expected.get("reviewed_complete_output")
    if not isinstance(evidence, Mapping):
        raise ValueError("SDK expected output is summary-only; complete reviewed output bytes are required")

    url = evidence.get("url")
    if not isinstance(url, str) or not url:
        raise ValueError("reviewed complete output must be exact inline bytes or one HTTPS URL")
    _validate_reviewed_url(url)
    try:
        raw = downloader(url)
    except Exception as error:
        raise ValueError("reviewed complete output download failed") from error
    if not isinstance(raw, bytes):
        raise ValueError("reviewed complete output downloader must return bytes")

    byte_count = evidence.get("bytes")
    if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count != len(raw):
        raise ValueError("reviewed complete output byte count mismatch")
    digest = evidence.get("sha256")
    if not isinstance(digest, str) or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("reviewed complete output SHA-256 mismatch")

    complete = _parse_complete_output(raw)

    summary = expected.get("output")
    if not isinstance(summary, Mapping):
        raise ValueError("reviewed complete output component summary is missing")
    for member, hash_field in _COMPONENT_HASH_FIELDS:
        if summary.get(hash_field) != _sha256_json(complete[member]):
            raise ValueError(f"reviewed complete output {member} SHA-256 mismatch")
    if summary.get("diagnostic_count") != len(complete["diagnostics"]):
        raise ValueError("reviewed complete output diagnostics count mismatch")
    if summary.get("source_provenance_count") != len(complete["source_provenance"]):
        raise ValueError("reviewed complete output source provenance count mismatch")

    return complete, raw


def assert_reassembly_matches_reviewed_output(
    actual: Mapping[str, Any],
    expected: Mapping[str, Any] | bytes,
    *,
    downloader: Callable[[str], bytes],
) -> dict[str, Any]:
    reviewed, reviewed_bytes = _resolve_reviewed_complete_output_bytes(expected, downloader=downloader)
    missing = [member for member in COMPLETE_OUTPUT_MEMBERS if member not in actual]
    if missing:
        raise AssertionError("protected SDK replay actual output is missing complete members: " + ", ".join(missing))
    actual_complete = {member: copy.deepcopy(actual[member]) for member in COMPLETE_OUTPUT_MEMBERS}
    if _canonical_json_bytes(actual_complete) != reviewed_bytes:
        raise AssertionError("complete reviewed SDK reassembly output mismatch")
    return reviewed


def _parse_complete_output(raw: bytes) -> dict[str, Any]:
    try:
        complete = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("reviewed complete output is not valid JSON") from error
    if not isinstance(complete, dict):
        raise ValueError("reviewed complete output JSON must be an object")
    missing = [member for member in COMPLETE_OUTPUT_MEMBERS if member not in complete]
    if missing:
        raise ValueError(f"reviewed complete output is missing required member: {missing[0]}")
    extras = sorted(set(complete) - set(COMPLETE_OUTPUT_MEMBERS))
    if extras:
        raise ValueError(f"reviewed complete output has unexpected member: {extras[0]}")
    if not isinstance(complete["diagnostics"], list):
        raise ValueError("reviewed complete output diagnostics must be an array")
    if not isinstance(complete["source_provenance"], list):
        raise ValueError("reviewed complete output source_provenance must be an array")
    if raw != _canonical_json_bytes(complete):
        raise ValueError("reviewed complete output is not canonical JSON")
    return {member: copy.deepcopy(complete[member]) for member in COMPLETE_OUTPUT_MEMBERS}


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _validate_reviewed_url(url: str) -> None:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise ValueError("reviewed complete output URL must be clean") from error
    if parsed.scheme != "https":
        raise ValueError("reviewed complete output URL must use HTTPS")
    if (
        not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or port not in (None, 443)
    ):
        raise ValueError("reviewed complete output URL must be clean")


def _sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
