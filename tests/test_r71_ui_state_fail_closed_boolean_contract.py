from types import SimpleNamespace

from dashboard.ui_state import build_ui_state


def _base_state():
    return SimpleNamespace(
        symbol="BTCUSDT",
        timeframe="15m",
        market={},
        idm={"decision": "WAIT", "approved": False},
        risk={"approved": False},
        execution={
            "ready": False,
            "approved": False,
            "status": "WAIT",
            "gate": "IDM",
            "mode": "PAPER",
        },
    )


def test_r71_malformed_string_booleans_fail_closed():
    report = {
        "enterprise": {
            "approved": "false",
            "risk": {
                "approved": "false",
            },
            "execution": {
                "ready": "false",
                "approved": "false",
            },
        }
    }

    ui = build_ui_state(_base_state(), report)

    assert ui["idm"]["approved"] is False
    assert ui["risk"]["approved"] is False
    assert ui["execution"]["ready"] is False
    assert ui["execution"]["approved"] is False


def test_r71_real_boolean_values_are_preserved():
    state = SimpleNamespace(
        symbol="BTCUSDT",
        timeframe="15m",
        market={},
        idm={"decision": "ENTER_LONG", "approved": True},
        risk={"approved": True},
        execution={
            "ready": True,
            "approved": True,
            "status": "EXECUTE",
            "gate": "AUTHORIZED",
            "mode": "PAPER",
        },
    )

    report = {
        "enterprise": {
            "approved": True,
            "risk": {
                "approved": True,
            },
            "execution": {
                "ready": True,
                "approved": True,
            },
        }
    }

    ui = build_ui_state(state, report)

    assert ui["idm"]["approved"] is True
    assert ui["risk"]["approved"] is True
    assert ui["execution"]["ready"] is True
    assert ui["execution"]["approved"] is True
