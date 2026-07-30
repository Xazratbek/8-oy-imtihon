import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from sqlalchemy import text

from app.api.v1.router import api_router
from app.common.exceptions import register_exception_handlers
from app.core.config import settings
from app.db.session import engine


def create_app() -> FastAPI:
    allowed_origins = {
        settings.frontend_origin,
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    }
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Exode clone backend MVP: schools, courses, video, payments, learning, messenger, analytics.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router)

    @app.middleware("http")
    async def response_envelope(request: Request, call_next):
        response = await call_next(request)
        if request.url.path in {"/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect", "/api/v1/auth/token"}:
            return response
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type or not 200 <= response.status_code < 300:
            return response
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        try:
            data = json.loads(body.decode("utf-8")) if body else None
        except json.JSONDecodeError:
            return Response(content=body, status_code=response.status_code, headers=dict(response.headers), media_type=content_type)
        if isinstance(data, dict) and "success" in data and "code" in data:
            wrapped = data
        else:
            wrapped = {"success": True, "code": "OK", "payload": data}
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(
            content=json.dumps(wrapped, default=str),
            status_code=response.status_code,
            headers=headers,
            media_type="application/json",
        )

    @app.get("/health", tags=["System"], summary="API health")
    async def health() -> dict:
        return {"success": True, "code": "OK", "payload": {"status": "ok"}}

    @app.get("/ready", tags=["System"], summary="DB readiness")
    async def ready() -> dict:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
        return {"success": True, "code": "OK", "payload": {"database": "ok"}}

    @app.get("/api/v1/config/public", tags=["System"], summary="Frontend public config")
    async def public_config() -> dict:
        return {"google_client_id": settings.google_client_id}

    return app


app = create_app()
