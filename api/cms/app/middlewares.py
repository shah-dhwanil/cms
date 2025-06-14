from uuid import uuid4
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger
from structlog.contextvars import bind_contextvars, clear_contextvars


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        bind_contextvars(request_id=request.state.request_id)
        response = await call_next(request)
        clear_contextvars()
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = get_logger()
        logger.info(
            event="request_recieved", method=request.method, path=request.url.path
        )
        response = await call_next(request)
        logger.info(
            event="response_sent",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        return response
