from core.kernel import JaguarKernel
from core.logger import JaguarLogger
from core.registry import ModuleRegistry
from core.event_bus import EventBus
from engine.master_decision import analyze as master_decision
from data.market_data import get_klines
from analysis.multi_timeframe import report
from engine.trade_planner import trade_plan
from analysis.support_resistance_engine import support_resistance
from engine.trade_manager import TradeManager
from engine.position_manager import PositionManager
from engine.trade_journal import TradeJournal
from engine.performance import Performance
from engine.live_feed import LiveFeed

print("=" * 50)
print("              JAGUAR QUANT X v2.0")
print("=" * 50)

# Logger
log = JaguarLogger()
log.info("Starting Jaguar Quant X...")

# Kernel
kernel = JaguarKernel()
kernel.initialize("BTCUSDT", "15m")

# Registry
registry = ModuleRegistry()

modules = [
    "Kernel",
    "Market Data",
    "Indicators",
    "Gann Engine",
    "SMC Engine",
    "AI Brain",
    "Probability Engine",
    "Risk Engine",
    "Trade Engine",
]

for module in modules:
    registry.register(module)

registry.show()

# Event Bus
bus = EventBus()
bus.publish("startup", "All Systems Online")

print("\n" + "=" * 50)
print("Jaguar Quant X Ready To Trade")
print("=" * 50)

# ===================================================
# LOAD LIVE MARKET DATA
# ===================================================

candles = get_klines()

latest = candles[-1]

state = kernel.get_state()

state.symbol = "BTCUSDT"
state.timeframe = "15m"
state.price = latest["close"]
state.volume = latest["volume"]

print("\n========= LIVE MARKET =========")
print("Symbol     :", state.symbol)
print("Timeframe  :", state.timeframe)
print("Price      :", state.price)
print("High       :", latest["high"])
print("Low        :", latest["low"])
print("Volume     :", state.volume)

print("\nMarket State")
print(state.summary())
from indicators.indicator_engine import update_market_state

volume_status = update_market_state(state)

print("\nIndicators")
print("-------------------------")
print("EMA20 :", state.ema20)
print("EMA50 :", state.ema50)
print("EMA100:", state.ema100)
print("EMA200:", state.ema200)
print("RSI   :", state.rsi)
print("ATR   :", state.atr)
print("Volume:", volume_status)

mtf = report()
print("\n====== MULTI TIMEFRAME ======")
for tf, trend in mtf.items():
    print(f"{tf:4} : {trend}")

report = master_decision(state)

state.ai_score = report["score"]
state.probability = report["probability"]
state.confidence = report["confidence"]

reasons = []
reasons.extend(report["ai"]["reasons"])
reasons.extend(report["smart_money"]["reasons"])

plan = report["plan"]

print("======== AI DECISION ========")
print(f"AI Score     : {state.ai_score}")
print(f"Confidence   : {state.confidence}")
print(f"Probability  : {state.probability}%")
print(f"Decision     : {state.decision}")

levels = support_resistance()

print("\n====== SUPPORT / RESISTANCE ======")
print("Support   :", round(levels["support"], 2))
print("Resistance:", round(levels["resistance"], 2))

performance = Performance()

journal = TradeJournal()

position = PositionManager()

manager = TradeManager()

if plan is not None:
    trade_status = manager.manage(state, plan)
else:
    trade_status = {
        "Action": "NO TRADE",
        "StopLoss": 0,
        "BreakEven": False,
        "Trailing": False
    }

if plan:
    journal.save(state, plan)

    if plan["Direction"] == "🟢 STRONG BUY":
        position.open_trade(
            "LONG",
            plan["Entry"],
            plan["StopLoss"],
            plan["TP1"]
        )

    elif plan["Direction"] == "🔴 STRONG SELL":
        position.open_trade(
            "SHORT",
            plan["Entry"],
            plan["StopLoss"],
            plan["TP1"]
        )

    print("\n========== TRADE PLAN ==========")

    print("Direction     :", plan["Direction"])
    print("Entry         :", plan["Entry"])
    print("Stop Loss     :", plan["StopLoss"])

    print("TP1           :", plan["TP1"])
    print("TP2           :", plan["TP2"])
    print("TP3           :", plan["TP3"])

    print("Risk Reward   : 1 :", plan["RiskReward"])

    print("Position Size :", plan["PositionSize"])

    print("Risk Amount   : $", plan["RiskAmount"])

else:
    print("\nNo Trade Plan Available")

if plan:
    position.update(state.price)
    status = position.status()

    print("\n======== POSITION MANAGER ========")
    print("Position :", status["Position"])
    print("Entry    :", status["Entry"])
    print("PnL      :", status["PnL"])
else:
    print("\nNo Position")

    print("\n======== TRADE MANAGER ========")

    print("Action      :", trade_status["Action"])
    print("Stop Loss   :", trade_status["StopLoss"])
    print("Break Even  :", trade_status["BreakEven"])
    print("Trailing SL :", trade_status["Trailing"])

    stats = performance.summary()

    print("\n========== PERFORMANCE ==========")
    print("Total Trades :", stats["Trades"])
    print("Wins         :", stats["Wins"])
    print("Losses       :", stats["Losses"])
    print("Win Rate     :", f'{stats["WinRate"]}%')
    print("=================================")

    print("\nReasons")
    unique_reasons = list(dict.fromkeys(reasons))

    for r in unique_reasons:
        print("✓", r)

    print("\n========== LIVE BINANCE FEED ==========")

    feed = LiveFeed(
        state,
        plan,
        trade_status,
        "btcusdt"
    )
    feed.start()
