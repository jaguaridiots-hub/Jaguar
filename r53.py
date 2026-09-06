#!/usr/bin/env python3

import ast
from pathlib import Path

tree = ast.parse(Path("main.py").read_text(encoding="utf-8"))

print("========== IMPORTS ==========\n")

for node in tree.body:
    if isinstance(node, ast.Import):
        for alias in node.names:
            print(f"import {alias.name}")

    elif isinstance(node, ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            if alias.asname:
                print(f"from {module} import {alias.name} as {alias.asname}")
            else:
                print(f"from {module} import {alias.name}")
