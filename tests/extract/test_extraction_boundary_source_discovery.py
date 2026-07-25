from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "src" / "groundx" / "extract" / "custom_outputs.py"
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


def _catalog() -> dict[str, object]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


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
