from core.kernel import JaguarKernel
from core.jaguar_analysis_engine import JaguarAnalysisEngine


def test_jaguar_analysis_populates_session(monkeypatch):
    import market.live_loader as live_loader
    import indicators.indicator_engine as indicator_engine
    import engine.institutional_master as institutional_master

    monkeypatch.setattr(
        live_loader,
        "update_state",
        lambda state, symbol: state,
    )

    monkeypatch.setattr(
        indicator_engine,
        "update_market_state",
        lambda state: state,
    )

    monkeypatch.setattr(
        institutional_master,
        "analyze",
        lambda state: {"test": True},
    )

    kernel = JaguarKernel()
    kernel.initialize("BTCUSDT", "15m")

    result = JaguarAnalysisEngine(kernel).run("BTCUSDT")
    state = result["state"]

    assert hasattr(state, "session")
    assert isinstance(state.session, dict)
    assert state.session.get("session")
    assert "score" in state.session
    assert "reasons" in state.session
