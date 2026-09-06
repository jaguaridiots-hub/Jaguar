#!/usr/bin/env python3

import ast
from pathlib import Path

TARGET = Path("intelligence/enterprise_adapter.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

classes = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef)
]

print("CLASS_COUNT:", len(classes))
print()

for cls in classes:
    print("CLASS:", cls.name)
    print("LINE :", cls.lineno)

    methods = [
        m for m in cls.body
        if isinstance(m, ast.FunctionDef)
    ]

    print("METHODS:")

    for m in methods:
        print("-", m.name, "@", m.lineno)

    print()
