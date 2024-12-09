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

class HealthResponse(schemas.DictSchema):
    """
    This class is auto generated by Konfig (https://konfigthis.com)
    """

    class MetaOapg:
        required = {
            "health",
        }

        class properties:
            @staticmethod
            def health() -> typing.Type["HealthResponseHealth"]:
                return HealthResponseHealth
            __annotations__ = {
                "health": health,
            }

    health: "HealthResponseHealth"

    @typing.overload
    def __getitem__(
        self, name: typing_extensions.Literal["health"]
    ) -> "HealthResponseHealth": ...
    @typing.overload
    def __getitem__(self, name: str) -> schemas.UnsetAnyTypeSchema: ...
    def __getitem__(
        self, name: typing.Union[typing_extensions.Literal["health",], str]
    ):
        # dict_instance[name] accessor
        return super().__getitem__(name)

    @typing.overload
    def get_item_oapg(
        self, name: typing_extensions.Literal["health"]
    ) -> "HealthResponseHealth": ...
    @typing.overload
    def get_item_oapg(
        self, name: str
    ) -> typing.Union[schemas.UnsetAnyTypeSchema, schemas.Unset]: ...
    def get_item_oapg(
        self, name: typing.Union[typing_extensions.Literal["health",], str]
    ):
        return super().get_item_oapg(name)

    def __new__(
        cls,
        *args: typing.Union[
            dict,
            frozendict.frozendict,
        ],
        health: "HealthResponseHealth",
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
    ) -> "HealthResponse":
        return super().__new__(
            cls,
            *args,
            health=health,
            _configuration=_configuration,
            **kwargs,
        )

from groundx.legacy.model.health_response_health import HealthResponseHealth
