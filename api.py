# api.py – FastAPI backend for Jaguar Quant X
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from pydantic import BaseModel
import uvicorn
from core.orchestrator import JaguarOrchestrator
from core.kernel import JaguarKernel
from core.jaguar_analysis_engine import JaguarAnalysisEngine
from dashboard.ui_state import build_ui_state
from dashboard.command_center_v2 import render_command_center_v2
from core.state import JaguarState
from assistant.service import AssistantService, AssistantServiceError

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
        orch = JaguarOrchestrator()
        state = orch.analyze(req.symbol, req.interval, req.mode)
        # Return minimal JSON (you can expand later)
        md = state.master_decision
        return {
            "symbol": req.symbol,
            "mode": req.mode,
            "decision": md.get("decision"),
            "score": md.get("score"),
            "grade": md.get("grade"),
            "confidence": md.get("confidence"),
            "reasoning": md.get("reasoning", []),
            "trade_plan": state.trade_plan,
            "risk": state.risk,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

assistant_service = AssistantService()


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
        # Uses the existing canonical MarketProvider/LiveLoader routing and
        # IndicatorEngine. It does not alter IDM, risk, execution, or LIVE
        # authorization state.
        from indicators.indicator_engine import IndicatorEngine
        from market.live_loader import load_market

        mtf = {}

        for frame in ("15m", "1h", "4h", "1d"):
            try:
                frame_candles = load_market(
                    symbol,
                    frame,
                    300,
                )
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

        market = getattr(canonical_state, "market_current", None)
        if not isinstance(market, dict):
            market = getattr(canonical_state, "market", None)
        if not isinstance(market, dict):
            market = {}

        candles = market.get("candles", [])
        if not isinstance(candles, list):
            candles = []

        safe_candles = []
        for candle in candles[-180:]:
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
