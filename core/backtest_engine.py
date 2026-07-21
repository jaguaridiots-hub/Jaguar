from core.backtest_result import BacktestResult
from core.timeframe_loader import TimeframeLoader

class BacktestEngine:
    """
    Jaguar Quant X
    Institutional Backtesting Engine V2
    """

    def __init__(self, registry=None):
        self.registry = registry
        self.result = BacktestResult()

    @property
    def name(self):
        return "BacktestEngine"

    def replay(self, state, candles):
        """
        Replay historical candles and simulate trades.
        """

        from core.trade import Trade
        from core.trade_simulator import TradeSimulator

        simulator = TradeSimulator()

        print("\nStarting historical replay...")

        for index in range(200, len(candles) - 1):

            candle = candles[index]

            replay_time = candle["time"]

            for tf, market in state.market.items():

                tf_candles = market.get("candles", [])

                historical_tf = [
                    c for c in tf_candles
                    if c.get("time", 0) <= replay_time
                ]

                market["candles"] = historical_tf

            state.market_current = state.market.get(state.interval)

            state.timeframes = TimeframeLoader.load(state)

            print("Decision :", getattr(state, "decision", None))
            print("Execution:", getattr(state, "execution", None))
            print("Trade Plan:", getattr(state, "trade_plan", None))
            print("Master:", getattr(state, "master_decision", None))

            input("Press Enter to continue...")

            state.price = candle["close"]
            state.high = candle["high"]
            state.low = candle["low"]
            state.volume = candle["volume"]

            self.registry.run(
                state,
                self.bus,
                skip={
                        "BacktestEngine",
                        "MarketEngine",
                    },
            )

            master = getattr(state, "master_decision", {})
            planner = getattr(state, "trade_plan", {})

            plan = planner or master.get("plan")

            if not plan:
                continue

            direction = str(
                plan.get("Direction", "")
            ).upper()

            if direction not in ("BUY", "SELL"):
                continue

            trade = Trade(
                direction=direction,
                entry_price=plan["Entry"],
                stop_loss=plan["StopLoss"],
                take_profit_1=plan["TP1"],
                take_profit_2=plan.get("TP2", plan["TP1"]),
            )

            future = candles[index + 1 :]

            trade = simulator.simulate(
                trade,
                future,
            )

            self.result.total_trades += 1

            if trade.status == "WIN":
                self.result.wins += 1
            elif trade.status == "LOSS":
                self.result.losses += 1

            self.result.trades.append(
                {
                    "direction": trade.direction,
                    "entry": trade.entry_price,
                    "exit": trade.exit_price,
                    "status": trade.status,
                }
            )

        if self.result.total_trades:

            self.result.win_rate = round(
                self.result.wins
                * 100
                / self.result.total_trades,
                2,
            )

            self.result.loss_rate = round(
                self.result.losses
                * 100
                / self.result.total_trades,
                2,
            )

        print(
            f"Replay complete. Trades: {self.result.total_trades}"
        )

    def run(self, state, bus):
        print("\n========== BACKTEST ENGINE STARTED ==========")

        self.bus = bus

        bus.publish("BACKTEST_ANALYSIS")

        # Get market data
        market = getattr(state, "market", {})

        tf15 = market.get("15m", {})
        candles = tf15.get("candles", [])

        print("=" * 60)
        print("BACKTEST ENGINE")
        print("=" * 60)
        print(f"Historical candles : {len(candles)}")

        # Initialize result
        self.result.total_trades = 0
        self.result.wins = 0
        self.result.losses = 0
        self.result.win_rate = 0.0
        self.result.loss_rate = 0.0

        # Replay historical candles
        self.replay(state, candles)

        # Save result
        state.backtest = self.result

        bus.publish("BACKTEST_READY")

        return state
