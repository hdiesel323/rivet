from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from core.constants import VERSION
from core.data_models import (
    ChatCompletionRequest,
    Connector,
    EvalCompareRequest,
    EvalRunRequest,
    HealthResponse,
)
from core.errors import RouteError, WorkerError
from core.evalset import FIXTURE, fixture
from core.ledger import count, get, list_rows, to_csv
from core.orchestrator import complete
from core.settings import load_settings

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("rivet")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    from core.ledger import init_db

    settings = load_settings()
    init_db(settings.db_path)
    logger.info("rivet %s db=%s demo=%s", VERSION, settings.db_path, settings.demo)
    yield


app = FastAPI(title="Rivet", version=VERSION, lifespan=lifespan)


def _cors() -> list[str]:
    return list(load_settings().cors)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors() or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_gate(request: Request, call_next):
    settings = load_settings()
    if not settings.api_key:
        return await call_next(request)
    if request.url.path in {"/health", "/docs", "/openapi.json"}:
        return await call_next(request)
    auth = request.headers.get("authorization", "")
    expected = "Bearer " + settings.api_key
    if auth != expected:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "message": "Missing or invalid API key",
                    "type": "invalid_request_error",
                    "code": "unauthorized",
                }
            },
        )
    return await call_next(request)


@app.exception_handler(RouteError)
async def route_error_handler(_request: Request, exc: RouteError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"message": exc.message, "type": exc.type, "code": exc.code}},
    )


@app.exception_handler(WorkerError)
async def worker_error_handler(_request: Request, exc: WorkerError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"message": exc.message, "type": exc.type, "code": exc.code}},
    )



@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = load_settings()
    connectors = [m.provider for m in settings.available_models()]
    unique = list(dict.fromkeys(connectors))
    return HealthResponse(
        status="ok",
        version=VERSION,
        demo=settings.demo,
        connectors=unique,
        ledger_rows=count(settings.db_path),
    )


@app.get("/v1/models")
def models() -> dict[str, Any]:
    settings = load_settings()
    data = [{"id": "auto", "object": "model", "owned_by": "rivet"}]
    for info in settings.available_models():
        data.append({"id": info.id, "object": "model", "owned_by": info.provider})
    return {"object": "list", "data": data}


@app.get("/v1/connectors")
def connectors() -> dict[str, list[Connector]]:
    settings = load_settings()
    items = [
        Connector(
            id="demo",
            kind="local",
            status="granted" if settings.demo else "off",
            models=["demo-small", "demo-frontier"],
        ),
        Connector(
            id="openai",
            kind="cloud",
            status="granted" if settings.openai_enabled else "missing_key",
            models=list(settings.openai_models),
        ),
        Connector(
            id="local",
            kind="local",
            status="granted" if settings.local_enabled else "missing_url",
            models=[settings.local_model],
        ),
        Connector(
            id="jev",
            kind="classifier",
            status="granted" if settings.jev_url else "missing_url",
            models=[],
        ),
    ]
    return {"connectors": items}


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    return complete(req)


@app.get("/v1/ledger")
def ledger_list(
    limit: int = Query(50, ge=1, le=500),
    cluster: Optional[str] = None,
    cell: Optional[str] = None,
    slot: Optional[str] = None,
):
    settings = load_settings()
    return {"object": "list", "data": list_rows(settings.db_path, limit, cluster, cell, slot)}


@app.get("/v1/ledger.csv")
def ledger_csv(
    limit: int = Query(500, ge=1, le=5000),
    cluster: Optional[str] = None,
    cell: Optional[str] = None,
    slot: Optional[str] = None,
):
    settings = load_settings()
    rows = list_rows(settings.db_path, limit, cluster, cell, slot)
    return PlainTextResponse(to_csv(rows), media_type="text/csv")


@app.get("/v1/ledger/{receipt_id}")
def ledger_one(receipt_id: str):
    settings = load_settings()
    row = get(settings.db_path, receipt_id)
    if row is None:
        raise HTTPException(status_code=404, detail="receipt not found")
    return row


@app.get("/v1/eval/fixture")
def eval_fixture(limit: int = Query(50, ge=1, le=50)):
    return {"object": "list", "count": len(FIXTURE), "data": fixture(limit)}


def _run_slot(slot: str, limit: int, route: str) -> dict[str, Any]:
    from core.data_models import Message, RivetOptions

    rows = []
    for item in fixture(limit):
        req = ChatCompletionRequest(
            model="auto",
            messages=[Message(role="user", content=item["prompt"])],
            rivet=RivetOptions(slot=slot, route=route),  # type: ignore[arg-type]
        )
        t0 = time.perf_counter()
        try:
            resp = complete(req)
            rows.append(
                {
                    "id": item["id"],
                    "task": item["task"],
                    "hardness": item["hardness"],
                    "model_used": resp.rivet.model_used,
                    "vendor_usd": resp.rivet.vendor_usd,
                    "rivet_usd": resp.rivet.rivet_usd,
                    "escalated": resp.rivet.escalated,
                    "cache_hit": resp.rivet.cache_hit,
                    "why": resp.rivet.why,
                    "error": None,
                    "ms": int((time.perf_counter() - t0) * 1000),
                }
            )
        except (RouteError, WorkerError) as exc:
            rows.append(
                {
                    "id": item["id"],
                    "task": item["task"],
                    "hardness": item["hardness"],
                    "model_used": None,
                    "vendor_usd": 0.0,
                    "rivet_usd": 0.0,
                    "escalated": False,
                    "cache_hit": False,
                    "why": None,
                    "error": exc.message,
                    "ms": int((time.perf_counter() - t0) * 1000),
                }
            )
    total = round(sum(r["vendor_usd"] or 0 for r in rows), 6)
    by_model: dict[str, int] = {}
    for row in rows:
        key = row["model_used"] or "error"
        by_model[key] = by_model.get(key, 0) + 1
    return {
        "slot": slot,
        "n": len(rows),
        "vendor_usd": total,
        "rivet_usd": 0.0,
        "by_model": by_model,
        "escalated": sum(1 for r in rows if r["escalated"]),
        "cache_hits": sum(1 for r in rows if r["cache_hit"]),
        "rows": rows,
    }


@app.post("/v1/eval/run")
def eval_run(req: EvalRunRequest):
    return _run_slot(req.slot, req.limit, req.route)


@app.post("/v1/eval/compare")
def eval_compare(req: EvalCompareRequest):
    columns = [_run_slot(slot, req.limit, "cascade") for slot in req.slots]
    quality_delta = None
    return {
        "slots": req.slots,
        "quality_delta": quality_delta,
        "note": "No quality delta: fixture rows are unscored.",
        "columns": [
            {
                "slot": c["slot"],
                "n": c["n"],
                "vendor_usd": c["vendor_usd"],
                "by_model": c["by_model"],
                "escalated": c["escalated"],
            }
            for c in columns
        ],
        "detail": columns,
    }


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("RIVET_HOST", "127.0.0.1")
    port = int(os.environ.get("RIVET_PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=True)
