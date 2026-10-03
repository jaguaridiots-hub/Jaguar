"""
Jaguar Quant X Enterprise
Institutional Configuration
"""

# ===========================
# Multi-Timeframe Weights
# ===========================

MTF_WEIGHTS = {
    "ema": 20,
    "structure": 20,
    "orderflow": 15,
    "volume_profile": 10,
    "vwap": 10,
    "rsi": 10,
    "premium_discount": 5,
    "gann": 10,

    # New Sprint 1 weights
    "macd": 15,
    "supertrend": 15,
    "adx": 10,
    "volume": 5,
}
# ==========================================================
# Timeframe Weights
# ==========================================================

TIMEFRAME_WEIGHTS = {
    "15m": 10,
    "1h": 20,
    "4h": 30,
    "1d": 40,
}

# ==========================================================
# MTF Component Weights
# ==========================================================

MTF_COMPONENT_WEIGHTS = {
    "ema": 20,
    "supertrend": 15,
    "macd": 15,
    "vwap": 10,
    "rsi": 10,
    "adx": 10,
    "volume": 5,
    "smc": 15,
}

# ===========================
# MTF Signal Thresholds
# ===========================

MTF_THRESHOLDS = {
    "strong_buy": 70,
    "buy": 40,
    "wait_high": 39,
    "wait_low": -39,
    "sell": -40,
    "strong_sell": -70,
}

# ===========================
# Institutional Decision Matrix
# ===========================

IDM_THRESHOLDS = {
    "enter_long": 70,
    "enter_short": -70,
    "watch": 40,
    "alignment_required": 3,
}

# ===========================
# Execution Confirmation
# ===========================

EXECUTION_THRESHOLDS = {
    "execute": 75,
    "wait": 55,
}

# ===========================
# Risk Management
# ===========================

RISK = {
    "capital": 100000,
    "risk_percent": 1.0,
}
