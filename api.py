# api.py – FastAPI backend for Jaguar Quant X
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from pydantic import BaseModel
import uvicorn
from core.kernel import JaguarKernel
from core.jaguar_analysis_engine import JaguarAnalysisEngine
from dashboard.ui_state import build_ui_state
from dashboard.command_center_v2 import render_command_center_v2
from dashboard.command_center_v3 import render_command_center_v3
from core.state import JaguarState
from assistant.service import AssistantService, AssistantServiceError
from news.service import JaguarNewsService
from scanner.service import ScannerService

app = FastAPI(title="Jaguar Quant X API", version="2.0")

DASHBOARD_ROOT = Path(__file__).resolve().parent
_DASHBOARD_FIXED_FILES = {"index.html", "portfolio.html", "command_center.html"}

class AnalyzeRequest(BaseModel):
    symbol: str = "BTCUSDT"
    interval: str = "15m"
    mode: str = "SWING"

class AssistantChatRequest(BaseModel):
    model_config = {"extra": "forbid"}

    question: str
    symbol: str = "BTCUSDT"
    interval: str = "15m"
    mode: str = "SWING"


class ChatRequest(BaseModel):
    question: str
    state: dict = {}

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    try:
        if req.mode.upper() not in {"SCALP", "SWING", "CLASSIC"}:
            raise HTTPException(status_code=400, detail="Invalid analysis mode")

        kernel = JaguarKernel()
        kernel.initialize(req.symbol, req.interval)

        state = kernel.get_state()
        state.mode = req.mode.upper()

        result = JaguarAnalysisEngine(kernel).run(req.symbol)

        if not isinstance(result, dict):
            raise RuntimeError("Canonical analysis returned invalid result")

        state = result.get("state")
        report = result.get("report")

        if state is None or not isinstance(report, dict):
            raise RuntimeError("Canonical analysis result is incomplete")

        enterprise = report.get("enterprise", {})

        if not isinstance(enterprise, dict):
            enterprise = {}

        decision = report.get("decision", {})
        if not isinstance(decision, dict):
            decision = {}

        return {
            "symbol": req.symbol,
            "interval": req.interval,
            "mode": req.mode.upper(),
            "decision": enterprise.get("decision"),
            "score": enterprise.get("score"),
            "grade": enterprise.get("grade"),
            "confidence": enterprise.get("confidence"),
            "reasoning": decision.get("reasons", []),
            "trade": enterprise.get("trade", getattr(state, "trade", {})),
            "risk": enterprise.get("risk", getattr(state, "risk", {})),
            "execution": enterprise.get("execution", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

assistant_service = AssistantService()
news_service = JaguarNewsService()
scanner_service = ScannerService()


@app.post("/assistant/chat")
async def assistant_chat(req: AssistantChatRequest):
    try:
        reply = assistant_service.answer(
            question=req.question,
            symbol=req.symbol,
            interval=req.interval,
            mode=req.mode,
        )
        return {"reply": reply}
    except AssistantServiceError:
        raise HTTPException(
            status_code=503,
            detail="Assistant unavailable",
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Assistant request failed",
        )




@app.get("/news", include_in_schema=False)
async def news(
    symbol: str | None = None,
    category: str = "MARKET",
    limit: int = 20,
    refresh: bool = False,
):
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 50",
        )

    snapshot = news_service.get_news(
        symbol=symbol,
        category=category,
        limit=limit,
        refresh=refresh,
    )

    return snapshot.to_dict()



@app.get("/scanner", include_in_schema=False)
async def scanner(
    symbol: str | None = None,
):
    if symbol is not None:
        normalized_symbol = str(symbol).strip().upper()

        if not normalized_symbol:
            raise HTTPException(
                status_code=400,
                detail="symbol must not be empty",
            )

        symbols = (normalized_symbol,)

    else:
        symbols = None

    try:
        snapshot = scanner_service.scan_watchlist(
            symbols=symbols,
        )

        return snapshot.to_dict()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Scanner request failed",
        )


@app.get("/dashboard/assets/jaguar_quant_x_logo.png", include_in_schema=False)
async def dashboard_logo():
    logo = Path(__file__).resolve().parent / "dashboard" / "assets" / "jaguar_quant_x_logo.png"
    if not logo.is_file():
        raise HTTPException(status_code=404, detail="Dashboard logo not found")
    return FileResponse(logo, media_type="image/png")

