#!/usr/bin/env python3

import ast
from pathlib import Path

tree = ast.parse(
    Path("strategy/trade_validator_engine.py").read_text(
        encoding="utf-8"
    )
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

for i, node in enumerate(
    [n for n in ast.walk(run) if isinstance(n, ast.If)],
    1,
):
    print("=" * 60)
    print("IF", i)
    print(ast.unparse(node.test))
    print()

    for stmt in node.body:
        print(" ", ast.unparse(stmt))

    print()
