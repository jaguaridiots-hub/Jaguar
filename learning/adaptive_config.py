# learning/adaptive_config.py
import json
import os
from paper_trading import load_ledger
from learning.performance_analyzer import analyze_performance

CONFIG_FILE = "config/adaptive_config.json"

def get_adaptive_thresholds(symbol):
    stats = analyze_performance()
    sym_stats = stats.get("symbol_stats", {}).get(symbol, {"wins": 0, "losses": 0})
    total = sym_stats["wins"] + sym_stats["losses"]
    win_rate = round(sym_stats["wins"] / total * 100, 2) if total > 0 else 50

    # Base defaults
    scalp_threshold = 65
    swing_threshold = 80
    classic_threshold = 90
    scalp_boost = 35

    if win_rate > 60:
        scalp_threshold = 60
        swing_threshold = 75
    elif win_rate < 40:
        scalp_threshold = 70
        swing_threshold = 85
        scalp_boost = 25

    return {
        "SCALP": {"threshold": scalp_threshold, "boost": scalp_boost},
        "SWING": {"threshold": swing_threshold, "boost": 10},
        "CLASSIC": {"threshold": classic_threshold, "boost": 0}
    }

def update_config_auto(symbol):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    config = get_adaptive_thresholds(symbol)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    return config
