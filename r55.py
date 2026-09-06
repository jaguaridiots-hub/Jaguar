#!/usr/bin/env python3

import ast
from pathlib import Path

TARGET = Path("engine/institutional_master.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

print("========== ADAPTER CLASS ==========\n")

for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
    methods = [m.name for m in cls.body if isinstance(m, ast.FunctionDef)]
    if "process" in methods:
        print("CLASS :", cls.name)
        print("LINE  :", cls.lineno)

        process = next(
            m for m in cls.body
            if isinstance(m, ast.FunctionDef)
            and m.name == "process"
        )

        print("\nPARAMETERS:",
              [a.arg for a in process.args.args])

        print("\nCALLS:\n")

        for node in ast.walk(process):
            if isinstance(node, ast.Call):
                try:
                    print(ast.unparse(node))
                except Exception:
                    pass
