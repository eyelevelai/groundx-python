from __future__ import annotations

import ast
import json
from pathlib import Path
import typing

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "src" / "groundx" / "extract" / "custom_outputs.py"
REPLAY_PATH = ROOT / "tests" / "extract" / "test_extraction_boundary_reassembly.py"
CATALOG_PATH = (
    ROOT
    / "tests"
    / "extract"
    / "fixtures"
    / "extraction-boundary"
    / "writer_registry.json"
)


def _qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        owner = _qualified_name(node.value)
        return f"{owner}.{node.attr}" if owner else node.attr
    return ""


def _discover(source: str) -> dict[str, list[str]]:
    tree = ast.parse(source, filename=str(SOURCE_PATH.relative_to(ROOT)))
    definitions: list[str] = []
    calls: list[str] = []
    scope: list[str] = []
    ordinals: dict[tuple[str, str], int] = {}

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            scope.append(node.name)
            if node.name == "reassemble_custom_outputs_from_xray":
                definitions.append(
                    "src/groundx/extract/custom_outputs.py:"
                    "reassemble_custom_outputs_from_xray"
                )
            self.generic_visit(node)
            scope.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            scope.append(node.name)
            self.generic_visit(node)
            scope.pop()

        def visit_Call(self, node: ast.Call) -> None:
            call_name = _qualified_name(node.func)
            if call_name.rsplit(".", 1)[-1] == "reassemble_custom_outputs_from_xray":
                function = ".".join(scope)
                ordinal_key = (function, call_name)
                ordinal = ordinals.get(ordinal_key, 0) + 1
                ordinals[ordinal_key] = ordinal
                calls.append(
                    "src/groundx/extract/custom_outputs.py:"
                    f"{function}:reassemble_custom_outputs_from_xray:{ordinal}"
                )
            self.generic_visit(node)

    Visitor().visit(tree)
    return {
        "definitions": sorted(definitions),
        "calls": sorted(calls),
    }


