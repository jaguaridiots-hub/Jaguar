# api.py – FastAPI backend for Jaguar Quant X
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from core.orchestrator import JaguarOrchestrator
from core.state import JaguarState

app = FastAPI(title="Jaguar Quant X API", version="2.0")

class AnalyzeRequest(BaseModel):
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

@app.post("/chat")
async def chat(req: ChatRequest):
    # Placeholder – you can connect to llm_server.py logic
    return {"reply": "Jaguar Brain will respond here."}

@app.get("/health")
async def health():
    return {"status": "online", "version": "2.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
