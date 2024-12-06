# This file was auto-generated by Fern from our API Definition.

import typing
from ..core.client_wrapper import SyncClientWrapper
from ..core.request_options import RequestOptions
from ..types.bucket_list_response import BucketListResponse
from ..core.pydantic_utilities import parse_obj_as
from json.decoder import JSONDecodeError
from ..core.api_error import ApiError
from ..types.bucket_response import BucketResponse
from ..errors.bad_request_error import BadRequestError
from ..core.jsonable_encoder import jsonable_encoder
from ..errors.unauthorized_error import UnauthorizedError
from ..types.bucket_update_response import BucketUpdateResponse
from ..types.message_response import MessageResponse
from ..core.client_wrapper import AsyncClientWrapper

# this is used as the default value for optional parameters
OMIT = typing.cast(typing.Any, ...)


class BucketsClient:
    def __init__(self, *, client_wrapper: SyncClientWrapper):
        self._client_wrapper = client_wrapper

    def list(
        self,
        *,
        n: typing.Optional[int] = None,
        next_token: typing.Optional[str] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> BucketListResponse:
        """
        List all buckets within your GroundX account

        Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.

        Parameters
        ----------
        n : typing.Optional[int]
            The maximum number of returned buckets. Accepts 1-100 with a default of 20.

        next_token : typing.Optional[str]
            A token for pagination. If the number of buckets for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n buckets.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        BucketListResponse
            Look up success

        Examples
        --------
        from eyelevel import EyeLevel

        client = EyeLevel(
            api_key="YOUR_API_KEY",
        )
        client.buckets.list()
        """
        _response = self._client_wrapper.httpx_client.request(
            "v1/bucket",
            method="GET",
            params={
                "n": n,
                "nextToken": next_token,
            },
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    BucketListResponse,
                    parse_obj_as(
                        type_=BucketListResponse,  # type: ignore
                        object_=_response.json(),
                    ),
                )
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def create(self, *, name: str, request_options: typing.Optional[RequestOptions] = None) -> BucketResponse:
        """
        Create a new bucket.

        Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.

        Parameters
        ----------
        name : str

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        BucketResponse
            Bucket successfully created

        Examples
        --------
        from eyelevel import EyeLevel

        client = EyeLevel(
            api_key="YOUR_API_KEY",
        )
        client.buckets.create(
            name="your_bucket_name",
        )
        """
        _response = self._client_wrapper.httpx_client.request(
            "v1/bucket",
            method="POST",
            json={
                "name": name,
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    BucketResponse,
                    parse_obj_as(
                        type_=BucketResponse,  # type: ignore
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
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def get(self, bucket_id: int, *, request_options: typing.Optional[RequestOptions] = None) -> BucketResponse:
        """
        Look up a specific bucket by its bucketId.

        Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.

        Parameters
        ----------
        bucket_id : int
            The bucketId of the bucket to look up.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        BucketResponse
            Look up success

        Examples
        --------
        from eyelevel import EyeLevel

        client = EyeLevel(
            api_key="YOUR_API_KEY",
        )
        client.buckets.get(
            bucket_id=1,
        )
        """
        _response = self._client_wrapper.httpx_client.request(
            f"v1/bucket/{jsonable_encoder(bucket_id)}",
            method="GET",
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    BucketResponse,
                    parse_obj_as(
                        type_=BucketResponse,  # type: ignore
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

    def update(
        self, bucket_id: int, *, new_name: str, request_options: typing.Optional[RequestOptions] = None
    ) -> BucketUpdateResponse:
        """
        Rename a bucket.

        Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.

        Parameters
        ----------
        bucket_id : int
            The bucketId of the bucket being updated.

        new_name : str
            The new name of the bucket being renamed.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        BucketUpdateResponse
            Bucket successfully updated

        Examples
        --------
        from eyelevel import EyeLevel

        client = EyeLevel(
            api_key="YOUR_API_KEY",
        )
        client.buckets.update(
            bucket_id=1,
            new_name="your_bucket_name",
        )
        """
        _response = self._client_wrapper.httpx_client.request(
            f"v1/bucket/{jsonable_encoder(bucket_id)}",
            method="PUT",
            json={
                "newName": new_name,
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    BucketUpdateResponse,
                    parse_obj_as(
                        type_=BucketUpdateResponse,  # type: ignore
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

    def delete(self, bucket_id: int, *, request_options: typing.Optional[RequestOptions] = None) -> MessageResponse:
        """
        Delete a bucket.

        Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.

        Parameters
        ----------
        bucket_id : int
            The bucketId of the bucket being deleted.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        MessageResponse
            Bucket successfully deleted

        Examples
        --------
        from eyelevel import EyeLevel

        client = EyeLevel(
            api_key="YOUR_API_KEY",
        )
        client.buckets.delete(
            bucket_id=1,
        )
        """
        _response = self._client_wrapper.httpx_client.request(
            f"v1/bucket/{jsonable_encoder(bucket_id)}",
            method="DELETE",
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    MessageResponse,
                    parse_obj_as(
                        type_=MessageResponse,  # type: ignore
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


class AsyncBucketsClient:
    def __init__(self, *, client_wrapper: AsyncClientWrapper):
        self._client_wrapper = client_wrapper

    async def list(
        self,
        *,
        n: typing.Optional[int] = None,
        next_token: typing.Optional[str] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> BucketListResponse:
        """
        List all buckets within your GroundX account

        Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.

        Parameters
        ----------
        n : typing.Optional[int]
            The maximum number of returned buckets. Accepts 1-100 with a default of 20.

        next_token : typing.Optional[str]
            A token for pagination. If the number of buckets for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n buckets.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        BucketListResponse
            Look up success

        Examples
        --------
        import asyncio

        from eyelevel import AsyncEyeLevel

        client = AsyncEyeLevel(
            api_key="YOUR_API_KEY",
        )


        async def main() -> None:
            await client.buckets.list()


        asyncio.run(main())
        """
        _response = await self._client_wrapper.httpx_client.request(
            "v1/bucket",
            method="GET",
            params={
                "n": n,
                "nextToken": next_token,
            },
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    BucketListResponse,
                    parse_obj_as(
                        type_=BucketListResponse,  # type: ignore
                        object_=_response.json(),
                    ),
                )
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    async def create(self, *, name: str, request_options: typing.Optional[RequestOptions] = None) -> BucketResponse:
        """
        Create a new bucket.

        Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.

        Parameters
        ----------
        name : str

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        BucketResponse
            Bucket successfully created

        Examples
        --------
        import asyncio

        from eyelevel import AsyncEyeLevel

        client = AsyncEyeLevel(
            api_key="YOUR_API_KEY",
        )


        async def main() -> None:
            await client.buckets.create(
                name="your_bucket_name",
            )


        asyncio.run(main())
        """
        _response = await self._client_wrapper.httpx_client.request(
            "v1/bucket",
            method="POST",
            json={
                "name": name,
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    BucketResponse,
                    parse_obj_as(
                        type_=BucketResponse,  # type: ignore
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
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    async def get(self, bucket_id: int, *, request_options: typing.Optional[RequestOptions] = None) -> BucketResponse:
        """
        Look up a specific bucket by its bucketId.

        Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.

        Parameters
        ----------
        bucket_id : int
            The bucketId of the bucket to look up.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        BucketResponse
            Look up success

        Examples
        --------
        import asyncio

        from eyelevel import AsyncEyeLevel

        client = AsyncEyeLevel(
            api_key="YOUR_API_KEY",
        )


        async def main() -> None:
            await client.buckets.get(
                bucket_id=1,
            )


        asyncio.run(main())
        """
        _response = await self._client_wrapper.httpx_client.request(
            f"v1/bucket/{jsonable_encoder(bucket_id)}",
            method="GET",
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    BucketResponse,
                    parse_obj_as(
                        type_=BucketResponse,  # type: ignore
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

    async def update(
        self, bucket_id: int, *, new_name: str, request_options: typing.Optional[RequestOptions] = None
    ) -> BucketUpdateResponse:
        """
        Rename a bucket.

        Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.

        Parameters
        ----------
        bucket_id : int
            The bucketId of the bucket being updated.

        new_name : str
            The new name of the bucket being renamed.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        BucketUpdateResponse
            Bucket successfully updated

        Examples
        --------
        import asyncio

        from eyelevel import AsyncEyeLevel

        client = AsyncEyeLevel(
            api_key="YOUR_API_KEY",
        )


        async def main() -> None:
            await client.buckets.update(
                bucket_id=1,
                new_name="your_bucket_name",
            )


        asyncio.run(main())
        """
        _response = await self._client_wrapper.httpx_client.request(
            f"v1/bucket/{jsonable_encoder(bucket_id)}",
            method="PUT",
            json={
                "newName": new_name,
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    BucketUpdateResponse,
                    parse_obj_as(
                        type_=BucketUpdateResponse,  # type: ignore
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

    async def delete(
        self, bucket_id: int, *, request_options: typing.Optional[RequestOptions] = None
    ) -> MessageResponse:
        """
        Delete a bucket.

        Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.

        Parameters
        ----------
        bucket_id : int
            The bucketId of the bucket being deleted.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        MessageResponse
            Bucket successfully deleted

        Examples
        --------
        import asyncio

        from eyelevel import AsyncEyeLevel

        client = AsyncEyeLevel(
            api_key="YOUR_API_KEY",
        )


        async def main() -> None:
            await client.buckets.delete(
                bucket_id=1,
            )


        asyncio.run(main())
        """
        _response = await self._client_wrapper.httpx_client.request(
            f"v1/bucket/{jsonable_encoder(bucket_id)}",
            method="DELETE",
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    MessageResponse,
                    parse_obj_as(
                        type_=MessageResponse,  # type: ignore
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
