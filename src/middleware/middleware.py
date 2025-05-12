from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware


class CustomMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super(CustomMiddleware, self).__init__(app)

    async def dispatch(self, request: Response, call_next):
        response = await call_next(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
