import typing

from groundx.extract.tasks import error_response, fatal_error_response


class _Request:
    document_id = "document-1"
    model_id = 10
    processor_id = 20
    task_id = "task-1"


def test_fatal_error_response_builds_minimal_callback_body() -> None:
    assert fatal_error_response(
        document_id="document-1",
        task_id="task-1",
        message="failed before request hydration",
    ) == {
        "code": 500,
        "documentID": "document-1",
        "message": "failed before request hydration",
        "taskID": "task-1",
    }


def test_error_response_preserves_optional_processor_identity() -> None:
    assert error_response(typing.cast(typing.Any, _Request()), "failed") == {
        "code": 500,
        "documentID": "document-1",
        "message": "failed",
        "modelID": 10,
        "processorID": 20,
        "taskID": "task-1",
    }
