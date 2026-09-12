from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from app.core.config import settings
from app.core.database import engine, Base, init_db
from app.api.v1.router import api_router
from app.api.v1.endpoints.websocket import websocket_endpoint
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
from app.core.exceptions import register_exception_handlers

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    logger.info("BlackSentinel Pulse starting up", version=settings.VERSION)

    # Auto-generate SECRET_KEY if using default (development only)
    import os, secrets
    if settings.SECRET_KEY == "change-me-in-production":
        auto_key = secrets.token_hex(32)
        os.environ["SECRET_KEY"] = auto_key
        settings.SECRET_KEY = auto_key
        logger.warning("SECRET_KEY auto-generated for development. Set SECRET_KEY env var for production.")

    # Initialize encryption vault
    from app.core.vault import init_vault
    init_vault()
    logger.info("Encryption vault initialized")

    # Create database tables
    await init_db()
    logger.info("Database tables initialized")

    yield

    logger.info("BlackSentinel Pulse shutting down")
    await engine.dispose()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="BlackSentinel Pulse",
        description="AI Autonomous Attack Surface Management Platform",
        version=settings.VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # CORS - restrict in production
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(RateLimitMiddleware, max_requests=settings.RATE_LIMIT_PER_MINUTE, window_seconds=60)
    application.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(application)
    application.include_router(api_router, prefix="/api/v1")

    # WebSocket endpoint
    application.websocket("/ws")(websocket_endpoint)

    return application


app = create_application()
