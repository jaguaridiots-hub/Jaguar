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

        position.update_stop_loss(
            trade_status["StopLoss"],
        )

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
