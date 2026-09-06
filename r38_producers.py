#!/usr/bin/env python3

"""
R38
Trade Planner Producer Authority
"""

import ast
from pathlib import Path

TARGET = Path("strategy/trade_planner_engine.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

planner = next(
    node for node in ast.walk(tree)
    if isinstance(node, ast.ClassDef)
    and node.name == "TradePlannerEngine"
)

run = next(
    node for node in planner.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "run"
)

attributes = []

for node in ast.walk(run):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "state"
            ):
                attributes.append((target.attr, ast.unparse(node.value)))

print("STATE_ASSIGNMENT_COUNT:", len(attributes))

for name, source in attributes:
    print(f"{name} = {source}")
