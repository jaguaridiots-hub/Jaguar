# research/research_trade_planner.py
"""
Research‑only trade planner.
Replicates the TradePlannerEngine logic for rejected Master Decisions,
without modifying any production code.
"""
import copy

def generate_research_plan(state):
    """
    Produce a trade plan dict with entry, stop, tp1, tp2, risk_reward
    using the same logic as the production TradePlannerEngine.
    """
    mode = getattr(state, 'mode', 'SCALP')
    price = state.price
    atr = _get_atr(state)
    # Default stop/TP distances (fallback if ATR unavailable)
    stop_pips = 20.0
    tp1_pips = 40.0
    tp2_pips = 60.0

    if atr and atr > 0:
        if mode == 'SCALP':
            stop_pips = atr * 1.0
            tp1_pips = atr * 1.5
            tp2_pips = atr * 2.5
        elif mode == 'SWING':
            stop_pips = atr * 2.0
            tp1_pips = atr * 3.0
            tp2_pips = atr * 5.0
        elif mode == 'CLASSIC':
            stop_pips = atr * 1.5
            tp1_pips = atr * 2.5
            tp2_pips = atr * 4.0

    # Direction: always assume BUY for simulated plan (we don't know the actual signal,
    # but the Master Decision tells us BUY/SELL – we'll extract it later)
    direction = getattr(state, 'master_decision', {}).get('decision', 'BUY')
    if direction not in ('BUY', 'SELL'):
        direction = 'BUY'   # fallback

    if direction == 'BUY':
        stop = price - stop_pips
        tp1 = price + tp1_pips
        tp2 = price + tp2_pips
    else:
        stop = price + stop_pips
        tp1 = price - tp1_pips
        tp2 = price - tp2_pips

    return {
        'entry': price,
        'stop': stop,
        'tp1': tp1,
        'tp2': tp2,
        'risk_reward': 2.0,   # not critical for simulation
        'direction': direction
    }


def _get_atr(state):
    """Extract ATR from state.indicators if available."""
    ind = getattr(state, 'indicators', None)
    if ind is None:
        return None
    atr_data = ind.get('atr', None)
    if atr_data is None:
        return None
    # ATR may be a dict with 'value', or a plain number
    if isinstance(atr_data, dict):
        return atr_data.get('value', None)
    return atr_data
