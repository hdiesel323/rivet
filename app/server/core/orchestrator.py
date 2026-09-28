from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from core.classifier import Labels, classify
from core.data_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    ChoiceMessage,
    ClassifierReceipt,
    RivetOptions,
    RivetReceipt,
    Usage,
)
from core.errors import RouteError, WorkerError
from core.ledger import insert, lookup_exact
from core.pricing import vendor_usd
from core.router import Decision, apply_cell, assign_cell, route
from core.settings import Settings, load_settings
from core.workers import last_user_text, run_worker


def _now() -> datetime:
    return datetime.now(timezone.utc)


def request_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def cluster_id(task: str, text: str) -> str:
    norm = re.sub(r"\s+", " ", text.lower()).strip()[:48]
    digest = hashlib.sha256(norm.encode()).hexdigest()[:10]
    return f"{task}:{digest}"


def merge_policy(settings: Settings, override: Optional[RivetOptions]) -> RivetOptions:
    base = RivetOptions(
        slot=settings.slot if settings.slot in {"none", "rules", "jev", "classifier:heuristic"} else "rules",
        route=settings.route if settings.route in {"cascade", "pin-local", "pin-frontier"} else "cascade",
        residency=settings.residency if settings.residency in {"any", "local"} else "any",
        max_usd=settings.max_usd,
        split_challenger_pct=0,
    )
    if override is None:
        return base
    return override


def _new_id() -> str:
    return "chatcmpl_rvt_" + uuid.uuid4().hex[:12]


def complete(
    req: ChatCompletionRequest,
    settings: Optional[Settings] = None,
) -> ChatCompletionResponse:
    settings = settings or load_settings()
    started = time.perf_counter()
    if req.stream:
        raise RouteError("streaming is not supported in this MVP", code="stream_not_supported")
    if not req.messages:
        raise RouteError("messages must not be empty", code="invalid_request")

    policy = merge_policy(settings, req.rivet)
    user_text = last_user_text(req.messages)
    labels, confidence, classifier_id = classify(policy.slot, user_text, settings)
    task = labels.task if labels else "chat"
    cluster = cluster_id(task, user_text)

    hash_payload = {
        "model": req.model,
        "messages": [m.model_dump() for m in req.messages],
        "slot": policy.slot,
        "route": policy.route,
        "residency": policy.residency,
        "max_usd": policy.max_usd,
        "split": policy.split_challenger_pct,
    }
    digest = request_hash(hash_payload)
    cached = lookup_exact(settings.db_path, digest)
    if cached:
        return _replay_cache(cached, started, policy.slot, settings.db_path)

    available = settings.available_models()
    decision = route(
        req.model,
        policy,
        labels,
        confidence,
        available,
        user_text,
        policy.slot,
    )
    cell = assign_cell(digest, policy.split_challenger_pct)
    decision = apply_cell(decision, cell)

    fallback_used = False
    try:
        completion = run_worker(
            settings, decision.model, req.messages, req.temperature, req.max_tokens
        )
    except WorkerError:
        if decision.fallback is None:
            raise
        completion = run_worker(
            settings, decision.fallback, req.messages, req.temperature, req.max_tokens
        )
        decision = Decision(
            decision.fallback,
            decision.why + " Fallback worker.",
            decision.escalated,
            None,
        )
        fallback_used = True

    cost = vendor_usd(decision.model, completion.prompt_tokens, completion.completion_tokens)
    latency = int((time.perf_counter() - started) * 1000)
    created = _now()
    receipt_id = _new_id()
    response = ChatCompletionResponse(
        id=receipt_id,
        created=int(created.timestamp()),
        model=decision.model.id,
        choices=[
            Choice(
                index=0,
                message=ChoiceMessage(role="assistant", content=completion.content),
                finish_reason=completion.finish_reason,
            )
        ],
        usage=Usage(
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            total_tokens=completion.prompt_tokens + completion.completion_tokens,
        ),
        rivet=RivetReceipt(
            receipt_id=receipt_id,
            model_used=decision.model.id,
            provider=decision.model.provider,
            why=decision.why,
            vendor_usd=cost,
            rivet_usd=0.0,
            escalated=decision.escalated,
            fallback=fallback_used,
            cache_hit=False,
            classifier=ClassifierReceipt(
                slot=classifier_id,
                labels=labels.as_dict() if labels else None,
                confidence=confidence,
            ),
            experiment_cell=cell,
            cluster=cluster,
            latency_ms=latency,
        ),
    )
    _persist(settings.db_path, digest, cluster, response, user_text, labels, confidence, classifier_id)
    return response


