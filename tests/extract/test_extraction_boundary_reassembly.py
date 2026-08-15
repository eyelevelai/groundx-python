import copy
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import typing
import urllib.parse

import pytest

from groundx.extract.custom_outputs import reassemble_custom_outputs_from_xray

ROOT = pathlib.Path(__file__).resolve().parents[2]
_REPLAY_INPUTS_SPEC = importlib.util.spec_from_file_location(
    "boundary_replay_inputs",
    pathlib.Path(__file__).with_name("_boundary_replay_inputs.py"),
)
assert _REPLAY_INPUTS_SPEC is not None and _REPLAY_INPUTS_SPEC.loader is not None
_replay_inputs = importlib.util.module_from_spec(_REPLAY_INPUTS_SPEC)
_REPLAY_INPUTS_SPEC.loader.exec_module(_replay_inputs)
read_exact_xray_predecessor = _replay_inputs.read_exact_xray_predecessor
DIAGNOSTIC_ROOT = ROOT / "tests" / "extract" / "fixtures" / "extraction-diagnostics" / "expected-answer-projection"
DIAGNOSTIC_GOLDENS_ROOT = DIAGNOSTIC_ROOT / "boundary-goldens"
DIAGNOSTIC_HANDOFF_ROOT = DIAGNOSTIC_ROOT / "boundary-handoffs"
DIAGNOSTIC_INPUT_ROOT = DIAGNOSTIC_ROOT / "inputs"
BOUNDARY_ROOT = ROOT / "tests" / "extract" / "fixtures" / "extraction-boundary"
BOUNDARY_INPUT_ROOT = BOUNDARY_ROOT / "inputs"
BOUNDARY_GOLDENS_ROOT = BOUNDARY_ROOT / "boundary-goldens"
CATALOG_PATH = ROOT / "tests" / "extract" / "fixtures" / "extraction-boundary" / "catalog.json"
CATALOG_SHA256 = "98c198436c00548fd2de34cb7bf42bbf9698d9690b4e9672b1ecc1ac5c450466"
WRITER_REGISTRY_PATH = BOUNDARY_ROOT / "writer_registry.json"
ADP_EXPECTED_SECTION_COUNT = 11
ADP_EXPECTED_FIELD_COUNT = 159
ADP_MIN_POPULATED_FIELDS = 100
ADP_MAX_POPULATED_FIELDS = 159
ADP_MIN_NULL_FIELDS = 0
ADP_MAX_NULL_FIELDS = 59
ADP_MIN_SECTION_POPULATED_RATIO = 0.6
_PROJECTION = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
SURFACES = [case["surface"] for case in _PROJECTION["cases"]]
REAL_BOUNDARY_SURFACES = tuple(SURFACES)


GOVERNED_REMOVAL_CONDITION = (
    "Remove this protected case only from the canonical Harness certification "
    "registry, then regenerate the owner projections. Never add a skip."
)
REVIEWED_COMPLETE_OUTPUT_URL = "https://fixtures.groundx.ai/reviewed/groundx-python-sdk-reassembly.json"
COMPLETE_OUTPUT_MEMBERS = (
    "workflow_output",
    "relationship_output",
    "final_output",
    "diagnostics",
    "source_provenance",
)


def _protected_fixture_paths(surface: str) -> typing.Tuple[pathlib.Path, ...]:
    expected = BOUNDARY_GOLDENS_ROOT / surface / "groundx_python_xray_reassembly.expected.json"
    return (
        BOUNDARY_INPUT_ROOT / surface / "internal_arcadia_download_workflow_load.handoff.json",
        BOUNDARY_INPUT_ROOT / surface / "internal_arcadia_agent_load_xray.xray.json",
        expected,
        expected.with_name("groundx_python_xray_reassembly.expected.diff.json"),
        expected.with_name("groundx_python_xray_reassembly.expected.review.json"),
    )


def _require_protected_fixture_pack(surface: str) -> None:
    for path in _protected_fixture_paths(surface):
        if not path.is_file():
            display_path = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
            pytest.fail(
                "INTENTIONAL RED: protected extraction boundary fixture is missing: "
                f"{display_path}. {GOVERNED_REMOVAL_CONDITION}"
            )


def test_extraction_boundary_owner_projection_is_pinned() -> None:
    catalog = _read_json(CATALOG_PATH)

    assert _sha256_file(CATALOG_PATH) == CATALOG_SHA256
    assert catalog["schema_version"] == "extraction_boundary_owner_projection_v1"
    assert catalog["catalog_version"] == "2026-07-23.1"
    assert catalog["owner"] == "groundx-python"
    assert catalog["surfaces"] == SURFACES
    assert "source_artifact_catalog_sha256" not in catalog
    assert catalog["writer_registry_sha256"] == _sha256_file(WRITER_REGISTRY_PATH)
    for case in catalog["cases"]:
        assert case["fixture_status"] in {"complete", "pending"}
        assert case["required_stage_ids"]
        assert case["trace_preset"] in catalog["trace_stage_presets"]
    [artifact] = catalog["artifacts"]
    assert artifact["name"] == "groundx_python_xray_reassembly"
    assert artifact["owner"] == "groundx-python"
    assert artifact["required"] is True
    assert artifact["fixture_policy"] == "commit_sanitized_fixture"
    assert artifact["input_from"] == "internal_arcadia_load_xray_predecessor"
    assert artifact["input_path_template"] == (
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        "inputs/{surface}/internal_arcadia_agent_load_xray.xray.json"
    )
    assert artifact["companion_input_from"] == "internal_arcadia_download_workflow_load"
    assert artifact["companion_input_path_template"] == (
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        "inputs/{surface}/internal_arcadia_download_workflow_load.handoff.json"
    )
    assert artifact["path_template"] == (
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        "boundary-goldens/{surface}/groundx_python_xray_reassembly.expected.json"
    )
    assert artifact["stage"] == "sdk_xray_reassembly"
    assert artifact["validator"] == ("groundx-python/tests/extract/test_extraction_boundary_reassembly.py")
    assert artifact["production_entrypoint"] == ("groundx.extract.custom_outputs.reassemble_custom_outputs")
    assert artifact["evidence_writer_function"] == ("classes.pipeline_trace.capture_sdk_reassembly_output")
    assert artifact["writer"] == (
        "classes/statement.py _sdk_custom_output_reassembly_result -> "
        "classes/pipeline_trace.py capture_sdk_reassembly_output"
    )
    assert artifact["s3_path_template"] == (
        "layout/processed/{task_id}/{document_id}-extract-trace/"
        "internal-arcadia-agents/{stage_run}/sdk.reassembly_output.json"
    )


