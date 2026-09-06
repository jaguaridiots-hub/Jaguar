#!/usr/bin/env python3

import ast
from pathlib import Path

tree = ast.parse(Path("main.py").read_text(encoding="utf-8"))

targets = [
    "brain",
    "probability",
    "decision",
    "mtf",
    "regime",
    "session",
    "orderflow",
    "volume_profile",
    "gann",
    "risk",
    "trade_validator",
    "execution_confirmation",
]

calls = [
    ast.unparse(node)
    for node in ast.walk(tree)
    if isinstance(node, ast.Call)
]

print("========== RUNTIME DIAGNOSTIC CHECK ==========\n")

for name in targets:
    found = any(f"getattr(state, '{name}'" in c or f'getattr(state, "{name}"' in c for c in calls)
    print(f"{name:<26} {'FOUND' if found else 'MISSING'}")
