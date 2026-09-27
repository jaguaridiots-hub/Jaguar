from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
V3 = (ROOT / "dashboard" / "command_center_v3.py").read_text(
    encoding="utf-8"
)


def block(source, start, end=None):
    pos = source.find(start)
    assert pos >= 0, f"MISSING={start}"

    if end is None:
        return source[pos:]

    end_pos = source.find(end, pos + len(start))
    assert end_pos >= 0, f"MISSING_END={end}"

    return source[pos:end_pos]


# --------------------------------------------------
# R54-D persistence boundary
# --------------------------------------------------

r54d = block(
    V3,
    "/* R54D_ANALYSIS_CONTEXT_STORAGE_START */",
    "/* R54D_ANALYSIS_CONTEXT_STORAGE_END */",
)

assert "sessionStorage" in r54d

assert "jaguar.r54d.analysisContext" in r54d

assert "interval" in r54d
assert "mode" in r54d

# --------------------------------------------------
# Normalization must remain canonical
# --------------------------------------------------

assert "normalizeAnalysisInterval" in r54d
assert "normalizeAnalysisMode" in r54d

# --------------------------------------------------
# Persistence operations
# --------------------------------------------------

assert "sessionStorage.getItem" in r54d
assert "sessionStorage.setItem" in r54d

# --------------------------------------------------
# Context restore
# --------------------------------------------------

assert re.search(
    r"restoreAnalysisContext\s*\(",
    r54d,
)

# --------------------------------------------------
# Context persistence
# --------------------------------------------------

assert re.search(
    r"persistAnalysisContext\s*\(",
    r54d,
)

# --------------------------------------------------
# Restore must feed canonical state
# --------------------------------------------------

assert (
    "state.interval" in r54d
    or "setActiveAnalysisContext" in r54d
)

assert (
    "state.mode" in r54d
    or "setActiveAnalysisContext" in r54d
)

# --------------------------------------------------
# Storage isolation
# --------------------------------------------------

for forbidden in (
    "localStorage",
    "broker_order",
    "position_size",
    "risk_percent",
    "execution_override",
):
    assert forbidden not in r54d, (
        f"FORBIDDEN_R54D_TOKEN={forbidden}"
    )

# --------------------------------------------------
# V3 integration
# --------------------------------------------------

assert re.search(
    r"restoreAnalysisContext\s*\(",
    V3,
)

print("R54D_STORAGE_BOUNDARY=PASS")
print("R54D_SESSION_STORAGE=PASS")
print("R54D_CONTEXT_NORMALIZATION=PASS")
print("R54D_RESTORE_CONTRACT=PASS")
print("R54D_PERSIST_CONTRACT=PASS")
print("R54D_STORAGE_ISOLATION=PASS")
print("R54D_ANALYSIS_CONTEXT_PERSISTENCE_CONTRACT=PASS")
