from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

VERSION = "0.1.0"

HARD_RE = re.compile(
    r"(?i)\b(legal opinion|refactor|architecture|multi-step|code review|prove that)\b"
)
CODE_RE = re.compile(
    r"(?i)\b(code|function|python|typescript|javascript|refactor|bug|stack trace|compile|pull request)\b"
)
EXTRACT_RE = re.compile(r"(?i)\b(extract|json|csv|table|parse|fields|schema)\b")
TOOL_RE = re.compile(r"(?i)\b(tool|function call|webhook|http get|api request)\b")
RESIDENCY_RE = re.compile(
    r"(?i)\b(pii|hipaa|air-?gapped|on-?prem|must stay local|residency)\b"
)
PROSE_RE = re.compile(r"(?i)\b(write|draft|essay|blog|paragraph|story)\b")

LOW_CONFIDENCE = 0.4


@dataclass(frozen=True)
class ModelInfo:
    id: str
    provider: str
    kind: Literal["local", "cloud"]
    typical_usd: float
    in_per_million: float
    out_per_million: float


CATALOG: dict[str, ModelInfo] = {
    "demo-small": ModelInfo("demo-small", "demo", "local", 0.0001, 0.0, 0.0),
    "demo-frontier": ModelInfo("demo-frontier", "demo", "local", 0.008, 0.0, 0.0),
    "gpt-4o-mini": ModelInfo("gpt-4o-mini", "openai", "cloud", 0.002, 0.15, 0.60),
    "gpt-4o": ModelInfo("gpt-4o", "openai", "cloud", 0.02, 2.50, 10.0),
    "local-llama": ModelInfo("local-llama", "local", "local", 0.0004, 0.0, 0.0),
}

OPENAI_DEFAULT_MODELS = ("gpt-4o-mini", "gpt-4o")
