from __future__ import annotations

import pytest

from core.classifier import heuristic_labels, is_hard
from core.constants import CATALOG
from core.data_models import RivetOptions
from core.errors import RouteError
from core.router import route


DEMO = [CATALOG["demo-small"], CATALOG["demo-frontier"]]
MIXED = [
    CATALOG["local-llama"],
    CATALOG["gpt-4o-mini"],
    CATALOG["gpt-4o"],
]


def test_improve_is_not_hard():
    assert is_hard("Can you improve this sentence: Rivet is a switchboard.") is False
    assert is_hard("Improve the README so the quick start is three commands.") is False


def test_illegal_is_not_legal_opinion():
    assert is_hard("Is this illegal?") is False


def test_code_review_is_hard():
    assert is_hard("Please do a code review of this PR that adds a FastAPI proxy.") is True


def test_cascade_easy_picks_cheap(db_path):
    decision = route(
        "auto",
        RivetOptions(slot="rules", route="cascade", max_usd=0.05),
        None,
        None,
        DEMO,
        "Hello, what can Rivet do in one sentence?",
        "rules",
    )
    assert decision.model.id == "demo-small"
    assert decision.escalated is False


def test_cascade_hard_escalates(db_path):
    decision = route(
        "auto",
        RivetOptions(slot="rules", route="cascade", max_usd=0.05),
        None,
        None,
        DEMO,
        "Please do a code review of this PR.",
        "rules",
    )
    assert decision.model.id == "demo-frontier"
    assert decision.escalated is True


def test_pin_frontier_respects_max_usd(db_path):
    with pytest.raises(RouteError) as exc:
        route(
            "auto",
            RivetOptions(slot="rules", route="pin-frontier", max_usd=0.001),
            None,
            None,
            DEMO,
            "hello",
            "rules",
        )
    assert exc.value.code == "over_budget"


def test_residency_requires_local(db_path):
    cloud = [CATALOG["gpt-4o-mini"], CATALOG["gpt-4o"]]
    with pytest.raises(RouteError) as exc:
        route(
            "auto",
            RivetOptions(slot="rules", residency="local", max_usd=1),
            None,
            None,
            cloud,
            "hello",
            "rules",
        )
    assert exc.value.code == "residency_blocked"


def test_none_uses_named_model(db_path):
    decision = route(
        "gpt-4o-mini",
        RivetOptions(slot="none", route="cascade", max_usd=1),
        None,
        None,
        MIXED,
        "Please do a code review of this PR.",
        "none",
    )
    assert decision.model.id == "gpt-4o-mini"
    assert decision.escalated is False


def test_heuristic_residency_pins_local(db_path):
    labels = heuristic_labels("This request contains PII and must stay local.")
    assert labels.residency is True
    decision = route(
        "auto",
        RivetOptions(slot="classifier:heuristic", route="cascade", max_usd=1),
        labels,
        labels.confidence,
        MIXED,
        "This request contains PII and must stay local.",
        "classifier:heuristic",
    )
    assert decision.model.id == "local-llama"
    assert decision.why == "Residency pin."
