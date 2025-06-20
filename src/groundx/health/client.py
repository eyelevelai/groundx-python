# This file was auto-generated by Fern from our API Definition.

import typing

from ..core.client_wrapper import AsyncClientWrapper, SyncClientWrapper
from ..core.request_options import RequestOptions
from ..types.health_response import HealthResponse
from .raw_client import AsyncRawHealthClient, RawHealthClient


class HealthClient:
    def __init__(self, *, client_wrapper: SyncClientWrapper):
        self._raw_client = RawHealthClient(client_wrapper=client_wrapper)

    @property
    def with_raw_response(self) -> RawHealthClient:
        """
        Retrieves a raw implementation of this client that returns raw responses.

        Returns
        -------
        RawHealthClient
        """
        return self._raw_client

    def list(self, *, request_options: typing.Optional[RequestOptions] = None) -> HealthResponse:
        """
        List the current health status of all services. Statuses update every 5 minutes.

        Parameters
        ----------
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        HealthResponse
            Look up success

        Examples
        --------
        from groundx import GroundX

        client = GroundX(
            api_key="YOUR_API_KEY",
        )
        client.health.list()
        """
        _response = self._raw_client.list(request_options=request_options)
        return _response.data

    def get(self, service: str, *, request_options: typing.Optional[RequestOptions] = None) -> HealthResponse:
        """
        Look up the current health status of a specific service. Statuses update every 5 minutes.

        Parameters
        ----------
        service : str
            The name of the service to look up.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        HealthResponse
            Look up success

        Examples
        --------
        from groundx import GroundX

        client = GroundX(
            api_key="YOUR_API_KEY",
        )
        client.health.get(
            service="search",
        )
        """
        _response = self._raw_client.get(service, request_options=request_options)
        return _response.data


class AsyncHealthClient:
    def __init__(self, *, client_wrapper: AsyncClientWrapper):
        self._raw_client = AsyncRawHealthClient(client_wrapper=client_wrapper)

    @property
    def with_raw_response(self) -> AsyncRawHealthClient:
        """
        Retrieves a raw implementation of this client that returns raw responses.

        Returns
        -------
        AsyncRawHealthClient
        """
        return self._raw_client

    async def list(self, *, request_options: typing.Optional[RequestOptions] = None) -> HealthResponse:
        """
        List the current health status of all services. Statuses update every 5 minutes.

        Parameters
        ----------
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        HealthResponse
            Look up success

        Examples
        --------
        import asyncio

        from groundx import AsyncGroundX

        client = AsyncGroundX(
            api_key="YOUR_API_KEY",
        )


        async def main() -> None:
            await client.health.list()


        asyncio.run(main())
        """
        _response = await self._raw_client.list(request_options=request_options)
        return _response.data

    async def get(self, service: str, *, request_options: typing.Optional[RequestOptions] = None) -> HealthResponse:
        """
        Look up the current health status of a specific service. Statuses update every 5 minutes.

        Parameters
        ----------
        service : str
            The name of the service to look up.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        HealthResponse
            Look up success

        Examples
        --------
        import asyncio

        from groundx import AsyncGroundX

        client = AsyncGroundX(
            api_key="YOUR_API_KEY",
        )


        async def main() -> None:
            await client.health.get(
                service="search",
            )


        asyncio.run(main())
        """
        _response = await self._raw_client.get(service, request_options=request_options)
        return _response.data
