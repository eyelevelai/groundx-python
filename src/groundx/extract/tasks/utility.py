import typing

from ..classes.api import ErrorResponse
from ..classes.document import DocumentRequest
from ..classes.groundx import GroundXResponse


def error_response(req: DocumentRequest, msg: str) -> typing.Dict[str, typing.Any]:
    return ErrorResponse(
        code=500,
        documentID=req.document_id,
        message=msg,
        taskID=req.task_id,
    ).model_dump(by_alias=True)


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
