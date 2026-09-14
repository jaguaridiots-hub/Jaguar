import os
import time
from datetime import datetime

from core.kernel import JaguarKernel
from core.logger import JaguarLogger
from core.registry import ModuleRegistry
from core.event_bus import EventBus

from indicators.indicator_engine import (
    update_market_state,
)

from engine.institutional_master import (
    analyze as institutional_master,
)

from engine.trade_manager import TradeManager
from engine.position_manager import PositionManager
from engine.trade_journal import TradeJournal
from engine.performance import Performance
from engine.live_feed import LiveFeed
from core.jaguar_analysis_engine import JaguarAnalysisEngine
from engine.state_manager import (
    save,
    load,
    clear,
)

from market.live_loader import update_state
from research.recorder import (
    record_decision_snapshot,
)
from research.database import (
    insert_execution_intent,
    update_execution_intent,
)

from intelligence.execution_identity import bind_execution_identity
from intelligence.execution_dispatch_composition import build_execution_dispatch_runtime
from intelligence.paper_post_fill import execute_paper_post_fill


SYMBOL = "BTCUSDT"
TIMEFRAME = "15m"


# ==================================================
# HEADER
# ==================================================

print("=" * 50)
print("              JAGUAR QUANT X v2.0")
print("=" * 50)


# ==================================================
# LOGGER
# ==================================================

log = JaguarLogger()

log.info(
    "Starting Jaguar Quant X..."
)


# ==================================================
# KERNEL
# ==================================================

kernel = JaguarKernel()
analysis = JaguarAnalysisEngine(kernel)

kernel.initialize(
    SYMBOL,
    TIMEFRAME,
)


# ==================================================
# MODULE REGISTRY
# ==================================================

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


# ==================================================
# EVENT BUS
# ==================================================

bus = EventBus()

bus.publish(
    "startup",
    "All Systems Online",
)


print("\n" + "=" * 50)

print(
    "Jaguar Quant X Ready To Trade"
)

print("=" * 50)


# ==================================================
# CANONICAL STARTUP MARKET HYDRATION
# ==================================================

result = analysis.run(SYMBOL)

state = result["state"]
report = result["report"]

run_id = os.environ.get("JAGUAR_PAPER_RUN")

if not isinstance(run_id, str) or not run_id.strip():
    run_id = (
        "PAPER-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
    )

state.run_id = run_id

decision_id = record_decision_snapshot(
    state,
    candle_timestamp=getattr(
        state,
        "_candle_time",
        None,
    ),
)

print(
    "📊 Research: Decision snapshot recorded:",
    decision_id,
)

print(
    "📊 Research: Run ID:",
    state.run_id,
)


state.timeframe = TIMEFRAME

candles = (
    state.market.get("candles", [])
    if isinstance(getattr(state, "market", None), dict)
    else []
)

if not candles:
    print("WARNING: No canonical candles found in state.market")

latest = candles[-1]


# ==================================================
# LIVE MARKET
# ==================================================

print(
    "\n========= LIVE MARKET ========="
)

print(
    "Symbol     :",
    state.symbol,
)

print(
    "Timeframe  :",
    state.timeframe,
)

print(
    "Price      :",
    latest.get("close", 0.0),
)

print(
    "High       :",
    latest["high"],
)

print(
    "Low        :",
    latest["low"],
)

print(
    "Volume     :",
    state.volume,
)


# ==================================================
# INDICATORS
# ==================================================


print(
    "\n========= INDICATORS ========="
)

print(
    "EMA20  :",
    state.ema20,
)

print(
    "EMA50  :",
    state.ema50,
)

print(
    "EMA100 :",
    state.ema100,
)

print(
    "EMA200 :",
    state.ema200,
)

print(
    "RSI    :",
    state.rsi,
)

print(
    "ATR    :",
    state.atr,
)

print(
    "Volume :",
    state.volume,
)

# ==================================================
# JAGUAR MASTER ANALYSIS
# ==================================================



context = report.get(
    "context",
    report.get(
        "decision",
        {},
    ),
)

enterprise = report.get(
    "enterprise",
    {},
)

# ==================================================
# CANONICAL ENTERPRISE TRADE
# ==================================================

enterprise_execution = enterprise.get(
    "execution",
    {},
)

plan = {}

