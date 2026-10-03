"""
=========================================
Jaguar Quant X Enterprise Configuration
=========================================
"""

# -----------------------------
# Trading
# -----------------------------

# -----------------------------
# Execution Mode
# -----------------------------

# Authoritative transport selection.
# Unset defaults to PAPER. LIVE must be selected explicitly at runtime.
EXECUTION_MODE_ENV = "JAGUAR_EXECUTION_MODE"
DEFAULT_EXECUTION_MODE = "PAPER"
ALLOWED_EXECUTION_MODES = frozenset({"PAPER", "LIVE"})

DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "15m"

# -----------------------------
# Capital
# -----------------------------

ACCOUNT_CAPITAL = 100000.0
RISK_PERCENT = 1.0

# -----------------------------
# ATR
# -----------------------------

ATR_PERIOD = 14
ATR_STOP_MULTIPLIER = 1.5
ATR_TP1_MULTIPLIER = 2.0
ATR_TP2_MULTIPLIER = 3.0

# -----------------------------
# AI Thresholds
# -----------------------------

STRONG_BUY_SCORE = 80
BUY_SCORE = 50
SELL_SCORE = -50
STRONG_SELL_SCORE = -80

# -----------------------------
# Confidence
# -----------------------------

GRADE_A_PLUS = 90
GRADE_A = 80
GRADE_B = 70
GRADE_C = 60

# -----------------------------
# Dashboard
# -----------------------------

SHOW_EVENTS = True
SHOW_REASONS = True
SHOW_DEBUG = False

# -----------------------------
# Logging
# -----------------------------

ENABLE_LOGGING = True
LOG_LEVEL = "INFO"