def test_protected_replay_cases_are_never_marked_or_skipped() -> None:
    params = [pytest.param(surface, id=surface) for surface in SURFACES]

    assert [param.values[0] for param in params] == SURFACES
    assert all(param.marks == () for param in params)


def test_missing_protected_fixture_names_exact_path_and_governed_removal(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    monkeypatch.setitem(globals(), "BOUNDARY_INPUT_ROOT", tmp_path / "inputs")
    monkeypatch.setitem(globals(), "BOUNDARY_GOLDENS_ROOT", tmp_path / "boundary-goldens")

    with pytest.raises(pytest.fail.Exception) as error:
        _require_protected_fixture_pack("arcadia_v1")

    message = str(error.value)
    assert "INTENTIONAL RED" in message
    assert "inputs/arcadia_v1/internal_arcadia_download_workflow_load.handoff.json" in message
    assert GOVERNED_REMOVAL_CONDITION in message


def _complete_reviewed_output() -> typing.Dict[str, typing.Any]:
    return {
        "workflow_output": {"statement": {"account_number": "reviewed"}},
        "relationship_output": {"meters": [{"charges": []}]},
        "final_output": {
            "statement": {"account_number": "reviewed"},
            "meters": [{"charges": []}],
        },
        "diagnostics": [],
        "source_provenance": [
            {
                "final_path": "/statement/account_number",
                "output_source": "customChunkOutputs",
                "page_numbers": [1],
                "record_index": None,
                "workflow_field": "account_number",
                "workflow_group": "statement",
            }
        ],
    }


def _canonical_json_bytes(value: typing.Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash_backed_expected_packet(
    complete_output_bytes: bytes,
    *,
    url: str = REVIEWED_COMPLETE_OUTPUT_URL,
) -> typing.Dict[str, typing.Any]:
    return {
        "reviewed_complete_output": {
            "url": url,
            "bytes": len(complete_output_bytes),
            "sha256": hashlib.sha256(complete_output_bytes).hexdigest(),
        },
    }


def _resolve_reviewed_complete_output(
    expected: typing.Mapping[str, typing.Any] | bytes,
    *,
    downloader: typing.Callable[[str], bytes],
) -> typing.Dict[str, typing.Any]:
    resolver = getattr(_replay_inputs, "resolve_reviewed_complete_output", None)
    if not callable(resolver):
        pytest.fail("INTENTIONAL RED: hash-only SDK expected output has no executable download-and-rehash resolver")
    return typing.cast(
        typing.Dict[str, typing.Any],
        resolver(expected, downloader=downloader),
    )


def _reviewed_output_evidence(expected_path: pathlib.Path) -> typing.Mapping[str, typing.Any] | bytes:
    raw = expected_path.read_bytes()
    parsed = json.loads(raw)
    if isinstance(parsed, dict) and set(parsed) == set(COMPLETE_OUTPUT_MEMBERS):
        return raw
    return typing.cast(typing.Mapping[str, typing.Any], parsed)


def _assert_replay_matches_reviewed_complete_output(
    actual: typing.Mapping[str, typing.Any],
    expected_path: pathlib.Path,
    *,
    downloader: typing.Callable[[str], bytes],
    diff_path: pathlib.Path | None = None,
) -> typing.Dict[str, typing.Any]:
    expected = _reviewed_output_evidence(expected_path)
    assert_matches = getattr(_replay_inputs, "assert_reassembly_matches_reviewed_output", None)
    if not callable(assert_matches):
        pytest.fail("INTENTIONAL RED: protected replay has no shared complete-output comparison")
    try:
        reviewed = typing.cast(
            typing.Dict[str, typing.Any],
            assert_matches(actual, expected, downloader=downloader),
        )
    except AssertionError:
        if diff_path is not None:
            _write_json(
                diff_path,
                {
                    "kind": "machine_readable_json_diff",
                    "status": "failed",
                    "expected": _resolve_reviewed_complete_output(expected, downloader=downloader),
                    "actual": {member: copy.deepcopy(actual.get(member)) for member in COMPLETE_OUTPUT_MEMBERS},
                },
            )
        raise
    return reviewed


def _download_reviewed_complete_output(url: str) -> bytes:
    downloader = getattr(_replay_inputs, "download_reviewed_complete_output", None)
    if not callable(downloader):
        pytest.fail("INTENTIONAL RED: protected replay has no bounded HTTPS downloader")
    return typing.cast(bytes, downloader(url))


def _assert_resolver_rejects(
    expected: typing.Mapping[str, typing.Any] | bytes,
    *,
    downloader: typing.Callable[[str], bytes],
    expected_error: str,
) -> None:
    with pytest.raises(ValueError) as error:
        _resolve_reviewed_complete_output(expected, downloader=downloader)
    assert str(error.value) == expected_error


def test_hash_backed_expected_output_downloads_exact_url_without_reconstructed_summary() -> None:
    complete_output = _complete_reviewed_output()
    downloaded = _canonical_json_bytes(complete_output)
    expected = _hash_backed_expected_packet(downloaded)
    requested_urls: typing.List[str] = []

    def download(url: str) -> bytes:
        requested_urls.append(url)
        return downloaded

    resolved = _resolve_reviewed_complete_output(expected, downloader=download)

    assert requested_urls == [REVIEWED_COMPLETE_OUTPUT_URL]
    assert resolved == complete_output


def test_reviewed_complete_output_downloader_bounds_timeout_and_response_size() -> None:
    downloader = getattr(_replay_inputs, "download_reviewed_complete_output", None)
    if not callable(downloader):
        pytest.fail("INTENTIONAL RED: protected replay has no bounded HTTPS downloader")

    class Response:
        def __init__(self, payload: bytes) -> None:
            self.payload = payload
            self.requested_bytes: int | None = None

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: typing.Any) -> None:
            return None

        def read(self, byte_count: int) -> bytes:
            self.requested_bytes = byte_count
            return self.payload[:byte_count]

    response = Response(b"1234")
    opened: typing.List[typing.Tuple[str, float]] = []

    def open_url(url: str, *, timeout: float) -> Response:
        opened.append((url, timeout))
        return response

    downloaded = downloader(
        REVIEWED_COMPLETE_OUTPUT_URL,
        opener=open_url,
        timeout_seconds=2.5,
        max_bytes=4,
    )

    assert downloaded == b"1234"
    assert opened == [(REVIEWED_COMPLETE_OUTPUT_URL, 2.5)]
    assert response.requested_bytes == 5


def test_reviewed_complete_output_downloader_rejects_oversized_response() -> None:
    downloader = getattr(_replay_inputs, "download_reviewed_complete_output", None)
    if not callable(downloader):
        pytest.fail("INTENTIONAL RED: protected replay has no bounded HTTPS downloader")

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: typing.Any) -> None:
            return None

        def read(self, byte_count: int) -> bytes:
            return b"12345"[:byte_count]

    with pytest.raises(ValueError, match="reviewed complete output exceeds 4-byte limit"):
        downloader(
            REVIEWED_COMPLETE_OUTPUT_URL,
            opener=lambda _url, *, timeout: Response(),
            timeout_seconds=2.5,
            max_bytes=4,
        )


