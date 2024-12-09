# coding: utf-8

"""
    GroundX APIs

    RAG Made Simple, Secure and Hallucination Free

    The version of the OpenAPI document: 1.3.26
    Contact: support@eyelevel.ai
    Created by: https://www.eyelevel.ai/
"""

from dataclasses import dataclass
import typing_extensions
import urllib3
from groundx.legacy.request_before_hook import request_before_hook
import json
from urllib3._collections import HTTPHeaderDict

from groundx.legacy.api_response import AsyncGeneratorResponse
from groundx.legacy import api_client, exceptions
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

from groundx.legacy.model.bucket_response import BucketResponse as BucketResponseSchema
from groundx.legacy.model.bucket_create_request import (
    BucketCreateRequest as BucketCreateRequestSchema,
)

from groundx.legacy.type.bucket_create_request import BucketCreateRequest
from groundx.legacy.type.bucket_response import BucketResponse

# body param
SchemaForRequestBodyApplicationJson = BucketCreateRequestSchema

request_body_bucket_create_request = api_client.RequestBody(
    content={
        "application/json": api_client.MediaType(
            schema=SchemaForRequestBodyApplicationJson
        ),
    },
    required=True,
)
SchemaFor200ResponseBodyApplicationJson = BucketResponseSchema

@dataclass
class ApiResponseFor200(api_client.ApiResponse):
    body: BucketResponse

@dataclass
class ApiResponseFor200Async(api_client.AsyncApiResponse):
    body: BucketResponse

_response_for_200 = api_client.OpenApiResponse(
    response_cls=ApiResponseFor200,
    response_cls_async=ApiResponseFor200Async,
    content={
        "application/json": api_client.MediaType(
            schema=SchemaFor200ResponseBodyApplicationJson
        ),
    },
)

@dataclass
class ApiResponseFor400(api_client.ApiResponse):
    body: schemas.Unset = schemas.unset

@dataclass
class ApiResponseFor400Async(api_client.AsyncApiResponse):
    body: schemas.Unset = schemas.unset

_response_for_400 = api_client.OpenApiResponse(
    response_cls=ApiResponseFor400,
    response_cls_async=ApiResponseFor400Async,
)
_all_accept_content_types = ("application/json",)

