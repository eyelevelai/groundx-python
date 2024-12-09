# This file was auto-generated by Fern from our API Definition.

from ..core.pydantic_utilities import UniversalBaseModel
import typing
import pydantic
from .document_detail import DocumentDetail
import typing_extensions
from ..core.serialization import FieldMetadata
from ..core.pydantic_utilities import IS_PYDANTIC_V2


class DocumentLookupResponse(UniversalBaseModel):
    count: typing.Optional[int] = pydantic.Field(default=None)
    """
    The number of results returned in the current response
    """

    documents: typing.Optional[typing.List[DocumentDetail]] = None
    next_token: typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="nextToken")] = None
    total: typing.Optional[int] = pydantic.Field(default=None)
    """
    The total number of results found
    """

    if IS_PYDANTIC_V2:
        model_config: typing.ClassVar[pydantic.ConfigDict] = pydantic.ConfigDict(extra="allow", frozen=True)  # type: ignore # Pydantic v2
    else:

        class Config:
            frozen = True
            smart_union = True
            extra = pydantic.Extra.allow