"""Construcción de la aplicación FastAPI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ..biometrics.engine import FaceEngine, OpenCVFaceEngine, ensure_models
from ..biometrics.gallery import Gallery
from ..config import Settings
from ..crypto import load_keyring
from ..db import connect, migrate
from ..door import DoorClient
from ..kiosk_flow import KioskFlow
from ..state import AppState
from . import routes_admin, routes_auth, routes_kiosk, routes_people
from .deps import LoginRequired, render

_CSP = (
    "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; "
    "connect-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; "
    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)


class _BodyTooLarge(Exception):
    pass


class BodyLimitMiddleware:
    """Corta peticiones demasiado grandes aunque oculten su tamaño con transferencia por partes."""

    def __init__(self, app: ASGIApp, limit: int) -> None:
        self.app = app
        self.limit = limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        too_large = JSONResponse({"detail": "Archivo demasiado grande"}, status_code=413)
        declared = Headers(scope=scope).get("content-length", "0")
        if declared.isdigit() and int(declared) > self.limit:
            await too_large(scope, receive, send)
            return

        received = 0
        started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.limit:
                raise _BodyTooLarge
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal started
            started = started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _BodyTooLarge:
            if not started:
                await too_large(scope, receive, send)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope["path"]

        async def with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Content-Security-Policy"] = _CSP
                headers["X-Content-Type-Options"] = "nosniff"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
                # El panel muestra datos personales: el navegador no debe guardarlos en caché.
                if not path.startswith("/static/"):
                    headers["Cache-Control"] = "no-store"
            await send(message)

        await self.app(scope, receive, with_headers)


def create_app(
    settings: Settings | None = None,
    engine: FaceEngine | None = None,
    door: DoorClient | None = None,
) -> FastAPI:
    settings = settings or Settings()
    keys = load_keyring(settings.master_key, settings.data_dir)
    conn = connect(settings.db_path)
    migrate(conn)
    conn.close()

    if engine is None:
        ensure_models(settings.models_dir)
        engine = OpenCVFaceEngine(settings.models_dir)

    state = AppState(
        settings=settings,
        keys=keys,
        engine=engine,
        gallery=Gallery(settings.match_threshold, settings.match_margin),
        door=door or DoorClient(),
    )
    state.reload_gallery()

    app = FastAPI(
        title="Portero",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.portero = state
    app.state.flow = KioskFlow(state)

    app.add_middleware(BodyLimitMiddleware, limit=settings.max_frame_bytes + 64 * 1024)
    app.add_middleware(SecurityHeadersMiddleware)

    @app.exception_handler(LoginRequired)
    async def login_required(request: Request, _: LoginRequired) -> Response:
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": "Sesión requerida"}, status_code=401)
        return RedirectResponse("/login", status_code=303)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> Response:
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        message = {404: "Esa página no existe."}.get(exc.status_code, str(exc.detail))
        html: HTMLResponse = render(
            request,
            "error.html",
            status_code=exc.status_code,
            code=exc.status_code,
            message=message,
        )
        return html

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict:
        return {"status": "ok", "personas_en_galeria": state.gallery.size()}

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(routes_auth.router)
    app.include_router(routes_admin.router)
    app.include_router(routes_people.router)
    app.include_router(routes_kiosk.router)
    return app