def _persist(
    db_path: str,
    digest: str,
    cluster: str,
    response: ChatCompletionResponse,
    prompt: str,
    labels: Optional[Labels],
    confidence: Optional[float],
    classifier_id: str,
) -> None:
    rivet = response.rivet
    insert(
        db_path,
        {
            "id": response.id,
            "created_at": datetime.fromtimestamp(response.created, tz=timezone.utc).isoformat(),
            "request_hash": digest,
            "cluster": cluster,
            "classifier_id": classifier_id,
            "labels_json": json.dumps(labels.as_dict()) if labels else None,
            "confidence": confidence,
            "model_used": rivet.model_used,
            "provider": rivet.provider,
            "experiment_cell": rivet.experiment_cell,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "vendor_usd": rivet.vendor_usd,
            "rivet_usd": 0.0,
            "latency_ms": rivet.latency_ms,
            "fallback": int(rivet.fallback),
            "cache_hit": int(rivet.cache_hit),
            "why": rivet.why,
            "prompt": prompt,
            "response": response.choices[0].message.content,
            "slot": rivet.classifier.slot,
            "escalated": int(rivet.escalated),
        },
    )


def _replay_cache(row: dict[str, Any], started: float, slot: str, db_path: str) -> ChatCompletionResponse:
    receipt_id = _new_id()
    created = _now()
    latency = int((time.perf_counter() - started) * 1000)
    labels_raw = row.get("labels_json")
    labels = json.loads(labels_raw) if labels_raw else None
    response = ChatCompletionResponse(
        id=receipt_id,
        created=int(created.timestamp()),
        model=row["model_used"],
        choices=[
            Choice(
                index=0,
                message=ChoiceMessage(role="assistant", content=row["response"] or ""),
                finish_reason="stop",
            )
        ],
        usage=Usage(
            prompt_tokens=int(row["input_tokens"]),
            completion_tokens=int(row["output_tokens"]),
            total_tokens=int(row["input_tokens"]) + int(row["output_tokens"]),
        ),
        rivet=RivetReceipt(
            receipt_id=receipt_id,
            model_used=row["model_used"],
            provider=row["provider"],
            why="Exact cache hit.",
            vendor_usd=0.0,
            rivet_usd=0.0,
            escalated=bool(row.get("escalated")),
            fallback=False,
            cache_hit=True,
            classifier=ClassifierReceipt(
                slot=row.get("slot") or slot,
                labels=labels,
                confidence=row.get("confidence"),
            ),
            experiment_cell=row["experiment_cell"],
            cluster=row["cluster"],
            latency_ms=latency,
        ),
    )
    insert(
        db_path,
        {
            "id": receipt_id,
            "created_at": created.isoformat(),
            "request_hash": row["request_hash"],
            "cluster": row["cluster"],
            "classifier_id": row.get("classifier_id") or slot,
            "labels_json": row.get("labels_json"),
            "confidence": row.get("confidence"),
            "model_used": row["model_used"],
            "provider": row["provider"],
            "experiment_cell": row["experiment_cell"],
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "vendor_usd": 0.0,
            "rivet_usd": 0.0,
            "latency_ms": latency,
            "fallback": 0,
            "cache_hit": 1,
            "why": "Exact cache hit.",
            "prompt": row.get("prompt"),
            "response": row.get("response"),
            "slot": row.get("slot") or slot,
            "escalated": row.get("escalated") or 0,
        },
    )
    return response

