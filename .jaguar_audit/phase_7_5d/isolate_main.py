from pathlib import Path
import ast
import subprocess


AUDIT = Path(
    ".jaguar_audit/phase_7_5d"
)

CANDIDATE = (
    AUDIT
    / "main.index_candidate.py"
)

WORKTREE_BACKUP = (
    AUDIT
    / "main.worktree.before_index_isolation.py"
)


def git_text(spec):
    result = subprocess.run(
        [
            "git",
            "show",
            spec,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout


def replace_once(
    text,
    old,
    new,
    contract,
):
    count = text.count(old)

    if count != 1:
        raise SystemExit(
            f"FAIL: {contract} count={count}"
        )

    return text.replace(
        old,
        new,
        1,
    )


AUDIT.mkdir(
    parents=True,
    exist_ok=True,
)

worktree = Path(
    "main.py"
).read_text()

WORKTREE_BACKUP.write_text(
    worktree
)

text = git_text(
    "HEAD:main.py"
)


old_import = (
    "from data.market_data import get_klines"
)

text = replace_once(
    text,
    old_import,
    "",
    "HEAD get_klines import contract",
)


old_startup = """# ===================================================
# LOAD LIVE MARKET DATA
# ===================================================

candles = get_klines()

latest = candles[-1]

state = kernel.get_state()

state.symbol = "BTCUSDT"
state.timeframe = "15m"
state.price = latest["close"]
state.volume = latest["volume"]
"""


new_startup = """# ===================================================
# CANONICAL STARTUP MARKET HYDRATION
# ===================================================

state = kernel.get_state()

state = update_state(
    state,
    SYMBOL,
)

candles = state.market["candles"]

latest = candles[-1]
"""


text = replace_once(
    text,
    old_startup,
    new_startup,
    "HEAD startup contract",
)


old_loop = """    position.update(state.price)
    while position.position != "NONE":

        candles = get_klines()
        latest = candles[-1]

        state = update_state(state, "BTCUSDT")
"""


new_loop = """    position.update(state.price)
    while position.position != "NONE":

        state = update_state(
            state,
            SYMBOL,
        )
"""


text = replace_once(
    text,
    old_loop,
    new_loop,
    "HEAD active-loop contract",
)


tree = ast.parse(
    text
)

errors = []

imports = []

calls = []


for node in ast.walk(tree):

    if isinstance(
        node,
        ast.ImportFrom,
    ):

        for alias in node.names:

            imports.append(
                (
                    node.module,
                    alias.name,
                    node.lineno,
                )
            )

    if isinstance(
        node,
        ast.Call,
    ):

        if isinstance(
            node.func,
            ast.Name,
        ):

            calls.append(
                (
                    node.func.id,
                    len(node.args),
                    node.lineno,
                )
            )


direct_imports = [
    item
    for item in imports
    if item[0] == "data.market_data"
    and item[1] == "get_klines"
]


direct_calls = [
    item
    for item in calls
    if item[0] == "get_klines"
]


update_state_calls = [
    item
    for item in calls
    if item[0] == "update_state"
]


indicator_calls = [
    item
    for item in calls
    if item[0] == "update_market_state"
]


if direct_imports:
    errors.append(
        "direct get_klines import remains"
    )


if direct_calls:
    errors.append(
        "direct get_klines call remains"
    )


if len(update_state_calls) != 2:
    errors.append(
        "unexpected update_state call count: "
        f"{len(update_state_calls)}"
    )


if len(indicator_calls) != 1:
    errors.append(
        "unexpected update_market_state "
        "call count: "
        f"{len(indicator_calls)}"
    )

elif indicator_calls[0][1] != 1:
    errors.append(
        "indicator bridge does not use "
        "state authority"
    )


required = (
    "CANONICAL STARTUP MARKET HYDRATION",
    'candles = state.market["candles"]',
    "latest = candles[-1]",
)


for fragment in required:

    if fragment not in text:

        errors.append(
            f"missing fragment: {fragment!r}"
        )


if errors:

    print(
        "INDEX_CANDIDATE_CONTRACT: FAIL"
    )

    for error in errors:

        print(
            "ERROR:",
            error,
        )

    raise SystemExit(1)


CANDIDATE.write_text(
    text
)


if Path(
    "main.py"
).read_text() != worktree:

    raise SystemExit(
        "FAIL: worktree main.py changed"
    )


print(
    "PHASE_7_5D_INDEX_CANDIDATE: BUILT"
)

print(
    "INDEX_CANDIDATE_CONTRACT: PASS"
)

print(
    "Direct get_klines imports:",
    len(direct_imports),
)

print(
    "Direct get_klines calls  :",
    len(direct_calls),
)

print(
    "update_state calls       :",
    len(update_state_calls),
)

print(
    "update_market_state      :",
    "STATE_AUTHORITY",
)

print(
    "WORKTREE_PRESERVATION    : PASS"
)
