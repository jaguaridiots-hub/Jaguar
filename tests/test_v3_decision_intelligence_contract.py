from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_decision_gate_contract():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert '"decision_gate": decision_gate' in source
    assert '"blocker": blocker' in source
    assert '"next_conditions": next_conditions' in source
    assert '"authorization": authorization' in source


def test_mtf_sufficiency_contract():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert '"mtf_sufficiency": mtf_sufficiency' in source
    assert '"required_count": mtf_required_count' in source
    assert '"available_count": mtf_available_count' in source
    assert '"unavailable_count": len(unavailable_mtf)' in source


def test_v3_decision_gate_presentation_contract():
    source = (
        ROOT / "dashboard" / "command_center_v3.py"
    ).read_text()

    assert 'id="gateDecision"' in source
    assert 'id="gateAuthorization"' in source
    assert 'id="gateBlocker"' in source
    assert 'id="gateReason"' in source
    assert 'id="gateConditions"' in source


def test_v3_mtf_sufficiency_presentation_contract():
    source = (
        ROOT / "dashboard" / "command_center_v3.py"
    ).read_text()

    assert 'id="mtfSufficiency"' in source
    assert 'mtfSuff.available_count' in source
    assert 'mtfSuff.unavailable' in source
