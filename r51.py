#!/usr/bin/env python3

import ast
from pathlib import Path

tree = ast.parse(Path("main.py").read_text(encoding="utf-8"))

engine_names = [
    "Brain",
    "Probability",
    "TradeValidator",
    "ExecutionConfirmation",
    "RiskManager",
    "TradePlanner",
    "Institutional",
]

print("========== ENGINE INVOCATION CHECK ==========\n")

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        try:
            text = ast.unparse(node)
        except Exception:
            continue

        for name in engine_names:
            if name.lower() in text.lower():
                print(text)
