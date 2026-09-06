#!/usr/bin/env python3

import ast
from pathlib import Path

TARGET = Path("engine/institutional_master.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

func = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.FunctionDef)
    and n.name == "analyze"
)

print("FUNCTION_LINE:", func.lineno)

params = [a.arg for a in func.args.args]
print("PARAMETERS:", params)

calls = [
    ast.unparse(n)
    for n in ast.walk(func)
    if isinstance(n, ast.Call)
]

print("\n========== CALLS ==========\n")

for call in calls:
    print(call)