class BaseApi(api_client.Api):
    def _create_mapped_args(
        self,
        name: str,
    ) -> api_client.MappedArgs:
        args: api_client.MappedArgs = api_client.MappedArgs()
        _body = {}
        if name is not None:
            _body["name"] = name
        args.body = _body
        return args

    async def _acreate_oapg(
        self,
        body: typing.Any = None,
        skip_deserialization: bool = True,
        timeout: typing.Optional[typing.Union[float, typing.Tuple]] = None,
        accept_content_types: typing.Tuple[str] = _all_accept_content_types,
        content_type: str = "application/json",
        stream: bool = False,
        **kwargs,
    ) -> typing.Union[
        ApiResponseFor200Async,
        api_client.ApiResponseWithoutDeserializationAsync,
        AsyncGeneratorResponse,
    ]:
        """
        create
        :param skip_deserialization: If true then api_response.response will be set but
            api_response.body and api_response.headers will not be deserialized into schema
            class instances
        """
        used_path = path.value

        _headers = HTTPHeaderDict()
        # TODO add cookie handling
        if accept_content_types:
            for accept_content_type in accept_content_types:
                _headers.add("Accept", accept_content_type)
        method = "post".upper()
        _headers.add("Content-Type", content_type)

        if body is schemas.unset:
            raise exceptions.ApiValueError(
                "The required body parameter has an invalid value of: unset. Set a valid value instead"
            )
        _fields = None
        _body = None
        request_before_hook(
            resource_path=used_path,
            method=method,
            configuration=self.api_client.configuration,
            path_template="/v1/bucket",
            body=body,
            auth_settings=_auth,
            headers=_headers,
        )
        serialized_data = request_body_bucket_create_request.serialize(
            body, content_type
        )
        if "fields" in serialized_data:
            _fields = serialized_data["fields"]
        elif "body" in serialized_data:
            _body = serialized_data["body"]

        response = await self.api_client.async_call_api(
            resource_path=used_path,
            method=method,
            headers=_headers,
            fields=_fields,
            serialized_body=_body,
            body=body,
            auth_settings=_auth,
            timeout=timeout,
            **kwargs,
        )

        if stream:
            if not 200 <= response.http_response.status <= 299:
                body = (await response.http_response.content.read()).decode("utf-8")
                raise exceptions.ApiStreamingException(
                    status=response.http_response.status,
                    reason=response.http_response.reason,
                    body=body,
                )

            async def stream_iterator():
                """
                iterates over response.http_response.content and closes connection once iteration has finished
                """
                async for line in response.http_response.content:
                    if line == b"\r\n":
                        continue
                    yield line
                response.http_response.close()
                await response.session.close()
            return AsyncGeneratorResponse(
                content=stream_iterator(),
                headers=response.http_response.headers,
                status=response.http_response.status,
                response=response.http_response,
            )

        response_for_status = _status_code_to_response.get(
            str(response.http_response.status)
        )
        if response_for_status:
            api_response = await response_for_status.deserialize_async(
                response,
                self.api_client.configuration,
                skip_deserialization=skip_deserialization,
            )
        else:
            # If response data is JSON then deserialize for SDK consumer convenience
            is_json = api_client.JSONDetector._content_type_is_json(
                response.http_response.headers.get("Content-Type", "")
            )
            api_response = api_client.ApiResponseWithoutDeserializationAsync(
                body=(
                    await response.http_response.json()
                    if is_json
                    else await response.http_response.text()
                ),
                response=response.http_response,
                round_trip_time=response.round_trip_time,
                status=response.http_response.status,
                headers=response.http_response.headers,
            )

        if not 200 <= api_response.status <= 299:
            raise exceptions.ApiException(api_response=api_response)

        # cleanup session / response
        response.http_response.close()
        await response.session.close()

        return api_response

    def _create_oapg(
        self,
        body: typing.Any = None,
        skip_deserialization: bool = True,
        timeout: typing.Optional[typing.Union[float, typing.Tuple]] = None,
        accept_content_types: typing.Tuple[str] = _all_accept_content_types,
        content_type: str = "application/json",
        stream: bool = False,
    ) -> typing.Union[
        ApiResponseFor200,
        api_client.ApiResponseWithoutDeserialization,
    ]:
        """
        create
        :param skip_deserialization: If true then api_response.response will be set but
            api_response.body and api_response.headers will not be deserialized into schema
            class instances
        """
        used_path = path.value

        _headers = HTTPHeaderDict()
        # TODO add cookie handling
        if accept_content_types:
            for accept_content_type in accept_content_types:
                _headers.add("Accept", accept_content_type)
        method = "post".upper()
        _headers.add("Content-Type", content_type)

        if body is schemas.unset:
            raise exceptions.ApiValueError(
                "The required body parameter has an invalid value of: unset. Set a valid value instead"
            )
        _fields = None
        _body = None
        request_before_hook(
            resource_path=used_path,
            method=method,
            configuration=self.api_client.configuration,
            path_template="/v1/bucket",
            body=body,
            auth_settings=_auth,
            headers=_headers,
        )
        serialized_data = request_body_bucket_create_request.serialize(
            body, content_type
        )
        if "fields" in serialized_data:
            _fields = serialized_data["fields"]
        elif "body" in serialized_data:
            _body = serialized_data["body"]

        response = self.api_client.call_api(
            resource_path=used_path,
            method=method,
            headers=_headers,
            fields=_fields,
            serialized_body=_body,
            body=body,
            auth_settings=_auth,
            timeout=timeout,
        )

        response_for_status = _status_code_to_response.get(
            str(response.http_response.status)
        )
        if response_for_status:
            api_response = response_for_status.deserialize(
                response,
                self.api_client.configuration,
                skip_deserialization=skip_deserialization,
            )
        else:
            # If response data is JSON then deserialize for SDK consumer convenience
            is_json = api_client.JSONDetector._content_type_is_json(
                response.http_response.headers.get("Content-Type", "")
            )
            api_response = api_client.ApiResponseWithoutDeserialization(
                body=(
                    json.loads(response.http_response.data)
                    if is_json
                    else response.http_response.data
                ),
                response=response.http_response,
                round_trip_time=response.round_trip_time,
                status=response.http_response.status,
                headers=response.http_response.headers,
            )

        if not 200 <= api_response.status <= 299:
            raise exceptions.ApiException(api_response=api_response)

        return api_response

class Create(BaseApi):
    # this class is used by api classes that refer to endpoints with operationId fn names

    async def acreate(
        self,
        name: str,
        **kwargs,
    ) -> typing.Union[
        ApiResponseFor200Async,
        api_client.ApiResponseWithoutDeserializationAsync,
        AsyncGeneratorResponse,
    ]:
        args = self._create_mapped_args(
            name=name,
        )
        return await self._acreate_oapg(
            body=args.body,
            **kwargs,
        )

    def create(
        self,
        name: str,
    ) -> typing.Union[
        ApiResponseFor200,
        api_client.ApiResponseWithoutDeserialization,
    ]:
        """Create a new bucket.  Interact with the \"Request Body\" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments."""
        args = self._create_mapped_args(
            name=name,
        )
        return self._create_oapg(
            body=args.body,
        )

class ApiForpost(BaseApi):
    # this class is used by api classes that refer to endpoints by path and http method names

    async def apost(
        self,
        name: str,
        **kwargs,
    ) -> typing.Union[
        ApiResponseFor200Async,
        api_client.ApiResponseWithoutDeserializationAsync,
        AsyncGeneratorResponse,
    ]:
        args = self._create_mapped_args(
            name=name,
        )
        return await self._acreate_oapg(
            body=args.body,
            **kwargs,
        )

    def post(
        self,
        name: str,
    ) -> typing.Union[
        ApiResponseFor200,
        api_client.ApiResponseWithoutDeserialization,
    ]:
        """Create a new bucket.  Interact with the \"Request Body\" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments."""
        args = self._create_mapped_args(
            name=name,
        )
        return self._create_oapg(
            body=args.body,
        )