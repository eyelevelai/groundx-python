import typing

from ..classes.api import ErrorResponse
from ..classes.document import DocumentRequest
from ..classes.groundx import GroundXResponse


def error_response(req: DocumentRequest, msg: str) -> typing.Dict[str, typing.Any]:
    return fatal_error_response(
        document_id=req.document_id,
        task_id=req.task_id,
        message=msg,
        model_id=req.model_id,
        processor_id=req.processor_id,
    )


def fatal_error_response(
    *,
    document_id: str,
    task_id: str,
    message: str,
    code: int = 500,
    model_id: typing.Optional[int] = None,
    processor_id: typing.Optional[int] = None,
) -> typing.Dict[str, typing.Any]:
    return ErrorResponse(
        code=code,
        documentID=document_id,
        message=message,
        modelID=model_id,
        processorID=processor_id,
        taskID=task_id,
    ).model_dump(by_alias=True, exclude_none=True)


def success_response(
    req: DocumentRequest, result_url: str
) -> typing.Dict[str, typing.Any]:
    return GroundXResponse(
        code=200,
        documentID=req.document_id,
        modelID=req.model_id,
        processorID=req.processor_id,
        resultURL=result_url,
        taskID=req.task_id,
    ).model_dump(by_alias=True)
