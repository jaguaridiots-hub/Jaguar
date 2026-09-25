from pathlib import Path
import re

SOURCE_PATH = Path("dashboard/command_center_v3.py")
SOURCE = SOURCE_PATH.read_text()

def section(start_marker: str, end_marker: str) -> str:
    start = SOURCE.index(start_marker)
    end = SOURCE.index(end_marker, start)
    return SOURCE[start:end]

TEXT_START = "/* R42_DASHBOARD_TEXT_CONTENT_STATE_START */"
TEXT_END = "/* R42_DASHBOARD_TEXT_CONTENT_STATE_END */"

HTML_START = "/* R42_DASHBOARD_INNERHTML_STATE_START */"
HTML_END = "/* R42_DASHBOARD_INNERHTML_STATE_END */"

APPEND_START = "/* R42_DASHBOARD_HTML_APPEND_STATE_START */"
APPEND_END = "/* R42_DASHBOARD_HTML_APPEND_STATE_END */"

TEXT_HELPER = section(TEXT_START, TEXT_END)
HTML_HELPER = section(HTML_START, HTML_END)
APPEND_HELPER = section(APPEND_START, APPEND_END)

# ------------------------------------------------------------------
# Helper existence
# ------------------------------------------------------------------

assert TEXT_START in SOURCE
assert TEXT_END in SOURCE
assert HTML_START in SOURCE
assert HTML_END in SOURCE
assert APPEND_START in SOURCE
assert APPEND_END in SOURCE

assert "function setDashboardTextContent(" in TEXT_HELPER
assert "function setDashboardInnerHTML(" in HTML_HELPER
assert "function appendDashboardHTML(" in APPEND_HELPER

# ------------------------------------------------------------------
# Helper semantics
# ------------------------------------------------------------------

assert re.search(
    r'element\.textContent\s*=\s*String\(value\?\?""\)',
    TEXT_HELPER,
)

assert re.search(
    r'element\.innerHTML\s*=\s*String\(value\?\?""\)',
    HTML_HELPER,
)

assert "element.insertAdjacentHTML(" in APPEND_HELPER
assert 'position,' in APPEND_HELPER
assert 'String(value??"")' in APPEND_HELPER

# Defensive guards remain mandatory.
assert '!("textContent" in element)' in TEXT_HELPER
assert '!("innerHTML" in element)' in HTML_HELPER
assert 'typeof position!=="string"' in APPEND_HELPER

# ------------------------------------------------------------------
# Direct mutations are allowed ONLY inside their canonical helpers.
# ------------------------------------------------------------------

def outside_helper_matches(pattern: str, ranges: list[tuple[int, int]]) -> list[int]:
    matches = [m.start() for m in re.finditer(pattern, SOURCE)]
    lines = SOURCE.splitlines(keepends=True)

    offsets = []
    total = 0
    for i, line in enumerate(lines, 1):
        offsets.append((total, total + len(line), i))
        total += len(line)

    result = []
    for pos in matches:
        inside = any(start <= pos < end for start, end in ranges)
        if not inside:
            for start, end, line_no in offsets:
                if start <= pos < end:
                    result.append(line_no)
                    break
    return result


helper_ranges = []

for start_marker, end_marker in (
    (TEXT_START, TEXT_END),
    (HTML_START, HTML_END),
    (APPEND_START, APPEND_END),
):
    start = SOURCE.index(start_marker)
    end = SOURCE.index(end_marker, start) + len(end_marker)
    helper_ranges.append((start, end))

assert not outside_helper_matches(
    r'\.innerHTML\s*=',
    helper_ranges,
), "Direct innerHTML assignment remains outside R42 helper"

assert not outside_helper_matches(
    r'\.textContent\s*=',
    helper_ranges,
), "Direct textContent assignment remains outside R42 helper"

assert not outside_helper_matches(
    r'\.innerText\s*=',
    helper_ranges,
), "Direct innerText assignment remains outside R42 helper"

assert not outside_helper_matches(
    r'\.insertAdjacentHTML\(',
    helper_ranges,
), "Direct insertAdjacentHTML usage remains outside R42 helper"

# ------------------------------------------------------------------
# No second implementation / no duplicate helper definitions.
# ------------------------------------------------------------------

assert len(re.findall(r'function setDashboardTextContent\(', SOURCE)) == 1
assert len(re.findall(r'function setDashboardInnerHTML\(', SOURCE)) == 1
assert len(re.findall(r'function appendDashboardHTML\(', SOURCE)) == 1

# ------------------------------------------------------------------
# All known content-rendering surfaces must route through helpers.
# ------------------------------------------------------------------

for token in (
    "setDashboardTextContent(",
    "setDashboardInnerHTML(",
    "appendDashboardHTML(",
):
    assert token in SOURCE

# Assistant chat must use the append helper rather than a direct DOM
# insertion, while preserving existing beforeend semantics.
assistant_section = SOURCE[
    SOURCE.index('document.getElementById("aiForm")')
    :
]

import re

assert re.search(
    r'appendDashboardHTML\(log\s*,\s*"beforeend"\s*,',
    assistant_section,
)

assert len(re.findall(
    r'appendDashboardHTML\(log\s*,\s*"beforeend"\s*,',
    assistant_section,
)) == 3

print("R42 DOM CONTENT STATE CONTRACT: PASS")
