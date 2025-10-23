import typing

from dataclasses import asdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from ..classes.api import ProcessResponse
from .logger import Logger
from .status import Status
from ..settings.settings import ContainerSettings
from .utility import get_gunicorn_threads, get_thread_id, get_worker_id


class RateLimit(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        settings: ContainerSettings,
        logger: Logger,
    ) -> None:
        super().__init__(app)

        self.worker_id = get_worker_id()
        num_threads = get_gunicorn_threads()
        if num_threads > 1:
            num_threads = num_threads - 1

        self.status = Status(
            settings,
            logger,
        )

        self.settings = settings
        self.logger = logger

        self.thread_ids: typing.Dict[str, typing.Any] = {}

        self.status.set_worker_available(self.worker_id)

        self.logger.info_msg(
            f"[{self.settings.service}] ratelimit init [{num_threads}]"
        )

    async def dispatch(
        self,
        request: Request,
        call_next: typing.Callable[[Request], typing.Awaitable[Response]],
    ) -> Response:
        thread_id, self.thread_ids = get_thread_id(self.thread_ids)
        wasSet = False

        try:
            if request.url.path == "/health":
                response = await call_next(request)

                self.status.refresh_worker(self.worker_id)

                available, total = self.status.get_worker_state(self.worker_id)

                response = self.status.set_headers(
                    response, self.worker_id, available, total
                )

                return response

            api_key = request.headers.get("X-API-Key") or request.headers.get(
                "Authorization"
            )
            if api_key and api_key.startswith("Bearer "):
                api_key = api_key.split("Bearer ")[1]
            if not api_key or api_key not in self.settings.get_valid_api_keys():
                raise HTTPException(status_code=403, detail="Invalid API key")

            request.state.api_key = api_key

            wasSet = True
            self.status.set_worker_unavailable(self.worker_id)

            response = await call_next(request)

            wasSet = False
            self.status.set_worker_available(self.worker_id)

            available, total = self.status.get_service_state()

            response.headers.update(
                {
                    "X-RateLimit-Limit-Requests": str(total),
                    "X-RateLimit-Remaining-Requests": str(max(0, available)),
                    "X-Worker-ID": f"{self.worker_id}:{thread_id}",
                }
            )

            return response
        except HTTPException as exc:
            if wasSet:
                self.status.set_worker_available(self.worker_id)

            return JSONResponse(
                status_code=exc.status_code,
                content=asdict(ProcessResponse(message=exc.detail)),
            )