if isinstance(enterprise_execution, dict):
    execution_ready = (
        enterprise_execution.get("ready") is True
        and enterprise_execution.get("approved") is True
        and enterprise_execution.get("status") == "EXECUTE"
        and enterprise_execution.get("gate") == "AUTHORIZED"
    )

    if execution_ready:
        # Canonical execution identity is established once, before any
        # transport-specific execution path consumes the authorized contract.
        enterprise_execution = bind_execution_identity(
            enterprise_execution
        )
        enterprise["execution"] = enterprise_execution

        execution_mode = enterprise_execution.get("mode", "PAPER")
        if execution_mode not in {"PAPER", "LIVE"}:
            raise RuntimeError(
                "FAIL-CLOSED: unsupported execution mode"
            )

        if execution_mode == "LIVE":
            enterprise_execution = dict(enterprise_execution)
        else:
            paper_authorization = execution_dispatch_runtime.paper_authorizer(
                enterprise_execution
            )
            enterprise_execution = paper_authorization["execution"]

        decision = str(
            enterprise_execution.get(
                "decision",
                "WAIT",
            )
        ).upper().strip()

        direction = {
            "ENTER_LONG": "BUY",
            "ENTER_SHORT": "SELL",
        }.get(
            decision,
            "",
        )

        targets = enterprise_execution.get(
            "targets",
            [],
        )

        if (
            direction in ("BUY", "SELL")
            and enterprise_execution.get("entry") is not None
            and enterprise_execution.get("stop_loss") is not None
            and isinstance(targets, list)
            and len(targets) >= 3
        ):
            plan = {
                "Direction": direction,
                "Entry": enterprise_execution["entry"],
                "StopLoss": enterprise_execution["stop_loss"],
                "TP1": targets[0],
                "TP2": targets[1],
                "TP3": targets[2],
                "PositionSize": enterprise_execution.get(
                    "position_size",
                    0.0,
                ),
                "RiskAmount": enterprise_execution.get(
                    "risk_amount",
                    0.0,
                ),
                "RiskPercent": enterprise_execution.get(
                    "risk_percent",
                    0.0,
                ),
                "AuthorizationID": enterprise_execution.get(
                    "authorization_id",
                ),
            }


# ==================================================
# MARKET CONTEXT
# ==================================================

context_direction = context.get(
    "direction",
    "NEUTRAL",
)

context_decision = context.get(
    "decision",
    "WAIT",
)

context_grade = context.get(
    "confidence",
    "D",
)

context_probability = context.get(
    "probability",
    0,
)

context_score = context.get(
    "score",
    0,
)


print(
    "\n========== MARKET CONTEXT =========="
)

print(
    "Bias          :",
    context_direction,
)

print(
    "Setup Status  :",
    context_decision,
)

print(
    "Context Grade :",
    context_grade,
)

print(
    "Probability   :",
    f"{context_probability}%",
)

print(
    "Context Score :",
    context_score,
)

# ==================================================
# ENTERPRISE DECISION
# ==================================================

execution = enterprise.get(
    "execution",
    {},
)



enterprise_approved = (
    isinstance(execution, dict)
    and execution.get("approved") is True
    and execution.get("status") == "EXECUTE"
    and execution.get("gate") == "AUTHORIZED"
)


print(
    "\n========== ENTERPRISE DECISION =========="
)

print(
    "Score         :",
    enterprise.get(
        "score",
        0,
    ),
)

print(
    "Grade         :",
    enterprise.get(
        "grade",
        "F",
    ),
)

print(
    "Confidence    :",
    enterprise.get(
        "confidence",
        0,
    ),
)

print(
    "IDM Decision  :",
    enterprise.get(
        "decision",
        "WAIT",
    ),
)

print(
    "Priority      :",
    enterprise.get(
        "priority",
        "LOW",
    ),
)

print(
    "Approved      :",
    enterprise_approved,
)

print(
    "Execution     :",
    execution.get(
        "status",
        "WAIT",
    ),
)

print(
    "Ready         :",
    execution.get(
        "ready",
        False,
    ),
)

print(
    "Reason        :",
    execution.get(
        "reason",
        "",
    ),
)

# ==================================================
# SUPPORT / RESISTANCE
# ==================================================

engines = report.get(
    "engines",
    {},
)

gann = engines.get(
    "Gann",
    {},
)

gann_metadata = gann.get(
    "metadata",
    {},
)

