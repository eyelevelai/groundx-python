# This file was auto-generated by Fern from our API Definition.

import typing

import pydantic
import typing_extensions
from ..core.pydantic_utilities import IS_PYDANTIC_V2, UniversalBaseModel
from ..core.serialization import FieldMetadata


class BoundingBoxDetail(UniversalBaseModel):
    bottom_right_x: typing_extensions.Annotated[typing.Optional[float], FieldMetadata(alias="bottomRightX")] = (
        pydantic.Field(default=None)
    )
    """
    The x coordinate of the lower right corner of the bounding box
    """

    bottom_right_y: typing_extensions.Annotated[typing.Optional[float], FieldMetadata(alias="bottomRightY")] = (
        pydantic.Field(default=None)
    )
    """
    The y coordinate of the lower right corner of the bounding box
    """

    page_number: typing_extensions.Annotated[typing.Optional[int], FieldMetadata(alias="pageNumber")] = pydantic.Field(
        default=None
    )
    """
    The page number the bounding box appears on, using a 1-based array indexing (starts with page 1, not page 0)
    """

    top_left_x: typing_extensions.Annotated[typing.Optional[float], FieldMetadata(alias="topLeftX")] = pydantic.Field(
        default=None
    )
    """
    The x coordinate of the upper left corner of the bounding box
    """

    top_left_y: typing_extensions.Annotated[typing.Optional[float], FieldMetadata(alias="topLeftY")] = pydantic.Field(
        default=None
    )
    """
    The y coordinate of the upper left corner of the bounding box
    """

    if IS_PYDANTIC_V2:
        model_config: typing.ClassVar[pydantic.ConfigDict] = pydantic.ConfigDict(extra="allow", frozen=True)  # type: ignore # Pydantic v2
    else:

        class Config:
            frozen = True
            smart_union = True
            extra = pydantic.Extra.allow
