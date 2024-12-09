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

from groundx.legacy.model.sort_order import SortOrder as SortOrderSchema
from groundx.legacy.model.processing_status import (
    ProcessingStatus as ProcessingStatusSchema,
)
from groundx.legacy.model.document_list_response import (
    DocumentListResponse as DocumentListResponseSchema,
)
from groundx.legacy.model.sort import Sort as SortSchema

from groundx.legacy.type.processing_status import ProcessingStatus
from groundx.legacy.type.sort_order import SortOrder
from groundx.legacy.type.sort import Sort
from groundx.legacy.type.document_list_response import DocumentListResponse

# Query params
NSchema = schemas.IntSchema
FilterSchema = schemas.StrSchema
SortSchema = SortSchema
SortOrderSchema = SortOrderSchema
StatusSchema = ProcessingStatusSchema
NextTokenSchema = schemas.StrSchema
RequestRequiredQueryParams = typing_extensions.TypedDict(
    "RequestRequiredQueryParams", {}
)
RequestOptionalQueryParams = typing_extensions.TypedDict(
    "RequestOptionalQueryParams",
    {
        "n": typing.Union[
            NSchema,
            decimal.Decimal,
            int,
        ],
        "filter": typing.Union[
            FilterSchema,
            str,
        ],
        "sort": typing.Union[SortSchema,],
        "sortOrder": typing.Union[SortOrderSchema,],
        "status": typing.Union[StatusSchema,],
        "nextToken": typing.Union[
            NextTokenSchema,
            str,
        ],
    },
    total=False,
)

class RequestQueryParams(RequestRequiredQueryParams, RequestOptionalQueryParams):
    pass

request_query_n = api_client.QueryParameter(
    name="n",
    style=api_client.ParameterStyle.FORM,
    schema=NSchema,
    explode=True,
)
request_query_filter = api_client.QueryParameter(
    name="filter",
    style=api_client.ParameterStyle.FORM,
    schema=FilterSchema,
    explode=True,
)
request_query_sort = api_client.QueryParameter(
    name="sort",
    style=api_client.ParameterStyle.FORM,
    schema=SortSchema,
    explode=True,
)
request_query_sort_order = api_client.QueryParameter(
    name="sortOrder",
    style=api_client.ParameterStyle.FORM,
    schema=SortOrderSchema,
    explode=True,
)
request_query_status = api_client.QueryParameter(
    name="status",
    style=api_client.ParameterStyle.FORM,
    schema=ProcessingStatusSchema,
    explode=True,
)
request_query_next_token = api_client.QueryParameter(
    name="nextToken",
    style=api_client.ParameterStyle.FORM,
    schema=NextTokenSchema,
    explode=True,
)
SchemaFor200ResponseBodyApplicationJson = DocumentListResponseSchema

@dataclass
class ApiResponseFor200(api_client.ApiResponse):
    body: DocumentListResponse

@dataclass
class ApiResponseFor200Async(api_client.AsyncApiResponse):
    body: DocumentListResponse

_response_for_200 = api_client.OpenApiResponse(
    response_cls=ApiResponseFor200,
    response_cls_async=ApiResponseFor200Async,
    content={
        "application/json": api_client.MediaType(
            schema=SchemaFor200ResponseBodyApplicationJson
        ),
    },
)
_all_accept_content_types = ("application/json",)

