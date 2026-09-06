#!/usr/bin/env python3

import ast
from pathlib import Path

TARGET = Path("intelligence/execution_gateway_v2.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

cls = next(
    c for c in ast.walk(tree)
    if isinstance(c, ast.ClassDef)
    and c.name == "ExecutionGatewayV2"
)

process = next(
    m for m in cls.body
    if isinstance(m, ast.FunctionDef)
    and m.name == "process"
)

print("PROCESS_LINE:", process.lineno)
print("PARAMETERS:", [a.arg for a in process.args.args])

print("\n========== ASSIGNMENTS ==========\n")

for node in ast.walk(process):
    if isinstance(node, ast.Assign):
        try:
            print(ast.unparse(node))
        except Exception:
            pass

print("\n========== IF CONDITIONS ==========\n")

for node in ast.walk(process):
    if isinstance(node, ast.If):
        try:
            print(ast.unparse(node.test))
        except Exception:
            pass