def test_reviewed_complete_output_downloader_rejects_unsafe_redirect_before_read() -> None:
    downloader = getattr(_replay_inputs, "download_reviewed_complete_output", None)
    if not callable(downloader):
        pytest.fail("INTENTIONAL RED: protected replay has no bounded HTTPS downloader")

    class RedirectedResponse:
        def __init__(self) -> None:
            self.read_called = False

        def __enter__(self) -> "RedirectedResponse":
            return self

        def __exit__(self, *_args: typing.Any) -> None:
            return None

        def geturl(self) -> str:
            return "http://fixtures.groundx.ai/reviewed/redirected.json"

        def read(self, _byte_count: int) -> bytes:
            self.read_called = True
            return b"unsafe"

    response = RedirectedResponse()
    with pytest.raises(ValueError, match="reviewed complete output URL must use HTTPS"):
        downloader(
            REVIEWED_COMPLETE_OUTPUT_URL,
            opener=lambda _url, *, timeout: response,
            timeout_seconds=2.5,
            max_bytes=64,
        )
    assert response.read_called is False


def test_inline_expected_output_resolves_complete_bytes_without_download() -> None:
    complete_output = _complete_reviewed_output()
    inline_bytes = _canonical_json_bytes(complete_output)

    resolved = _resolve_reviewed_complete_output(
        inline_bytes,
        downloader=lambda _url: pytest.fail("inline reviewed output must not use the downloader"),
    )

    assert resolved == complete_output


def test_inline_expected_output_rejects_noncanonical_bytes() -> None:
    noncanonical = json.dumps(_complete_reviewed_output(), indent=2, sort_keys=True).encode("utf-8")

    _assert_resolver_rejects(
        noncanonical,
        downloader=lambda _url: pytest.fail("inline reviewed output must not use the downloader"),
        expected_error="reviewed complete output is not canonical JSON",
    )


@pytest.mark.parametrize(
    ("url", "error"),
    (
        ("http://fixtures.groundx.ai/reviewed/output.json", "reviewed complete output URL must use HTTPS"),
        ("https://fixtures.groundx.ai/reviewed/output.json?token=secret", "reviewed complete output URL must be clean"),
        ("https://user:secret@fixtures.groundx.ai/reviewed/output.json", "reviewed complete output URL must be clean"),
    ),
)
def test_hash_backed_expected_output_rejects_unsafe_url(url: str, error: str) -> None:
    complete_output = _complete_reviewed_output()
    downloaded = _canonical_json_bytes(complete_output)
    expected = _hash_backed_expected_packet(downloaded, url=url)

    _assert_resolver_rejects(
        expected,
        downloader=lambda _url: pytest.fail("unsafe URL must fail before download"),
        expected_error=error,
    )


def test_hash_backed_expected_output_rejects_unavailable_download() -> None:
    complete_output = _complete_reviewed_output()
    downloaded = _canonical_json_bytes(complete_output)
    expected = _hash_backed_expected_packet(downloaded)

    def unavailable(_url: str) -> bytes:
        raise OSError("fixture unavailable")

    _assert_resolver_rejects(
        expected,
        downloader=unavailable,
        expected_error="reviewed complete output download failed",
    )


@pytest.mark.parametrize(
    ("metadata_field", "metadata_value", "expected_error"),
    (
        ("bytes", 1, "reviewed complete output byte count mismatch"),
        ("sha256", "0" * 64, "reviewed complete output SHA-256 mismatch"),
    ),
)
def test_hash_backed_expected_output_rejects_byte_or_hash_mismatch(
    metadata_field: str,
    metadata_value: typing.Any,
    expected_error: str,
) -> None:
    complete_output = _complete_reviewed_output()
    downloaded = _canonical_json_bytes(complete_output)
    expected = _hash_backed_expected_packet(downloaded)
    expected["reviewed_complete_output"][metadata_field] = metadata_value

    _assert_resolver_rejects(
        expected,
        downloader=lambda _url: downloaded,
        expected_error=expected_error,
    )


def test_hash_backed_expected_output_rejects_invalid_json() -> None:
    downloaded = b"not json"
    expected = _hash_backed_expected_packet(downloaded)

    _assert_resolver_rejects(
        expected,
        downloader=lambda _url: downloaded,
        expected_error="reviewed complete output is not valid JSON",
    )


@pytest.mark.parametrize("missing_member", COMPLETE_OUTPUT_MEMBERS)
def test_hash_backed_expected_output_requires_every_complete_member(missing_member: str) -> None:
    complete_output = _complete_reviewed_output()
    del complete_output[missing_member]
    downloaded = _canonical_json_bytes(complete_output)
    expected = _hash_backed_expected_packet(downloaded)

    _assert_resolver_rejects(
        expected,
        downloader=lambda _url: downloaded,
        expected_error=f"reviewed complete output is missing required member: {missing_member}",
    )


def test_replay_shared_comparison_detects_nested_drift(tmp_path: pathlib.Path) -> None:
    reviewed = _complete_reviewed_output()
    downloaded = _canonical_json_bytes(reviewed)
    expected_path = tmp_path / "reviewed.expected.json"
    expected_path.write_bytes(downloaded)
    actual = copy.deepcopy(reviewed)
    actual["final_output"]["meters"][0]["charges"].append({"amount": "drift"})

    with pytest.raises(AssertionError, match="complete reviewed SDK reassembly output mismatch"):
        _assert_replay_matches_reviewed_complete_output(
            actual,
            expected_path,
            downloader=lambda _url: downloaded,
        )


