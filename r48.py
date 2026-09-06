#!/usr/bin/env python3

import ast
from pathlib import Path

tree = ast.parse(
    Path("strategy/execution_confirmation_engine.py").read_text(
        encoding="utf-8"
    )
)

engine = next(
    c for c in ast.walk(tree)
    if isinstance(c, ast.ClassDef)
    and c.name == "ExecutionConfirmationEngine"
)

run = next(
    f for f in engine.body
    if isinstance(f, ast.FunctionDef)
    and f.name == "run"
)

assignments = [
    n for n in ast.walk(run)
    if isinstance(n, ast.Assign)
]

print("ASSIGNMENT_COUNT:", len(assignments))
print()

for a in assignments:
    print(ast.unparse(a))
    print()
