#!/usr/bin/env python3

import ast
from pathlib import Path

for path in Path(".").rglob("*.py"):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "institutional_master":
            print("FILE :", path)
            print("LINE :", node.lineno)
            print("ARGS :", [a.arg for a in node.args.args])
