# coding: utf-8

# flake8: noqa

"""
    GroundX APIs

    RAG Made Simple, Secure and Hallucination Free

    The version of the OpenAPI document: 1.3.26
    Contact: support@eyelevel.ai
    Created by: https://www.eyelevel.ai/
"""

__version__ = "1.3.29"

# import ApiClient
from groundx.legacy.api_client import ApiClient

# import Configuration
from groundx.legacy.configuration import Configuration

# import exceptions
from groundx.legacy.exceptions import OpenApiException
from groundx.legacy.exceptions import ApiAttributeError
from groundx.legacy.exceptions import ApiTypeError
from groundx.legacy.exceptions import ApiValueError
from groundx.legacy.exceptions import ApiKeyError
from groundx.legacy.exceptions import ApiException

from groundx.legacy.client import Groundx
