"""
==========================================================
        JAGUAR QUANT X v3.0 CONFIGURATION
==========================================================
"""

# ========================================================
# MARKET
# ========================================================

SYMBOL = "BTCUSDT"
TIMEFRAME = "15m"
EXCHANGE = "BINANCE"

WS_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL.lower()}@trade"

# ========================================================
# ACCOUNT
# ========================================================

ACCOUNT_BALANCE = 1000.0
LEVERAGE = 1

RISK_PERCENT = 2.0
MAX_OPEN_TRADES = 1

# ========================================================
# AI
# ========================================================

MIN_AI_SCORE = 15

STRONG_BUY_SCORE = 23
BUY_SCORE = 18

STRONG_SELL_SCORE = -23
SELL_SCORE = -18

MIN_PROBABILITY = 60

# ========================================================
# EMA
# ========================================================

EMA_FAST = 20
EMA_MID = 50
EMA_MAJOR = 100
EMA_TREND = 200

# ========================================================
# RSI
# ========================================================

RSI_PERIOD = 14

RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# ========================================================
# ATR
# ========================================================

ATR_PERIOD = 14

SL_ATR_MULTIPLIER = 1.5

TP1_RR = 1.0
TP2_RR = 2.0
TP3_RR = 3.0

# ========================================================
# SMART MONEY
# ========================================================

USE_ORDER_BLOCK = True
USE_FVG = True
USE_BOS = True
USE_CHOCH = True
USE_LIQUIDITY = True
USE_INDUCEMENT = True
USE_PREMIUM_DISCOUNT = True
USE_SMT = True

# ========================================================
# FILTERS
# ========================================================

USE_VOLUME_FILTER = True
USE_MULTI_TIMEFRAME = True
USE_REGIME_FILTER = True
USE_CONFLUENCE = True

# ========================================================
# TERMINAL
# ========================================================

REFRESH_RATE = 1

SHOW_TIME = True
SHOW_MARKET = True
SHOW_PNL = True
SHOW_SCORE = True
SHOW_POSITION = True
SHOW_REASON = True

# ========================================================
# LOGGING
# ========================================================

ENABLE_LOGGER = True
LOG_FILE = "logs/trades.csv"

# ========================================================
# COLORS
# ========================================================

TITLE = "yellow"

BUY = "green"

SELL = "red"

NO_TRADE = "white"

WARNING = "yellow"

INFO = "cyan"

SUCCESS = "green"

ERROR = "red"

# ========================================================
# TERMINAL
# ========================================================

LINE = "=" * 58
SMALL_LINE = "-" * 58

APP_NAME = "JAGUAR QUANT X"

VERSION = "3.0 Institutional"

# ========================================================
# PERFORMANCE
# ========================================================

ENABLE_BACKTEST = True
ENABLE_TRADE_LOG = True
ENABLE_ANALYTICS = True

# ========================================================
# END
# ========================================================
