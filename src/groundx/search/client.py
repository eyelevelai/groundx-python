# This file was auto-generated by Fern from our API Definition.

import typing
from ..core.client_wrapper import SyncClientWrapper
from .types.search_content_request_id import SearchContentRequestId
from ..core.request_options import RequestOptions
from ..types.search_response import SearchResponse
from ..core.jsonable_encoder import jsonable_encoder
from ..core.pydantic_utilities import parse_obj_as
from ..errors.bad_request_error import BadRequestError
from ..errors.unauthorized_error import UnauthorizedError
from json.decoder import JSONDecodeError
from ..core.api_error import ApiError
from ..core.client_wrapper import AsyncClientWrapper

# this is used as the default value for optional parameters
OMIT = typing.cast(typing.Any, ...)


class SearchClient:
    def __init__(self, *, client_wrapper: SyncClientWrapper):
        self._client_wrapper = client_wrapper

    def content(
        self,
        id: SearchContentRequestId,
        *,
        query: str,
        n: typing.Optional[int] = None,
        next_token: typing.Optional[str] = None,
        verbosity: typing.Optional[int] = None,
        relevance: typing.Optional[float] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> SearchResponse:
        """
        Search documents on GroundX for the most relevant information to a given query.
        The result of this query is typically used in one of two ways; `result.search.text` can be used to provide context to a language model, facilitating RAG, or `result.search.results` can be used to observe chunks of text which are relevant to the query, facilitating citation.

        Parameters
        ----------
        id : SearchContentRequestId
            The bucketId, groupId, projectId, or documentId to be searched. The document or documents within the specified container will be compared to the query, and relevant information will be extracted.

        query : str
            The search query to be used to find relevant documentation.

        n : typing.Optional[int]
            The maximum number of returned search results. Accepts 1-100 with a default of 20.

        next_token : typing.Optional[str]
            A token for pagination. If the number of search results for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n search results.

        verbosity : typing.Optional[int]
            The amount of data returned with each search result. 0 == no search results, only the recommended context. 1 == search results but no searchData. 2 == search results and searchData.

        relevance : typing.Optional[float]
            The minimum search relevance score required to include the result. By default, this is 10.0.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        SearchResponse
            Search query success

        Examples
        --------
        from groundx import GroundX

        client = GroundX(
            api_key="YOUR_API_KEY",
        )
        client.search.content(
            id=1,
            next_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
            query="my search query",
        )
        """
        _response = self._client_wrapper.httpx_client.request(
            f"v1/search/{jsonable_encoder(id)}",
            method="POST",
            params={
                "n": n,
                "nextToken": next_token,
                "verbosity": verbosity,
            },
            json={
                "query": query,
                "relevance": relevance,
            },
            headers={
                "content-type": "application/json",
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    SearchResponse,
                    parse_obj_as(
                        type_=SearchResponse,  # type: ignore
                        object_=_response.json(),
                    ),
                )
            if _response.status_code == 400:
                raise BadRequestError(
                    typing.cast(
                        typing.Optional[typing.Any],
                        parse_obj_as(
                            type_=typing.Optional[typing.Any],  # type: ignore
                            object_=_response.json(),
                        ),
                    )
                )
            if _response.status_code == 401:
                raise UnauthorizedError(
                    typing.cast(
                        typing.Optional[typing.Any],
                        parse_obj_as(
                            type_=typing.Optional[typing.Any],  # type: ignore
                            object_=_response.json(),
                        ),
                    )
                )
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def documents(
        self,
        *,
        query: str,
        document_ids: typing.Sequence[str],
        n: typing.Optional[int] = None,
        next_token: typing.Optional[str] = None,
        verbosity: typing.Optional[int] = None,
        relevance: typing.Optional[float] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> SearchResponse:
        """
        Search documents on GroundX for the most relevant information to a given query by documentId(s).
        The result of this query is typically used in one of two ways; `result.search.text` can be used to provide context to a language model, facilitating RAG, or `result.search.results` can be used to observe chunks of text which are relevant to the query, facilitating citation.

        Parameters
        ----------
        query : str
            The search query to be used to find relevant documentation.

        document_ids : typing.Sequence[str]
            An array of unique documentIds to be searched.

        n : typing.Optional[int]
            The maximum number of returned search results. Accepts 1-100 with a default of 20.

        next_token : typing.Optional[str]
            A token for pagination. If the number of search results for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n search results.

        verbosity : typing.Optional[int]
            The amount of data returned with each search result. 0 == no search results, only the recommended context. 1 == search results but no searchData. 2 == search results and searchData.

        relevance : typing.Optional[float]
            The minimum search relevance score required to include the result. By default, this is 10.0.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        SearchResponse
            Search query success

        Examples
        --------
        from groundx import GroundX

        client = GroundX(
            api_key="YOUR_API_KEY",
        )
        client.search.documents(
            next_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
            query="my search query",
            document_ids=["docUUID1", "docUUID2"],
        )
        """
        _response = self._client_wrapper.httpx_client.request(
            "v1/search/documents",
            method="POST",
            params={
                "n": n,
                "nextToken": next_token,
                "verbosity": verbosity,
            },
            json={
                "query": query,
                "documentIds": document_ids,
                "relevance": relevance,
            },
            headers={
                "content-type": "application/json",
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    SearchResponse,
                    parse_obj_as(
                        type_=SearchResponse,  # type: ignore
                        object_=_response.json(),
                    ),
                )
            if _response.status_code == 400:
                raise BadRequestError(
                    typing.cast(
                        typing.Optional[typing.Any],
                        parse_obj_as(
                            type_=typing.Optional[typing.Any],  # type: ignore
                            object_=_response.json(),
                        ),
                    )
                )
            if _response.status_code == 401:
                raise UnauthorizedError(
                    typing.cast(
                        typing.Optional[typing.Any],
                        parse_obj_as(
                            type_=typing.Optional[typing.Any],  # type: ignore
                            object_=_response.json(),
                        ),
                    )
                )
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)


class AsyncSearchClient:
    def __init__(self, *, client_wrapper: AsyncClientWrapper):
        self._client_wrapper = client_wrapper

    async def content(
        self,
        id: SearchContentRequestId,
        *,
        query: str,
        n: typing.Optional[int] = None,
        next_token: typing.Optional[str] = None,
        verbosity: typing.Optional[int] = None,
        relevance: typing.Optional[float] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> SearchResponse:
        """
        Search documents on GroundX for the most relevant information to a given query.
        The result of this query is typically used in one of two ways; `result.search.text` can be used to provide context to a language model, facilitating RAG, or `result.search.results` can be used to observe chunks of text which are relevant to the query, facilitating citation.

        Parameters
        ----------
        id : SearchContentRequestId
            The bucketId, groupId, projectId, or documentId to be searched. The document or documents within the specified container will be compared to the query, and relevant information will be extracted.

        query : str
            The search query to be used to find relevant documentation.

        n : typing.Optional[int]
            The maximum number of returned search results. Accepts 1-100 with a default of 20.

        next_token : typing.Optional[str]
            A token for pagination. If the number of search results for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n search results.

        verbosity : typing.Optional[int]
            The amount of data returned with each search result. 0 == no search results, only the recommended context. 1 == search results but no searchData. 2 == search results and searchData.

        relevance : typing.Optional[float]
            The minimum search relevance score required to include the result. By default, this is 10.0.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        SearchResponse
            Search query success

        Examples
        --------
        import asyncio

        from groundx import AsyncGroundX

        client = AsyncGroundX(
            api_key="YOUR_API_KEY",
        )


        async def main() -> None:
            await client.search.content(
                id=1,
                next_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
                query="my search query",
            )


        asyncio.run(main())
        """
        _response = await self._client_wrapper.httpx_client.request(
            f"v1/search/{jsonable_encoder(id)}",
            method="POST",
            params={
                "n": n,
                "nextToken": next_token,
                "verbosity": verbosity,
            },
            json={
                "query": query,
                "relevance": relevance,
            },
            headers={
                "content-type": "application/json",
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    SearchResponse,
                    parse_obj_as(
                        type_=SearchResponse,  # type: ignore
                        object_=_response.json(),
                    ),
                )
            if _response.status_code == 400:
                raise BadRequestError(
                    typing.cast(
                        typing.Optional[typing.Any],
                        parse_obj_as(
                            type_=typing.Optional[typing.Any],  # type: ignore
                            object_=_response.json(),
                        ),
                    )
                )
            if _response.status_code == 401:
                raise UnauthorizedError(
                    typing.cast(
                        typing.Optional[typing.Any],
                        parse_obj_as(
                            type_=typing.Optional[typing.Any],  # type: ignore
                            object_=_response.json(),
                        ),
                    )
                )
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    async def documents(
        self,
        *,
        query: str,
        document_ids: typing.Sequence[str],
        n: typing.Optional[int] = None,
        next_token: typing.Optional[str] = None,
        verbosity: typing.Optional[int] = None,
        relevance: typing.Optional[float] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> SearchResponse:
        """
        Search documents on GroundX for the most relevant information to a given query by documentId(s).
        The result of this query is typically used in one of two ways; `result.search.text` can be used to provide context to a language model, facilitating RAG, or `result.search.results` can be used to observe chunks of text which are relevant to the query, facilitating citation.

        Parameters
        ----------
        query : str
            The search query to be used to find relevant documentation.

        document_ids : typing.Sequence[str]
            An array of unique documentIds to be searched.

        n : typing.Optional[int]
            The maximum number of returned search results. Accepts 1-100 with a default of 20.

        next_token : typing.Optional[str]
            A token for pagination. If the number of search results for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n search results.

        verbosity : typing.Optional[int]
            The amount of data returned with each search result. 0 == no search results, only the recommended context. 1 == search results but no searchData. 2 == search results and searchData.

        relevance : typing.Optional[float]
            The minimum search relevance score required to include the result. By default, this is 10.0.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        SearchResponse
            Search query success

        Examples
        --------
        import asyncio

        from groundx import AsyncGroundX

        client = AsyncGroundX(
            api_key="YOUR_API_KEY",
        )


        async def main() -> None:
            await client.search.documents(
                next_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
                query="my search query",
                document_ids=["docUUID1", "docUUID2"],
            )


        asyncio.run(main())
        """
        _response = await self._client_wrapper.httpx_client.request(
            "v1/search/documents",
            method="POST",
            params={
                "n": n,
                "nextToken": next_token,
                "verbosity": verbosity,
            },
            json={
                "query": query,
                "documentIds": document_ids,
                "relevance": relevance,
            },
            headers={
                "content-type": "application/json",
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    SearchResponse,
                    parse_obj_as(
                        type_=SearchResponse,  # type: ignore
                        object_=_response.json(),
                    ),
                )
            if _response.status_code == 400:
                raise BadRequestError(
                    typing.cast(
                        typing.Optional[typing.Any],
                        parse_obj_as(
                            type_=typing.Optional[typing.Any],  # type: ignore
                            object_=_response.json(),
                        ),
                    )
                )
            if _response.status_code == 401:
                raise UnauthorizedError(
                    typing.cast(
                        typing.Optional[typing.Any],
                        parse_obj_as(
                            type_=typing.Optional[typing.Any],  # type: ignore
                            object_=_response.json(),
                        ),
                    )
                )
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)
