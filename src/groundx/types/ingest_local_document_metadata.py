# This file was auto-generated by Fern from our API Definition.

from ..core.pydantic_utilities import UniversalBaseModel
import typing_extensions
import typing
from ..core.serialization import FieldMetadata
import pydantic
from .document_type import DocumentType
from .process_level import ProcessLevel
from ..core.pydantic_utilities import IS_PYDANTIC_V2


class IngestLocalDocumentMetadata(UniversalBaseModel):
    bucket_id: typing_extensions.Annotated[typing.Optional[int], FieldMetadata(alias="bucketId")] = pydantic.Field(
        default=None
    )
    """
    The bucketId of the bucket which this local file will be ingested into.
    """

    file_name: typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="fileName")] = pydantic.Field(
        default=None
    )
    """
    The name of the file being ingested
    """

    file_type: typing_extensions.Annotated[typing.Optional[DocumentType], FieldMetadata(alias="fileType")] = None
    process_level: typing_extensions.Annotated[typing.Optional[ProcessLevel], FieldMetadata(alias="processLevel")] = (
        None
    )
    search_data: typing_extensions.Annotated[
        typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]], FieldMetadata(alias="searchData")
    ] = pydantic.Field(default=None)
    """
    Custom metadata which can be used to influence GroundX's search functionality. This data can be used to further hone GroundX search.
    """

    if IS_PYDANTIC_V2:
        model_config: typing.ClassVar[pydantic.ConfigDict] = pydantic.ConfigDict(extra="allow", frozen=True)  # type: ignore # Pydantic v2
    else:

        class Config:
            frozen = True
            smart_union = True
            extra = pydantic.Extra.allow
