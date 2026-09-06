#!/usr/bin/env python3

import ast
from pathlib import Path

TARGET = Path("strategy/trade_validator_engine.py")

tree = ast.parse(
    TARGET.read_text(encoding="utf-8")
)

engine = next(
    c for c in ast.walk(tree)
    if isinstance(c, ast.ClassDef)
    and c.name == "TradeValidatorEngine"
)

run = next(
    f for f in engine.body
    if isinstance(f, ast.FunctionDef)
    and f.name == "run"
)

ifs = [
    n for n in ast.walk(run)
    if isinstance(n, ast.If)
]

print("IF_COUNT:", len(ifs))
print()

for i, node in enumerate(ifs, 1):
    print(f"IF_{i}:")
    print(ast.unparse(node.test))
    print()