support = gann_metadata.get(
    "support",
)

resistance = gann_metadata.get(
    "resistance",
)

print("\n====== SUPPORT / RESISTANCE ======")
support_display = (
    round(support, 2)
    if isinstance(
        support,
        (int, float),
    )
    else "N/A"
)

resistance_display = (
    round(resistance, 2)
    if isinstance(
        resistance,
        (int, float),
    )
    else "N/A"
)

print(
    "Support   :",
    support_display,
)

print(
    "Resistance:",
    resistance_display,
)

performance = Performance()

journal = TradeJournal()

position = PositionManager()

manager = TradeManager()
execution_dispatch_runtime = build_execution_dispatch_runtime()


# ==================================================
# RESTORE POSITION
# ==================================================

position_loaded = load(position)


if position_loaded:

    print(
        "\nExisting trade state loaded."
    )

    restored_trade_uuid = getattr(
        position,
        "trade_uuid",
        None,
    )

    # FAIL-CLOSED: an active restored position must have
    # a valid trade identity.
    if (
        position.position not in ("LONG", "SHORT")
        or not isinstance(restored_trade_uuid, str)
        or not restored_trade_uuid.strip()
    ):
        raise RuntimeError(
            "FAIL-CLOSED: Invalid restored active trade identity"
        )

    state._trade_id = restored_trade_uuid

    manager.activate()


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

execution_ready = (
    isinstance(execution, dict)
    and execution.get("ready") is True
    and execution.get("approved") is True
    and execution.get("status") == "EXECUTE"
    and execution.get("gate") == "AUTHORIZED"
)

