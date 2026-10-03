from core.engine_result import EngineResult


def analyze(state):
    market = getattr(state, "market", {})

    structural = market.get("structural_zone", {})
    execution_trigger = structural.get("execution_trigger", {})
    fvg = market.get("fvg_result", {})
    order_block = market.get("order_block_result", {})

    zone_interaction = structural.get("interacting", False)

    trigger_confirmed = execution_trigger.get("confirmed", False)
    trigger_fresh = execution_trigger.get("fresh", False)

    trend = getattr(state, "trend", "UNKNOWN")

    ready = (
        zone_interaction
        and trigger_confirmed
        and trigger_fresh
    )

    signal = "READY" if ready else "WAIT"

    reasons = []

    if not zone_interaction:
        reasons.append("Waiting for zone interaction")

    if not trigger_confirmed:
        reasons.append("Execution trigger not confirmed")

    if not trigger_fresh:
        reasons.append("Execution trigger not fresh")

    metadata = {
        "zone_interaction": zone_interaction,
        "trigger_confirmed": trigger_confirmed,
        "trigger_fresh": trigger_fresh,
        "trend": trend,
        "fvg_signal": fvg.get("signal"),
        "order_block_signal": order_block.get("signal"),
    }

    print("========== EXECUTION CONFIRMATION ==========")
    print("Signal :", signal)
    print("Zone Interaction :", zone_interaction)
    print("Trigger Confirmed :", trigger_confirmed)
    print("Trigger Fresh :", trigger_fresh)
    print("Reasons :", reasons)

    return EngineResult(
        name="Execution Confirmation",
        signal=signal,
        score=100 if ready else 0,
        confidence=100.0 if ready else 0.0,
        metadata=metadata,
        reasons=reasons,
    )
