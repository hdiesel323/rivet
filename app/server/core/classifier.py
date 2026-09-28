from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from core.constants import (
    CODE_RE,
    EXTRACT_RE,
    HARD_RE,
    LOW_CONFIDENCE,
    PROSE_RE,
    RESIDENCY_RE,
    TOOL_RE,
)
from core.data_models import TaskLabel
from core.errors import RouteError
from core.settings import Settings


@dataclass
class Labels:
    task: TaskLabel
    hardness: float
    residency: bool
    experiment: Optional[str]
    duplicate_of: Optional[str]
    confidence: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "hardness": self.hardness,
            "residency": self.residency,
            "experiment": self.experiment,
            "duplicate_of": self.duplicate_of,
        }


def is_hard(text: str) -> bool:
    return HARD_RE.search(text) is not None


def heuristic_labels(text: str) -> Labels:
    if CODE_RE.search(text):
        task: TaskLabel = "code"
    elif EXTRACT_RE.search(text):
        task = "extract"
    elif TOOL_RE.search(text):
        task = "tool"
    elif PROSE_RE.search(text) or len(text.split()) > 40:
        task = "prose"
    else:
        task = "chat"
    hard = is_hard(text)
    hardness = 0.85 if hard else (0.45 if task == "code" else 0.2)
    return Labels(
        task=task,
        hardness=hardness,
        residency=RESIDENCY_RE.search(text) is not None,
        experiment=None,
        duplicate_of=None,
        confidence=0.72 if task != "chat" else 0.55,
    )


def jev_labels(text: str, url: str) -> Labels:
    try:
        response = httpx.post(url, json={"text": text}, timeout=10.0)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise RouteError(f"Jev classifier failed: {exc}", code="jev_failed", status=502) from exc
    task = data.get("task", "chat")
    if task not in {"code", "prose", "extract", "tool", "chat"}:
        task = "chat"
    return Labels(
        task=task,
        hardness=float(data.get("hardness", 0.5)),
        residency=bool(data.get("residency", False)),
        experiment=data.get("experiment"),
        duplicate_of=data.get("duplicate_of"),
        confidence=float(data.get("confidence", 0.5)),
    )


def classify(slot: str, text: str, settings: Settings) -> tuple[Optional[Labels], Optional[float], str]:
    if slot in {"none", "rules"}:
        return None, None, slot
    if slot == "classifier:heuristic":
        labels = heuristic_labels(text)
        return labels, labels.confidence, slot
    if slot == "jev":
        if not settings.jev_url:
            raise RouteError(
                "Jev slot selected but JEV_URL is not set",
                code="jev_unconfigured",
            )
        labels = jev_labels(text, settings.jev_url)
        return labels, labels.confidence, slot
    raise RouteError(f"Unknown classifier slot: {slot}", code="unknown_slot")


def wants_escalate(labels: Optional[Labels], confidence: Optional[float], text: str, slot: str) -> bool:
    if confidence is not None and confidence < LOW_CONFIDENCE:
        return True
    if labels is not None:
        return labels.hardness >= 0.7
    if slot == "rules":
        return is_hard(text)
    return False