def test_replay_requires_all_five_complete_actual_members(tmp_path: pathlib.Path) -> None:
    reviewed = _complete_reviewed_output()
    downloaded = _canonical_json_bytes(reviewed)
    expected_path = tmp_path / "reviewed.expected.json"
    expected_path.write_bytes(downloaded)
    actual = copy.deepcopy(reviewed)
    del actual["source_provenance"]

    with pytest.raises(
        AssertionError,
        match="actual output is missing complete members: source_provenance",
    ):
        _assert_replay_matches_reviewed_complete_output(
            actual,
            expected_path,
            downloader=lambda _url: downloaded,
        )


@pytest.mark.parametrize(
    "surface",
    SURFACES,
)
def test_sdk_reassembly_expected_answer_projection_is_diagnostic_only(surface: str) -> None:
    previous = _read_json(_diagnostic_previous_boundary_input_path(surface))

    _assert_expected_answer_projection_diagnostic(previous)
    result = reassemble_custom_outputs_from_xray(
        previous["xray"],
        workflow_extract=previous["workflow_extract"],
    )

    assert isinstance(result.final_output, dict)
    assert previous["certification_eligible"] is False


@pytest.mark.parametrize(
    "surface",
    REAL_BOUNDARY_SURFACES,
)
@pytest.mark.release_intentional_fixture_red
def test_boundary_workflow_leaf_repetition_scope_is_api_enum(surface: str) -> None:
    """Stored production workflows carry enum scopes, not pointer-format ones."""
    _require_protected_fixture_pack(surface)
    handoff = _read_json(
        BOUNDARY_INPUT_ROOT / surface / "internal_arcadia_download_workflow_load.handoff.json"
    )
    leaves = handoff["workflow_extract"].get("workflow", {}).get("leaf_fields", [])

    for leaf in leaves:
        expected = "item" if leaf["is_repeated"] else "none"
        assert leaf["repetition_scope"] == expected, (
            f"{surface} leaf {leaf['final_path']} carries repetition_scope "
            f"{leaf['repetition_scope']!r}, expected {expected!r}"
        )


@pytest.mark.parametrize(
    "surface",
    REAL_BOUNDARY_SURFACES,
)
@pytest.mark.release_intentional_fixture_red
def test_sdk_xray_reassembly_real_boundary_packets(
    tmp_path: pathlib.Path,
    surface: str,
) -> None:
    _require_protected_fixture_pack(surface)
    actual, expected_path, diff_path = _write_xray_reassembly_boundary_artifact(
        tmp_path,
        surface,
    )
    expected = _stable_boundary_output(actual)
    _assert_replay_matches_reviewed_complete_output(
        expected,
        expected_path,
        downloader=_download_reviewed_complete_output,
        diff_path=diff_path,
    )
    _write_json(diff_path, {"kind": "machine_readable_json_diff", "status": "passed"})
    _assert_reviewed_expected_output_sidecar(expected_path)


@pytest.mark.release_intentional_fixture_red
def test_adp_boundary_reassembly_detects_corrupted_real_input(
    tmp_path: pathlib.Path,
) -> None:
    _require_protected_fixture_pack("adp_v1")
    handoff_path, xray_path, expected_path = _copy_adp_boundary_packet(tmp_path)
    handoff = _read_json(handoff_path)
    xray_packet = _read_json(xray_path)
    corrupted_employer_name = "CORRUPTED-ADP-EMPLOYER"
    xray_packet["value"]["chunks"][0]["customSectionOutputs"]["adp_f1_employer_and_plan_information"][
        "employer_name"
    ] = corrupted_employer_name
    _write_json(xray_path, xray_packet)

    result = reassemble_custom_outputs_from_xray(
        _read_json(xray_path)["value"],
        workflow_extract=handoff["workflow_extract"],
    )

    assert result.final_output["employer_information"]["employer_name"] == (corrupted_employer_name)
    with pytest.raises(
        AssertionError,
        match="complete reviewed output mismatch",
    ):
        _assert_replay_matches_reviewed_complete_output(
            _complete_reassembly_output(result),
            expected_path,
            downloader=_download_reviewed_complete_output,
        )


@pytest.mark.release_intentional_fixture_red
def test_adp_boundary_reassembly_detects_corrupted_expected_output(
    tmp_path: pathlib.Path,
) -> None:
    _require_protected_fixture_pack("adp_v1")
    handoff_path, xray_path, expected_path = _copy_adp_boundary_packet(tmp_path)
    handoff = _read_json(handoff_path)
    xray_packet = _read_json(xray_path)
    result = reassemble_custom_outputs_from_xray(
        xray_packet["value"],
        workflow_extract=handoff["workflow_extract"],
    )
    actual = _complete_reassembly_output(result)
    _assert_replay_matches_reviewed_complete_output(
        actual,
        expected_path,
        downloader=_download_reviewed_complete_output,
    )

    expected = _read_json(expected_path)
    expected["final_output"]["__corrupted__"] = True
    expected_path.write_bytes(_canonical_json_bytes(expected))

    with pytest.raises(
        AssertionError,
        match="complete reviewed output mismatch",
    ):
        _assert_replay_matches_reviewed_complete_output(
            actual,
            expected_path,
            downloader=_download_reviewed_complete_output,
        )


@pytest.mark.release_intentional_fixture_red
def test_adp_boundary_reassembly_rejects_invalid_identity_threshold_metadata(
    tmp_path: pathlib.Path,
) -> None:
    _require_protected_fixture_pack("adp_v1")
    handoff_path, xray_path, _expected_path = _copy_adp_boundary_packet(tmp_path)
    handoff = _read_json(handoff_path)
    workflow_extract = handoff["workflow_extract"]
    employer_group = workflow_extract["_groundx_persisted_extract"]["employer_information"]
    employer_group["unique_attrs"] = ["employer_name"]
    employer_group["identity_match"] = {
        "threshold_attrs": ["employer_name"],
        "activate_threshold_at": True,
        "minimum_threshold_matches": 1,
    }
    employer_name_route = next(
        route
        for route in workflow_extract["workflow"]["output_routes"]
        if route["final_path"] == "/employer_information/employer_name"
    )
    employer_name_route["final_path"] = "/employer_information/*/employer_name"
    _write_json(handoff_path, handoff)

    with pytest.raises(
        ValueError,
        match=r"identity_match\.activate_threshold_at must be an integer",
    ):
        reassemble_custom_outputs_from_xray(
            _read_json(xray_path)["value"],
            workflow_extract=_read_json(handoff_path)["workflow_extract"],
        )


