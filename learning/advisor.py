# learning/advisor.py
import os
from groq import Groq
from learning.performance_analyzer import get_performance_summary
from paper_trading import load_ledger

def get_llm_advice():
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    except:
        return "❌ Groq API key not set. Set GROQ_API_KEY in environment."

    summary = get_performance_summary()
    ledger = load_ledger()
    open_positions = [p for p in ledger.get("positions", []) if p["status"] == "OPEN"]
    closed_positions = [p for p in ledger.get("positions", []) if p["status"] == "CLOSED"]

    prompt = f"""
You are the Chief Strategy Officer of Jaguar Quant X, an institutional trading AI.
Analyze the following performance data and provide actionable, specific advice.

PERFORMANCE SUMMARY:
{summary}

OPEN POSITIONS: {len(open_positions)}
CLOSED POSITIONS: {len(closed_positions)}

Your advice must include:
1. Which asset/mode is performing best and why.
2. Which asset/mode is underperforming and recommended changes (threshold, boost, stop‑loss).
3. Any risk management suggestions.
Keep it concise, professional, and actionable (max 200 words).
"""
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "system", "content": "You are a professional trading strategist."},
                      {"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ LLM error: {e}"
