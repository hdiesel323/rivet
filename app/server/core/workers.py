from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from core.constants import ModelInfo
from core.errors import WorkerError
from core.pricing import estimate_tokens
from core.settings import Settings


@dataclass
class Completion:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str


def last_user_text(messages: list[Any]) -> str:
    texts: list[str] = []
    for message in messages:
        role = message.role if hasattr(message, "role") else message.get("role")
        content = message.content if hasattr(message, "content") else message.get("content")
        text = _content_text(content)
        if role == "user" and text:
            texts.append(text)
    if texts:
        return texts[-1]
    return " ".join(_content_text(m.content if hasattr(m, "content") else m.get("content")) for m in messages)


def _content_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text", "")))
        return " ".join(parts)
    return str(content)


def demo_complete(model: str, messages: list[Any]) -> Completion:
    heard = last_user_text(messages)
    content = (
        f"Demo worker ({model}) answered without leaving this machine.\n"
        f"Heard: {heard[:240]}\n"
        "Set OPENAI_API_KEY or LOCAL_BASE_URL for a live model. rivet_usd stays 0."
    )
    prompt_tokens = estimate_tokens(heard)
    completion_tokens = estimate_tokens(content)
    return Completion(content, model, prompt_tokens, completion_tokens, "stop")


def openai_complete(
    settings: Settings,
    model: ModelInfo,
    messages: list[Any],
    temperature: Optional[float],
    max_tokens: Optional[int],
) -> Completion:
    if model.provider == "local":
        base = settings.local_base or ""
        key = settings.local_key
    else:
        base = settings.openai_base
        key = settings.openai_key
    if not base:
        raise WorkerError(f"No base URL for provider {model.provider}", code="no_base_url")
    url = base.rstrip("/") + "/chat/completions"
    payload: dict[str, Any] = {
        "model": settings.local_model if model.provider == "local" else model.id,
        "messages": [
            {
                "role": m.role,
                "content": m.content if isinstance(m.content, (str, list)) else str(m.content),
            }
            for m in messages
        ],
        "stream": False,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise WorkerError(f"{model.provider} worker failed: {exc}", code="worker_http") from exc
    try:
        content = data["choices"][0]["message"]["content"] or ""
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or estimate_tokens(last_user_text(messages)))
        completion_tokens = int(usage.get("completion_tokens") or estimate_tokens(content))
        finish = data["choices"][0].get("finish_reason") or "stop"
        used = data.get("model") or model.id
    except (KeyError, IndexError, TypeError) as exc:
        raise WorkerError("Worker returned an unexpected payload", code="bad_worker_payload") from exc
    return Completion(content, used, prompt_tokens, completion_tokens, finish)


def run_worker(
    settings: Settings,
    model: ModelInfo,
    messages: list[Any],
    temperature: Optional[float],
    max_tokens: Optional[int],
) -> Completion:
    if model.provider == "demo":
        return demo_complete(model.id, messages)
    return openai_complete(settings, model, messages, temperature, max_tokens)