def test_repo_evidence_path_accepts_canonical_repo_prefix(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(globals(), "ROOT", tmp_path / "renamed-worktree")

    assert _repo_evidence_path("groundx-python/tests/extract/fixtures/example.json") == pathlib.Path(
        "tests/extract/fixtures/example.json"
    )


def test_projection_fixtures_are_diagnostic_only() -> None:
    for fixture_path in DIAGNOSTIC_ROOT.glob("**/*.json"):
        fixture = _read_json(fixture_path)
        if _has_projection_marker(fixture):
            assert fixture.get("evidence_level") == ("expected_answer_projection_diagnostic"), fixture_path
            assert fixture.get("certification_eligible") is False, fixture_path


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


def test_sdk_reassembly_diagnostic_consumes_projection_input() -> None:
    for surface in SURFACES:
        previous_path = _diagnostic_previous_boundary_input_path(surface)
        assert previous_path == (DIAGNOSTIC_INPUT_ROOT / surface / "internal_arcadia_extract_chain.handoff.json")
        previous = _read_json(previous_path)
        assert previous["stage"] == "internal_arcadia_extract_chain"
        assert previous["input_from"] == "internal_arcadia_download_workflow_load"
        assert previous["evidence_level"] == "expected_answer_projection_diagnostic"
        assert previous["certification_eligible"] is False


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
        final_output["meters"][index % 8]["charges"].append({"charge_amount": index})
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
        "meters": [{"charges": [{"charge_amount": meter_index}]} for meter_index in range(8)],
        "charges": [{"charge_amount": charge_index} for charge_index in range(account_charge_count)],
    }
    final_output.update({f"statement_field_{index}": index for index in range(14)})

    assertions = _shape_assertions(
        "arcadia_v1",
        final_output,
        diagnostics=[],
        relationship_output={"meters": final_output["meters"]},
    )

    assert assertions["has_expected_account_child_count"] is expected


def test_utility_shape_assertions_follow_workflow_relationship_metadata() -> None:
    parent_group = "customer_parent_records"
    child_group = "customer_unmatched_children"
    child_field = "customer_nested_children"
    workflow_extract = {
        "workflow": {
            "output_relationships": [
                {
                    "parent_group": parent_group,
                    "child_group": child_group,
                    "parent_output_field": child_field,
                }
            ],
            "output_routes": [{"final_path": f"/customer_statement_field_{index}"} for index in range(14)],
        }
    }
    parents: typing.List[typing.Dict[str, typing.Any]] = [{child_field: []} for _unused in range(8)]
    for index in range(24):
        parents[index % len(parents)][child_field].append({"amount": index})
    final_output: typing.Dict[str, typing.Any] = {
        parent_group: parents,
        child_group: [{"amount": "account-level"}],
    }
    final_output.update({f"customer_statement_field_{index}": index for index in range(14)})

    final_assertions = _shape_assertions(
        "generic_v1",
        final_output,
        diagnostics=[],
        relationship_output={"relationships": []},
        workflow_extract=workflow_extract,
    )
    xray_assertions = _xray_reassembly_shape_assertions(
        "generic_v1",
        final_output,
        diagnostics=[],
        relationship_output={"relationships": []},
        workflow_extract=workflow_extract,
    )

    assert final_assertions["has_expected_parent_count"] is True
    assert final_assertions["every_parent_has_child_rows"] is True
    assert final_assertions["has_expected_meter_charge_count"] is True
    assert final_assertions["has_expected_account_child_count"] is True
    assert final_assertions["has_statement_fields"] is True
    assert xray_assertions["has_minimum_parent_candidates"] is True
    assert xray_assertions["has_minimum_total_child_candidates"] is True
    assert xray_assertions["has_statement_fields"] is True


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
    previous_path = _diagnostic_previous_boundary_input_path(surface)
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
    handoff_actual_path = out_dir / "groundx_python_sdk_reassembly.actual_handoff.json"
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
            "consumes_internal_extract_chain_handoff": previous["stage"] == "internal_arcadia_extract_chain",
            "has_no_error_diagnostics": assertions["has_no_error_diagnostics"],
            "shape_contract_passed": all(assertions.values()),
            "handoff_written_for_save_callback": handoff_actual_path.exists()
            and handoff["output_for"] == "internal_arcadia_save_callback",
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
    expected_path = DIAGNOSTIC_GOLDENS_ROOT / surface / "groundx_python_sdk_reassembly.expected.json"
    diff_path = out_dir / "groundx_python_sdk_reassembly.diff.json"
    handoff_path = DIAGNOSTIC_HANDOFF_ROOT / surface / "groundx_python_sdk_reassembly.handoff.json"
    _write_json(actual_path, actual)
    return actual, actual_path, expected_path, diff_path, previous_path, handoff_path


def _diagnostic_previous_boundary_input_path(surface: str) -> pathlib.Path:
    return DIAGNOSTIC_INPUT_ROOT / surface / "internal_arcadia_extract_chain.handoff.json"


def _real_download_workflow_load_input_path(surface: str) -> pathlib.Path:
    return BOUNDARY_INPUT_ROOT / surface / "internal_arcadia_download_workflow_load.handoff.json"


def _real_xray_predecessor_path(surface: str) -> pathlib.Path:
    return BOUNDARY_INPUT_ROOT / surface / "internal_arcadia_agent_load_xray.xray.json"


def _copy_adp_boundary_packet(
    tmp_path: pathlib.Path,
) -> typing.Tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    sources = (
        _real_download_workflow_load_input_path("adp_v1"),
        _real_xray_predecessor_path("adp_v1"),
        BOUNDARY_GOLDENS_ROOT / "adp_v1" / "groundx_python_xray_reassembly.expected.json",
    )
    copies = []
    for source in sources:
        destination = tmp_path / source.name
        shutil.copyfile(source, destination)
        copies.append(destination)
    return copies[0], copies[1], copies[2]


