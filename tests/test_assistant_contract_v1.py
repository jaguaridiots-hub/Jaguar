"""Offline Jaguar Assistant V1 contract tests."""

from pathlib import Path
from types import SimpleNamespace

from assistant.context import build_assistant_context
from assistant.service import AssistantService
import ast


class FakeLLM:
    def __init__(self):
        self.question = None
        self.context = None

    def generate(self, question, context):
        self.question = question
        self.context = context
        return "GROUNDED_ASSISTANT_RESPONSE"


def fake_analysis(symbol, interval, mode):
    state = SimpleNamespace(
        symbol=symbol,
        interval=interval,
        timeframe=interval,
        mode=mode,
        run_id="TEST-RUN",
        master_decision={
            "decision": "WAIT",
            "approved": False,
            "score": 52,
            "confidence": 0.52,
            "reasons": ["Insufficient confirmation"],
            "components": {},
        },
        institutional_report={
            "enterprise": {
                "decision": "WAIT",
                "approved": False,
                "score": 52,
                "grade": "C",
                "confidence": 0.52,
                "risk": {
                    "approved": False,
                    "status": "REJECTED",
                },
                "execution": {
                    "ready": False,
                    "approved": False,
                    "status": "WAIT",
                    "gate": "IDM",
                    "mode": "PAPER",
                    "authorization_id": "MUST_NOT_LEAK",
                },
            }
        },
        structure={},
        market={
            interval: {
                "candles": [
                    {"close": 100.0, "timestamp": "TEST"}
                ]
            }
        },
        mtf_indicators={},
    )

    return {
        "state": state,
        "report": state.institutional_report,
    }


def test_context_is_canonical_and_read_only():
    result = fake_analysis("BTCUSDT", "15m", "SWING")

    context = build_assistant_context(
        result["state"],
        result["report"],
    )

    assert context["source"] == "JAGUAR_CANONICAL_ENTERPRISE_STATE"
    assert context["read_only"] is True
    assert context["ui_state"]["idm"]["decision"] == "WAIT"
    assert "authorization_id" not in context["ui_state"]["execution"]


def test_context_preserves_canonical_enterprise_state():
    state = SimpleNamespace(
        symbol="BTCUSDT",
        interval="15m",
        timeframe="15m",
        mode="SWING",
        idm={
            "decision": "WAIT",
            "approved": False,
            "score": 62.2,
            "confidence": 67.2,
            "priority": "HIGH",
            "structural": {
                "direction": "BULLISH",
                "structure_state": "STRUCTURE_BREAK",
                "trigger_status": "BOS_CONFIRMED",
                "zone_type": "FVG",
                "zone_lifecycle": "PARTIAL_FILL",
                "location_quality": "INTERACTING",
                "readiness": "ZONE_INTERACTION",
            },
        },
        market={
            "symbol": "BTCUSDT",
            "price": 77483.31,
            "candles": [
                {"close": 77483.31, "timestamp": "TEST"}
            ],
        },
        risk={
            "approved": False,
            "status": "REJECTED",
            "position_size": 0.0,
        },
        execution={
            "ready": False,
            "approved": False,
            "status": "WAIT",
            "gate": "IDM",
            "mode": "PAPER",
            "authorization_id": "MUST_NOT_LEAK",
        },
        mtf_indicators={},
        structure={},
        run_id="TEST-RUN",
    )

    report = {
        "enterprise": {
            "score": 62.2,
            "grade": "C",
            "confidence": 67.2,
            "decision": "WAIT",
            "priority": "HIGH",
            "approved": False,
        }
    }

    context = build_assistant_context(state, report)
    ui = context["ui_state"]

    assert ui["market"]["price"] == 77483.31
    assert ui["idm"]["decision"] == "WAIT"
    assert ui["idm"]["score"] == 62.2
    assert ui["idm"]["confidence"] == 67.2
    assert ui["idm"]["grade"] == "C"
    assert ui["idm"]["priority"] == "HIGH"
    assert ui["structure"]["direction"] == "BULLISH"
    assert ui["structure"]["state"] == "STRUCTURE_BREAK"
    assert ui["execution"]["mode"] == "PAPER"
    assert "authorization_id" not in ui["execution"]



def test_service_uses_server_owned_analysis():
    llm = FakeLLM()

    service = AssistantService(
        analysis_fn=fake_analysis,
        llm=llm,
    )

    reply = service.answer(
        question="Why is Jaguar waiting?",
        symbol="BTCUSDT",
        interval="15m",
        mode="SWING",
    )

    assert reply == "GROUNDED_ASSISTANT_RESPONSE"
    assert llm.question == "Why is Jaguar waiting?"
    assert llm.context["source"] == "JAGUAR_CANONICAL_ENTERPRISE_STATE"


def test_assistant_request_contract_is_strict():
    api_source = Path("api.py").read_text()
    tree = ast.parse(api_source)

    model = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AssistantChatRequest"
        ),
        None,
    )

    assert model is not None, "AssistantChatRequest must exist"

    fields = {
        node.target.id
        for node in model.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
    }

    assert fields == {
        "question",
        "symbol",
        "interval",
        "mode",
    }

    model_config = next(
        (
            node.value
            for node in model.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "model_config"
                for target in node.targets
            )
        ),
        None,
    )

    assert isinstance(model_config, ast.Dict)

    config = {}
    for key, value in zip(model_config.keys, model_config.values):
        if isinstance(key, ast.Constant) and isinstance(value, ast.Constant):
            config[key.value] = value.value

    assert config.get("extra") == "forbid"
    assert "context" not in fields
