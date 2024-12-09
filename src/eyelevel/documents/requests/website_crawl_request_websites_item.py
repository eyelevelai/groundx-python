# This file was auto-generated by Fern from our API Definition.

import typing_extensions
import typing_extensions
from ...core.serialization import FieldMetadata
import typing


class WebsiteCrawlRequestWebsitesItemParams(typing_extensions.TypedDict):
    bucket_id: typing_extensions.Annotated[int, FieldMetadata(alias="bucketId")]
    """
    the bucketId of the bucket which this website will be ingested to.
    """

    cap: typing_extensions.NotRequired[int]
    """
    The maximum number of pages to crawl
    """

    depth: typing_extensions.NotRequired[int]
    """
    The maximum depth of linked pages to follow from the sourceUrl
    """

    search_data: typing_extensions.NotRequired[
        typing_extensions.Annotated[typing.Dict[str, typing.Optional[typing.Any]], FieldMetadata(alias="searchData")]
    ]
    """
    Custom metadata which can be used to influence GroundX's search functionality. This data can be used to further hone GroundX search.
    """

    source_url: typing_extensions.Annotated[str, FieldMetadata(alias="sourceUrl")]
    """
    The URL from which the crawl is initiated.
    """