def _build_xray_reassembly_boundary_artifact(
    tmp_path: pathlib.Path,
    surface: str,
) -> typing.Tuple[typing.Dict[str, typing.Any], pathlib.Path, pathlib.Path]:
    out_dir = tmp_path / surface
    previous_path = _real_download_workflow_load_input_path(surface)
    xray_path = _real_xray_predecessor_path(surface)
    previous = _read_json(previous_path)
    xray_envelope, xray_payload = read_exact_xray_predecessor(xray_path)
    xray_source = xray_envelope["source"]
    request = previous["request"]
    workflow_capture = request["workflow_capture"]
    assert xray_source["run_id"] == workflow_capture["run_id"]
    assert xray_source["process_id"] == request["task_id"]
    assert xray_source["document_id"] == request["document_id"]
    result = reassemble_custom_outputs_from_xray(
        xray_payload,
        workflow_extract=previous["workflow_extract"],
    )
    complete_output = _complete_reassembly_output(result)
    diagnostics = complete_output["diagnostics"]
    source_provenance = complete_output["source_provenance"]
    final_output = complete_output["final_output"]
    assertions = _xray_reassembly_shape_assertions(
        surface,
        final_output,
        diagnostics,
        result.relationship_output,
        workflow_extract=previous["workflow_extract"],
    )
    actual = {
        "schema_version": "groundx-python-xray-reassembly-boundary-v1",
        "surface": surface,
        "stage": "groundx_python_xray_reassembly",
        "input_from": "internal_arcadia_download_workflow_load",
        "output_for": "sdk_reassembly_proof",
        "workflow_schema_hash": _workflow_schema_hash(previous),
        "request": previous["request"],
        "input_sha256": _sha256_file(previous_path),
        **complete_output,
        "output": {
            "diagnostic_count": len(diagnostics),
            "final_output_sha256": _sha256_json(final_output),
            "relationship_output_sha256": _sha256_json(result.relationship_output),
            "source_provenance_count": len(source_provenance),
            "workflow_output_sha256": _sha256_json(result.workflow_output),
        },
        "shape_assertions": assertions,
        "artifacts": {
            "previous_download_workflow_load": {
                "path": str(previous_path),
                "sha256": _sha256_file(previous_path),
            },
            "xray_predecessor": {
                "path": str(xray_path),
                "sha256": _sha256_file(xray_path),
            },
        },
        "assertions": {
            "consumes_download_workflow_load_handoff": previous["stage"] == "internal_arcadia_download_workflow_load",
            "consumes_exact_xray_predecessor": xray_envelope["kind"] == "xray_predecessor",
            "has_no_error_diagnostics": assertions["has_no_error_diagnostics"],
            "shape_contract_passed": all(assertions.values()),
        },
    }
    expected_path = BOUNDARY_GOLDENS_ROOT / surface / "groundx_python_xray_reassembly.expected.json"
    diff_path = out_dir / "groundx_python_xray_reassembly.diff.json"
    return actual, expected_path, diff_path


def _write_xray_reassembly_boundary_artifact(
    tmp_path: pathlib.Path,
    surface: str,
) -> typing.Tuple[typing.Dict[str, typing.Any], pathlib.Path, pathlib.Path]:
    actual, expected_path, diff_path = _build_xray_reassembly_boundary_artifact(
        tmp_path,
        surface,
    )
    previous = _read_json(_real_download_workflow_load_input_path(surface))
    xray_path = _real_xray_predecessor_path(surface)

    assert actual["assertions"]["consumes_download_workflow_load_handoff"]
    assert actual["assertions"]["consumes_exact_xray_predecessor"]
    _assert_no_synthetic_protected_marker(previous)
    _assert_no_synthetic_protected_marker(_read_json(xray_path))
    _assert_no_synthetic_protected_marker(actual)
    return actual, expected_path, diff_path


def _workflow_schema_hash(previous: typing.Mapping[str, typing.Any]) -> str:
    value = previous.get("workflow_schema_hash")
    if isinstance(value, str) and value:
        return value
    workflow_identity = previous.get("workflow_identity")
    if isinstance(workflow_identity, typing.Mapping):
        value = workflow_identity.get("workflow_schema_hash")
        if isinstance(value, str) and value:
            return value
    raise KeyError("workflow_schema_hash")


def _assert_reviewed_expected_output_sidecar(packet_path: pathlib.Path) -> None:
    review_path = packet_path.with_name(packet_path.name.replace(".expected.json", ".expected.review.json"))
    diff_path = packet_path.with_name(packet_path.name.replace(".expected.json", ".expected.diff.json"))
    review = _read_json(review_path)
    catalog = _read_json(CATALOG_PATH)
    evidence = review["reviewed_expected_output"]
    assert re.fullmatch(r"[a-f0-9]{64}", evidence["artifact_catalog_sha256"])
    assert evidence["artifact_catalog_version"] == catalog["catalog_version"]
    assert evidence["packet_sha256"] == _sha256_file(packet_path)
    assert evidence["expected_sha256"] == _sha256_file(packet_path)
    assert _repo_evidence_path(evidence["expected_path"]) == packet_path.relative_to(ROOT)
    assert _repo_evidence_path(evidence["diff_path"]) == diff_path.relative_to(ROOT)
    assert evidence["diff_status"] == "passed"
    assert evidence["reviewer_identity"] != evidence["author_identity"]
    assert re.fullmatch(r"[a-f0-9]{64}", evidence["source_sha256"])
    if "source_path" in evidence:
        source_path = ROOT / _repo_evidence_path(evidence["source_path"])
        assert source_path.exists()
        assert evidence["source_sha256"] == _sha256_file(source_path)
    else:
        source_url = urllib.parse.urlsplit(evidence["source_url"])
        assert source_url.scheme == "https"
        assert not source_url.query
        assert not source_url.fragment
        assert source_url.path.endswith(f"/{evidence['source_hosted_path']}")
    diff = _read_json(diff_path)
    assert diff["status"] == "passed"
    assert diff["actual_sha256"] == _sha256_file(packet_path)
    assert diff["expected_sha256"] == _sha256_file(packet_path)
    assert isinstance(evidence["source_run_id"], str)
    assert evidence["source_run_id"]


def _repo_evidence_path(value: str) -> pathlib.Path:
    path = pathlib.Path(value)
    if path.parts and path.parts[0] in {ROOT.name, "groundx-python"}:
        return pathlib.Path(*path.parts[1:])
    return path


