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

class SearchDocumentsRequest(schemas.DictSchema):
    """
    This class is auto generated by Konfig (https://konfigthis.com)
    """

    class MetaOapg:
        required = {
            "query",
            "documentIds",
        }

        class properties:
            query = schemas.StrSchema

            @staticmethod
            def documentIds() -> typing.Type["SearchDocumentsRequestDocumentIds"]:
                return SearchDocumentsRequestDocumentIds
            relevance = schemas.Float32Schema
            __annotations__ = {
                "query": query,
                "documentIds": documentIds,
                "relevance": relevance,
            }

    query: MetaOapg.properties.query
    documentIds: "SearchDocumentsRequestDocumentIds"

    @typing.overload
    def __getitem__(
        self, name: typing_extensions.Literal["query"]
    ) -> MetaOapg.properties.query: ...
    @typing.overload
    def __getitem__(
        self, name: typing_extensions.Literal["documentIds"]
    ) -> "SearchDocumentsRequestDocumentIds": ...
    @typing.overload
    def __getitem__(
        self, name: typing_extensions.Literal["relevance"]
    ) -> MetaOapg.properties.relevance: ...
    @typing.overload
    def __getitem__(self, name: str) -> schemas.UnsetAnyTypeSchema: ...
    def __getitem__(
        self,
        name: typing.Union[
            typing_extensions.Literal[
                "query",
                "documentIds",
                "relevance",
            ],
            str,
        ],
    ):
        # dict_instance[name] accessor
        return super().__getitem__(name)

    @typing.overload
    def get_item_oapg(
        self, name: typing_extensions.Literal["query"]
    ) -> MetaOapg.properties.query: ...
    @typing.overload
    def get_item_oapg(
        self, name: typing_extensions.Literal["documentIds"]
    ) -> "SearchDocumentsRequestDocumentIds": ...
    @typing.overload
    def get_item_oapg(
        self, name: typing_extensions.Literal["relevance"]
    ) -> typing.Union[MetaOapg.properties.relevance, schemas.Unset]: ...
    @typing.overload
    def get_item_oapg(
        self, name: str
    ) -> typing.Union[schemas.UnsetAnyTypeSchema, schemas.Unset]: ...
    def get_item_oapg(
        self,
        name: typing.Union[
            typing_extensions.Literal[
                "query",
                "documentIds",
                "relevance",
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
        query: typing.Union[
            MetaOapg.properties.query,
            str,
        ],
        documentIds: "SearchDocumentsRequestDocumentIds",
        relevance: typing.Union[
            MetaOapg.properties.relevance, decimal.Decimal, int, float, schemas.Unset
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
    ) -> "SearchDocumentsRequest":
        return super().__new__(
            cls,
            *args,
            query=query,
            documentIds=documentIds,
            relevance=relevance,
            _configuration=_configuration,
            **kwargs,
        )

from groundx.legacy.model.search_documents_request_document_ids import (
    SearchDocumentsRequestDocumentIds,
)
