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

class DocumentLookupResponse(schemas.DictSchema):
    """
    This class is auto generated by Konfig (https://konfigthis.com)
    """

    class MetaOapg:
        class properties:
            count = schemas.IntSchema

            class documents(schemas.ListSchema):
                class MetaOapg:
                    @staticmethod
                    def items() -> typing.Type["DocumentDetail"]:
                        return DocumentDetail

                def __new__(
                    cls,
                    arg: typing.Union[
                        typing.Tuple["DocumentDetail"], typing.List["DocumentDetail"]
                    ],
                    _configuration: typing.Optional[schemas.Configuration] = None,
                ) -> "documents":
                    return super().__new__(
                        cls,
                        arg,
                        _configuration=_configuration,
                    )

                def __getitem__(self, i: int) -> "DocumentDetail":
                    return super().__getitem__(i)

            nextToken = schemas.StrSchema
            total = schemas.IntSchema
            __annotations__ = {
                "count": count,
                "documents": documents,
                "nextToken": nextToken,
                "total": total,
            }

    @typing.overload
    def __getitem__(
        self, name: typing_extensions.Literal["count"]
    ) -> MetaOapg.properties.count: ...
    @typing.overload
    def __getitem__(
        self, name: typing_extensions.Literal["documents"]
    ) -> MetaOapg.properties.documents: ...
    @typing.overload
    def __getitem__(
        self, name: typing_extensions.Literal["nextToken"]
    ) -> MetaOapg.properties.nextToken: ...
    @typing.overload
    def __getitem__(
        self, name: typing_extensions.Literal["total"]
    ) -> MetaOapg.properties.total: ...
    @typing.overload
    def __getitem__(self, name: str) -> schemas.UnsetAnyTypeSchema: ...
    def __getitem__(
        self,
        name: typing.Union[
            typing_extensions.Literal[
                "count",
                "documents",
                "nextToken",
                "total",
            ],
            str,
        ],
    ):
        # dict_instance[name] accessor
        return super().__getitem__(name)

    @typing.overload
    def get_item_oapg(
        self, name: typing_extensions.Literal["count"]
    ) -> typing.Union[MetaOapg.properties.count, schemas.Unset]: ...
    @typing.overload
    def get_item_oapg(
        self, name: typing_extensions.Literal["documents"]
    ) -> typing.Union[MetaOapg.properties.documents, schemas.Unset]: ...
    @typing.overload
    def get_item_oapg(
        self, name: typing_extensions.Literal["nextToken"]
    ) -> typing.Union[MetaOapg.properties.nextToken, schemas.Unset]: ...
    @typing.overload
    def get_item_oapg(
        self, name: typing_extensions.Literal["total"]
    ) -> typing.Union[MetaOapg.properties.total, schemas.Unset]: ...
    @typing.overload
    def get_item_oapg(
        self, name: str
    ) -> typing.Union[schemas.UnsetAnyTypeSchema, schemas.Unset]: ...
    def get_item_oapg(
        self,
        name: typing.Union[
            typing_extensions.Literal[
                "count",
                "documents",
                "nextToken",
                "total",
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
        count: typing.Union[
            MetaOapg.properties.count, decimal.Decimal, int, schemas.Unset
        ] = schemas.unset,
        documents: typing.Union[
            MetaOapg.properties.documents, list, tuple, schemas.Unset
        ] = schemas.unset,
        nextToken: typing.Union[
            MetaOapg.properties.nextToken, str, schemas.Unset
        ] = schemas.unset,
        total: typing.Union[
            MetaOapg.properties.total, decimal.Decimal, int, schemas.Unset
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
    ) -> "DocumentLookupResponse":
        return super().__new__(
            cls,
            *args,
            count=count,
            documents=documents,
            nextToken=nextToken,
            total=total,
            _configuration=_configuration,
            **kwargs,
        )

from groundx.legacy.model.document_detail import DocumentDetail
