from __future__ import annotations

from core.data_models import ChatCompletionRequest, Message, RivetOptions
from core.evalset import FIXTURE
from core.ledger import get, list_rows
from core.orchestrator import complete
from core.settings import load_settings


def _req(prompt: str, **rivet) -> ChatCompletionRequest:
    return ChatCompletionRequest(
        model=rivet.pop("model", "auto"),
        messages=[Message(role="user", content=prompt)],
        rivet=RivetOptions(**rivet) if rivet else RivetOptions(),
    )


def test_receipt_shape_and_zero_cut(db_path):
    resp = complete(_req("Hello from Rivet."), load_settings())
    assert resp.object == "chat.completion"
    assert resp.model == resp.rivet.model_used
    assert resp.model != "auto"
    assert resp.choices[0].finish_reason == "stop"
    assert resp.usage.total_tokens == resp.usage.prompt_tokens + resp.usage.completion_tokens
    assert resp.usage.total_tokens > 0
    assert resp.created > 0
    assert resp.rivet.rivet_usd == 0.0
    assert resp.rivet.vendor_usd == 0.0
    assert resp.rivet.cache_hit is False
    assert resp.rivet.receipt_id == resp.id
    row = get(str(db_path), resp.id)
    assert row is not None
    assert row["rivet_usd"] == 0.0


def test_cache_hit_zeroes_vendor(db_path):
    prompt = "Cache me exactly once please."
    first = complete(_req(prompt), load_settings())
    second = complete(_req(prompt), load_settings())
    assert first.rivet.cache_hit is False
    assert second.rivet.cache_hit is True
    assert second.rivet.vendor_usd == 0.0
    assert second.rivet.why == "Exact cache hit."
    assert second.choices[0].message.content == first.choices[0].message.content
    rows = list_rows(str(db_path), limit=10)
    assert len(rows) == 2


def test_stream_rejected(db_path):
    from core.errors import RouteError

    req = ChatCompletionRequest(
        model="auto",
        messages=[Message(role="user", content="hi")],
        stream=True,
    )
    try:
        complete(req, load_settings())
        assert False, "expected RouteError"
    except RouteError as exc:
        assert exc.code == "stream_not_supported"


def test_fixture_has_fifty_labeled_prompts():
    assert len(FIXTURE) == 50
    for item in FIXTURE:
        assert item["task"] in {"code", "prose", "extract", "tool", "chat"}
        assert item["hardness"] in {"easy", "hard"}
        assert item["prompt"]
