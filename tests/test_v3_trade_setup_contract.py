from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_trade_setup_state_contract():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert '"trade_setup": trade_setup' in source
    assert '"status": setup_status' in source
    assert '"setup_type": setup_value' in source
    assert '"zone_lifecycle":' in source
    assert '"location":' in source
    assert '"readiness":' in source
    assert '"trigger":' in source
    assert '"execution_confirmation":' in source
    assert '"risk_status":' in source
    assert '"execution_status":' in source


def test_trade_setup_uses_canonical_sources():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert 'master.get("setup")' in source
    assert 'structural.get("zone_type")' in source
    assert 'structural.get("readiness")' in source
    assert 'execution_confirmation.get(' in source
    assert 'risk.get("status")' in source
    assert 'execution.get("status")' in source


def test_trade_setup_presentation_contract():
    source = (
        ROOT / "dashboard" / "command_center_v3.py"
    ).read_text()

    assert 'id="tradeSetup"' in source

    compact = "".join(source.split())

    assert 'u.trade_setup||{}' in compact
    assert 'tradeSetup.status' in source
    assert 'tradeSetup.setup_type' in source
    assert 'tradeSetup.readiness' in source
    assert 'tradeSetup.trigger' in source
    assert 'tradeSetup.execution_confirmation' in source


def test_trade_setup_does_not_create_new_score():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    block_start = source.find(
        "# Jaguar V3 Trade Setup Presentation"
    )
    block_end = source.find(
        "# Jaguar V3 Confidence Breakdown",
        block_start,
    )

    assert block_start >= 0
    assert block_end > block_start

    block = source[block_start:block_end]

    assert "score" not in block.lower()
    assert "confidence" not in block.lower()
