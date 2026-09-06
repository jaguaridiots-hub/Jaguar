#!/usr/bin/env python3

import ast
from pathlib import Path

TARGET = Path("intelligence/enterprise_pipeline.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

cls = next(
    c for c in ast.walk(tree)
    if isinstance(c, ast.ClassDef)
    and c.name == "EnterprisePipeline"
)

init = next(
    m for m in cls.body
    if isinstance(m, ast.FunctionDef)
    and m.name == "__init__"
)

print("INIT_LINE:", init.lineno)
print()

for node in ast.walk(init):
    if isinstance(node, ast.Assign):
        try:
            print(ast.unparse(node))
        except Exception:
            pass

print("\n========== CALLS ==========\n")

for node in ast.walk(init):
    if isinstance(node, ast.Call):
        try:
            print(ast.unparse(node))
        except Exception:
            pass
