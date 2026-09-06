#!/usr/bin/env python3

"""
R39
Risk Manager Producer Authority
"""

import ast
from pathlib import Path

TARGET = Path("strategy/risk_manager_engine.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

engine = next(
    node
    for node in ast.walk(tree)
    if isinstance(node, ast.ClassDef)
    and node.name == "RiskManagerEngine"
)

run = next(
    node
    for node in engine.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "run"
)

assignments = []

for node in ast.walk(run):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "state"
            ):
                assignments.append(
                    (
                        target.attr,
                        ast.unparse(node.value),
                    )
                )

print("STATE_ASSIGNMENT_COUNT:", len(assignments))

for name, source in assignments:
    print(f"{name} = {source}")