if (
    plan
    and plan.get("Direction")
    and execution_ready
):

    if position.position == "NONE":

        # FINAL FAIL-CLOSED EXECUTION AUTHORIZATION
        if not (
            isinstance(execution, dict)
            and execution.get("ready") is True
            and execution.get("approved") is True
            and execution.get("status") == "EXECUTE"
            and execution.get("gate") == "AUTHORIZED"
        ):
            raise RuntimeError(
                "FAIL-CLOSED: Unauthorized position-open attempt"
            )


        # CANONICAL EXECUTION CONSISTENCY
        # The position must use exactly what the gateway authorized.
        authorized_entry = execution.get("entry")
        authorized_stop = execution.get("stop_loss")
        authorized_targets = execution.get("targets")
        authorized_size = execution.get("position_size")
        authorized_risk_amount = execution.get("risk_amount")

        if (
            authorized_entry != plan.get("Entry")
            or authorized_stop != plan.get("StopLoss")
            or not isinstance(authorized_targets, list)
            or len(authorized_targets) < 3
            or authorized_targets[:3] != [
                plan.get("TP1"),
                plan.get("TP2"),
                plan.get("TP3"),
            ]
        ):
            raise RuntimeError(
                "FAIL-CLOSED: Position plan differs from authorized execution"
            )

        if float(authorized_size or 0.0) <= 0:
            raise RuntimeError(
                "FAIL-CLOSED: Authorized position size is invalid"
            )

        if float(authorized_risk_amount or 0.0) <= 0:
            raise RuntimeError(
                "FAIL-CLOSED: Authorized risk amount is invalid"
            )

        direction = plan.get(
            "Direction",
            "",
        )

        risk_data = getattr(
            state,
            "risk",
            {},
        ) or {}

        # ==================================================
        # BROKER-SHAPED PAPER EXECUTION
        # ==================================================
        # Gateway authorization precedes broker execution.
        # PositionManager must only mirror the confirmed fill.
        # ==================================================

        # ==================================================
        # V8 EXECUTION INTENT — PRE-SUBMISSION DURABILITY
        # ==================================================
        broker_execution_completed = False

        def rollback_execution_if_pre_submission(result):
            if broker_execution_completed:
                return None
            return execution_dispatch_runtime.paper_rollback

        def preserve_trade_for_recovery(trade_uuid):
            if (
                not isinstance(trade_uuid, str)
                or not trade_uuid.strip()
            ):
                raise RuntimeError(
                    "FAIL-CLOSED: Invalid trade UUID during recovery preservation"
                )
            return trade_uuid

        # The runtime transaction identity is allocated before
        # broker submission and durably recorded as AUTHORIZED.
        # ==================================================

        authorization_id = execution.get(
            "authorization_id"
        )

        if (
            not isinstance(authorization_id, str)
            or not authorization_id.strip()
        ):
            raise RuntimeError(
                "FAIL-CLOSED: Authorized execution has no authorization ID"
            )

        trade_uuid = execution.get(
            "trade_uuid"
        )

        if (
            not isinstance(trade_uuid, str)
            or not trade_uuid.strip()
        ):
            raise RuntimeError(
                "FAIL-CLOSED: Authorized execution has no trade UUID"
            )

        client_order_id = execution.get(
            "client_order_id"
        )

        if (
            not isinstance(client_order_id, str)
            or not client_order_id.strip()
        ):
            raise RuntimeError(
                "FAIL-CLOSED: Authorized execution has no client order ID"
            )

        intent_timestamp = datetime.utcnow().isoformat()

        targets_for_intent = execution.get(
            "targets",
            [],
        )

        if (
            not isinstance(targets_for_intent, list)
            or not targets_for_intent
        ):
            targets_for_intent = []

        intent_decision = {
            "ENTER_LONG": "LONG",
            "ENTER_SHORT": "SHORT",
        }.get(
            str(
                execution.get(
                    "decision",
                    "",
                )
            ).upper().strip()
        )

        if intent_decision not in {"LONG", "SHORT"}:
            raise RuntimeError(
                "FAIL-CLOSED: Invalid execution decision for "
                "durable execution intent"
            )

        try:
            insert_execution_intent(
                {
                    "authorization_id": authorization_id,
                    "trade_uuid": trade_uuid,
                    "client_order_id": client_order_id,
                    "symbol": execution.get(
                        "symbol",
                        SYMBOL,
                    ),
                    "timeframe": TIMEFRAME,
                    "mode": execution.get(
                        "mode",
                        "PAPER",
                    ),
                    "decision": intent_decision,
                    "quantity": float(
                        execution.get(
                            "position_size",
                            0.0,
                        ) or 0.0
                    ),
                    "requested_price": execution.get(
                        "entry"
                    ),
                    "stop_loss": execution.get(
                        "stop_loss"
                    ),
                    "take_profit": targets_for_intent[0],
                    "run_id": getattr(
                        state,
                        "run_id",
                        None,
                    ),
                    "status": "AUTHORIZED",
                    "created_at": intent_timestamp,
                    "updated_at": intent_timestamp,
                }
            )
        except Exception as intent_error:
            raise RuntimeError(
                "FAIL-CLOSED: Execution intent persistence failed"
            ) from intent_error

        try:
            execution_mode = execution.get("mode", "PAPER")
            if execution_mode not in {"PAPER", "LIVE"}:
                raise RuntimeError(
                    "FAIL-CLOSED: unsupported execution mode"
                )

            if execution_mode == "LIVE":
                try:
                    live_result = execution_dispatch_runtime.dispatch(
                        execution,
                        market_metadata=state.market_metadata,
                        activation_requested=True,
                    )
                except Exception as live_error:
                    raise RuntimeError(
                        "FAIL-CLOSED: LIVE submission failed"
                    ) from live_error

                if not isinstance(live_result, dict):
                    raise RuntimeError(
                        "FAIL-CLOSED: LIVE dispatch returned an invalid result"
                    )

                if live_result.get("status") != "SUBMITTED":
                    raise RuntimeError(
                        "FAIL-CLOSED: LIVE dispatch did not reach SUBMITTED"
                    )

                if live_result.get("authorization_id") != authorization_id:
                    raise RuntimeError(
                        "FAIL-CLOSED: LIVE dispatch returned mismatched authorization ID"
                    )

                if live_result.get("client_order_id") != client_order_id:
                    raise RuntimeError(
                        "FAIL-CLOSED: LIVE dispatch returned mismatched client order ID"
                    )

                if (
                    not isinstance(live_result.get("broker_order_id"), str)
                    or not live_result.get("broker_order_id").strip()
                ):
                    raise RuntimeError(
                        "FAIL-CLOSED: LIVE dispatch returned no broker order ID"
                    )

                execution_result = live_result
            else:
                execution_result = execution_dispatch_runtime.dispatch(
                    execution
                )
        except Exception as execution_error:
            raise RuntimeError(
                "FAIL-CLOSED: Paper execution failed"
            ) from execution_error

        # The broker operation has completed.  From this point
        # onward the external execution must never be erased by
        # local compensation.  Durable V8 recovery owns the
        # unresolved transaction.
        broker_execution_completed = True

        returned_authorization_id = execution_result.get(
            "authorization_id"
        )

        if returned_authorization_id != authorization_id:
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as rollback_error:
                raise RuntimeError(
                    "FAIL-CLOSED: Authorization identity mismatch "
                    "AND execution rollback failed"
                ) from rollback_error

            raise RuntimeError(
                "FAIL-CLOSED: Broker returned mismatched authorization ID"
            )

        if execution_mode == "LIVE":
            broker_order_id = execution_result.get("broker_order_id")
        else:
            order = execution_result.get(
                "order",
                {},
            ) or {}

            broker_order_id = order.get(
                "broker_order_id"
            )

        if (
            not isinstance(broker_order_id, str)
            or not broker_order_id.strip()
        ):
            raise RuntimeError(
                "FAIL-CLOSED: Broker execution returned no broker order ID"
            )

        try:
            update_execution_intent(
                authorization_id,
                broker_order_id=broker_order_id,
                status="SUBMITTED",
            )
        except Exception as intent_error:
            raise RuntimeError(
                "FAIL-CLOSED: Broker submitted but "
                "SUBMITTED intent persistence failed"
            ) from intent_error

        if execution_mode == "PAPER":
            execute_paper_post_fill(
                execution=execution,
                execution_result=execution_result,
                authorization_id=authorization_id,
                trade_uuid=trade_uuid,
                authorized_stop=authorized_stop,
                authorized_targets=authorized_targets,
                direction=direction,
                state=state,
                position=position,
                manager=manager,
                journal=journal,
                plan=plan,
                rollback_execution_if_pre_submission=rollback_execution_if_pre_submission,
                preserve_trade_for_recovery=preserve_trade_for_recovery,
                SYMBOL=SYMBOL,
                TIMEFRAME=TIMEFRAME,
            )
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

            # FAIL-CLOSED: active position must retain
            # a valid persistent trade identity.
            trade_uuid = getattr(
                position,
                "trade_uuid",
                None,
            )

            if (
                not isinstance(trade_uuid, str)
                or not trade_uuid.strip()
            ):
                raise RuntimeError(
                    "FAIL-CLOSED: Active position has no valid trade UUID"
                )

            state._trade_id = trade_uuid

            # Manage using the actual persisted stop.
            trade_status = manager.manage(
                state,
                plan,
                current_stop=position.stop_loss,
            )

            new_stop = trade_status.get(
                "StopLoss"
            )

            if isinstance(
                new_stop,
                (int, float),
            ) and new_stop > 0:

                position.update_stop_loss(
                    new_stop
                )

            # Persist AFTER stop-loss changes.
            if not save(position, SYMBOL):
                raise RuntimeError(
                    "FAIL-CLOSED: Active position persistence failed"
                )

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

                from research.recorder import record_trade_close

                trade_uuid = getattr(
                    position,
                    "trade_uuid",
                    None,
                )

                if (
                    not isinstance(trade_uuid, str)
                    or not trade_uuid.strip()
                ):
                    raise RuntimeError(
                        "FAIL-CLOSED: Cannot close trade without trade UUID"
                    )

                exit_price = float(
                    state.price
                )

                entry_price = float(
                    position.entry
                )

                position_size = float(
                    getattr(
                        position,
                        "position_size",
                        0.0,
                    ) or 0.0
                )

                if position_size <= 0:
                    raise RuntimeError(
                        "FAIL-CLOSED: Invalid position size during close"
                    )

                if position.position == "LONG":
                    price_delta = (
                        exit_price
                        - entry_price
                    )
                else:
                    price_delta = (
                        entry_price
                        - exit_price
                    )

                pnl = (
                    price_delta
                    * position_size
                )

                initial_risk = float(
                    getattr(
                        position,
                        "initial_risk",
                        0.0,
                    ) or 0.0
                )

                r_multiple = (
                    pnl / initial_risk
                    if initial_risk > 0
                    else 0.0
                )

                record_trade_close(
                    trade_uuid,
                    exit_price=exit_price,
                    pnl=pnl,
                    r_multiple=r_multiple,
                    win_loss=(pnl > 0),
                    holding_time=0,
                )

                state._trade_id = None

                position.close_trade()

                manager.deactivate()

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


