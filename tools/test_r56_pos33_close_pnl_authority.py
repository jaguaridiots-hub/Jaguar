from pathlib import Path
import ast

src = Path("main.py").read_text()
tree = ast.parse(src)
lines = src.splitlines()

def line_for_call(name):
    rows = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == name
        ):
            rows.append(node.lineno)
    return rows

recovery_lines = line_for_call("recover_active_trade_plan")
record_lines = line_for_call("record_trade_close")

assert recovery_lines, "recover_active_trade_plan() not found"
assert record_lines, "record_trade_close() not found"

record_line = max(record_lines)
recovery_candidates = [
    line for line in recovery_lines
    if line < record_line
]
assert recovery_candidates, "No recovery call before close persistence"

recovery_line = max(recovery_candidates)

entry_lines = []
position_size_lines = []
pnl_lines = []

for node in ast.walk(tree):
    if not isinstance(node, ast.Assign):
        continue

    if len(node.targets) != 1:
        continue

    target = node.targets[0]

    if not isinstance(target, ast.Name):
        continue

    value_text = ast.get_source_segment(src, node.value) or ""

    if target.id == "entry_price":
        entry_lines.append((node.lineno, value_text))

    elif target.id == "position_size":
        position_size_lines.append((node.lineno, value_text))

    elif target.id == "pnl":
        pnl_lines.append((node.lineno, value_text))

close_entries = [
    item for item in entry_lines
    if recovery_line < item[0] < record_line
]
close_sizes = [
    item for item in position_size_lines
    if recovery_line < item[0] < record_line
]
close_pnls = [
    item for item in pnl_lines
    if recovery_line < item[0] < record_line
]

assert close_entries, "No close entry assignment after durable revalidation"
assert close_sizes, "No close position-size assignment after durable revalidation"
assert close_pnls, "No close PnL assignment after durable revalidation"

entry_line, entry_expr = close_entries[-1]
size_line, size_expr = close_sizes[-1]
pnl_line, _ = close_pnls[-1]

assert "close_contract" in entry_expr
assert "position.entry" not in entry_expr
assert "close_contract" in size_expr
assert "position.entry" not in size_expr

assert recovery_line < entry_line
assert recovery_line < size_line
assert recovery_line < pnl_line
assert pnl_line < record_line

region = "\n".join(
    lines[recovery_line - 1 : record_line]
)

assert "position.entry" not in region
assert 'close_contract["Entry"]' in region
assert 'close_contract["PositionSize"]' in region

print(f"R56_POS33_RECOVERY_LINE={recovery_line}")
print(f"R56_POS33_ENTRY_AUTHORITY_LINE={entry_line}")
print(f"R56_POS33_POSITION_SIZE_AUTHORITY_LINE={size_line}")
print(f"R56_POS33_PNL_LINE={pnl_line}")
print(f"R56_POS33_RECORD_CLOSE_LINE={record_line}")

print(
    "R56_POS33_CLOSE_PNL_USES_VALIDATED_DURABLE_ENTRY: PASS"
)
print(
    "R56_POS33_CLOSE_PNL_BEFORE_REVALIDATION_GAP_REMOVED: PASS"
)
print(
    "R56_POS33_MUTABLE_POSITION_ENTRY_CANNOT_SET_CLOSE_PNL: PASS"
)
print("R56_POS33_CLOSE_PNL_AUTHORITY: PASS")
