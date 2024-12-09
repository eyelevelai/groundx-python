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

class Sort(schemas.EnumBase, schemas.StrSchema):
    """
    This class is auto generated by Konfig (https://konfigthis.com)

    The attribute to use to sort results
    """

    @schemas.classproperty
    def NAME(cls):
        return cls("name")

    @schemas.classproperty
    def CREATED(cls):
        return cls("created")
