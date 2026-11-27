"""
WebScout Backend Application.

Configures FastAPI, lifespan hooks for browser resource management,
CORS middleware, and modular API routers.
"""

from contextlib import asynccontextmanager
import logging
import sys

# On Windows, Playwright requires the ProactorEventLoop to manage browser subprocesses
if sys.platform == "win32":
    import asyncio
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health, research
from app.config import settings
from app.services.orchestrator import get_playwright_fetcher

# Configure application logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("webscout")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes and warms up the Playwright browser on startup,
    and guarantees reliable browser resource teardown on shutdown.
    """
    logger.info("WebScout Backend starting up...")
    logger.info(
        "Active Fetcher: %s | Active Analyzer: %s",
        settings.active_fetcher,
        settings.active_analyzer,
    )

    # Pre-warm Playwright Chromium if running in playwright mode
    if settings.active_fetcher == "playwright":
        try:
            fetcher = get_playwright_fetcher()
            await fetcher.start()
            logger.info("Playwright Chromium browser warmed up.")
        except Exception as e:
            logger.warning(
                "Could not pre-warm Playwright Chromium on startup: %s (%s)",
                type(e).__name__,
                e,
                exc_info=True,
            )

    yield

    logger.info("WebScout Backend shutting down...")
    # Clean up browser and driver resources
    if settings.active_fetcher == "playwright":
        try:
            fetcher = get_playwright_fetcher()
            await fetcher.close()
            logger.info("Playwright Chromium browser resources cleaned up.")
        except Exception as e:
            logger.error("Error during Playwright browser cleanup: %s", e)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API Foundation for WebScout Multi-Website AI Research Agent",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    clean_messages = []
    for err in errors:
        loc = " -> ".join([str(x) for x in err.get("loc", []) if x != "body"])
        msg = err.get("msg", "Invalid value")
        clean_messages.append(f"{loc}: {msg}" if loc else msg)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "; ".join(clean_messages) or "Validation error.",
            "errors": jsonable_encoder(errors),
        },
    )


# Generic catch-all exception handler to prevent leaking stack traces
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )


# Root verification endpoint
@app.get("/", tags=["Root"])
def read_root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "fetcher": settings.active_fetcher,
        "analyzer": settings.active_analyzer,
        "docs": "/docs",
    }


# Include modular routers under /api
app.include_router(health.router, prefix="/api")
app.include_router(research.router, prefix="/api")