def _catalog() -> dict[str, typing.Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _production_call_graph(source: str) -> dict[str, set[str]]:
    tree = ast.parse(source, filename=str(SOURCE_PATH.relative_to(ROOT)))
    calls: dict[str, set[str]] = {}
    scope: list[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            scope.append(node.name)
            calls.setdefault(node.name, set())
            self.generic_visit(node)
            scope.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            scope.append(node.name)
            calls.setdefault(node.name, set())
            self.generic_visit(node)
            scope.pop()

        def visit_Call(self, node: ast.Call) -> None:
            if scope:
                name = _qualified_name(node.func).rsplit(".", 1)[-1]
                if name:
                    calls.setdefault(scope[-1], set()).add(name)
            self.generic_visit(node)

    Visitor().visit(tree)
    return calls


def _production_module_symbols(source: str) -> set[str]:
    tree = ast.parse(source, filename=str(SOURCE_PATH.relative_to(ROOT)))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _reachable_symbols(call_graph: dict[str, set[str]], entrypoint: str) -> set[str]:
    reachable = {entrypoint}
    pending = [entrypoint]
    while pending:
        caller = pending.pop()
        for callee in call_graph.get(caller, set()):
            if callee in reachable:
                continue
            reachable.add(callee)
            if callee in call_graph:
                pending.append(callee)
    return reachable


def _replay_policy_violations(
    source: str,
    policy: dict[str, typing.Any],
) -> list[str]:
    tree = ast.parse(source, filename=str(REPLAY_PATH.relative_to(ROOT)))
    protected = {
        item["symbol"].rsplit(".", 1)[-1]
        for item in policy["protected_production_symbols"]
    }
    production_symbols = _production_module_symbols(
        SOURCE_PATH.read_text(encoding="utf-8")
    )
    required_callers = set(policy["required_replay_callers"])
    production_entrypoint = next(
        item["symbol"].rsplit(".", 1)[-1]
        for item in policy["protected_production_symbols"]
        if item["role"] == "reassembly"
    )
    callers: dict[str, set[str]] = {}
    violations: list[str] = []
    scope: list[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node.name in protected:
                violations.append(f"replay defines protected symbol {node.name}")
            scope.append(node.name)
            callers.setdefault(node.name, set())
            self.generic_visit(node)
            scope.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            if node.name in protected:
                violations.append(f"replay defines protected symbol {node.name}")
            scope.append(node.name)
            callers.setdefault(node.name, set())
            self.generic_visit(node)
            scope.pop()

        def visit_Assign(self, node: ast.Assign) -> None:
            rebound: set[str] = set()
            for target in node.targets:
                if isinstance(target, ast.Name):
                    rebound.add(target.id)
                elif isinstance(target, ast.Attribute):
                    rebound.add(target.attr)
            for name in sorted(rebound & production_symbols):
                violations.append(f"replay rebinds protected symbol {name}")
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            call_name = _qualified_name(node.func)
            short_name = call_name.rsplit(".", 1)[-1]
            if scope and short_name:
                callers.setdefault(scope[-1], set()).add(short_name)
            if short_name in {
                "delattr",
                "delitem",
                "patch",
                "setattr",
                "setitem",
            } or call_name.endswith("patch.object"):
                rendered = ast.unparse(node)
                for name in sorted(production_symbols):
                    if name in rendered:
                        violations.append(f"replay patches protected symbol {name}")
            self.generic_visit(node)

    Visitor().visit(tree)
    for caller in sorted(required_callers):
        if production_entrypoint not in callers.get(caller, set()):
            violations.append(
                f"{caller} does not call production {production_entrypoint}"
            )
    return violations


def test_reassembly_boundary_declarations_match_production_source() -> None:
    catalog = _catalog()
    discovery = catalog["source_discovery"]
    assert isinstance(discovery, dict)

    actual = _discover(SOURCE_PATH.read_text(encoding="utf-8"))

    assert sorted(actual["definitions"] + actual["calls"]) == sorted(
        discovery["production_boundaries"]
    )
    assert {
        stage
        for rule in discovery["rules"]
        for stage in rule["catalog_stages"]
    } == {"sdk_xray_reassembly"}


def test_source_discovery_rejects_an_undeclared_reassembly_call() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    source += (
        "\n\ndef source_discovery_extra_reassembly(xray):\n"
        "    return reassemble_custom_outputs_from_xray(xray)\n"
    )

    actual = _discover(source)
    declared = _catalog()["source_discovery"]
    assert isinstance(declared, dict)

    assert (
        "src/groundx/extract/custom_outputs.py:"
        "source_discovery_extra_reassembly:"
        "reassemble_custom_outputs_from_xray:1"
    ) in actual["calls"]
    assert (
        sorted(actual["definitions"] + actual["calls"])
        != sorted(declared["production_boundaries"])
    )


def test_boundary_replay_declares_its_mock_policy() -> None:
    policy = _catalog()["replay_mock_policy"]

    assert policy == {
        "allowed_external_io_seams": [],
        "certifying_replay_files": [
            "tests/extract/test_extraction_boundary_reassembly.py",
        ],
        "required_replay_callers": [
            "_build_xray_reassembly_boundary_artifact",
            "_write_boundary_artifacts",
        ],
        "protected_production_symbols": [
            {
                "role": "parser",
                "symbol": "groundx.extract.custom_outputs._get",
            },
            {
                "role": "reassembly",
                "symbol": (
                    "groundx.extract.custom_outputs."
                    "reassemble_custom_outputs_from_xray"
                ),
            },
            {
                "role": "result_builder",
                "symbol": (
                    "groundx.extract.custom_outputs.CustomOutputReassemblyResult"
                ),
            },
        ],
    }


def test_certifying_replay_runs_the_protected_production_path() -> None:
    policy = _catalog()["replay_mock_policy"]
    replay_source = REPLAY_PATH.read_text(encoding="utf-8")
    production_source = SOURCE_PATH.read_text(encoding="utf-8")
    protected = {
        item["symbol"].rsplit(".", 1)[-1]
        for item in policy["protected_production_symbols"]
    }
    reachable = _reachable_symbols(
        _production_call_graph(production_source),
        "reassemble_custom_outputs_from_xray",
    )

    assert _replay_policy_violations(replay_source, policy) == []
    assert protected <= reachable


@pytest.mark.parametrize(
    ("mutation", "expected_violation"),
    [
        (
            lambda source: source.replace(
                "result = reassemble_custom_outputs_from_xray(",
                "result = dict(",
                1,
            ),
            "_write_boundary_artifacts does not call production",
        ),
        (
            lambda source: source
            + "\n\ndef bypass(monkeypatch, custom_outputs):\n"
            + '    monkeypatch.setattr(custom_outputs, "_apply_relationships", '
            + "lambda *_args: {})\n",
            "replay patches protected symbol",
        ),
        (
            lambda source: source
            + "\n\ndef reassemble_custom_outputs_from_xray(*_args, **_kwargs):\n"
            + "    return {}\n",
            "replay defines protected symbol",
        ),
        (
            lambda source: source
            + "\n\ndef bypass(custom_outputs):\n"
            + "    custom_outputs._get = lambda *_args: None\n",
            "replay rebinds protected symbol",
        ),
    ],
)
def test_replay_policy_rejects_production_path_bypasses(
    mutation,
    expected_violation: str,
) -> None:
    policy = _catalog()["replay_mock_policy"]
    violations = _replay_policy_violations(
        mutation(REPLAY_PATH.read_text(encoding="utf-8")),
        policy,
    )

    assert any(expected_violation in violation for violation in violations)


@pytest.mark.parametrize(
    ("role", "mutation"),
    [
        ("parser", lambda source: source.replace("_get(", "_bypassed_get(")),
        (
            "result_builder",
            lambda source: source.replace("CustomOutputReassemblyResult(", "dict("),
        ),
    ],
)
def test_production_path_guard_rejects_skipped_symbol(role, mutation) -> None:
    policy = _catalog()["replay_mock_policy"]
    reachable = _reachable_symbols(
        _production_call_graph(
            mutation(SOURCE_PATH.read_text(encoding="utf-8")),
        ),
        "reassemble_custom_outputs_from_xray",
    )
    protected = next(
        item["symbol"].rsplit(".", 1)[-1]
        for item in policy["protected_production_symbols"]
        if item["role"] == role
    )

    assert protected not in reachable
