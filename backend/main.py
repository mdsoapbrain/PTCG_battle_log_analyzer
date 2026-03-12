from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes_matches import router as matches_router
from backend.api.routes_parse import router as parse_router
from backend.api.routes_stats import router as stats_router
from backend.core.config import get_settings
from backend.core.database import init_db
from backend.utils.responses import error_response, success_response


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for parsing PTCG Live battle logs, storing match history, and exposing analytics for frontend apps.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins if settings.cors_allowed_origins else ["*"],
    allow_origin_regex=settings.cors_allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code=f"HTTP_{exc.status_code}", detail=str(exc.detail), message="Request failed").model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(code="VALIDATION_ERROR", detail=str(exc), message="Validation failed").model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(code="INTERNAL_ERROR", detail=str(exc), message="Internal server error").model_dump(),
    )


@app.get("/health", summary="Health check", description="Basic liveness check for frontend and deployment probes.")
def health():
    return success_response(
        message="Service is healthy.",
        data={"status": "ok", "env": settings.app_env},
    )


@app.get("/version", summary="Version info", description="Returns backend version and runtime configuration metadata.")
def version():
    return success_response(
        message="Version fetched successfully.",
        data={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "app_env": settings.app_env,
            "auth_mode": settings.auth_mode,
            "api_base_url": settings.api_base_url,
        },
    )


app.include_router(parse_router, prefix=settings.api_prefix)
app.include_router(matches_router, prefix=settings.api_prefix)
app.include_router(stats_router, prefix=settings.api_prefix)
