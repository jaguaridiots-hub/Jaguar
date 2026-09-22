from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_thesis_state_contract():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert (
        '"thesis_invalidation": thesis_invalidation'
        in source
    )
    assert '"direction": thesis_direction' in source
    assert '"status": thesis_status' in source
    assert '"supporting_evidence": thesis_support' in source
    assert '"weakening_evidence": thesis_weakening' in source
    assert '"canonical_invalidation_gates":' in source
    assert '"active_invalidation":' in source


def test_uses_canonical_evidence():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert 'structural.get("direction")' in source
    assert 'bos_engine.get("signal")' in source
    assert 'choch_engine.get("signal")' in source
    assert 'getattr(\n            state,\n            "mtf"' in source
    assert 'master.get(\n            "conflicts"' in source
    assert 'institutional_state.get("warnings"' in source


def test_invalidation_gates_are_existing_idm_concepts():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    for gate in (
        "DIRECTION_CONFLICT",
        "STRUCTURAL_CONFLICT",
        "ZONE_CONFLICT",
        "CONFLICT_CLEARANCE",
    ):
        assert gate in source


def test_no_new_trade_rule_or_price_logic():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    start = source.find(
        "# Jaguar V3 Thesis / Invalidation"
    )
    end = source.find(
        "    what_would_change = {",
        start,
    )

    assert start >= 0
    assert end > start

    block = source[start:end]

    assert "entry_price" not in block
    assert "stop_loss" not in block
    assert "target" not in block
    assert "probability" not in block
    assert "score" not in block.lower()


def test_v3_presentation_contract():
    source = (
        ROOT / "dashboard" / "command_center_v3.py"
    ).read_text()

    assert 'id="thesisInvalidation"' in source
    assert 'const thesis' in source
    assert 'u.thesis_invalidation || {}' in source
    assert 'thesis.supporting_evidence' in source
    assert 'thesis.weakening_evidence' in source
    assert 'thesis.canonical_invalidation_gates' in source
    assert 'thesis.active_invalidation' in source
