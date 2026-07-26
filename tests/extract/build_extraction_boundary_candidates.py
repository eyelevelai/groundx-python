from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import typing
from pathlib import Path

SURFACES = ("arcadia_legacy", "arcadia_v1", "generic_v1", "adp_v1")


def _read_json(path: Path) -> dict[str, typing.Any]:
    return typing.cast(dict[str, typing.Any], json.loads(path.read_text()))


def _write_json(path: Path, value: typing.Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_inside(root: Path, relative: str) -> Path:
    root = root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"candidate path escapes its root: {relative}") from error
    return path


def _changes(
    accepted: typing.Any,
    candidate: typing.Any,
    pointer: str = "",
) -> list[dict[str, typing.Any]]:
    if type(accepted) is not type(candidate):
        return [{"path": pointer or "/", "before": accepted, "after": candidate}]
    if isinstance(accepted, dict):
        result: list[dict[str, typing.Any]] = []
        for key in sorted(set(accepted) | set(candidate)):
            child = f"{pointer}/{key}"
            if key not in accepted:
                result.append({"path": child, "before": None, "after": candidate[key]})
            elif key not in candidate:
                result.append({"path": child, "before": accepted[key], "after": None})
            else:
                result.extend(_changes(accepted[key], candidate[key], child))
        return result
    if isinstance(accepted, list):
        if accepted == candidate:
            return []
        return [{"path": pointer or "/", "before": accepted, "after": candidate}]
    if accepted != candidate:
        return [{"path": pointer or "/", "before": accepted, "after": candidate}]
    return []


def _load_replay_module(repo_root: Path) -> typing.Any:
    path = repo_root / "tests" / "extract" / "test_extraction_boundary_reassembly.py"
    spec = importlib.util.spec_from_file_location("extraction_boundary_replay", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load boundary replay from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _selected_surfaces(value: str | None) -> tuple[str, ...]:
    if value is None:
        return SURFACES
    selected = tuple(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))
    invalid = sorted(set(selected) - set(SURFACES))
    if invalid:
        raise ValueError(f"unsupported surfaces: {', '.join(invalid)}")
    if not selected:
        raise ValueError("at least one surface is required")
    return selected


def _candidate_entry(
    *,
    surface: str,
    packet_path: Path,
    diff_path: Path,
    source: dict[str, typing.Any],
    sidecar_manifest: dict[str, typing.Any],
) -> dict[str, typing.Any]:
    relative_packet = (
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        f"boundary-goldens/{surface}/groundx_python_xray_reassembly.expected.json"
    )
    relative_diff = relative_packet.replace(".expected.json", ".expected.diff.json")
    relative_review = relative_packet.replace(".expected.json", ".expected.review.json")
    return {
        "surface": surface,
        "artifact_name": "groundx_python_xray_reassembly",
        "candidate_path": relative_packet,
        "proposed_fixture_path": relative_packet,
        "candidate_diff_path": relative_diff,
        "candidate_diff_sha256": _sha256(diff_path),
        "proposed_review_path": relative_review,
        "next_boundary_inputs": [],
        "seed_policy": "commit_sanitized_fixture",
        "sha256": _sha256(packet_path),
        "source_sha256": source["source_sha256"],
        "source_run_id": sidecar_manifest["run_id"],
        "source_run_mode": sidecar_manifest["run_mode"],
        "source_hosted_path": source["source_hosted_path"],
        "source_path": None,
        "source_boundary_manifest_sha256": sidecar_manifest["source_boundary_manifest_sha256"],
        "test_path": ("groundx-python/tests/extract/test_extraction_boundary_reassembly.py"),
    }


