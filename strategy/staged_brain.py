# strategy/staged_brain.py
import math

class StagedBrain:
    """
    A staged decision pipeline that replaces the flat additive Brain for
    research and comparison purposes.
    """

    def __init__(self, probability_threshold=0.55):
        self.threshold = probability_threshold

    def _safe_get(self, state, attr, default=None):
        obj = getattr(state, attr, None)
        return obj if obj is not None else (default or {})

    def evaluate(self, state):
        """
        Main entry point. Returns a dict compatible with master_decision format.
        """
        # Gather engine outputs
        regime = self._safe_get(state, 'regime', {})
        session = self._safe_get(state, 'session', {})
        gann = self._safe_get(state, 'gann', {})
        structure = self._safe_get(state, 'structure', {})
        mss = self._safe_get(state, 'mss', {})
        equal_levels = self._safe_get(state, 'equal_levels', {})
        smc = self._safe_get(state, 'smc', {})
        liquidity = self._safe_get(state, 'liquidity', {})
        order_block = self._safe_get(state, 'order_block', {})
        fvg = self._safe_get(state, 'fvg', {})
        orderflow = self._safe_get(state, 'orderflow', {})
        volume_profile = self._safe_get(state, 'volume_profile', {})
        wyckoff = self._safe_get(state, 'wyckoff', {})

        # --- Stage 1: Market Permission ---
        # Hard filters: if any fail, REJECT immediately
        reasons = []

        regime_signal = regime.get('signal', 'NEUTRAL')
        if regime_signal == 'COMPRESSION':
            reasons.append("Market regime is COMPRESSION – no directional edge")
        session_score = session.get('score', 0)
        if session_score < 5:
            reasons.append("Session quality too low")

        # Volatility filter – use ATR from indicators if available
        atr = getattr(state, 'indicators', {}).get('atr', {})
        if isinstance(atr, dict):
            atr_val = atr.get('value', 0)
        else:
            atr_val = atr if isinstance(atr, (int, float)) else 0
        if atr_val > 0 and atr_val < 10:   # example threshold
            reasons.append("Volatility too low for meaningful move")

        if reasons:
            return {
                "decision": "REJECT",
                "approved": False,
                "score": 0,
                "confidence": 0,
                "probability": 0.0,
                "reasons": reasons,
                "components": {}
            }

        # --- Stage 2: Structural Permission ---
        structure_confidence = 0.5  # neutral
        bearish_count = 0
        if structure.get('bos', {}).get('signal') == 'BEARISH':
            bearish_count += 1
        if structure.get('choch', {}).get('signal') == 'BEARISH':
            bearish_count += 1
        if mss.get('signal') == 'BEARISH':
            bearish_count += 1
        if equal_levels.get('signal') == 'EQH':
            bearish_count += 1

        if bearish_count >= 3:
            return {
                "decision": "REJECT",
                "approved": False,
                "score": 0,
                "confidence": 0,
                "probability": 0.0,
                "reasons": ["Multiple bearish structural signals – trade vetoed"],
                "components": {}
            }
        elif bearish_count == 2:
            structure_confidence = 0.3
        elif bearish_count == 1:
            structure_confidence = 0.7

        # --- Stage 3: Smart Money Confirmation ---
        smart_money = 0.0
        for eng in [smc, liquidity, order_block, fvg]:
            sig = eng.get('signal')
            if sig in ('BULLISH', 'BUY'):
                smart_money += 0.2
            elif sig in ('BEARISH', 'SELL'):
                smart_money -= 0.2
        smart_money = max(-0.5, min(0.5, smart_money))

        # --- Stage 4: Entry Quality ---
        entry_quality = 0.0
        for eng, weight in [(orderflow, 0.3), (volume_profile, 0.2), (wyckoff, 0.1)]:
            raw = eng.get('score', 0)
            # Normalize to [-1,1] assuming typical max score ~100
            normalized = raw / 100.0
            entry_quality += normalized * weight
        entry_quality = max(-0.3, min(0.3, entry_quality))

        # --- Stage 5: Final Probability ---
        evidence = structure_confidence + smart_money + entry_quality
        # Logistic function
        probability = 1.0 / (1.0 + math.exp(-evidence * 3))

        decision = "BUY" if probability >= self.threshold else "REJECT"

        return {
            "decision": decision,
            "approved": decision in ("BUY", "SELL"),
            "score": round(probability * 100, 1),
            "confidence": round(probability * 100, 0),
            "probability": round(probability, 4),
            "reasons": ["Below threshold"] if decision == "REJECT" else [],
            "components": {
                "structure_confidence": structure_confidence,
                "smart_money": smart_money,
                "entry_quality": entry_quality,
                "evidence": evidence
            }
        }
