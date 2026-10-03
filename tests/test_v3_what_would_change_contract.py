from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_state_contract():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert '"what_would_change": what_would_change' in source
    assert '"required_conditions":' in source
    assert '"structural_readiness":' in source
    assert '"trigger_status":' in source
    assert '"execution_confirmation":' in source
    assert '"execution_confirmation_reasons":' in source
    assert '"conflicts":' in source


def test_uses_canonical_structural_trigger():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert 'structural.get("trigger_status"' in source
    assert 'structural.get("readiness"' in source


def test_does_not_create_trade_signal():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    start = source.find(
        '"what_would_change": what_would_change'
    )

    assert start >= 0

    block_start = source.find(
        "what_would_change = {"
    )
    block_end = source.find(
        "# Jaguar V3 Trade Setup Presentation",
        block_start,
    )

    assert block_start >= 0
    assert block_end > block_start

    block = source[block_start:block_end]

    assert "price" not in block.lower()
    assert "entry_price" not in block.lower()
    assert "score" not in block.lower()
    assert "probability" not in block.lower()


def test_v3_presentation_contract():
    source = (
        ROOT / "dashboard" / "command_center_v3.py"
    ).read_text()

    assert 'id="whatWouldChange"' in source
    assert 'const whatWouldChange' in source
    assert 'whatWouldChange.required_conditions' in source
    assert 'whatWouldChange.execution_confirmation' in source
    assert 'whatWouldChange.conflicts' in source