def build_candidates(
    *,
    repo_root: Path,
    xray_candidate_manifest_path: Path,
    candidate_root: Path,
    surfaces: tuple[str, ...],
) -> Path:
    if candidate_root.exists() and any(candidate_root.iterdir()):
        raise ValueError("candidate root must be empty")
    candidate_root.mkdir(parents=True, exist_ok=True)

    sidecar_manifest = _read_json(xray_candidate_manifest_path)
    if sidecar_manifest.get("schema_version") != "extraction_boundary_fixture_candidate_v1":
        raise ValueError("invalid X-Ray candidate manifest schema")
    if sidecar_manifest.get("status") != "pending_review":
        raise ValueError("X-Ray candidate manifest must be pending review")
    sidecar_root = xray_candidate_manifest_path.parent
    sidecars: dict[str, dict[str, typing.Any]] = {}
    for entry in sidecar_manifest["candidates"]:
        if entry["artifact_name"] != "groundx_python_xray_reassembly_xray_sidecar":
            continue
        surface = entry["surface"]
        if surface in sidecars:
            raise ValueError(f"duplicate X-Ray candidate for {surface}")
        sidecar_path = _resolve_inside(sidecar_root, entry["candidate_path"])
        if not sidecar_path.exists() or _sha256(sidecar_path) != entry["sha256"]:
            raise ValueError(f"X-Ray candidate hash does not match for {surface}")
        sidecars[surface] = entry
    missing = sorted(set(surfaces) - set(sidecars))
    if missing:
        raise ValueError(f"X-Ray candidates missing surfaces: {', '.join(missing)}")

    replay = _load_replay_module(repo_root)
    replay._real_xray_sidecar_path = lambda surface: _resolve_inside(sidecar_root, sidecars[surface]["candidate_path"])
    candidates = []
    for surface in surfaces:
        actual, accepted_path, _unused_diff_path = replay._write_xray_reassembly_boundary_artifact(
            candidate_root, surface
        )
        packet = replay._stable_boundary_output(actual)
        relative_packet = Path(
            "groundx-python/tests/extract/fixtures/extraction-boundary/"
            f"boundary-goldens/{surface}/groundx_python_xray_reassembly.expected.json"
        )
        packet_path = candidate_root / relative_packet
        _write_json(packet_path, packet)

        accepted = _read_json(accepted_path)
        diff_path = packet_path.with_name("groundx_python_xray_reassembly.expected.diff.json")
        _write_json(
            diff_path,
            {
                "kind": "machine_readable_json_diff",
                "status": "pending_review",
                "artifact_name": "groundx_python_xray_reassembly",
                "candidate_sha256": _sha256(packet_path),
                "current_accepted_sha256": _sha256(accepted_path),
                "source_artifact_sha256": sidecars[surface]["source_sha256"],
                "source_run_id": sidecar_manifest["run_id"],
                "changes": _changes(accepted, packet),
            },
        )
        candidates.append(
            _candidate_entry(
                surface=surface,
                packet_path=packet_path,
                diff_path=diff_path,
                source=sidecars[surface],
                sidecar_manifest=sidecar_manifest,
            )
        )

    manifest_path = candidate_root / "fixture_candidate_manifest.json"
    _write_json(
        manifest_path,
        {
            "schema_version": "extraction_boundary_fixture_candidate_v1",
            "status": "pending_review",
            "run_id": sidecar_manifest["run_id"],
            "run_mode": sidecar_manifest["run_mode"],
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "artifact_catalog_version": sidecar_manifest["artifact_catalog_version"],
            "artifact_catalog_sha256": sidecar_manifest["artifact_catalog_sha256"],
            "source_boundary_manifest_sha256": sidecar_manifest["source_boundary_manifest_sha256"],
            "upstream_candidate_manifest_sha256": _sha256(xray_candidate_manifest_path),
            "generator": {
                "candidate_builder_sha256": _sha256(Path(__file__)),
                "boundary_replay_sha256": _sha256(
                    repo_root / "tests" / "extract" / "test_extraction_boundary_reassembly.py"
                ),
                "production_reassembly_sha256": _sha256(
                    repo_root / "src" / "groundx" / "extract" / "custom_outputs.py"
                ),
            },
            "candidates": candidates,
            "private_references": [],
        },
    )
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xray-candidate-manifest", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--surfaces")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    try:
        manifest_path = build_candidates(
            repo_root=repo_root,
            xray_candidate_manifest_path=args.xray_candidate_manifest.resolve(),
            candidate_root=args.candidate_root.resolve(),
            surfaces=_selected_surfaces(args.surfaces),
        )
    except (KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(manifest_path)


if __name__ == "__main__":
    main()
