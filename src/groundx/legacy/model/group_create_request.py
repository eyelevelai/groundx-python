# coding: utf-8

"""
    GroundX APIs

    RAG Made Simple, Secure and Hallucination Free

    The version of the OpenAPI document: 1.3.26
    Contact: support@eyelevel.ai
    Created by: https://www.eyelevel.ai/
"""

from datetime import date, datetime  # noqa: F401
import decimal  # noqa: F401
import functools  # noqa: F401
import io  # noqa: F401
import re  # noqa: F401
import typing  # noqa: F401
import typing_extensions  # noqa: F401
import uuid  # noqa: F401

import frozendict  # noqa: F401

from groundx.legacy import schemas  # noqa: F401


class GroupCreateRequest(schemas.DictSchema):
    """
    This class is auto generated by Konfig (https://konfigthis.com)
    """

    class MetaOapg:
        required = {
            "name",
        }

        class properties:
            name = schemas.StrSchema
            bucketName = schemas.StrSchema
            __annotations__ = {
                "name": name,
                "bucketName": bucketName,
            }

    name: MetaOapg.properties.name

    @typing.overload
    def __getitem__(
        self, name: typing_extensions.Literal["name"]
    ) -> MetaOapg.properties.name: ...

    @typing.overload
    def __getitem__(
        self, name: typing_extensions.Literal["bucketName"]
    ) -> MetaOapg.properties.bucketName: ...

    @typing.overload
    def __getitem__(self, name: str) -> schemas.UnsetAnyTypeSchema: ...

    def __getitem__(
        self,
        name: typing.Union[
            typing_extensions.Literal[
                "name",
                "bucketName",
            ],
            str,
        ],
    ):
        # dict_instance[name] accessor
        return super().__getitem__(name)

    @typing.overload
    def get_item_oapg(
        self, name: typing_extensions.Literal["name"]
    ) -> MetaOapg.properties.name: ...

    @typing.overload
    def get_item_oapg(
        self, name: typing_extensions.Literal["bucketName"]
    ) -> typing.Union[MetaOapg.properties.bucketName, schemas.Unset]: ...

    @typing.overload
    def get_item_oapg(
        self, name: str
    ) -> typing.Union[schemas.UnsetAnyTypeSchema, schemas.Unset]: ...

    def get_item_oapg(
        self,
        name: typing.Union[
            typing_extensions.Literal[
                "name",
                "bucketName",
            ],
            str,
        ],
    ):
        return super().get_item_oapg(name)

    def __new__(
        cls,
        *args: typing.Union[
            dict,
            frozendict.frozendict,
        ],
        name: typing.Union[
            MetaOapg.properties.name,
            str,
        ],
        bucketName: typing.Union[
            MetaOapg.properties.bucketName, str, schemas.Unset
        ] = schemas.unset,
        _configuration: typing.Optional[schemas.Configuration] = None,
        **kwargs: typing.Union[
            schemas.AnyTypeSchema,
            dict,
            frozendict.frozendict,
            str,
            date,
            datetime,
            uuid.UUID,
            int,
            float,
            decimal.Decimal,
            None,
            list,
            tuple,
            bytes,
        ],
    ) -> "GroupCreateRequest":
        return super().__new__(
            cls,
            *args,
            name=name,
            bucketName=bucketName,
            _configuration=_configuration,
            **kwargs,
        )
