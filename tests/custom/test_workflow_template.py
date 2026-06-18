import json
import typing

import httpx

from groundx import GroundX, WorkflowStep, WorkflowSteps
from groundx.types import WorkflowDetail, WorkflowRequest


def _model_fields(model: typing.Type[typing.Any]) -> typing.Mapping[str, typing.Any]:
    fields = getattr(model, "model_fields", None)
    if fields is None:
        fields = getattr(model, "__fields__", {})
    return typing.cast(typing.Mapping[str, typing.Any], fields)


def _request_json(request: httpx.Request) -> typing.Dict[str, typing.Any]:
    return typing.cast(typing.Dict[str, typing.Any], json.loads(request.content.decode()))


def test_workflow_create_serializes_template() -> None:
    captured: typing.List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "workflow": {
                    "workflowId": "workflow-1",
                    "template": {"statement_hint": "Prefer normalized values."},
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as httpx_client:
        client = GroundX(api_key="test-key", base_url="https://api.test", httpx_client=httpx_client)
        response = client.workflows.create(
            name="statement extraction",
            extract={"statement": {"fields": {}}},
            template={"statement_hint": "Prefer normalized values."},
        )

    assert response.workflow.template == {"statement_hint": "Prefer normalized values."}
    assert len(captured) == 1
    assert captured[0].method == "POST"
    assert captured[0].url.path == "/v1/workflow"
    assert _request_json(captured[0])["template"] == {"statement_hint": "Prefer normalized values."}


def test_workflow_update_serializes_template() -> None:
    captured: typing.List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "workflow": {
                    "workflowId": "workflow-1",
                    "template": {"statement_hint": "Prefer account summary values."},
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as httpx_client:
        client = GroundX(api_key="test-key", base_url="https://api.test", httpx_client=httpx_client)
        response = client.workflows.update(
            "workflow-1",
            template={"statement_hint": "Prefer account summary values."},
        )

    assert response.workflow.template == {"statement_hint": "Prefer account summary values."}
    assert len(captured) == 1
    assert captured[0].method == "PUT"
    assert captured[0].url.path == "/v1/workflow/workflow-1"
    assert _request_json(captured[0]) == {
        "template": {"statement_hint": "Prefer account summary values."}
    }


def test_workflow_update_preserves_explicit_null_step_configs() -> None:
    captured: typing.List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "workflow": {
                    "workflowId": "workflow-1",
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as httpx_client:
        client = GroundX(api_key="test-key", base_url="https://api.test", httpx_client=httpx_client)
        client.workflows.update(
            "workflow-1",
            steps=WorkflowSteps(
                chunk_instruct=WorkflowStep(
                    figure=None,
                    table_figure=None,
                ),
            ),
        )

    assert len(captured) == 1
    assert captured[0].method == "PUT"
    assert captured[0].url.path == "/v1/workflow/workflow-1"
    assert _request_json(captured[0]) == {
        "steps": {
            "chunk-instruct": {
                "figure": None,
                "table-figure": None,
            }
        }
    }


def test_workflow_template_is_declared_on_generated_models() -> None:
    assert "template" in _model_fields(WorkflowRequest)
    assert "template" in _model_fields(WorkflowDetail)

    detail = WorkflowDetail(template={"statement_hint": "Prefer normalized values."})

    assert detail.template == {"statement_hint": "Prefer normalized values."}
