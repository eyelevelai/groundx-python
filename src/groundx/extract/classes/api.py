import typing
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    code: int
    document_id: str = Field(alias="documentID")
    message: str
    model_id: typing.Optional[int] = Field(alias="modelID", default=None)
    processor_id: typing.Optional[int] = Field(alias="processorID", default=None)
    task_id: str = Field(alias="taskID")


@dataclass
class ProcessResponse:
    message: str
