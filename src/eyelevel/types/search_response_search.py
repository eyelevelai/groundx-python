# This file was auto-generated by Fern from our API Definition.

from ..core.pydantic_utilities import UniversalBaseModel
import typing
import pydantic
from .search_result_item import SearchResultItem
import typing_extensions
from ..core.serialization import FieldMetadata
from ..core.pydantic_utilities import IS_PYDANTIC_V2


class SearchResponseSearch(UniversalBaseModel):
    count: typing.Optional[int] = pydantic.Field(default=None)
    """
    Total results
    """

    results: typing.Optional[typing.List[SearchResultItem]] = pydantic.Field(default=None)
    """
    Search results
    """

    query: typing.Optional[str] = pydantic.Field(default=None)
    """
    The original search request query
    """

    score: typing.Optional[float] = pydantic.Field(default=None)
    """
    Confidence score in the search results
    """

    search_query: typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="searchQuery")] = (
        pydantic.Field(default=None)
    )
    """
    The actual search query, if the search request query was re-written
    """

    text: typing.Optional[str] = pydantic.Field(default=None)
    """
    Suggested context for LLM completion
    """

    next_token: typing_extensions.Annotated[typing.Optional[str], FieldMetadata(alias="nextToken")] = pydantic.Field(
        default=None
    )
    """
    For paginated results
    """

    if IS_PYDANTIC_V2:
        model_config: typing.ClassVar[pydantic.ConfigDict] = pydantic.ConfigDict(extra="allow", frozen=True)  # type: ignore # Pydantic v2
    else:

        class Config:
            frozen = True
            smart_union = True
            extra = pydantic.Extra.allow