# NO POSITION
# ==================================================

else:

    print(
        "\nNo Position"
    )


# ==================================================
# TRADE MANAGER REPORT
# ==================================================

print(
    "\n======== TRADE MANAGER ========"
)

print(
    "Action      :",
    trade_status.get(
        "Action",
        "NO TRADE",
    ),
)

print(
    "Stop Loss   :",
    trade_status.get(
        "StopLoss",
        0,
    ),
)

print(
    "Break Even  :",
    trade_status.get(
        "BreakEven",
        False,
    ),
)

print(
    "Trailing SL :",
    trade_status.get(
        "Trailing",
        False,
    ),
)


# ==================================================
# PERFORMANCE
# ==================================================

stats = performance.summary()


print(
    "\n========== PERFORMANCE =========="
)

print(
    "Total Trades :",
    stats.get(
        "Trades",
        0,
    ),
)

print(
    "Wins         :",
    stats.get(
        "Wins",
        0,
    ),
)

print(
    "Losses       :",
    stats.get(
        "Losses",
        0,
    ),
)

print(
    "Win Rate     :",
    f'{stats.get("WinRate", 0)}%',
)

print(
    "=" * 34
)


# ==================================================
# LEGACY ANALYSIS REASONS
# ==================================================

print(
    "\nMarket Bias Reasons"
)

