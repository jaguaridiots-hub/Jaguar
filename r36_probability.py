#!/usr/bin/env python3

"""
R36C
Probability Producer Authority
"""

import ast
from pathlib import Path

TARGET = Path("ai/probability_engine.py")

tree = ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)

# Locate ProbabilityEngine.calculate()

cls = next(
    node
    for node in ast.walk(tree)
    if isinstance(node, ast.ClassDef)
    and node.name == "ProbabilityEngine"
)

calculate = next(
    node
    for node in cls.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "calculate"
)

producer_names = [
    "probability",
    "reasons",
]

producer_assignments = {}

for name in producer_names:

    matches = []

    for node in ast.walk(calculate):

        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:

            if (
                isinstance(target, ast.Name)
                and target.id == name
            ):
                matches.append(node)

    producer_assignments[name] = matches

for name in producer_names:

    matches = producer_assignments[name]

    print(
        f"{name.upper()}_ASSIGNMENT_COUNT:",
        len(matches),
    )

    print(
        f"{name.upper()}_ASSIGNMENT_AUTHORITY:",
        "PASS" if len(matches) >= 1 else "FAIL",
    )

    for i, assignment in enumerate(matches, 1):

        print(
            f"{name.upper()}_{i}_TYPE:",
            type(assignment.value).__name__,
        )

        print(
            f"{name.upper()}_{i}_SOURCE:",
            ast.unparse(assignment.value),
        )
