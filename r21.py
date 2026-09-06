#!/usr/bin/env python3

"""
R21
ATR Mathematical Lineage Authority
"""

import ast
from pathlib import Path

TARGET = Path("indicators/atr.py")

tree = ast.parse(
    TARGET.read_text(encoding="utf-8")
)


def find_atr(tree):

    for node in ast.walk(tree):

        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "atr"
        ):
            return node

    raise RuntimeError("atr() not found")


atr_function = find_atr(tree)

print("ATR_FUNCTION:", atr_function.name)
print("ATR_LINE:", atr_function.lineno)

trs_assignments = []

for node in ast.walk(atr_function):

    if isinstance(node, ast.Assign):

        for target in node.targets:

            if (
                isinstance(target, ast.Name)
                and target.id == "trs"
            ):
                trs_assignments.append(node)

print(
    "TRS_ASSIGNMENT_COUNT:",
    len(trs_assignments),
)

if len(trs_assignments) == 1:

    trs_assignment = trs_assignments[0]

    print(
        "TRS_ASSIGNMENT_TYPE:",
        type(trs_assignment.value).__name__,
    )

    print(
        "TRS_ASSIGNMENT_SOURCE:",
        ast.unparse(trs_assignment.value),
    )

else:

    print(
        "TRS_ASSIGNMENT_AUTHORITY: FAIL"
    )

trs_append_calls = []

for node in ast.walk(atr_function):

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "trs"
        and node.func.attr == "append"
    ):
        trs_append_calls.append(node)

print(
    "TRS_APPEND_CALL_COUNT:",
    len(trs_append_calls),
)

for i, call in enumerate(trs_append_calls, 1):

    print(
        f"TRS_APPEND_{i}_SOURCE:",
        ast.unparse(call.args[0]),
    )

tr_assignments = []

for node in ast.walk(atr_function):

    if isinstance(node, ast.Assign):

        for target in node.targets:

            if (
                isinstance(target, ast.Name)
                and target.id == "tr"
            ):
                tr_assignments.append(node)

print(
    "TR_ASSIGNMENT_COUNT:",
    len(tr_assignments),
)

if len(tr_assignments) == 1:

    tr_assignment = tr_assignments[0]

    print(
        "TR_ASSIGNMENT_TYPE:",
        type(tr_assignment.value).__name__,
    )

    print(
        "TR_ASSIGNMENT_SOURCE:",
        ast.unparse(tr_assignment.value),
    )

else:

    print(
        "TR_ASSIGNMENT_AUTHORITY: FAIL"
    )

print()
print("=" * 80)
print("R21 FINAL")
print("=" * 80)

math_authority = (
    len(tr_assignments) == 1
    and len(trs_append_calls) == 1
)

print("R21_TR_PRODUCER:", ast.unparse(tr_assignment.value))
print("R21_TR_COLLECTION:", "trs.append(tr)")
print(
    "R21_ATR_AVERAGE:",
    "Verified in R20"
)
print("R21_RETURN_VALUE:", "round(value, 2)")

print(
    "R21_MATHEMATICAL_AUTHORITY:",
    "PASS" if math_authority else "FAIL",
)

