# core/backtest_engine.py
from core.backtest_result import BacktestResult
from core.filter_attribution import get_attribution
from datetime import datetime
import uuid


class BacktestEngine:
    """
    Jaguar Quant X
    Institutional Backtesting Engine V2
    """

    def __init__(self, registry=None):
        if registry is None:
            from core.engine_registry import EngineRegistry
            from core.register_engines import register

            registry = EngineRegistry()
            register(registry)

        self.registry = registry
        self.result = BacktestResult()
        self.bus = None

    @property
    def name(self):
        return "BacktestEngine"

    def replay(self, state, candles):
        """Replay candles through the canonical enterprise decision chain."""
        from core.trade import Trade
        from core.trade_simulator import TradeSimulator
        from core.filter_attribution import get_attribution
        from core.market_blackboard import MarketBlackboard
        from engine.institutional_master import analyze as institutional_master
        from research.recorder import (
            record_trade_open,
            record_trade_close,
            record_trade_abandoned,
            record_decision_snapshot,
        )
        from research.database import update_decision_outcome
        import uuid

        simulator = TradeSimulator()
        attribution = get_attribution()

        print("\nStarting historical replay...")

        if not isinstance(candles, list):
            raise TypeError(
                "FAIL-CLOSED: replay candles must be a list"
            )

        # --------------------------------------------------
        # Preserve only real timeframe market containers.
        #
        # state.market also contains canonical scalar/string
        # enterprise facts such as trend/regime/signal fields.
        # --------------------------------------------------
        timeframe_markets = {}

        for tf, market in getattr(
            state,
            "market",
            {},
        ).items():

            if not isinstance(market, dict):
                continue

            tf_candles = market.get(
                "candles",
                [],
            )

            if isinstance(tf_candles, list):
                timeframe_markets[tf] = market

        full_candles_by_tf = {
            tf: market.get(
                "candles",
                [],
            )[:]
            for tf, market in timeframe_markets.items()
        }

        if state.interval not in full_candles_by_tf:
            raise RuntimeError(
                "FAIL-CLOSED: replay timeframe "
                f"{state.interval!r} not found in market data"
            )

        # --------------------------------------------------
        # Historical replay
        # --------------------------------------------------
        replay_start = 200

        max_candles_raw = __import__("os").environ.get(
            "JAGUAR_BACKTEST_MAX_CANDLES"
        )

        if max_candles_raw:
            try:
                max_candles = int(max_candles_raw)
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    "FAIL-CLOSED: Invalid JAGUAR_BACKTEST_MAX_CANDLES"
                ) from exc

            if max_candles < replay_start + 1:
                raise RuntimeError(
                    "FAIL-CLOSED: JAGUAR_BACKTEST_MAX_CANDLES must be >= 201"
                )

            if len(candles) > max_candles:
                candles = candles[-max_candles:]

            print(
                f"Backtest candle bound : {len(candles)}"
            )

        # Live/backtest parity: one active position at a time.
        blocked_until = None

        for index in range(
            replay_start,
            len(candles) - 1,
        ):
            candle = candles[index]

            replay_time = candle.get(
                "time"
            )

            # SINGLE-POSITION BACKTEST GUARD
            if blocked_until is not None:
                current_dt = _parse_iso(
                    _to_iso(replay_time)
                )

                if current_dt <= blocked_until:
                    continue

                blocked_until = None

            if replay_time is None:
                continue

            attribution.count_candle()

            # --------------------------------------------------
            # Rebuild each timeframe progressively.
            # --------------------------------------------------
            for tf, market in timeframe_markets.items():

                full_list = full_candles_by_tf[tf]

                historical_tf = [
                    c
                    for c in full_list
                    if c.get(
                        "time",
                        0,
                    ) <= replay_time
                ]

                market["candles"] = historical_tf

            state.market_current = state.market.get(
                state.interval
            )

            if not isinstance(
                state.market_current,
                dict,
            ):
                continue

            # --------------------------------------------------
            # Prevent stale indicator/cache state.
            # --------------------------------------------------
            if hasattr(
                state,
                "indicators",
            ):
                state.indicators = {}

            # --------------------------------------------------
            # Reset blackboard so historical iterations do not
            # contaminate the next iteration with old evidence.
            # --------------------------------------------------
            state.blackboard = MarketBlackboard()

            # --------------------------------------------------
            # Current candle facts.
            # --------------------------------------------------
            state.price = float(
                candle.get(
                    "close",
                    0.0,
                )
                or 0.0
            )

            state.high = float(
                candle.get(
                    "high",
                    0.0,
                )
                or 0.0
            )

            state.low = float(
                candle.get(
                    "low",
                    0.0,
                )
                or 0.0
            )

            state.volume = float(
                candle.get(
                    "volume",
                    0.0,
                )
                or 0.0
            )

            # --------------------------------------------------
            # Run canonical specialist engines exactly once.
            # Yahoo market loading is skipped because historical
            # candles are already supplied by the replay.
            # --------------------------------------------------
            state._backtest_replay = True

            self.registry.run(
                state,
                self.bus,
                skip={
                    "BacktestEngine",
                    "YahooMarketEngine",
                },
            )

            # --------------------------------------------------
            # Run the SAME canonical enterprise authority chain
            # used by live analysis.
            #
            # Specialist engines
            #     ->
            # InstitutionalMaster
            #     ->
            # EnterpriseAdapter
            #     ->
            # EnterprisePipeline
            #     ->
            # IDM
            #     ->
            # TradePlannerV2
            #     ->
            # RiskManagerV2
            #     ->
            # ExecutionGatewayV2
            # --------------------------------------------------
            institutional_result = institutional_master(
                state
            )

            if isinstance(institutional_result, dict):
                state.institutional = institutional_result
            elif institutional_result is not None:
                state = institutional_result

            # --------------------------------------------------
            # Persist decision snapshot.
            # --------------------------------------------------
            decision_id = record_decision_snapshot(
                state,
                candle_timestamp=replay_time,
            )

            idm = getattr(
                state,
                "idm",
                {},
            )

            if not isinstance(
                idm,
                dict,
            ):
                idm = {}

            trade_plan = getattr(
                state,
                "trade",
                {},
            )

            if not isinstance(
                trade_plan,
                dict,
            ):
                trade_plan = {}

            risk = getattr(
                state,
                "risk",
                {},
            )

            if not isinstance(
                risk,
                dict,
            ):
                risk = {}

            execution = getattr(
                state,
                "execution",
                {},
            )

            if not isinstance(
                execution,
                dict,
            ):
                execution = {}

            # --------------------------------------------------
            # Backtest only canonical executable decisions.
            # --------------------------------------------------
            decision = str(
                idm.get(
                    "decision",
                    "WAIT",
                )
            ).upper().strip()

            if decision not in (
                "ENTER_LONG",
                "ENTER_SHORT",
            ):
                continue

            if trade_plan.get(
                "status"
            ) != "READY":
                continue

            if not bool(
                risk.get(
                    "approved",
                    False,
                )
            ):
                continue

            if not bool(
                execution.get(
                    "approved",
                    False,
                )
            ):
                continue

            # FAIL-CLOSED: executable backtest decisions require
            # the canonical enterprise authorization identity.
            authorization_id = execution.get(
                "authorization_id"
            )

            if (
                not isinstance(authorization_id, str)
                or not authorization_id.strip()
            ):
                raise RuntimeError(
                    "FAIL-CLOSED: Backtest execution missing authorization_id"
                )

            entry = trade_plan.get(
                "entry"
            )

            stop = trade_plan.get(
                "stop_loss"
            )

            targets = trade_plan.get(
                "targets",
                [],
            )

            if entry is None or stop is None:
                continue

            if not isinstance(
                targets,
                list,
            ) or not targets:
                continue

            # --------------------------------------------------
            # Canonical Trade -> simulator vocabulary.
            # --------------------------------------------------
            if decision == "ENTER_LONG":
                direction = "BUY"
            else:
                direction = "SELL"

            tp1 = targets[0]

            tp2 = (
                targets[1]
                if len(targets) > 1
                else tp1
            )

            quantity = float(
                risk.get(
                    "position_size",
                    0.0,
                )
                or 0.0
            )

            if quantity <= 0:
                continue

            attribution.count_candidate_setup()
            attribution.count_executed_trade()

            trade_uuid = str(
                uuid.uuid4()
            )

            entry_time_str = _to_iso(
                replay_time
            )

            trade = Trade(
                symbol=getattr(
                    state,
                    "symbol",
                    "",
                ),
                timeframe=getattr(
                    state,
                    "interval",
                    "",
                ),
                direction=direction,
                entry=float(entry),
                stop_loss=float(stop),
                take_profit_1=float(tp1),
                take_profit_2=float(tp2),
                entry_time=entry_time_str,
                quantity=quantity,
                uuid=trade_uuid,
            )

            # --------------------------------------------------
            # Persist canonical backtest trade.
            # --------------------------------------------------
            open_uuid = record_trade_open(
                state,
                run_id=getattr(
                    state,
                    "run_id",
                    None,
                ),
                entry_time=entry_time_str,
                trade_uuid=trade_uuid,
                authorization_id=authorization_id,
            )

            if open_uuid != trade_uuid:
                raise RuntimeError(
                    "FAIL-CLOSED: Backtest trade UUID mismatch "
                    f"(expected {trade_uuid}, recorded {open_uuid})"
                )

            # --------------------------------------------------
            # Simulate only candles after entry candle.
            # --------------------------------------------------
            future = candles[
                index + 1:
            ]

            trade = simulator.simulate(
                trade,
                future,
            )

            trade.compute_pnl()

            # RELEASE BACKTEST POSITION
            # Do not allow a new entry until the
            # historical exit candle has passed.
            if trade.status in (
                "WIN",
                "LOSS",
            ) and trade.exit_time is not None:

                blocked_until = _parse_iso(
                    _to_iso(trade.exit_time)
                )

            if trade.status in (
                "WIN",
                "LOSS",
            ):

                holding_seconds = 0

                if (
                    trade.entry_time
                    and trade.exit_time
                ):
                    try:
                        entry_dt = _parse_iso(
                            trade.entry_time
                        )

                        exit_dt = _parse_iso(
                            trade.exit_time
                        )

                        holding_seconds = (
                            exit_dt - entry_dt
                        ).total_seconds()

                    except Exception:
                        holding_seconds = 0

                record_trade_close(
                    uuid=trade.uuid,
                    exit_price=trade.exit_price,
                    pnl=trade.pnl,
                    r_multiple=trade.rr,
                    win_loss=(
                        trade.status == "WIN"
                    ),
                    holding_time=holding_seconds,
                    exit_time=trade.exit_time,
                )

                update_decision_outcome(
                    decision_id,
                    trade.status,
                    trade_uuid,
                )


            # --------------------------------------------------
            # FINITE REPLAY TERMINAL STATE
            # --------------------------------------------------
            # An unresolved historical position is right-censored.
            # It is not a realized WIN or LOSS.
            if trade.status == "OPEN":
                record_trade_abandoned(
                    trade.uuid,
                )

                update_decision_outcome(
                    decision_id,
                    "ABANDONED",
                    trade_uuid,
                )

            self.result.total_trades += 1

            if trade.status == "WIN":
                self.result.wins += 1
                attribution.count_winning_trade()

            elif trade.status == "LOSS":
                self.result.losses += 1
                attribution.count_losing_trade()

            # --------------------------------------------------
            # Canonical trade audit snapshot.
            # Captures the exact IDM/structural state that
            # authorized this historical trade.
            # --------------------------------------------------
            idm_structural = idm.get(
                "structural",
                {},
            )

            if not isinstance(
                idm_structural,
                dict,
            ):
                idm_structural = {}

            raw_regime = getattr(
                state,
                "regime",
                "UNKNOWN",
            )

            if isinstance(
                raw_regime,
                dict,
            ):
                audit_regime = raw_regime.get(
                    "regime",
                    raw_regime.get(
                        "REGIME",
                        "UNKNOWN",
                    ),
                )
            else:
                audit_regime = raw_regime

            self.result.trades.append(
                {
                    "direction": trade.direction,
                    "entry": trade.entry,
                    "exit": trade.exit_price,
                    "status": trade.status,

                    "authorization_id": authorization_id,

                    "idm_decision": decision,
                    "idm_setup": idm.get(
                        "setup",
                        "UNKNOWN",
                    ),
                    "idm_score": idm.get(
                        "score",
                        0,
                    ),
                    "idm_confidence": idm.get(
                        "confidence",
                        0,
                    ),
                    "idm_priority": idm.get(
                        "priority",
                        "LOW",
                    ),
                    "idm_conflicts": list(
                        idm.get(
                            "conflicts",
                            [],
                        )
                        if isinstance(
                            idm.get(
                                "conflicts",
                                [],
                            ),
                            list,
                        )
                        else []
                    ),

                    "trend": str(
                        getattr(
                            state,
                            "trend",
                            "UNKNOWN",
                        )
                    ).upper().strip(),

                    "regime": str(
                        audit_regime
                    ).upper().strip(),

                    "structural_direction": idm_structural.get(
                        "direction",
                        "UNKNOWN",
                    ),
                    "structure_state": idm_structural.get(
                        "structure_state",
                        "UNKNOWN",
                    ),
                    "trigger_status": idm_structural.get(
                        "trigger_status",
                        "UNKNOWN",
                    ),
                    "trigger_source": idm_structural.get(
                        "trigger_source",
                        "UNKNOWN",
                    ),
                    "trigger_direction": idm_structural.get(
                        "trigger_direction",
                        "UNKNOWN",
                    ),
                    "execution_trigger_confirmed": bool(
                        idm_structural.get(
                            "execution_trigger_confirmed",
                            False,
                        )
                    ),
                    "zone_status": idm_structural.get(
                        "zone_status",
                        "UNKNOWN",
                    ),
                    "zone_type": idm_structural.get(
                        "zone_type",
                        "UNKNOWN",
                    ),
                    "zone_direction": idm_structural.get(
                        "zone_direction",
                        "UNKNOWN",
                    ),
                    "zone_lifecycle": idm_structural.get(
                        "zone_lifecycle",
                        "UNKNOWN",
                    ),
                    "zone_interacting": bool(
                        idm_structural.get(
                            "interacting",
                            idm_structural.get(
                                "zone_interacting",
                                False,
                            ),
                        )
                    ),

                    "execution_trigger_age": (
                        idm_structural.get(
                            "execution_trigger",
                            {},
                        ).get(
                            "age",
                            None,
                        )
                        if isinstance(
                            idm_structural.get(
                                "execution_trigger",
                                {},
                            ),
                            dict,
                        )
                        else None
                    ),

                    "pnl": trade.pnl,
                    "r_multiple": trade.rr,
                }
            )

        # --------------------------------------------------
        # TRADE AUTHORIZATION AUDIT
        # Read-only diagnostic of every executed backtest trade.
        # --------------------------------------------------
        print(
            "========== TRADE AUTHORIZATION AUDIT =========="
        )

        for number, audit_trade in enumerate(
            self.result.trades,
            1,
        ):
            print(
                f"TRADE {number}: "
                f"entry={audit_trade.get('entry')} "
                f"direction={audit_trade.get('direction')} "
                f"decision={audit_trade.get('idm_decision')} "
                f"setup={audit_trade.get('idm_setup')} "
                f"trend={audit_trade.get('trend')} "
                f"regime={audit_trade.get('regime')} "
                f"score={audit_trade.get('idm_score')} "
                f"confidence={audit_trade.get('idm_confidence')} "
                f"structure={audit_trade.get('structure_state')} "
                f"trigger={audit_trade.get('trigger_status')} "
                f"trigger_source={audit_trade.get('trigger_source')} "
                f"zone={audit_trade.get('zone_type')} "
                f"zone_lifecycle={audit_trade.get('zone_lifecycle')} "
                f"interacting={audit_trade.get('zone_interacting')} "
                f"result={audit_trade.get('status')} "
                f"pnl={audit_trade.get('pnl')} "
                f"R={audit_trade.get('r_multiple')} "
                f"auth={audit_trade.get('authorization_id')}"
            )

        print(
            "==============================================="
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
            f"Replay complete. Trades: "
            f"{self.result.total_trades}"
        )

    def run(self, state, bus):
        print("\n========== BACKTEST ENGINE STARTED ==========")
        self.bus = bus
        bus.publish("BACKTEST_ANALYSIS")

        market = getattr(state, "market", {})
        tf15 = market.get("15m", {})
        candles = tf15.get("candles", [])

        print("=" * 60)
        print("BACKTEST ENGINE")
        print("=" * 60)
        print(f"Historical candles : {len(candles)}")

        self.result.total_trades = 0
        self.result.wins = 0
        self.result.losses = 0
        self.result.win_rate = 0.0
        self.result.loss_rate = 0.0

        from core.filter_attribution import reset_attribution
        reset_attribution()

        self.replay(state, candles)

        get_attribution().print_report()

        # --------------------------------------------------
        # DIRECTION-SPECIFIC BACKTEST ATTRIBUTION
        # --------------------------------------------------
        long_trades = [
            t for t in self.result.trades
            if str(t.get("direction", "")).upper() == "BUY"
        ]

        short_trades = [
            t for t in self.result.trades
            if str(t.get("direction", "")).upper() == "SELL"
        ]

        long_wins = sum(
            1 for t in long_trades
            if str(t.get("status", "")).upper() == "WIN"
        )

        long_losses = sum(
            1 for t in long_trades
            if str(t.get("status", "")).upper() == "LOSS"
        )

        short_wins = sum(
            1 for t in short_trades
            if str(t.get("status", "")).upper() == "WIN"
        )

        short_losses = sum(
            1 for t in short_trades
            if str(t.get("status", "")).upper() == "LOSS"
        )

        print("\n========== DIRECTION ATTRIBUTION ==========")
        print(f"LONG  Trades : {len(long_trades)}")
        print(f"LONG  Wins   : {long_wins}")
        print(f"LONG  Losses : {long_losses}")
        print(
            f"LONG  WinRate: "
            f"{(long_wins * 100 / len(long_trades)) if long_trades else 0.0:.2f}%"
        )

        print(f"SHORT Trades : {len(short_trades)}")
        print(f"SHORT Wins   : {short_wins}")
        print(f"SHORT Losses : {short_losses}")
        print(
            f"SHORT WinRate: "
            f"{(short_wins * 100 / len(short_trades)) if short_trades else 0.0:.2f}%"
        )
        print("============================================")

        state.backtest = self.result
        self._print_summary()

        bus.publish("BACKTEST_READY")
        return state

    def _print_summary(self):
        print("\n" + "=" * 60)
        print("BACKTEST PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Total Trades  : {self.result.total_trades}")
        print(f"Wins          : {self.result.wins}")
        print(f"Losses        : {self.result.losses}")
        print(f"Win Rate      : {self.result.win_rate}%")
        print(f"Loss Rate     : {self.result.loss_rate}%")
        print("=" * 60)


def _to_iso(ts):
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts).isoformat()
    try:
        datetime.fromisoformat(str(ts))
        return str(ts)
    except:
        return str(ts)

def _parse_iso(ts):
    try:
        return datetime.fromisoformat(ts)
    except:
        return datetime.fromtimestamp(float(ts))