def _inherited_evidence(previous: typing.Mapping[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    if _has_projection_marker(previous):
        return {
            "evidence_level": "expected_answer_projection_diagnostic",
            "certification_eligible": False,
            "diagnostic_only_reason": ("Expected-answer projection fixture; not protected boundary evidence."),
        }

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
            assert not (key == "certification_eligible" and item is False), ".".join(child_path)
            _assert_no_synthetic_protected_marker(item, child_path)
        return

    if isinstance(value, str):
        for marker in (
            "_parent_",
            "_account_level",
            "deterministic_from_cashbot_deployed_output_routes",
            "plumbing_only_synthetic",
            "_fake_xray_for_workflow",
            "boundary://",
        ):
            assert marker not in value, ".".join(path)


def _has_projection_marker(value: typing.Any) -> bool:
    if isinstance(value, list):
        return any(_has_projection_marker(item) for item in value)
    if isinstance(value, dict):
        return any(_has_projection_marker(item) for item in value.values())
    return isinstance(value, str) and "reviewed_expected_answer_shape_stress_projection" in value


def _is_expected_answer_projection_diagnostic(
    value: typing.Mapping[str, typing.Any],
) -> bool:
    return value.get("evidence_level") == "expected_answer_projection_diagnostic"


def _assert_expected_answer_projection_diagnostic(
    value: typing.Mapping[str, typing.Any],
) -> None:
    assert value.get("evidence_level") == "expected_answer_projection_diagnostic"
    assert value.get("certification_eligible") is False


def _shape_assertions(
    surface: str,
    final_output: typing.Mapping[str, typing.Any],
    diagnostics: typing.Sequence[typing.Mapping[str, typing.Any]],
    relationship_output: typing.Any,
    *,
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]] = None,
) -> typing.Dict[str, bool]:
    assertions = {
        "has_no_error_diagnostics": not any(diagnostic.get("severity") == "error" for diagnostic in diagnostics)
    }
    if surface == "adp_v1":
        assertions.update(_adp_shape_assertions(final_output, workflow_extract or {}))
        return assertions

    parent_group, child_group, child_field = _utility_groups(
        surface,
        workflow_extract=workflow_extract,
    )
    parent_records = final_output.get(parent_group)
    account_children = final_output.get(child_group)
    assertions.update(
        {
            "has_expected_parent_count": isinstance(parent_records, list) and 7 <= len(parent_records) <= 9,
            "every_parent_has_child_rows": isinstance(parent_records, list)
            and all(
                isinstance(parent, dict) and isinstance(parent.get(child_field), list) and len(parent[child_field]) >= 1
                for parent in parent_records
            ),
            "has_expected_account_child_count": isinstance(account_children, list) and 0 <= len(account_children) <= 3,
            "has_expected_meter_charge_count": isinstance(parent_records, list)
            and 22 <= _nested_child_count(parent_records, child_field) <= 32,
            "has_statement_fields": _statement_field_count(
                surface,
                final_output,
                workflow_extract=workflow_extract,
                utility_groups=(parent_group, child_group, child_field),
            )
            >= 14,
            "has_relationship_output": bool(relationship_output),
        }
    )
    return assertions


def _xray_reassembly_shape_assertions(
    surface: str,
    final_output: typing.Mapping[str, typing.Any],
    diagnostics: typing.Sequence[typing.Mapping[str, typing.Any]],
    relationship_output: typing.Any,
    *,
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]] = None,
) -> typing.Dict[str, bool]:
    assertions = {
        "has_no_error_diagnostics": not any(diagnostic.get("severity") == "error" for diagnostic in diagnostics)
    }
    if surface == "adp_v1":
        assertions.update(_adp_xray_reassembly_shape_assertions(final_output, workflow_extract or {}))
        return assertions

    parent_group, child_group, child_field = _utility_groups(
        surface,
        workflow_extract=workflow_extract,
    )
    parent_records = final_output.get(parent_group)
    account_children = final_output.get(child_group)
    assertions.update(
        {
            "has_minimum_parent_candidates": isinstance(parent_records, list) and len(parent_records) >= 7,
            "has_account_child_candidates": isinstance(account_children, list),
            "has_minimum_total_child_candidates": isinstance(parent_records, list)
            and isinstance(account_children, list)
            and _nested_child_count(parent_records, child_field) + len(account_children) >= 22,
            "has_statement_fields": _statement_field_count(
                surface,
                final_output,
                workflow_extract=workflow_extract,
                utility_groups=(parent_group, child_group, child_field),
            )
            >= _minimum_xray_statement_fields(surface),
            "has_relationship_output": bool(relationship_output),
        }
    )
    return assertions


def _adp_xray_reassembly_shape_assertions(
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
        f"{section_name}.{field_name}" for section_name, fields in expected_sections.items() for field_name in fields
    }

    populated_field_count = 0
    ratio_failures: typing.List[str] = []
    for section_name, fields in expected_sections.items():
        section_value = final_output.get(section_name)
        if not isinstance(section_value, typing.Mapping):
            ratio_failures.append(section_name)
            continue
        ratio_fields = _adp_section_ratio_fields(fields)
        ratio_populated = 0
        for field_name in fields:
            if _has_extracted_value(section_value.get(field_name)):
                populated_field_count += 1
                if field_name in ratio_fields:
                    ratio_populated += 1
        ratio = ratio_populated / len(ratio_fields) if ratio_fields else 1.0
        if ratio < ADP_MIN_SECTION_POPULATED_RATIO:
            ratio_failures.append(section_name)

    null_or_blank_count = len(expected_fields) - populated_field_count
    return {
        "has_expected_adp_section_count": len(expected_sections) == ADP_EXPECTED_SECTION_COUNT
        and actual_sections == set(expected_sections),
        "has_expected_adp_workflow_field_count": len(expected_fields) == ADP_EXPECTED_FIELD_COUNT,
        "has_no_unexpected_adp_fields": actual_fields <= expected_fields,
        "has_adp_populated_fields_in_range": ADP_MIN_POPULATED_FIELDS
        <= populated_field_count
        <= ADP_MAX_POPULATED_FIELDS,
        "has_adp_null_fields_in_range": ADP_MIN_NULL_FIELDS <= null_or_blank_count <= ADP_MAX_NULL_FIELDS,
        "has_adp_core_fields_populated_by_section": not ratio_failures,
    }


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
        f"{section_name}.{field_name}" for section_name, fields in expected_sections.items() for field_name in fields
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
        "has_expected_adp_section_count": len(expected_sections) == ADP_EXPECTED_SECTION_COUNT
        and actual_sections == set(expected_sections),
        "has_expected_adp_field_count": len(expected_fields) == ADP_EXPECTED_FIELD_COUNT
        and actual_fields == expected_fields,
        "has_adp_populated_fields_in_range": ADP_MIN_POPULATED_FIELDS
        <= populated_field_count
        <= ADP_MAX_POPULATED_FIELDS,
        "has_adp_null_fields_in_range": ADP_MIN_NULL_FIELDS <= null_or_blank_count <= ADP_MAX_NULL_FIELDS,
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
    return tuple(field_name for field_name in fields if not field_name.endswith("_other_specify"))


