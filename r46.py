#!/usr/bin/env python3

import ast
from pathlib import Path

TARGET = Path("strategy/execution_confirmation_engine.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

classes = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef)
]

print("CLASS_COUNT:", len(classes))

for cls in classes:
    print()
    print("CLASS_NAME:", cls.name)
    print("CLASS_LINE:", cls.lineno)

    methods = [
        m for m in cls.body
        if isinstance(m, ast.FunctionDef)
    ]

    print("METHOD_COUNT:", len(methods))

    for m in methods:
        print("-", m.name, "@ line", m.lineno)
