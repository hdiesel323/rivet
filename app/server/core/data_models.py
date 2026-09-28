from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


Slot = Literal["none", "rules", "jev", "classifier:heuristic"]
Route = Literal["cascade", "pin-local", "pin-frontier"]
Residency = Literal["any", "local"]
TaskLabel = Literal["code", "prose", "extract", "tool", "chat"]


class Message(BaseModel):
    role: str
    content: Any = None
    name: Optional[str] = None


class RivetOptions(BaseModel):
    slot: Slot = "rules"
    route: Route = "cascade"
    residency: Residency = "any"
    max_usd: float = Field(0.05, ge=0)
    split_challenger_pct: float = Field(0, ge=0, le=100)


class ChatCompletionRequest(BaseModel):
    model: str = "auto"
    messages: list[Message]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False
    rivet: Optional[RivetOptions] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChoiceMessage(BaseModel):
    role: str
    content: str


class Choice(BaseModel):
    index: int
    message: ChoiceMessage
    finish_reason: str


class ClassifierReceipt(BaseModel):
    slot: str
    labels: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None


class RivetReceipt(BaseModel):
    receipt_id: str
    model_used: str
    provider: str
    why: str
    vendor_usd: float
    rivet_usd: float = 0.0
    escalated: bool
    fallback: bool = False
    cache_hit: bool = False
    classifier: ClassifierReceipt
    experiment_cell: str = "control"
    cluster: str
    latency_ms: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: Usage
    rivet: RivetReceipt


class Connector(BaseModel):
    id: str
    kind: str
    status: str
    models: list[str]


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    version: str
    demo: bool
    connectors: list[str]
    ledger_rows: int


class EvalRunRequest(BaseModel):
    slot: Slot = "rules"
    limit: int = Field(50, ge=1, le=50)
    route: Route = "cascade"


class EvalCompareRequest(BaseModel):
    slots: list[Slot] = Field(default_factory=lambda: ["rules", "none"])
    limit: int = Field(50, ge=1, le=50)
