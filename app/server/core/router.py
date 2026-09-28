from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.classifier import Labels, wants_escalate
from core.constants import ModelInfo
from core.data_models import RivetOptions
from core.errors import RouteError


@dataclass
class Decision:
    model: ModelInfo
    why: str
    escalated: bool
    fallback: Optional[ModelInfo] = None
    challenger: Optional[ModelInfo] = None


def _cheap(models: list[ModelInfo]) -> ModelInfo:
    return sorted(models, key=lambda m: (m.typical_usd, m.id))[0]


def _frontier(models: list[ModelInfo]) -> ModelInfo:
    return sorted(models, key=lambda m: (m.typical_usd, m.id))[-1]


def _local(models: list[ModelInfo]) -> Optional[ModelInfo]:
    locals_ = [m for m in models if m.kind == "local"]
    if not locals_:
        return None
    return _cheap(locals_)


def _under_cap(model: ModelInfo, max_usd: float) -> bool:
    return model.typical_usd <= max_usd


def _other(models: list[ModelInfo], current: ModelInfo) -> Optional[ModelInfo]:
    rest = [m for m in models if m.id != current.id]
    if not rest:
        return None
    return _cheap(rest)


def route(
    request_model: str,
    policy: RivetOptions,
    labels: Optional[Labels],
    confidence: Optional[float],
    available: list[ModelInfo],
    user_text: str,
    slot: str,
) -> Decision:
    if not available:
        raise RouteError("No connectors granted.", code="no_connectors")

    local = _local(available)
    cheap = _cheap(available)
    frontier = _frontier(available)

    if policy.residency == "local" or (labels is not None and labels.residency):
        if local is None:
            raise RouteError(
                "Residency=local but no local worker is connected.",
                code="residency_blocked",
            )
        if not _under_cap(local, policy.max_usd):
            raise RouteError("No connected model under max vendor $.", code="over_budget")
        return Decision(local, "Residency pin.", False, None, None)

    if policy.route == "pin-local":
        if local is None:
            raise RouteError("Pinned local; connect a local worker.", code="pin_local_missing")
        if not _under_cap(local, policy.max_usd):
            raise RouteError("No connected model under max vendor $.", code="over_budget")
        return Decision(local, "Policy pin-local.", False, None, None)

    if policy.route == "pin-frontier":
        if not _under_cap(frontier, policy.max_usd):
            raise RouteError("No connected model under max vendor $.", code="over_budget")
        return Decision(frontier, "Policy pin-frontier.", False, _other(available, frontier), None)

    if slot == "none":
        if request_model and request_model != "auto":
            chosen = next((m for m in available if m.id == request_model), None)
            if chosen is None:
                raise RouteError(
                    f"Model {request_model} is not connected.",
                    code="unknown_model",
                )
            if not _under_cap(chosen, policy.max_usd):
                raise RouteError("No connected model under max vendor $.", code="over_budget")
            return Decision(chosen, "Slot none: request model.", False, _other(available, chosen), None)
        if not _under_cap(cheap, policy.max_usd):
            raise RouteError("No connected model under max vendor $.", code="over_budget")
        return Decision(cheap, "Slot none: workspace default (cheap).", False, _other(available, cheap), None)

    hard = wants_escalate(labels, confidence, user_text, slot)
    if hard and _under_cap(frontier, policy.max_usd):
        why = "Cascade: prompt looks hard; escalated."
        if confidence is not None and confidence < 0.4:
            why = "Cascade: low classifier confidence; escalated routing."
        fallback = cheap if cheap.id != frontier.id else None
        return Decision(frontier, why, True, fallback, None)

    if _under_cap(cheap, policy.max_usd):
        challenger = frontier if frontier.id != cheap.id else None
        return Decision(
            cheap,
            "Cascade: cheap-first under max $.",
            False,
            challenger,
            challenger,
        )
    raise RouteError("No connected model under max vendor $.", code="over_budget")


def assign_cell(request_hash: str, challenger_pct: float) -> str:
    if challenger_pct <= 0:
        return "control"
    bucket = int(request_hash[:8], 16) % 100
    if bucket < challenger_pct:
        return "challenger"
    return "control"


def apply_cell(decision: Decision, cell: str) -> Decision:
    if cell != "challenger" or decision.challenger is None:
        return decision
    return Decision(
        decision.challenger,
        "Split: challenger cell.",
        False,
        decision.model,
        decision.model,
    )