def _has_extracted_value(value: typing.Any) -> bool:
    if isinstance(value, typing.Mapping) and "value" in value:
        return _has_extracted_value(value.get("value"))
    if value in (None, "", [], {}):
        return False
    return True


def _pointer_parts(pointer: str) -> typing.Tuple[str, ...]:
    if not pointer.startswith("/"):
        return ()
    return tuple(part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:] if part)


_MISSING = object()


def _workflow_definition(
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]],
) -> typing.Mapping[str, typing.Any]:
    if not isinstance(workflow_extract, typing.Mapping):
        return {}
    workflow = workflow_extract.get("workflow")
    if isinstance(workflow, typing.Mapping):
        return workflow
    persisted = workflow_extract.get("_groundx_persisted_extract")
    if isinstance(persisted, typing.Mapping):
        workflow = persisted.get("workflow")
        if isinstance(workflow, typing.Mapping):
            return workflow
    return workflow_extract


def _workflow_output_relationships(
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]],
) -> typing.Sequence[typing.Mapping[str, typing.Any]]:
    workflow = _workflow_definition(workflow_extract)
    relationships = workflow.get("output_relationships") or workflow.get("outputRelationships")
    if not isinstance(relationships, list):
        return ()
    return tuple(relationship for relationship in relationships if isinstance(relationship, typing.Mapping))


def _relationship_string(
    relationship: typing.Mapping[str, typing.Any],
    *keys: str,
) -> typing.Optional[str]:
    for key in keys:
        value = relationship.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _utility_groups(
    surface: str,
    *,
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]] = None,
) -> typing.Tuple[str, str, str]:
    for relationship in _workflow_output_relationships(workflow_extract):
        parent_group = _relationship_string(
            relationship,
            "parent_group",
            "parentGroup",
        )
        child_group = _relationship_string(
            relationship,
            "unmatched_child_group",
            "unmatchedChildGroup",
            "child_group",
            "childGroup",
        )
        child_field = _relationship_string(
            relationship,
            "parent_output_field",
            "parentOutputField",
            "child_group",
            "childGroup",
        )
        if parent_group and child_group and child_field:
            return parent_group, child_group, child_field

    if surface == "generic_v1":
        return "generic_group_b", "generic_group_c", "generic_group_c"
    return "meters", "charges", "charges"


def _statement_field_count(
    surface: str,
    final_output: typing.Mapping[str, typing.Any],
    *,
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    utility_groups: typing.Optional[typing.Tuple[str, str, str]] = None,
) -> int:
    workflow_count = _workflow_statement_field_count(
        final_output,
        workflow_extract,
        utility_groups,
    )
    if workflow_count is not None:
        return workflow_count
    if surface == "arcadia_legacy":
        statement = final_output.get("statement")
        return len(statement) if isinstance(statement, dict) else 0
    if surface == "generic_v1":
        return sum(1 for key in final_output if isinstance(key, str) and key.startswith("generic_attr_"))
    excluded = {"meters", "charges"}
    return sum(1 for key in final_output if key not in excluded)


def _workflow_statement_field_count(
    final_output: typing.Mapping[str, typing.Any],
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]],
    utility_groups: typing.Optional[typing.Tuple[str, str, str]],
) -> typing.Optional[int]:
    workflow = _workflow_definition(workflow_extract)
    routes = workflow.get("output_routes") or workflow.get("outputRoutes")
    if not isinstance(routes, list):
        return None
    excluded_groups = set(utility_groups[:2]) if utility_groups else set()
    count = 0
    seen: typing.Set[typing.Tuple[str, ...]] = set()
    for route in routes:
        if not isinstance(route, typing.Mapping):
            continue
        final_path = route.get("final_path")
        if not isinstance(final_path, str):
            continue
        parts = _pointer_parts(final_path)
        if not parts or parts[0] in excluded_groups:
            continue
        if parts in seen:
            continue
        if _value_at_path(final_output, parts) is not _MISSING:
            seen.add(parts)
            count += 1
    return count


def _value_at_path(
    value: typing.Mapping[str, typing.Any],
    parts: typing.Sequence[str],
) -> typing.Any:
    current: typing.Any = value
    for part in parts:
        if not isinstance(current, typing.Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return current


def _minimum_xray_statement_fields(surface: str) -> int:
    if surface == "arcadia_legacy":
        return 12
    if surface == "generic_v1":
        return 12
    return 14


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


def _complete_reassembly_output(result: typing.Any) -> typing.Dict[str, typing.Any]:
    return {
        "workflow_output": copy.deepcopy(result.workflow_output),
        "relationship_output": copy.deepcopy(result.relationship_output),
        "final_output": copy.deepcopy(result.final_output),
        "diagnostics": [
            {
                "child_record_index": diagnostic.child_record_index,
                "code": diagnostic.code,
                "final_path": diagnostic.final_path,
                "message": diagnostic.message,
                "relationship": diagnostic.relationship,
                "severity": diagnostic.severity,
                "workflow_field": diagnostic.workflow_field,
                "workflow_group": diagnostic.workflow_group,
            }
            for diagnostic in result.diagnostics
        ],
        "source_provenance": [
            {
                "final_path": provenance.final_path,
                "output_source": provenance.output_source,
                "page_numbers": list(provenance.page_numbers),
                "record_index": provenance.record_index,
                "workflow_field": provenance.workflow_field,
                "workflow_group": provenance.workflow_group,
            }
            for provenance in result.source_provenance
        ],
    }


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(data: typing.Any) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
