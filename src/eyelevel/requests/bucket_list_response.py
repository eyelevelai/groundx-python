# This file was auto-generated by Fern from our API Definition.

import typing_extensions
import typing_extensions
import typing
from .bucket_detail import BucketDetailParams


class BucketListResponseParams(typing_extensions.TypedDict):
    buckets: typing_extensions.NotRequired[typing.Sequence[BucketDetailParams]]
