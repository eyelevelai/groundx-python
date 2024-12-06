# This file was auto-generated by Fern from our API Definition.

from ..core.pydantic_utilities import UniversalBaseModel
import typing
from .bucket_detail import BucketDetail
import pydantic
import datetime as dt
import typing_extensions
from ..core.serialization import FieldMetadata
from ..core.pydantic_utilities import IS_PYDANTIC_V2


class GroupDetail(UniversalBaseModel):
    buckets: typing.Optional[typing.List[BucketDetail]] = pydantic.Field(default=None)
    """
    The content buckets associated with the group
    """

    created: typing.Optional[dt.datetime] = pydantic.Field(default=None)
    """
    The data time when the group was created, in RFC3339 format
    """

    file_count: typing_extensions.Annotated[typing.Optional[int], FieldMetadata(alias="fileCount")] = pydantic.Field(
        default=None
    )
    """
    The number of files contained in the content buckets associated with the group
    """

    file_size: typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="fileSize")] = pydantic.Field(
        default=None
    )
    """
    The total file size of files contained in the content buckets associated with the group
    """

    group_id: typing_extensions.Annotated[int, FieldMetadata(alias="groupId")]
    name: typing.Optional[str] = None
    updated: typing.Optional[dt.datetime] = pydantic.Field(default=None)
    """
    The data time when the group was last updated, in RFC3339 format
    """

    if IS_PYDANTIC_V2:
        model_config: typing.ClassVar[pydantic.ConfigDict] = pydantic.ConfigDict(extra="allow", frozen=True)  # type: ignore # Pydantic v2
    else:

        class Config:
            frozen = True
            smart_union = True
            extra = pydantic.Extra.allow
