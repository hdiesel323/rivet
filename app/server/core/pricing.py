from __future__ import annotations

from core.constants import ModelInfo


def vendor_usd(model: ModelInfo, prompt_tokens: int, completion_tokens: int) -> float:
    cost = (prompt_tokens / 1_000_000) * model.in_per_million + (
        completion_tokens / 1_000_000
    ) * model.out_per_million
    return round(cost, 6)


def estimate_tokens(text: str) -> int:
    words = len(text.split())
    return max(1, int(words * 1.3 + 0.5))
