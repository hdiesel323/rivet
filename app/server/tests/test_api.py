from __future__ import annotations

from fastapi.testclient import TestClient

from server import app


def test_health(db_path):
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "demo" in body["connectors"]


def test_chat_completions_demo(db_path):
    client = TestClient(app)
    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "auto",
            "messages": [{"role": "user", "content": "Write a 2-line status update."}],
            "rivet": {"slot": "rules", "route": "cascade", "max_usd": 0.05},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["rivet"]["rivet_usd"] == 0.0
    assert "usage" in body
    receipt = client.get(f"/v1/ledger/{body['id']}")
    assert receipt.status_code == 200
    assert receipt.json()["id"] == body["id"]


def test_improve_does_not_escalate_via_http(db_path):
    client = TestClient(app)
    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "auto",
            "messages": [{"role": "user", "content": "Improve the README please."}],
            "rivet": {"slot": "rules", "route": "cascade"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["rivet"]["escalated"] is False
    assert resp.json()["rivet"]["model_used"] == "demo-small"


def test_jev_without_url(db_path):
    client = TestClient(app)
    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "auto",
            "messages": [{"role": "user", "content": "hello"}],
            "rivet": {"slot": "jev"},
        },
    )
    assert resp.status_code == 400
    err = resp.json()["error"]
    assert err["code"] == "jev_unconfigured"


def test_ledger_csv(db_path):
    client = TestClient(app)
    client.post(
        "/v1/chat/completions",
        json={"model": "auto", "messages": [{"role": "user", "content": "csv please"}]},
    )
    csv = client.get("/v1/ledger.csv")
    assert csv.status_code == 200
    assert "receipt" in csv.text or "id," in csv.text
    assert "rivet_usd" in csv.text


def test_eval_compare_does_not_invent_quality(db_path):
    client = TestClient(app)
    resp = client.post(
        "/v1/eval/compare",
        json={"slots": ["rules", "none"], "limit": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["quality_delta"] is None
    assert "unscored" in body["note"]
    assert len(body["columns"]) == 2


def test_openai_worker_maps_usage(db_path, monkeypatch):
    import core.workers as workers
    from core.constants import CATALOG
    from core.settings import load_settings
    from core.workers import Completion

    def fake_openai(settings, model, messages, temperature, max_tokens):
        return Completion("live answer", model.id, 11, 7, "stop")

    monkeypatch.setattr(workers, "openai_complete", fake_openai)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("RIVET_DEMO", "0")
    from core.data_models import ChatCompletionRequest, Message, RivetOptions
    from core.orchestrator import complete
    from core.pricing import vendor_usd

    settings = load_settings()
    assert settings.openai_enabled
    resp = complete(
        ChatCompletionRequest(
            model="gpt-4o-mini",
            messages=[Message(role="user", content="hi")],
            rivet=RivetOptions(slot="none", max_usd=1),
        ),
        settings,
    )
    expected = vendor_usd(CATALOG["gpt-4o-mini"], 11, 7)
    assert resp.rivet.vendor_usd == expected
    assert expected > 0
    assert resp.rivet.rivet_usd == 0.0
    assert resp.choices[0].message.content == "live answer"
