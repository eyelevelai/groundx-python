"""
Tests for the WorkflowTemplate type and the template field on WorkflowRequest/WorkflowDetail.

These are hand-written tests (tests/custom/) that verify the SDK surfaces introduced by
the AGE-149 change: WorkflowTemplate type alias, template on WorkflowRequest/WorkflowDetail,
and backward-compatibility (tolerant reader, optional field).
"""
import typing

import pytest

from groundx.types import WorkflowDetail, WorkflowRequest, WorkflowResponse, WorkflowTemplate


# ---------------------------------------------------------------------------
# Task 2.1 – WorkflowTemplate is importable and has the correct type
# ---------------------------------------------------------------------------


def test_workflow_template_importable() -> None:
    """WorkflowTemplate is importable from groundx.types and equals Dict[str, str]."""
    assert WorkflowTemplate == typing.Dict[str, str]


# ---------------------------------------------------------------------------
# Task 2.2 – WorkflowRequest serializes template into JSON body
# ---------------------------------------------------------------------------


def test_workflow_request_template_serializes() -> None:
    """WorkflowRequest(template={...}) includes template at the top level of model_dump."""
    req = WorkflowRequest(template={"lang": "en"})
    dumped = req.model_dump(exclude_none=True, by_alias=True)
    assert "template" in dumped
    assert dumped["template"] == {"lang": "en"}


# ---------------------------------------------------------------------------
# Task 2.3 – WorkflowRequest without template serializes without the key
# ---------------------------------------------------------------------------


def test_workflow_request_no_template_absent() -> None:
    """WorkflowRequest() without template results in template absent from dump."""
    req = WorkflowRequest()
    dumped = req.model_dump(exclude_none=True, by_alias=True)
    assert "template" not in dumped


# ---------------------------------------------------------------------------
# Task 2.4 – WorkflowRequest(template=None) serializes without the key
# ---------------------------------------------------------------------------


def test_workflow_request_template_none_absent() -> None:
    """WorkflowRequest(template=None) results in template absent from dump (exclude_none)."""
    req = WorkflowRequest(template=None)
    dumped = req.model_dump(exclude_none=True, by_alias=True)
    assert "template" not in dumped


# ---------------------------------------------------------------------------
# Task 2.5 – WorkflowDetail deserialization with template present
# ---------------------------------------------------------------------------


def test_workflow_detail_template_present() -> None:
    """WorkflowDetail from a response dict containing 'template' yields the correct mapping."""
    detail = WorkflowDetail.model_validate({"template": {"prompt_lang": "en"}})
    assert detail.template == {"prompt_lang": "en"}


# ---------------------------------------------------------------------------
# Task 2.6 – WorkflowDetail deserialization without template yields None
# ---------------------------------------------------------------------------


def test_workflow_detail_template_absent_is_none() -> None:
    """WorkflowDetail deserialization without 'template' yields template=None, no AttributeError."""
    detail = WorkflowDetail.model_validate({})
    assert detail.template is None


# ---------------------------------------------------------------------------
# Task 2.7 – WorkflowDetail is a tolerant reader (extra="allow")
# ---------------------------------------------------------------------------


def test_workflow_detail_tolerant_reader() -> None:
    """WorkflowDetail deserialization succeeds when response contains an unknown future field."""
    detail = WorkflowDetail.model_validate({"unknown_future_field": "some_value"})
    # No exception raised; template is None since it was not in the payload
    assert detail.template is None


# ---------------------------------------------------------------------------
# Task 2.8 – WorkflowResponse.workflow.template from update response path
# ---------------------------------------------------------------------------


def test_workflow_response_update_template() -> None:
    """WorkflowResponse deserialization from an update response surfaces template correctly."""
    response = WorkflowResponse.model_validate(
        {"workflow": {"template": {"tone": "formal"}}}
    )
    assert response.workflow.template == {"tone": "formal"}
