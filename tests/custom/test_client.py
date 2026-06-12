import typing

from groundx.types import (
    WorkflowDetail,
    WorkflowRequest,
    WorkflowStep,
    WorkflowStepConfig,
    WorkflowSteps,
)


def test_workflow_request_serializes_template_and_custom_steps() -> None:
    from groundx.types import (
        CustomWorkflowLeafField,
        CustomWorkflowOutputRoute,
        CustomWorkflowStep,
        CustomWorkflowStepConfig,
        CustomWorkflowStepElementConfig,
    )

    request = WorkflowRequest(
        name="line item workflow",
        template={
            "CUSTOM_WORKFLOW_GROUP": "line_items",
            "CUSTOM_WORKFLOW_FIELD": "description",
            "CUSTOM_WORKFLOW_OUTPUT_KEY": "label",
        },
        steps=WorkflowSteps(
            chunk_keys=WorkflowStep(
                all_=WorkflowStepConfig(includes={"text": True}),
            )
        ),
        custom_steps=[
            CustomWorkflowStep(
                name="line_item_labels",
                level="chunk",
                kind="keys",
                required_template_keys=["CUSTOM_WORKFLOW_GROUP"],
                config=CustomWorkflowStepConfig(
                    all_=CustomWorkflowStepElementConfig(
                        includes={"text": True},
                    )
                ),
            )
        ],
        output_routes=[
            CustomWorkflowOutputRoute(
                workflow_group="line_items",
                workflow_field="description",
                final_path="/line_items/*/description",
                step_name="line_item_labels",
                level="chunk",
                output_map="customChunkOutputs",
                output_key="label",
                readback_path="/chunks/*/customChunkOutputs/line_item_labels/label",
            )
        ],
        leaf_fields=[
            CustomWorkflowLeafField(
                final_path="/line_items/*/description",
                workflow_group="line_items",
                workflow_field="description",
                step_name="line_item_labels",
                level="chunk",
                output_key="label",
                field_type="str",
                is_repeated=True,
                repetition_scope="/line_items/*",
            )
        ],
    )

    payload = request.model_dump(by_alias=True, exclude_none=True)

    assert payload["template"]["CUSTOM_WORKFLOW_GROUP"] == "line_items"
    assert payload["steps"]["chunk-keys"]["all"]["includes"] == {"text": True}
    assert payload["customSteps"][0]["name"] == "line_item_labels"
    assert payload["customSteps"][0]["requiredTemplateKeys"] == [
        "CUSTOM_WORKFLOW_GROUP"
    ]
    assert payload["customSteps"][0]["config"]["all"]["includes"] == {"text": True}
    assert "field" not in payload["customSteps"][0]["config"]["all"]
    assert payload["outputRoutes"][0]["readbackPath"] == (
        "/chunks/*/customChunkOutputs/line_item_labels/label"
    )
    assert payload["leafFields"][0]["repetitionScope"] == "/line_items/*"


def test_workflow_detail_deserializes_custom_routes_and_outputs() -> None:
    from groundx.types import (
        CustomWorkflowLeafField,
        CustomWorkflowOutputRoute,
        CustomWorkflowStep,
    )

    payload: typing.Dict[str, typing.Any] = {
        "workflowId": "9c79a6d3-65ac-4108-83cf-572cc7b6dbd8",
        "name": "line item workflow",
        "extract": {"line_items": {"fields": {}}},
        "template": {"CUSTOM_WORKFLOW_GROUP": "line_items"},
        "customSteps": [
            {
                "name": "line_item_labels",
                "level": "chunk",
                "kind": "keys",
                "requiredTemplateKeys": ["CUSTOM_WORKFLOW_GROUP"],
            }
        ],
        "outputRoutes": [
            {
                "workflowGroup": "line_items",
                "workflowField": "description",
                "finalPath": "/line_items/*/description",
                "stepName": "line_item_labels",
                "level": "chunk",
                "outputMap": "customChunkOutputs",
                "outputKey": "label",
                "readbackPath": "/chunks/*/customChunkOutputs/line_item_labels/label",
            }
        ],
        "leafFields": [
            {
                "finalPath": "/line_items/*/description",
                "workflowGroup": "line_items",
                "workflowField": "description",
                "stepName": "line_item_labels",
                "level": "chunk",
                "outputKey": "label",
                "fieldType": "str",
                "isRepeated": True,
                "repetitionScope": "/line_items/*",
            }
        ],
        "steps": {
            "chunk-keys": {
                "all": {
                    "includes": {"text": True},
                }
            }
        },
    }

    detail = WorkflowDetail.model_validate(payload)

    assert isinstance(detail.custom_steps[0], CustomWorkflowStep)
    assert isinstance(detail.output_routes[0], CustomWorkflowOutputRoute)
    assert isinstance(detail.leaf_fields[0], CustomWorkflowLeafField)
    assert detail.custom_steps[0].name == "line_item_labels"
    assert detail.output_routes[0].readback_path == (
        "/chunks/*/customChunkOutputs/line_item_labels/label"
    )
    assert detail.leaf_fields[0].repetition_scope == "/line_items/*"
    assert detail.steps is not None
    assert detail.steps.chunk_keys is not None