class BaseApi(api_client.Api):
    def _list_mapped_args(
        self,
        n: typing.Optional[int] = None,
        filter: typing.Optional[str] = None,
        sort: typing.Optional[Sort] = None,
        sort_order: typing.Optional[SortOrder] = None,
        status: typing.Optional[ProcessingStatus] = None,
        next_token: typing.Optional[str] = None,
    ) -> api_client.MappedArgs:
        args: api_client.MappedArgs = api_client.MappedArgs()
        _query_params = {}
        if n is not None:
            _query_params["n"] = n
        if filter is not None:
            _query_params["filter"] = filter
        if sort is not None:
            _query_params["sort"] = sort
        if sort_order is not None:
            _query_params["sortOrder"] = sort_order
        if status is not None:
            _query_params["status"] = status
        if next_token is not None:
            _query_params["nextToken"] = next_token
        args.query = _query_params
        return args

    async def _alist_oapg(
        self,
        query_params: typing.Optional[dict] = {},
        skip_deserialization: bool = True,
        timeout: typing.Optional[typing.Union[float, typing.Tuple]] = None,
        accept_content_types: typing.Tuple[str] = _all_accept_content_types,
        stream: bool = False,
        **kwargs,
    ) -> typing.Union[
        ApiResponseFor200Async,
        api_client.ApiResponseWithoutDeserializationAsync,
        AsyncGeneratorResponse,
    ]:
        """
        list
        :param skip_deserialization: If true then api_response.response will be set but
            api_response.body and api_response.headers will not be deserialized into schema
            class instances
        """
        self._verify_typed_dict_inputs_oapg(RequestQueryParams, query_params)
        used_path = path.value

        prefix_separator_iterator = None
        for parameter in (
            request_query_n,
            request_query_filter,
            request_query_sort,
            request_query_sort_order,
            request_query_status,
            request_query_next_token,
        ):
            parameter_data = query_params.get(parameter.name, schemas.unset)
            if parameter_data is schemas.unset:
                continue
            if prefix_separator_iterator is None:
                prefix_separator_iterator = parameter.get_prefix_separator_iterator()
            serialized_data = parameter.serialize(
                parameter_data, prefix_separator_iterator
            )
            for serialized_value in serialized_data.values():
                used_path += serialized_value

        _headers = HTTPHeaderDict()
        # TODO add cookie handling
        if accept_content_types:
            for accept_content_type in accept_content_types:
                _headers.add("Accept", accept_content_type)
        method = "get".upper()
        request_before_hook(
            resource_path=used_path,
            method=method,
            configuration=self.api_client.configuration,
            path_template="/v1/ingest/documents",
            auth_settings=_auth,
            headers=_headers,
        )

        response = await self.api_client.async_call_api(
            resource_path=used_path,
            method=method,
            headers=_headers,
            auth_settings=_auth,
            prefix_separator_iterator=prefix_separator_iterator,
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

    def _list_oapg(
        self,
        query_params: typing.Optional[dict] = {},
        skip_deserialization: bool = True,
        timeout: typing.Optional[typing.Union[float, typing.Tuple]] = None,
        accept_content_types: typing.Tuple[str] = _all_accept_content_types,
        stream: bool = False,
    ) -> typing.Union[
        ApiResponseFor200,
        api_client.ApiResponseWithoutDeserialization,
    ]:
        """
        list
        :param skip_deserialization: If true then api_response.response will be set but
            api_response.body and api_response.headers will not be deserialized into schema
            class instances
        """
        self._verify_typed_dict_inputs_oapg(RequestQueryParams, query_params)
        used_path = path.value

        prefix_separator_iterator = None
        for parameter in (
            request_query_n,
            request_query_filter,
            request_query_sort,
            request_query_sort_order,
            request_query_status,
            request_query_next_token,
        ):
            parameter_data = query_params.get(parameter.name, schemas.unset)
            if parameter_data is schemas.unset:
                continue
            if prefix_separator_iterator is None:
                prefix_separator_iterator = parameter.get_prefix_separator_iterator()
            serialized_data = parameter.serialize(
                parameter_data, prefix_separator_iterator
            )
            for serialized_value in serialized_data.values():
                used_path += serialized_value

        _headers = HTTPHeaderDict()
        # TODO add cookie handling
        if accept_content_types:
            for accept_content_type in accept_content_types:
                _headers.add("Accept", accept_content_type)
        method = "get".upper()
        request_before_hook(
            resource_path=used_path,
            method=method,
            configuration=self.api_client.configuration,
            path_template="/v1/ingest/documents",
            auth_settings=_auth,
            headers=_headers,
        )

        response = self.api_client.call_api(
            resource_path=used_path,
            method=method,
            headers=_headers,
            auth_settings=_auth,
            prefix_separator_iterator=prefix_separator_iterator,
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

class List(BaseApi):
    # this class is used by api classes that refer to endpoints with operationId fn names

    async def alist(
        self,
        n: typing.Optional[int] = None,
        filter: typing.Optional[str] = None,
        sort: typing.Optional[Sort] = None,
        sort_order: typing.Optional[SortOrder] = None,
        status: typing.Optional[ProcessingStatus] = None,
        next_token: typing.Optional[str] = None,
        **kwargs,
    ) -> typing.Union[
        ApiResponseFor200Async,
        api_client.ApiResponseWithoutDeserializationAsync,
        AsyncGeneratorResponse,
    ]:
        args = self._list_mapped_args(
            n=n,
            filter=filter,
            sort=sort,
            sort_order=sort_order,
            status=status,
            next_token=next_token,
        )
        return await self._alist_oapg(
            query_params=args.query,
            **kwargs,
        )

    def list(
        self,
        n: typing.Optional[int] = None,
        filter: typing.Optional[str] = None,
        sort: typing.Optional[Sort] = None,
        sort_order: typing.Optional[SortOrder] = None,
        status: typing.Optional[ProcessingStatus] = None,
        next_token: typing.Optional[str] = None,
    ) -> typing.Union[
        ApiResponseFor200,
        api_client.ApiResponseWithoutDeserialization,
    ]:
        """lookup all documents across all resources which are currently on GroundX  Interact with the \"Request Body\" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments."""
        args = self._list_mapped_args(
            n=n,
            filter=filter,
            sort=sort,
            sort_order=sort_order,
            status=status,
            next_token=next_token,
        )
        return self._list_oapg(
            query_params=args.query,
        )

class ApiForget(BaseApi):
    # this class is used by api classes that refer to endpoints by path and http method names

    async def aget(
        self,
        n: typing.Optional[int] = None,
        filter: typing.Optional[str] = None,
        sort: typing.Optional[Sort] = None,
        sort_order: typing.Optional[SortOrder] = None,
        status: typing.Optional[ProcessingStatus] = None,
        next_token: typing.Optional[str] = None,
        **kwargs,
    ) -> typing.Union[
        ApiResponseFor200Async,
        api_client.ApiResponseWithoutDeserializationAsync,
        AsyncGeneratorResponse,
    ]:
        args = self._list_mapped_args(
            n=n,
            filter=filter,
            sort=sort,
            sort_order=sort_order,
            status=status,
            next_token=next_token,
        )
        return await self._alist_oapg(
            query_params=args.query,
            **kwargs,
        )

    def get(
        self,
        n: typing.Optional[int] = None,
        filter: typing.Optional[str] = None,
        sort: typing.Optional[Sort] = None,
        sort_order: typing.Optional[SortOrder] = None,
        status: typing.Optional[ProcessingStatus] = None,
        next_token: typing.Optional[str] = None,
    ) -> typing.Union[
        ApiResponseFor200,
        api_client.ApiResponseWithoutDeserialization,
    ]:
        """lookup all documents across all resources which are currently on GroundX  Interact with the \"Request Body\" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments."""
        args = self._list_mapped_args(
            n=n,
            filter=filter,
            sort=sort,
            sort_order=sort_order,
            status=status,
            next_token=next_token,
        )
        return self._list_oapg(
            query_params=args.query,
        )