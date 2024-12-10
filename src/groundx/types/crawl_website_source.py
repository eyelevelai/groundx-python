# This file was auto-generated by Fern from our API Definition.

from ..core.pydantic_utilities import UniversalBaseModel
import typing_extensions
from ..core.serialization import FieldMetadata
import pydantic
import typing
from ..core.pydantic_utilities import IS_PYDANTIC_V2


class CrawlWebsiteSource(UniversalBaseModel):
    bucket_id: typing_extensions.Annotated[int, FieldMetadata(alias="bucketId")] = pydantic.Field()
    """
    the bucketId of the bucket which this website will be ingested to.
    """

    cap: typing.Optional[int] = pydantic.Field(default=None)
    """
    The maximum number of pages to crawl
    """

    depth: typing.Optional[int] = pydantic.Field(default=None)
    """
    The maximum depth of linked pages to follow from the sourceUrl
    """

    search_data: typing_extensions.Annotated[
        typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]], FieldMetadata(alias="searchData")
    ] = pydantic.Field(default=None)
    """
    Custom metadata which can be used to influence GroundX's search functionality. This data can be used to further hone GroundX search.
    """

    source_url: typing_extensions.Annotated[str, FieldMetadata(alias="sourceUrl")] = pydantic.Field()
    """
    The URL from which the crawl is initiated.
    """

    if IS_PYDANTIC_V2:
        model_config: typing.ClassVar[pydantic.ConfigDict] = pydantic.ConfigDict(extra="allow", frozen=True)  # type: ignore # Pydantic v2
    else:

        class Config:
            frozen = True
            smart_union = True
            extra = pydantic.Extra.allow