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

ifs = [n for n in ast.walk(run) if isinstance(n, ast.If)]

print("IF_COUNT:", len(ifs))
print()

for i, node in enumerate(ifs, 1):
    print("=" * 60)
    print(f"IF {i}")
    print(ast.unparse(node.test))
    print()

    print("BODY:")
    for stmt in node.body:
        print(" ", ast.unparse(stmt))

    if node.orelse:
        print()
        print("ELSE:")
        for stmt in node.orelse:
            print(" ", ast.unparse(stmt))

    print()
