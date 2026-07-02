from groundx.extract.classes.document import DocumentRequest
from groundx.extract.tasks import error_response, fatal_error_response


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
    req = DocumentRequest.model_validate(
        {
            "documentID": "document-1",
            "fileName": "statement.pdf",
            "modelID": 10,
            "processorID": 20,
            "taskID": "task-1",
        }
    )

    assert error_response(req, "failed") == {
        "code": 500,
        "documentID": "document-1",
        "message": "failed",
        "modelID": 10,
        "processorID": 20,
        "taskID": "task-1",
    }
