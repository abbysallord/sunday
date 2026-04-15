"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sunday.api.middleware.errors import ErrorHandlerMiddleware
from sunday.api.routes import chat, conversations, health
from sunday.api.websocket.handler import websocket_endpoint
from sunday.config.constants import APP_FULL_NAME, APP_NAME, APP_VERSION
from sunday.database.engine import db
from sunday.utils.logging import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    log.info("sunday.starting", version=APP_VERSION)
    await db.connect()
    log.info("sunday.ready", msg=f"🌅 {APP_NAME} is ready!")
    yield
    await db.disconnect()
    log.info("sunday.shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=APP_NAME,
        description=APP_FULL_NAME,
        version=APP_VERSION,
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tauri app connects from localhost
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST routes
    app.include_router(health.router)
    app.include_router(chat.router, prefix="/api")
    app.include_router(conversations.router, prefix="/api")

    # WebSocket
    app.add_api_websocket_route("/ws", websocket_endpoint)

    return app
