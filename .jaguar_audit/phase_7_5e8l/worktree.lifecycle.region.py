position = PositionManager()

manager = TradeManager()


# ==================================================
# RESTORE POSITION
# ==================================================

position_loaded = load(position)


if position_loaded:

    print(
        "\nExisting trade state loaded."
    )


# ==================================================
# DEFAULT TRADE STATUS
# ==================================================

trade_status = {

    "Action": "NO TRADE",

    "StopLoss": 0,

    "BreakEven": False,

    "Trailing": False,

}


# ==================================================
# NEW TRADE
# ==================================================

execution_ready = execution.get(
    "ready",
    False,
)


if (
    plan
    and plan.get("Direction")
    and execution_ready
):

    trade_status = manager.manage(
        state,
        plan,
    )

    journal.save(
        state,
        plan,
    )

    if position.position == "NONE":

        direction = plan.get(
            "Direction",
            "",
        )

        if "BUY" in direction:

            position.open_trade(
                "LONG",
                plan["Entry"],
                plan["StopLoss"],
                plan["TP1"],
            )

            save(position)

        elif "SELL" in direction:

            position.open_trade(
                "SHORT",
                plan["Entry"],
                plan["StopLoss"],
                plan["TP1"],
            )

            save(position)


# ==================================================
# ACTIVE POSITION LOOP
# ==================================================

if position.position != "NONE":

    print(
        "\n========== POSITION ACTIVE =========="
    )

    try:

        while position.position != "NONE":

            state = update_state(
                state,
                SYMBOL,
            )

            position.update(
                state.price
            )

            save(position)

            trade_status = manager.manage(
                state,
                plan,
            )

            new_stop = trade_status.get(
                "StopLoss"
            )

            if isinstance(
                new_stop,
                (int, float),
            ) and new_stop > 0:

                position.update_stop_loss(new_stop)

            status = position.status()


            print(
                "\n===== LIVE MARKET ====="
            )

            print(
                "Symbol :",
                state.symbol,
            )

            print(
                "Price  :",
                state.price,
            )

            print(
                "High   :",
                state.high,
            )

            print(
                "Low    :",
                state.low,
            )

            print(
                "Volume :",
                state.volume,
            )

            print(
                "PnL    :",
                status.get(
                    "PnL",
                    0,
                ),
            )

            print(
                "Action :",
                trade_status.get(
                    "Action",
                    "WAIT",
                ),
            )

            print(
                "Stop Loss :",
                trade_status.get(
                    "StopLoss",
                    0,
                ),
            )

            print(
                "BreakEven :",
                trade_status.get(
                    "BreakEven",
                    False,
                ),
            )

            print(
                "Trailing :",
                trade_status.get(
                    "Trailing",
                    False,
                ),
            )


            if trade_status.get(
                "Action"
            ) in (
                "EXIT",
                "STOP LOSS",
            ):

                position.close_trade()

                clear()

                print(
                    "\nTrade Closed"
                )

                break


            time.sleep(5)


    except KeyboardInterrupt:

        print(
            "\nStopping active trade monitor..."
        )


# ==================================================
# NO POSITION
# ==================================================

else:

    print(
        "\nNo Position"
    )
