from pathlib import Path
import re

SRC = Path("dashboard/command_center_v3.py")

def balanced(text, start, wanted="section"):
    first = re.search(
        r"<\s*([A-Za-z][A-Za-z0-9:-]*)\b[^>]*?>",
        text[start:],
        re.S
    )
    assert first

    tag = first.group(1)
    assert tag.lower() == wanted.lower()

    rx = re.compile(
        r"<\s*(/?)\s*" + re.escape(tag) + r"\b[^>]*?>",
        re.I | re.S
    )

    depth = 0
    begin = start + first.start()

    for m in rx.finditer(text, begin):
        if not m.group(1):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return text[begin:m.end()]

    raise AssertionError("unclosed section")

src = SRC.read_text()

assert src.count('class="r24-tab-panel"') == 5
assert '<div class="r24-tab-panel"' not in src

names = ["overview","market","scanner","news","system"]

for name in names:
    assert src.count(f'id="r24-panel-{name}"') == 1

m = re.search(
    r'<section\b[^>]*id="r24-panel-overview"[^>]*>',
    src,
    re.I
)
assert m and " hidden" not in m.group(0)

for name in names[1:]:
    m = re.search(
        r'<section\b[^>]*id="r24-panel-' + name + r'"[^>]*>',
        src,
        re.I
    )
    assert m and " hidden" in m.group(0)

blocks = {
    name: balanced(src, re.search(
        r'<section\b[^>]*id="r24-panel-' + name + r'"[^>]*>',
        src,
        re.I
    ).start())
    for name in names
}

req = {
    "overview": [
        "hero",
        "pipeline",
        "JAGUAR DECISION GATE",
        "thesis-invalidation-card",
        "what-change-card",
        "trade-setup-card",
        "confidence-breakdown",
    ],
    "market": [
        "chart-card",
        "fibonacci-card",
        "coverage-card",
        "mtf-sufficiency",
        "MULTI-TIMEFRAME MARKET CONTEXT",
    ],
    "scanner": [
        "<!-- R19_SCANNER_UI_START -->",
        "<!-- R21_SCANNER_ALERT_UI_START -->",
        "<!-- R23_SCANNER_ALERT_CONTEXT_UI_START -->",
        "scanner-card",
        "scanner-alert-card",
        "scanner-alert-context-card",
    ],
    "news": [
        "<!-- R18_NEWS_UI_START -->",
        "news-card",
    ],
    "system": [
        "idmRows",
        'id="reasons"',
        "SYSTEM STATE",
    ],
}

for name, tokens in req.items():
    for token in tokens:
        assert token in blocks[name], f"{token} missing from {name}"

assert "chart-card" not in blocks["overview"]
assert "scanner-card" not in blocks["market"]
assert "news-card" not in blocks["market"]
assert "news-card" not in blocks["scanner"]

for marker in [
    "<!-- R19_SCANNER_UI_START -->",
    "<!-- R21_SCANNER_ALERT_UI_START -->",
    "<!-- R23_SCANNER_ALERT_CONTEXT_UI_START -->",
    "<!-- R18_NEWS_UI_START -->",
]:
    assert src.count(marker) == 1

assert '".hero"' in src
assert '".pipeline"' in src

router = re.search(
    r'name\s*:\s*"overview"\s*,\s*selectors\s*:\s*\[(.*?)\]',
    src,
    re.S
)
assert router

overview_selectors = router.group(1)
assert '".hero"' in overview_selectors
assert '".pipeline"' in overview_selectors
assert '".decision-gate"' not in overview_selectors

print("R52_TRUE_TAB_CONTAINMENT_CONTRACT=PASS")
