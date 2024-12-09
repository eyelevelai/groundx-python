# This file was auto-generated by Fern from our API Definition.

import typing_extensions
import typing_extensions
from ..core.serialization import FieldMetadata
import datetime as dt


class BucketDetailParams(typing_extensions.TypedDict):
    bucket_id: typing_extensions.Annotated[int, FieldMetadata(alias="bucketId")]
    created: typing_extensions.NotRequired[dt.datetime]
    """
    The data time when the bucket was created, in RFC3339 format
    """

    file_count: typing_extensions.NotRequired[typing_extensions.Annotated[int, FieldMetadata(alias="fileCount")]]
    """
    The number of files contained in the content bucket
    """

    file_size: typing_extensions.NotRequired[typing_extensions.Annotated[str, FieldMetadata(alias="fileSize")]]
    """
    The total file size of files contained in the content bucket
    """

    name: typing_extensions.NotRequired[str]
    updated: typing_extensions.NotRequired[dt.datetime]
    """
    The data time when the bucket was last updated, in RFC3339 format
    """