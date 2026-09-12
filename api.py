# api.py – FastAPI backend for Jaguar Quant X
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel
import uvicorn
from core.orchestrator import JaguarOrchestrator
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


@app.get("/dashboard", include_in_schema=False)
@app.get("/dashboard/", include_in_schema=False)
async def dashboard_home():
    index = DASHBOARD_ROOT / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="Dashboard index not found")
    return FileResponse(index)


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
