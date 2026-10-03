"""R57 /analyze execution presentation boundary contract."""

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import api


def test_analyze_sanitizes_execution_authorization_id():
    source = Path("api.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    analyze_node = None

    for node in tree.body:
        if not isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            continue

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            if not isinstance(decorator.func, ast.Attribute):
                continue

            if decorator.func.attr != "post":
                continue

            if not decorator.args:
                continue

            if (
                isinstance(decorator.args[0], ast.Constant)
                and decorator.args[0].value == "/analyze"
            ):
                analyze_node = node

    assert analyze_node is not None

    source_segment = ast.get_source_segment(
        source,
        analyze_node,
    )

    assert source_segment is not None
    assert 'execution.pop("authorization_id", None)' in source_segment


def test_analyze_does_not_mutate_canonical_execution():
    class FakeKernel:
        def initialize(self, symbol, interval):
            pass

        def get_state(self):
            return SimpleNamespace(
                mode="SWING",
                trade={},
                risk={},
            )

    original_execution = {
        "ready": False,
        "approved": False,
        "status": "WAIT",
        "gate": "IDM",
        "mode": "PAPER",
        "broker": "Paper",
        "reason": "TEST",
        "authorization_id": "MUST_NOT_ESCAPE",
    }

    class FakeAnalysisEngine:
        def __init__(self, kernel):
            self.kernel = kernel

        def run(self, symbol):
            return {
                "state": self.kernel.get_state(),
                "report": {
                    "enterprise": {
                        "decision": "WAIT",
                        "score": 50,
                        "grade": "C",
                        "confidence": 50,
                        "trade": {},
                        "risk": {},
                        "execution": original_execution,
                    },
                    "decision": {
                        "reasons": ["TEST"],
                    },
                },
            }

    async def probe():
        with patch.object(
            api,
            "JaguarKernel",
            FakeKernel,
        ), patch.object(
            api,
            "JaguarAnalysisEngine",
            FakeAnalysisEngine,
        ):
            req = api.AnalyzeRequest(
                symbol="BTCUSDT",
                interval="15m",
                mode="SWING",
            )

            result = await api.analyze(req)

        execution = result["execution"]

        assert "authorization_id" not in execution
        assert execution["mode"] == "PAPER"
        assert execution["status"] == "WAIT"
        assert execution["gate"] == "IDM"
        assert execution["broker"] == "Paper"

        assert (
            original_execution["authorization_id"]
            == "MUST_NOT_ESCAPE"
        )

    import asyncio

    asyncio.run(probe())
