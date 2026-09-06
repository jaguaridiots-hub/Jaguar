from core.kernel import JaguarKernel
from core.logger import JaguarLogger
from core.registry import ModuleRegistry
from core.event_bus import EventBus

from engine.trade_manager import TradeManager
from engine.position_manager import PositionManager
from engine.trade_journal import TradeJournal
from engine.performance import Performance
from engine.live_feed import LiveFeed
import time
from engine.state_manager import save, load, clear
from market.live_loader import update_state

SYMBOL = "BTCUSDT"
TIMEFRAME = "15m"

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
# CANONICAL STARTUP MARKET HYDRATION
# ===================================================

state = kernel.get_state()

state = update_state(
    state,
    SYMBOL,
)

candles = state.market["candles"]

latest = candles[-1]

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

#mtf = report()
#print("\n====== MULTI TIMEFRAME ======")
#for tf, trend in mtf.items():
#    print(f"{tf:4} : {trend}")

from engine.institutional_master import analyze as institutional_master

report = institutional_master(state)
print(report)

decision = report["decision"]

state.ai_score = decision["score"]
state.probability = decision["probability"]
state.confidence = decision["confidence"]
state.decision = decision["decision"]

plan = report["plan"]
risk = report["risk"]

print("\n========== MASTER DECISION ==========")
print("Decision    :", state.decision)
print("Confidence  :", state.confidence)
print(f"Probability : {state.probability}%")
print("AI Score    :", state.ai_score)

reasons = decision["reasons"]

plan = report["plan"]

#print("======== AI DECISION ========")
#print(f"AI Score     : {state.ai_score}")
#print(f"Confidence   : {state.confidence}")
#print(f"Probability  : {state.probability}%")
#print(f"Decision     : {state.decision}")

gann = report["engines"]["Gann"]

support = gann["metadata"]["support"]
resistance = gann["metadata"]["resistance"]

print("\n====== SUPPORT / RESISTANCE ======")
print("Support   :", round(support, 2))
print("Resistance:", round(resistance, 2))

performance = Performance()

journal = TradeJournal()

position = PositionManager()

load(position)

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

#if plan:
if plan and plan.get("Direction"):

    journal.save(state, plan)

    if plan.get("Direction") == "🟢 STRONG BUY":
        position.open_trade(
            "LONG",
            plan.get("Entry"),
            plan.get("StopLoss"),
            plan.get("TP1")
        )

    elif plan.get("Direction") == "🔴 STRONG SELL":
        position.open_trade(
            "SHORT",
            plan.get("Entry"),
            plan.get("StopLoss"),
            plan.get("TP1")
        )

else:
    print("\nNo trade setup.")

    print("\n========== TRADE PLAN ==========")


if plan and plan.get("Direction"):

    print("Direction :", plan.get("Direction"))
    print("Entry :", plan.get("Entry"))
    print("Stop Loss :", plan.get("StopLoss"))

    print("TP1 :", plan.get("TP1"))
    print("TP2 :", plan.get("TP2"))
    print("TP3 :", plan.get("TP3"))

    print("Risk Reward :", plan.get("RiskReward"))

#    print("Position Size :", plan.get("PositionSize"))

 #   print("Risk Amount :", plan.get("RiskAmount"))

else:
    print("\nNo Trade Plan Available")

if plan:

    if position.position == "NONE":

        if "BUY" in plan["Direction"]:
            position.open_trade(
                "LONG",
                plan["Entry"],
                plan["StopLoss"],
                plan["TP1"]
            )

            save(position)

        elif "SELL" in plan["Direction"]:
            position.open_trade(
                "SHORT",
                plan["Entry"],
                plan["StopLoss"],
                plan["TP1"]
            )

            save(position)

    position.update(state.price)
    while position.position != "NONE":

        state = update_state(
            state,
            SYMBOL,
        )

        print("\n===== LIVE MARKET =====")
        print("Symbol :", state.symbol)
        print("Price  :", state.price)
        print("High   :", state.high)
        print("Low    :", state.low)
        print("Volume :", state.volume)

        position.update(state.price)
        save(position)

        trade_status = manager.manage(state, plan)

        position.stop_loss = trade_status["StopLoss"]

        position.update(state.price)

        status = position.status()

        print("Price      :", state.price)
        print("PnL        :", status["PnL"])
        print("Action     :", trade_status["Action"])
        print("Stop Loss  :", trade_status["StopLoss"])
        print("BreakEven  :", trade_status["BreakEven"])
        print("Trailing   :", trade_status["Trailing"])

        if trade_status["Action"] in [
            "EXIT",
            "STOP LOSS",
        ]:
            position.close_trade()

            clear()

            print("\nTrade Closed")
            break

        time.sleep(5)

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

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Jaguar...")
        feed.stop()
