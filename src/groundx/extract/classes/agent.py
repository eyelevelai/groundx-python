import typing
from pydantic import BaseModel, field_validator

from .document import Document, DocumentRequest

ReqT = typing.TypeVar("ReqT", bound=DocumentRequest)
DocT = typing.TypeVar("DocT", bound=Document)


class AgentRequest(BaseModel, typing.Generic[ReqT, DocT]):
    allowed_request_types: typing.List[str] = []
    request: ReqT
    request_type: str
    statement: DocT

    @field_validator("request_type")
    def validate_request_type(cls, value: str):
        if value not in cls.allowed_request_types:
            raise ValueError(
                f"Invalid request_type '{value}'. Must be one of {cls.allowed_request_types}"
            )
        return value
