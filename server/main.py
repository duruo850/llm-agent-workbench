from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
import sys

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from common.env import get_database_url
from common.logging_config import configure_app_logging
from server.db.migrate import migrate_on_startup
from server.db.session import Database
from server.routers import register_routers

Database.init(get_database_url())

configure_app_logging()
request_logger = logging.getLogger("billmind.request")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await migrate_on_startup(Database.get().engine)
    yield


app = FastAPI(title="BillMind API", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    query = request.url.query
    path = request.url.path + (f"?{query}" if query else "")
    request_logger.info("%s %s -> %s (%.1fms)", request.method, path, response.status_code, duration_ms)
    return response


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
    detail = "Database constraint violation"
    message = str(exc.orig).lower() if exc.orig else ""
    if "unique" in message:
        detail = "Record already exists or unique constraint violated"
    elif "foreign key" in message:
        detail = "Referenced record not found"
    return JSONResponse(status_code=409, detail=detail)


register_routers(app)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
