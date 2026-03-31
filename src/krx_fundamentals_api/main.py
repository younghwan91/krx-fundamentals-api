from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from krx_fundamentals_api.config import settings
from krx_fundamentals_api.routes import company, market
from krx_fundamentals_api.services.cache import close_redis
from krx_fundamentals_api.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting KRX Fundamentals API")
    start_scheduler()
    yield
    logger.info("Shutting down KRX Fundamentals API")
    stop_scheduler()
    await close_redis()


app = FastAPI(
    title="KRX Fundamentals REST API",
    description="국내 기업 펀더멘탈 데이터 — 재무제표, 투자지표, 배당, 대주주",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed = time.monotonic() - start
        logger.info(
            "%s %s → %d (%.2fs)",
            request.method, request.url.path, response.status_code, elapsed,
        )
        return response


app.add_middleware(RequestLoggingMiddleware)

app.include_router(company.router)
app.include_router(market.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
