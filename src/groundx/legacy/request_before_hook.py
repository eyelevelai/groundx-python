# coding: utf-8

"""
    GroundX APIs

    RAG Made Simple, Secure and Hallucination Free

    The version of the OpenAPI document: 1.3.26
    Contact: support@eyelevel.ai
    Created by: https://www.eyelevel.ai/
"""

import typing
from urllib3._collections import HTTPHeaderDict
from groundx.legacy.configuration import Configuration


def request_before_hook(
    resource_path: str,
    method: str,
    configuration: Configuration,
    path_template: str,
    headers: typing.Optional[HTTPHeaderDict] = None,
    body: typing.Any = None,
    fields: typing.Optional[typing.Tuple[typing.Tuple[str, str], ...]] = None,
    auth_settings: typing.Optional[typing.List[str]] = None,
    **kwargs: typing.Any
):
    pass
