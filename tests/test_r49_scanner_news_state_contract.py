from pathlib import Path
import re

P = Path("dashboard/command_center_v3.py")
src = P.read_text()

print("=== R49 SCANNER / NEWS STATE CONTRACT ===")

# ------------------------------------------------------------
# Previous release boundaries must remain intact.
# ------------------------------------------------------------
previous_boundaries = [
    (
        "/* R45_DASHBOARD_CANVAS_SIZE_STATE_START */",
        "/* R45_DASHBOARD_CANVAS_SIZE_STATE_END */",
        "function setDashboardCanvasSize(canvas,width,height){",
    ),
    (
        "/* R46_DASHBOARD_CANVAS_CONTEXT_STATE_START */",
        "/* R46_DASHBOARD_CANVAS_CONTEXT_STATE_END */",
        "function setDashboardCanvasContextState(ctx,name,value){",
    ),
    (
        "/* R47_DASHBOARD_CANVAS_DASH_STATE_START */",
        "/* R47_DASHBOARD_CANVAS_DASH_STATE_END */",
        "function setDashboardCanvasLineDash(ctx,dash){",
    ),
    (
        "/* R48_DASHBOARD_STATE_SNAPSHOT_START */",
        "/* R48_DASHBOARD_STATE_SNAPSHOT_END */",
        "function setDashboardStateSnapshot(d){",
    ),
]

for start, end, func in previous_boundaries:
    assert start in src, start
    assert end in src, end
    assert func in src, func

print("R45_BOUNDARY=PASS")
print("R46_BOUNDARY=PASS")
print("R47_BOUNDARY=PASS")
print("R48_BOUNDARY=PASS")

# ------------------------------------------------------------
# R49 helper boundaries.
# ------------------------------------------------------------
scanner_start = "/* R49_DASHBOARD_SCANNER_STATE_START */"
scanner_end = "/* R49_DASHBOARD_SCANNER_STATE_END */"
news_start = "/* R49_DASHBOARD_NEWS_STATE_START */"
news_end = "/* R49_DASHBOARD_NEWS_STATE_END */"

scanner_match = re.search(
    re.escape(scanner_start) + r"(.*?)" + re.escape(scanner_end),
    src,
    re.S,
)
news_match = re.search(
    re.escape(news_start) + r"(.*?)" + re.escape(news_end),
    src,
    re.S,
)

assert scanner_match, "R49 scanner helper missing"
assert news_match, "R49 news helper missing"

scanner_helper = scanner_match.group(1)
news_helper = news_match.group(1)

assert "function setDashboardScannerState(data){" in scanner_helper
assert "function setDashboardNewsState(data){" in news_helper

print("R49_SCANNER_BOUNDARY=PASS")
print("R49_NEWS_BOUNDARY=PASS")

# ------------------------------------------------------------
# Each helper owns exactly one direct state assignment.
# ------------------------------------------------------------
assert scanner_helper.count("state.scanner=data;") == 1
assert news_helper.count("state.news=data;") == 1

assert "state.news" not in scanner_helper
assert "state.scanner" not in news_helper

print("R49_SCANNER_STATE_OWNERSHIP=PASS")
print("R49_NEWS_STATE_OWNERSHIP=PASS")
print("R49_CROSS_DOMAIN_SEPARATION=PASS")

# ------------------------------------------------------------
# Both helpers have a defensive input guard.
# ------------------------------------------------------------
guard = 'if(!data||typeof data!=="object")return;'

assert guard in scanner_helper
assert guard in news_helper

print("R49_INPUT_GUARDS=PASS")

# ------------------------------------------------------------
# Locate loaders.
# ------------------------------------------------------------
scanner_match = re.search(
    r"async function loadScanner\(symbol=null\)\{(.*?)\n\}",
    src,
    re.S,
)
news_match = re.search(
    r"async function loadNews\(refresh=false\)\{(.*?)\n\}",
    src,
    re.S,
)

assert scanner_match, "loadScanner() not found"
assert news_match, "loadNews() not found"

scanner_body = scanner_match.group(1)
news_body = news_match.group(1)

print("SCANNER_LOADER=PASS")
print("NEWS_LOADER=PASS")

# ------------------------------------------------------------
# Scanner success + fallback both use the setter.
# ------------------------------------------------------------
assert "state.scanner=data;" not in scanner_body
assert "state.scanner={" not in scanner_body

