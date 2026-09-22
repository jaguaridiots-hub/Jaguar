from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ui_state_exposes_canonical_data_quality():
    source = (
        ROOT / "dashboard" / "ui_state.py"
    ).read_text()

    assert '"data_quality": data_quality' in source
    assert 'market_metadata.get(' in source
    assert '"integrity_ok"' in source
    assert '"schema_valid"' in source
    assert '"ohlcv_valid"' in source
    assert '"timestamps_valid"' in source
    assert '"monotonic"' in source
    assert '"duplicates_clear"' in source
    assert '"interval_consistent"' in source
    assert '"gap_detected"' in source
    assert '"gap_count"' in source
    assert '"gap_policy"' in source


def test_v3_presents_data_quality():
    source = (
        ROOT / "dashboard" / "command_center_v3.py"
    ).read_text()

    compact = "".join(source.split())

    assert 'id="dataQualityBadge"' in source
    assert 'id="dataQualityLine"' in source
    assert 'u.data_quality||{}' in compact
    assert 'dataQuality.integrity_ok' in source
    assert 'dataQuality.status' in source
    assert 'dataQuality.gap_count' in source
    assert 'dataQuality.candle_count' in source


def test_v3_data_quality_is_presentation_only():
    source = (
        ROOT / "dashboard" / "command_center_v3.py"
    ).read_text()

    start = source.find(
        "const dataQuality=u.data_quality||{};"
    )

    assert start >= 0

    end = source.find(
        'document.getElementById("symbol")',
        start,
    )

    assert end > start

    block = source[start:end].lower()

    assert "entry_price" not in block
    assert "stop_loss" not in block
    assert "target" not in block
    assert "signal" not in block
    assert "score" not in block
    assert "probability" not in block
