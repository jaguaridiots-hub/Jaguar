#!/usr/bin/env python3

import ast
from pathlib import Path

TARGET = Path("intelligence/enterprise_pipeline.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
    if cls.name == "ExecutionGatewayV2":
        print("CLASS:", cls.name)
        print("LINE :", cls.lineno)

        for method in cls.body:
            if isinstance(method, ast.FunctionDef):
                print(f"\nMETHOD: {method.name} @ {method.lineno}")

                if method.name == "process":
                    print("\n========== CALLS ==========\n")
                    for node in ast.walk(method):
                        if isinstance(node, ast.Call):
                            try:
                                print(ast.unparse(node))
                            except Exception:
                                pass