reasons = context.get(
    "reasons",
    [],
)

unique_reasons = list(
    dict.fromkeys(reasons)
)

for reason in unique_reasons:

    print(
        "✓",
        reason,
    )


# ==================================================
# ENTERPRISE REASONS
# ==================================================

print(
    "\nEnterprise Reasons"
)

idm_reasons = state.idm.get(
    "reasons",
    [],
)

for reason in idm_reasons:

    print(
        "•",
        reason,
    )


# ==================================================
# LIVE FEED
# ==================================================

print(
    "\n========== LIVE BINANCE FEED =========="
)


from core.alert_engine import AlertEngine
from core.notification_adapter import TermuxNotificationAdapter
from core.canonical_portfolio_read_model import (
    build_canonical_portfolio_snapshot,
)


def observe_portfolio_for_alerts():
    try:
        portfolio = build_canonical_portfolio_snapshot()
    except Exception:
        return None
    return portfolio if isinstance(portfolio, dict) else None


alert_engine = AlertEngine(
    TermuxNotificationAdapter(),
    cooldown_seconds=300.0,
)

feed = LiveFeed(
    state,
    plan,
    trade_status,
    "btcusdt",
)
feed.alert_observer = observe_portfolio_for_alerts
feed.alert_engine = alert_engine
feed.alert_interval_seconds = 30.0

feed.start()

# Normal operation: keep the live feed running.
# Test operation: JAGUAR_ONESHOT=1 exits after initial analysis.
# Bounded operation: JAGUAR_MAX_RUNTIME_SECONDS=<seconds>.
try:

    if os.environ.get("JAGUAR_ONESHOT") == "1":

        print(
            "\nJAGUAR_ONESHOT=1 -> stopping after initial analysis."
        )

        feed.stop()

    else:

        max_runtime_raw = os.environ.get(
            "JAGUAR_MAX_RUNTIME_SECONDS"
        )

        deadline = None

        if max_runtime_raw:

            try:
                max_runtime = float(max_runtime_raw)
            except (TypeError, ValueError) as exc:

                raise RuntimeError(
                    "FAIL-CLOSED: Invalid JAGUAR_MAX_RUNTIME_SECONDS"
                ) from exc

            if max_runtime <= 0:

                raise RuntimeError(
                    "FAIL-CLOSED: JAGUAR_MAX_RUNTIME_SECONDS must be > 0"
                )

            deadline = time.monotonic() + max_runtime

            print(
                f"\nJAGUAR_MAX_RUNTIME_SECONDS={max_runtime:g}"
                " -> bounded live run."
            )

        while True:

            if (
                deadline is not None
                and time.monotonic() >= deadline
            ):

                print(
                    "\nMaximum runtime reached -> stopping Jaguar."
                )

                feed.stop()
                break

            time.sleep(1)

except KeyboardInterrupt:

    print(
        "\nStopping Jaguar..."
    )

    feed.stop()