@app.get("/dashboard/state", include_in_schema=False)
async def dashboard_state(
    symbol: str = "BTCUSDT",
    interval: str = "15m",
    mode: str = "SWING",
):
    if mode.upper() not in {"SCALP", "SWING", "CLASSIC"}:
        raise HTTPException(status_code=400, detail="Invalid analysis mode")

    try:
        kernel = JaguarKernel()
        kernel.initialize(symbol, interval)
        state = kernel.get_state()
        state.mode = mode.upper()

        result = JaguarAnalysisEngine(kernel).run(symbol)

        if not isinstance(result, dict):
            raise RuntimeError("Canonical analysis returned invalid result")

        canonical_state = result.get("state")
        report = result.get("report")

        if canonical_state is None or not isinstance(report, dict):
            raise RuntimeError("Canonical dashboard state is incomplete")

        ui = build_ui_state(canonical_state, report=report)

        # Dashboard-only MTF presentation enrichment.
        # Reuse the canonical MTF candle snapshot already fetched by
        # JaguarAnalysisEngine. Preserve the historical dashboard contract
        # by calculating presentation indicators from the latest 300 candles.
        # This avoids four duplicate provider requests per dashboard-state
        # call and does not alter IDM, risk, execution, or authorization state.
        from indicators.indicator_engine import IndicatorEngine

        mtf = {}

        canonical_mtf_market = getattr(
            canonical_state,
            "_dashboard_mtf_market",
            None,
        )

        if not isinstance(canonical_mtf_market, dict):
            canonical_mtf_market = {}

        for frame in ("15m", "1h", "4h", "1d"):
            try:
                frame_data = canonical_mtf_market.get(
                    frame,
                    {},
                )

                if not isinstance(frame_data, dict):
                    raise RuntimeError(
                        f"Canonical MTF snapshot for {frame} is invalid"
                    )

                frame_candles = frame_data.get(
                    "candles",
                    [],
                )

                if not isinstance(frame_candles, list) or not frame_candles:
                    raise RuntimeError(
                        f"Canonical MTF snapshot for {frame} has no candles"
                    )

                # Preserve the existing dashboard 300-candle semantics.
                frame_candles = frame_candles[-300:]

                indicators = IndicatorEngine.calculate(
                    frame_candles,
                )

                ema = indicators.get("ema", {})
                rsi = indicators.get("rsi", {})
                volume = indicators.get("volume", {})
                atr = indicators.get("atr", {})
                vwap = indicators.get("vwap", {})

                mtf[frame] = {
                    "trend": str(
                        ema.get("trend", "UNDEFINED")
                    ),
                    "rsi": rsi.get("value"),
                    "rsi_signal": str(
                        rsi.get("signal", "UNDEFINED")
                    ),
                    "volume_signal": str(
                        volume.get("signal", "UNDEFINED")
                    ),
                    "atr": atr.get("value"),
                    "atr_volatility": str(
                        atr.get("volatility", "UNDEFINED")
                    ),
                    "vwap_signal": str(
                        vwap.get("signal", "UNDEFINED")
                    ),
                }
            except Exception:
                mtf[frame] = {
                    "trend": "UNAVAILABLE",
                    "rsi": None,
                    "rsi_signal": "UNAVAILABLE",
                    "volume_signal": "UNAVAILABLE",
                    "atr": None,
                    "atr_volatility": "UNAVAILABLE",
                    "vwap_signal": "UNAVAILABLE",
                }

        ui["mtf"] = mtf

        execution = dict(ui.get("execution") or {})
        execution.pop("authorization_id", None)
        ui["execution"] = execution

        # Dashboard-only session presentation.
        # This mirrors canonical_state.session when populated.
        # It does not create or modify execution authority.
        canonical_session = getattr(canonical_state, "session", None)

        if isinstance(canonical_session, dict) and canonical_session:
            ui["session"] = {
                "session": canonical_session.get("session", "UNKNOWN"),
                "score": canonical_session.get("score", 0),
                "reasons": (
                    canonical_session.get("reasons", [])
                    if isinstance(
                        canonical_session.get("reasons", []),
                        list,
                    )
                    else []
                ),
                "status": "AVAILABLE",
            }
        else:
            ui["session"] = {
                "session": "UNAVAILABLE",
                "score": 0,
                "reasons": [
                    "Canonical Session Engine state is not populated."
                ],
                "status": "UNAVAILABLE",
            }

        market = getattr(canonical_state, "market_current", None)
        if not isinstance(market, dict):
            market = getattr(canonical_state, "market", None)
        if not isinstance(market, dict):
            market = {}

        candles = market.get("candles", [])
        if not isinstance(candles, list):
            candles = []

        safe_candles = []
        for candle in candles[-300:]:
            if not isinstance(candle, dict):
                continue
            safe_candles.append({
                key: candle[key]
                for key in (
                    "time", "timestamp", "datetime",
                    "open", "high", "low", "close", "volume"
                )
                if key in candle
            })

        return {"ui": ui, "candles": safe_candles}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Canonical dashboard state unavailable",
        )


@app.get("/dashboard", include_in_schema=False)
@app.get("/dashboard/", include_in_schema=False)
async def dashboard_home():
    return HTMLResponse(render_command_center_v2())


@app.get("/dashboard/command_center.html", include_in_schema=False)
async def dashboard_command_center():
    return HTMLResponse(render_command_center_v2())


@app.get("/dashboard/v3", include_in_schema=False)
@app.get("/dashboard/v3/", include_in_schema=False)
async def dashboard_v3():
    return HTMLResponse(render_command_center_v3())


@app.get("/dashboard/{filename:path}", include_in_schema=False)
async def dashboard_file(filename: str):
    candidate = (DASHBOARD_ROOT / filename).resolve()

    valid_name = (
        candidate.name in _DASHBOARD_FIXED_FILES
        or candidate.name.startswith("dashboard_")
    )

    if (
        candidate.parent != DASHBOARD_ROOT
        or candidate.suffix.lower() != ".html"
        or not valid_name
        or not candidate.is_file()
    ):
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return FileResponse(candidate)


@app.post("/chat")
async def chat(req: ChatRequest):
    # Placeholder – you can connect to llm_server.py logic
    return {"reply": "Jaguar Brain will respond here."}

@app.get("/health")
async def health():
    return {"status": "online", "version": "2.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
