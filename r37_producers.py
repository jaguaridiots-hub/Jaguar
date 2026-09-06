#!/usr/bin/env python3

"""
R37A
Jaguar Brain V4 Producer Authority
"""

import ast
from pathlib import Path

TARGET = Path("ai/jaguar_brain_v4.py")

tree = ast.parse(
    TARGET.read_text(encoding="utf-8")
)

# Locate JaguarBrainV4.analyze()

brain = next(
    node
    for node in ast.walk(tree)
    if isinstance(node, ast.ClassDef)
    and node.name == "JaguarBrainV4"
)

analyze = next(
    node
    for node in brain.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "analyze"
)

producer_names = [
    "signal",
    "score",
    "confidence_text",
    "grade",
    "reasons",
]

for producer in producer_names:

    assignments = []

    for node in ast.walk(analyze):

        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:

            if (
                isinstance(target, ast.Name)
                and target.id == producer
            ):
                assignments.append(node)

    print(
        f"{producer.upper()}_ASSIGNMENT_COUNT:",
        len(assignments),
    )

    print(
        f"{producer.upper()}_ASSIGNMENT_AUTHORITY:",
        "PASS" if len(assignments) >= 1 else "FAIL",
    )

    for i, assignment in enumerate(assignments, 1):

        print(
            f"{producer.upper()}_{i}_TYPE:",
            type(assignment.value).__name__,
        )

        print(
            f"{producer.upper()}_{i}_SOURCE:",
            ast.unparse(assignment.value),
        )
