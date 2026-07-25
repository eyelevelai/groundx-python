import hashlib
import json
import pathlib
import re
import typing

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEXT_FIXTURE_SUFFIXES = {".csv", ".json", ".md", ".txt", ".yaml", ".yml"}
BINARY_PRIVATE_SUFFIXES = {".jpeg", ".jpg", ".pdf", ".png", ".tiff"}
PRIVATE_ARTIFACT_KEYS = {
    "callback_body",
    "pageImages",
    "page_images",
    "provider_request",
    "provider_response",
    "raw_response",
    "xray",
}
IDENTITY_KEYS = {
    "documentID",
    "documentId",
    "document_id",
    "processID",
    "processId",
    "process_id",
    "taskID",
    "taskId",
    "task_id",
}
SENSITIVE_VALUE_KEYS = {
    "account_number",
    "address_street",
    "customer_name",
    "email",
    "employer_name",
    "phone",
    "recipient_name",
    "service_address",
    "ssn",
    "tax_identification_number",
    "telephone",
}
PLACEHOLDER_VALUES = {
    "",
    "A-100",
    "example",
    "placeholder",
    "test",
}
PINNED_SYNTHETIC_FIXTURES = {
    "tests/extract/fixtures/custom_output_reassembly_cases.json": (
        "096fd770111492f582588039348ff006839830ce8c8f57b8469f9e65d292e577"
    ),
}
TEXT_PATTERNS = {
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "email address": re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    ),
    "labeled sensitive value": re.compile(
        r"^\s*(?:account_number|email|phone|ssn|tax_identification_number|"
        r"telephone)[ \t]*:[ \t]*[\"']?"
        r"(?!<|\$\{|example\b|placeholder\b|test\b)"
        r"[A-Z0-9]",
        re.IGNORECASE | re.MULTILINE,
    ),
    "signed URL": re.compile(
        r"[?&](?:X-Amz-(?:Algorithm|Credential|Signature)|Signature)=",
        re.IGNORECASE,
    ),
    "social security number": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "street address": re.compile(
        r"\b\d{2,6}\s+[A-Z0-9][A-Z0-9 .'-]{2,60}\s"
        r"(?:AVE(?:NUE)?|BLVD|BOULEVARD|DR(?:IVE)?|LN|LANE|RD|ROAD|"
        r"ST(?:REET)?|WAY)\b",
        re.IGNORECASE,
    ),
    "tax identifier": re.compile(r"\b\d{2}-\d{7}\b"),
}
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _fixture_paths() -> typing.List[pathlib.Path]:
    paths = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if not any(part in {"fixture", "fixtures"} for part in path.parts):
            continue
        paths.append(path)
    return sorted(paths)


def _is_placeholder(value: str) -> bool:
    normalized = value.strip()
    return (
        normalized in PLACEHOLDER_VALUES
        or normalized.startswith("/")
        or normalized.startswith("<")
        or normalized.startswith("${")
        or normalized.startswith("blank reviewed expected value")
    )


def _inspect_json(
    value: typing.Any,
    *,
    path: pathlib.Path,
    location: typing.Tuple[str, ...] = (),
) -> typing.List[str]:
    findings = []
    if isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_inspect_json(item, path=path, location=location + (str(index),)))
        return findings
    if not isinstance(value, dict):
        return findings

    for key, item in value.items():
        item_location = location + (str(key),)
        location_text = ".".join(item_location)
        if key in PRIVATE_ARTIFACT_KEYS:
            findings.append(f"{path}: private artifact key {location_text}")
        if isinstance(item, str):
            if key in IDENTITY_KEYS and UUID_RE.fullmatch(item):
                findings.append(f"{path}: live identifier at {location_text}")
            if key in SENSITIVE_VALUE_KEYS and not _is_placeholder(item):
                findings.append(f"{path}: sensitive value at {location_text}")
            if key in {"prompt", "request", "response", "task"} and len(item) > 500:
                findings.append(f"{path}: captured model content at {location_text}")
        findings.extend(_inspect_json(item, path=path, location=item_location))
    return findings


def _scan_fixture(path: pathlib.Path) -> typing.List[str]:
    try:
        relative_path = str(path.relative_to(ROOT))
    except ValueError:
        relative_path = ""
    pinned_digest = PINNED_SYNTHETIC_FIXTURES.get(relative_path)
    if pinned_digest is not None:
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_digest == pinned_digest:
            return []
        return [f"{path}: pinned synthetic fixture changed"]
    if path.suffix.lower() in BINARY_PRIVATE_SUFFIXES:
        return [f"{path}: binary document or page image"]
    if path.suffix.lower() not in TEXT_FIXTURE_SUFFIXES:
        return []

    text = path.read_text(encoding="utf-8")
    findings = [f"{path}: {label}" for label, pattern in TEXT_PATTERNS.items() if pattern.search(text)]
    if path.suffix.lower() == ".json":
        findings.extend(_inspect_json(json.loads(text), path=path))
    return findings


def test_public_fixtures_do_not_contain_private_extraction_data() -> None:
    paths = _fixture_paths()
    assert paths, "privacy scan found no fixture files"

    findings = []
    for path in paths:
        findings.extend(_scan_fixture(path))
    assert not findings, "\n".join(findings)


@pytest.mark.parametrize(
    ("name", "payload"),
    [
        ("tax identifier", {"tax_identification_number": "82-2713261"}),
        ("account number", {"account_number": "00022829-7"}),
        ("live ID", {"documentID": "17c6a87d-3d01-4da0-b2ab-990680a86836"}),
        ("raw X-Ray", {"xray": {"chunks": []}}),
        ("captured prompt", {"request": "private prompt " * 100}),
    ],
)
def test_private_json_shapes_are_rejected(
    tmp_path: pathlib.Path,
    name: str,
    payload: typing.Dict[str, typing.Any],
) -> None:
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert _scan_fixture(path), name


def test_private_text_shapes_are_rejected(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "fixture.txt"
    path.write_text(
        "person@example.com\n8525 W 100th Ave\nhttps://example.com/file?X-Amz-Signature=secret\n",
        encoding="utf-8",
    )

    findings = _scan_fixture(path)
    assert len(findings) == 3


def test_private_yaml_values_are_rejected(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "fixture.yaml"
    path.write_text("account_number: 00022829-7\n", encoding="utf-8")

    assert _scan_fixture(path)
