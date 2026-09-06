#!/usr/bin/env python3

"""
R23
EMA Mathematical Authority
"""

import ast
from pathlib import Path

TARGET = Path("indicators/ema.py")

tree = ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)


def find_ema(tree):

    for node in ast.walk(tree):

        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "ema"
        ):
            return node

    raise RuntimeError(
        "ema() not found"
    )


ema_function = find_ema(tree)

print(
    "EMA_FUNCTION:",
    ema_function.name,
)

print(
    "EMA_LINE:",
    ema_function.lineno,
)
producer_names = [
    "ema20",
    "ema50",
    "ema100",
    "ema200",
    "trend",
]

producer_assignments = {}

for name in producer_names:

    matches = []

    for node in ast.walk(ema_function):

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

    if len(matches) >= 1:

        print(
            f"{name.upper()}_ASSIGNMENT_AUTHORITY:",
            "PASS",
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

    else:

        print(
            f"{name.upper()}_ASSIGNMENT_AUTHORITY:",
            "FAIL",
        )
helper_functions = []

for node in ast.walk(tree):

    if (
        isinstance(node, ast.FunctionDef)
        and node.name == "_ema"
    ):
        helper_functions.append(node)

print(
    "_EMA_FUNCTION_COUNT:",
    len(helper_functions),
)

if len(helper_functions) != 1:
    raise RuntimeError(
        "Expected exactly one _ema() helper"
    )

helper = helper_functions[0]

print(
    "_EMA_FUNCTION_LINE:",
    helper.lineno,
)

parameters = [
    arg.arg
    for arg in helper.args.args
]

print(
    "_EMA_PARAMETERS:",
    parameters,
)

print(
    "_EMA_PARAMETER_COUNT:",
    len(parameters),
)
body_length = len(helper.body)

print(
    "_EMA_BODY_STATEMENT_COUNT:",
    body_length,
)

helper_returns = [
    node
    for node in ast.walk(helper)
    if isinstance(node, ast.Return)
]

print(
    "_EMA_RETURN_COUNT:",
    len(helper_returns),
)

print(
    "_EMA_BODY_AUTHORITY:",
    "PASS"
    if (
        body_length > 0
        and len(helper_returns) >= 1
    )
    else "FAIL",
)

return_node = helper_returns[0]

print(
    "_EMA_RETURN_TYPE:",
    type(return_node.value).__name__,
)

print(
    "_EMA_RETURN_SOURCE:",
    ast.unparse(return_node.value),
)
ema_assignments = []

for node in ast.walk(helper):

    if isinstance(node, ast.Assign):

        for target in node.targets:

            if (
                isinstance(target, ast.Name)
                and target.id == "ema"
            ):
                ema_assignments.append(node)

print(
    "_EMA_LOCAL_ASSIGNMENT_COUNT:",
    len(ema_assignments),
)

if len(ema_assignments) >= 1:

    print(
        "_EMA_LOCAL_ASSIGNMENT_AUTHORITY:",
        "PASS",
    )

    for i, assignment in enumerate(ema_assignments, 1):

        print(
            f"_EMA_LOCAL_{i}_TYPE:",
            type(assignment.value).__name__,
        )

        print(
            f"_EMA_LOCAL_{i}_SOURCE:",
            ast.unparse(assignment.value),
        )

else:

    print(
        "_EMA_LOCAL_ASSIGNMENT_AUTHORITY:",
        "FAIL",
    )
