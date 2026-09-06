#!/usr/bin/env python3

"""
R32
Fibonacci Producer Authority
"""

import ast
from pathlib import Path

TARGET = Path("indicators/fibonacci.py")

tree = ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)

functions = []

for node in ast.walk(tree):

    if (
        isinstance(node, ast.FunctionDef)
        and node.name == "fibonacci"
    ):
        functions.append(node)

print(
    "FIBONACCI_FUNCTION_COUNT:",
    len(functions),
)

if len(functions) != 1:
    raise RuntimeError(
        "Expected exactly one fibonacci() function"
    )

fibonacci_function = functions[0]

print(
    "FIBONACCI_FUNCTION_NAME:",
    fibonacci_function.name,
)

print(
    "FIBONACCI_FUNCTION_LINE:",
    fibonacci_function.lineno,
)

parameters = [
    arg.arg
    for arg in fibonacci_function.args.args
]

print(
    "FIBONACCI_PARAMETERS:",
    parameters,
)

print(
    "FIBONACCI_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) >= 1
    and parameters[0] == "candles"
)

print(
    "FIBONACCI_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)
body_length = len(fibonacci_function.body)

print(
    "FIBONACCI_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(fibonacci_function)
    if isinstance(node, ast.Return)
]

print(
    "FIBONACCI_RETURN_COUNT:",
    len(return_nodes),
)

body_authority = (
    body_length > 0
    and len(return_nodes) >= 1
)

print(
    "FIBONACCI_BODY_AUTHORITY:",
    "PASS"
    if body_authority
    else "FAIL",
)
return_node = return_nodes[0]

print(
    "FIBONACCI_RETURN_TYPE:",
    type(return_node.value).__name__,
)

print(
    "FIBONACCI_RETURN_SOURCE:",
    ast.unparse(return_node.value),
)

return_contract_authority = (
    return_node.value is not None
)

print(
    "FIBONACCI_RETURN_CONTRACT_AUTHORITY:",
    "PASS"
    if return_contract_authority
    else "FAIL",
)
producer_names = [
    "levels",
]

producer_assignments = {}

for name in producer_names:

    matches = []

    for node in ast.walk(fibonacci_function):

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
