from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    code: int
    document_id: str = Field(alias="documentID")
    message: str
    task_id: str = Field(alias="taskID")


@dataclass
class ProcessResponse:
    message: str
