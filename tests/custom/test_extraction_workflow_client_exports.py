import builtins
import importlib
import inspect
import json
import os
import subprocess
import sys
import typing

import httpx
import pytest

from groundx import GroundX

CUSTOM_WORKFLOW_YAML = """
workflow:
  template:
    "{{LANGUAGE}}": English
    "{{LANGUAGE_UNKNOWN}}": ""
  custom_steps:
    - name: line_item_labels
      level: chunk
      kind: keys
      required_template_keys:
        - "{{LANGUAGE}}"

line_items:
  workflow_step: line_item_labels
  fields:
    description:
      workflow_output_key: label
      prompt:
        instructions: Return the printed line-item description.
        type: str
"""


def _request_json(request: httpx.Request) -> typing.Dict[str, typing.Any]:
    return typing.cast(typing.Dict[str, typing.Any], json.loads(request.content.decode()))


def test_extraction_definition_is_exported_from_extract_module() -> None:
    from groundx.extract import ExtractionDefinition

    assert ExtractionDefinition.__name__ == "ExtractionDefinition"


def test_extraction_workflow_helpers_have_method_level_docstrings() -> None:
    for method_name in (
        "load_extraction_definition",
        "load_extraction_definition_from_yaml",
        "load_extraction_definition_from_workflow",
        "create_extraction_workflow",
        "update_extraction_workflow",
    ):
        doc = inspect.getdoc(getattr(GroundX, method_name))
        assert doc is not None
        assert "Parameters" in doc, method_name
        assert "Returns" in doc, method_name
        assert "Examples" in doc, method_name

    update_doc = inspect.getdoc(GroundX.update_extraction_workflow)
    assert update_doc is not None
    assert "full extraction workflow settings" in update_doc


def test_base_groundx_import_does_not_import_extract_optional_dependencies() -> None:
    code = """
import builtins

optional_roots = {
    "boto3",
    "celery",
    "dateparser",
    "fastapi",
    "google",
    "gspread",
    "minio",
    "openai",
    "PIL",
    "redis",
    "smolagents",
    "yaml",
}
real_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".", 1)[0]
    if name.startswith("groundx.extract") or root in optional_roots:
        raise AssertionError(f"unexpected optional import: {name}")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import
import groundx
from groundx import AsyncGroundX, GroundX
assert GroundX.__name__ == "GroundX"
assert AsyncGroundX.__name__ == "AsyncGroundX"
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, ["src", env.get("PYTHONPATH", "")]))

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=os.getcwd(),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_extraction_methods_raise_install_hint_when_extract_extra_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = builtins.__import__
    extract_package = importlib.import_module("groundx.extract")

    def guarded_import(
        name: str,
        globals: typing.Optional[typing.Dict[str, typing.Any]] = None,
        locals: typing.Optional[typing.Dict[str, typing.Any]] = None,
        fromlist: typing.Sequence[str] = (),
        level: int = 0,
    ) -> typing.Any:
        if name.startswith("groundx.extract") or (level > 0 and name == "extract"):
            raise ImportError("simulated missing extract extra")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.delitem(sys.modules, "groundx.extract.workflows", raising=False)
    monkeypatch.delattr(extract_package, "workflows", raising=False)
    client = GroundX.__new__(GroundX)

    with pytest.raises(ImportError, match=r"pip install groundx\[extract\]"):
        client.load_extraction_definition_from_yaml(yaml_text=CUSTOM_WORKFLOW_YAML)


def test_create_extraction_workflow_gates_custom_steps_until_generated_client_release() -> None:
    captured: typing.List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "workflow": {
                    "workflowId": "workflow-1",
                    "name": "statement extraction",
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as httpx_client:
        client = GroundX(
            api_key="test-key",
            base_url="https://api.test",
            httpx_client=httpx_client,
        )
        with pytest.raises(RuntimeError, match="Regenerate and publish"):
            client.create_extraction_workflow(
                yaml_text=CUSTOM_WORKFLOW_YAML,
                name="statement extraction",
            )

    assert captured == []