assert scanner_body.count("setDashboardScannerState(data);") == 1
assert scanner_body.count("setDashboardScannerState({") == 1

assert scanner_body.count("renderScanner();") == 2

success_pos = scanner_body.find("setDashboardScannerState(data);")
success_render = scanner_body.find("renderScanner();", success_pos)

fallback_pos = scanner_body.find("setDashboardScannerState({")
fallback_render = scanner_body.find("renderScanner();", fallback_pos)

assert success_pos >= 0
assert success_render > success_pos
assert fallback_pos >= 0
assert fallback_render > fallback_pos

assert 'status:"UNAVAILABLE"' in scanner_body

print("R49_SCANNER_LOAD_USES_SETTER=PASS")
print("R49_SCANNER_RENDER_ORDER=PASS")
print("R49_SCANNER_FALLBACK_PRESERVED=PASS")

# ------------------------------------------------------------
# News success + fallback both use the setter.
# ------------------------------------------------------------
assert "state.news=data;" not in news_body
assert "state.news={" not in news_body

assert news_body.count("setDashboardNewsState(data);") == 1
assert news_body.count("setDashboardNewsState({") == 1

assert news_body.count("renderNews();") == 2

success_pos = news_body.find("setDashboardNewsState(data);")
success_render = news_body.find("renderNews();", success_pos)

fallback_pos = news_body.find("setDashboardNewsState({")
fallback_render = news_body.find("renderNews();", fallback_pos)

assert success_pos >= 0
assert success_render > success_pos
assert fallback_pos >= 0
assert fallback_render > fallback_pos

assert 'status:"UNAVAILABLE"' in news_body

print("R49_NEWS_LOAD_USES_SETTER=PASS")
print("R49_NEWS_RENDER_ORDER=PASS")
print("R49_NEWS_FALLBACK_PRESERVED=PASS")

# ------------------------------------------------------------
# Network remains in loaders and does not enter helpers.
# ------------------------------------------------------------
assert "fetch(" in scanner_body
assert "fetch(" in news_body

assert "fetch(" not in scanner_helper
assert "fetch(" not in news_helper

print("NETWORK_OWNERSHIP_PRESERVED=PASS")

# ------------------------------------------------------------
# No storage, application-state, or execution authority in
# the new helpers.
# ------------------------------------------------------------
for helper in (scanner_helper, news_helper):
    for forbidden in [
        "sessionStorage",
        "localStorage",
        "state.ui",
        "state.candles",
        "state.symbol",
        "state.decision",
        "state.trade",
        "state.risk",
        "state.execution",
        "IDM",
        "TradePlanner",
        "RiskManager",
        "ExecutionConfirmation",
        "ExecutionGateway",
        "execution_intent",
        "place_order",
        "submit_order",
    ]:
        assert forbidden not in helper, forbidden

print("R49_NO_STORAGE=PASS")
print("R49_NO_CROSS_DOMAIN_STATE=PASS")
print("R49_NO_EXECUTION_AUTHORITY=PASS")

# ------------------------------------------------------------
# Exact direct state-assignment counts after centralization.
# ------------------------------------------------------------
scanner_assignments = re.findall(
    r"\bstate\.scanner\s*=",
    src,
)
news_assignments = re.findall(
    r"\bstate\.news\s*=",
    src,
)

assert len(scanner_assignments) == 1
assert len(news_assignments) == 1

print("R49_SCANNER_DIRECT_ASSIGNMENTS=1")
print("R49_NEWS_DIRECT_ASSIGNMENTS=1")

# ------------------------------------------------------------
# Exact loader invocation counts: success + fallback.
# The regex includes both loader call sites, not declarations.
# ------------------------------------------------------------
assert scanner_body.count("setDashboardScannerState(") == 2
assert news_body.count("setDashboardNewsState(") == 2

print("R49_SCANNER_LOADER_CALLS=2")
print("R49_NEWS_LOADER_CALLS=2")

# ------------------------------------------------------------
# Previous state boundaries remain separate.
# ------------------------------------------------------------
assert len(re.findall(r"\bstate\.ui\s*=", src)) == 1
assert len(re.findall(r"\bstate\.candles\s*=", src)) == 1
assert len(re.findall(r"\bstate\.symbol\s*=", src)) == 1

print("R48_STATE_BOUNDARY_PRESERVED=PASS")
print("R28_STATE_SYMBOL_BOUNDARY_PRESERVED=PASS")

print("R49_CONTRACT=PASS")
