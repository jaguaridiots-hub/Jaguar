from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_confidence_breakdown_state_contract():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert (
        '"confidence_breakdown": confidence_breakdown'
        in source
    )

    assert (
        '"idm_confidence":'
        in source
    )

    assert (
        '"institutional_confidence":'
        in source
    )

    assert (
        '"probability":'
        in source
    )

    assert (
        '"engines": confidence_engines'
        in source
    )


def test_confidence_breakdown_uses_canonical_engine_evidence():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert (
        'report.get("engines", {})'
        in source
    )

    assert (
        '"confidence_percent":'
        in source
    )


def test_confidence_breakdown_presentation_contract():
    source = (
        ROOT / "dashboard" / "command_center_v3.py"
    ).read_text()

    assert 'id="confidenceSummary"' in source
    assert 'id="confidenceEngines"' in source
    assert 'id="confidenceMethod"' in source


def test_confidence_breakdown_does_not_create_composite_score():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert (
        '"method": (' in source
    )

    assert (
        "Canonical evidence only"
        in source
    )
