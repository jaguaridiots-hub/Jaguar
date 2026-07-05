from smc.smc_engine import smc_score
from analysis.multi_timeframe import report
from analysis.liquidity_engine import liquidity_score
from analysis.orderblock_engine import orderblock_score
from analysis.bos_engine import bos_score
from analysis.premium_discount_engine import premium_discount_score
from analysis.breaker_engine import breaker_score
from analysis.mitigation_engine import mitigation_score
from analysis.fvg_engine import fvg_score
from analysis.support_resistance_engine import support_resistance
from analysis.swing_engine import swing_score
from analysis.liquidity_sweep import liquidity_sweep_score
from analysis.killzone_engine import killzone_score
from analysis.mss_engine import mss_score
from analysis.inducement_engine import inducement_score
from analysis.smt_engine import smt_score
from analysis.cisd_engine import cisd_score
from analysis.ote_engine import ote_score
from analysis.vwap_engine import vwap_score
from analysis.cvd_engine import cvd_score
from analysis.volume_profile import volume_profile_score
from analysis.regime_engine import regime_score
from analysis.delta_engine import delta_score
from analysis.confidence_engine import confidence_score

def make_decision(state, volume_signal, mtf):

    score = 0
    reasons = []

    levels = support_resistance()

    support = levels["support"]
    resistance = levels["resistance"]

    # ==========================
    # Multi-Timeframe Bias
    # ==========================

    if mtf["1d"] == "BULLISH":
        score += 4
        reasons.append("Daily Trend Bullish")
    else:
        score -= 4
        reasons.append("Daily Trend Bearish")

    if mtf["4h"] == "BULLISH":
        score += 2
        reasons.append("4H Trend Bullish")
    elif mtf["4h"] == "BEARISH":
        score -= 2
        reasons.append("4H Trend Bearish")

    if mtf["1h"] == "BULLISH":
        score += 2
        reasons.append("1H Trend Bullish")
    elif mtf["1h"] == "BEARISH":
        score -= 2
        reasons.append("1H Trend Bearish")

    if mtf["15m"] == "BULLISH":
        score += 1
        reasons.append("15M Trend Bullish")
    elif mtf["15m"] == "BEARISH":
        score -= 1
        reasons.append("15M Trend Bearish")

    # -------------------------
    # SMC
    # -------------------------
    smc, smc_reasons = smc_score()

    score += smc
    reasons.extend(smc_reasons)
    ob, ob_reasons = orderblock_score()

    score += ob
    reasons.extend(ob_reasons)

    # -------------------------
    # Breaker Block
    # -------------------------

    breaker, breaker_reasons = breaker_score()

    score += breaker
    reasons.extend(breaker_reasons)

    # -------------------------
    # Liquidity
    # -------------------------
    liq, liq_reasons = liquidity_score()

    score += liq
    reasons.extend(liq_reasons)

    # -----------------------
    # BOS
    # -----------------------

    bos, bos_reasons = bos_score()

    score += bos
    reasons.extend(bos_reasons)

    # -----------------------
    # Premium / Discount
    # -----------------------

    pd_score, pd_reasons = premium_discount_score()

    score += pd_score
    reasons.extend(pd_reasons)

    # ------------------------
    # Mitigation Block
    # ------------------------

    mit_score, mit_reasons = mitigation_score()

    score += mit_score
    reasons.extend(mit_reasons)

    # ------------------------
    # Fair Value Gap
    # ------------------------

    fvg, fvg_reasons = fvg_score()

    score += fvg
    reasons.extend(fvg_reasons)

    # ------------------------
    # Swing Structure
    # ------------------------

    sw_score, sw_reasons = swing_score()

    score += sw_score
    reasons.extend(sw_reasons)

    ls_score, ls_reasons = liquidity_sweep_score()

    score += ls_score
    reasons.extend(ls_reasons)

    kz_score, kz_reasons = killzone_score()

    score += kz_score
    reasons.extend(kz_reasons)

    mss, mss_reasons = mss_score()

    score += mss
    reasons.extend(mss_reasons)

    ind_score, ind_reasons = inducement_score()

    score += ind_score
    reasons.extend(ind_reasons)

    smt, smt_reasons = smt_score()

    score += smt
    reasons.extend(smt_reasons)

    cisd, cisd_reasons = cisd_score()

    score += cisd
    reasons.extend(cisd_reasons)

    ote, ote_reasons = ote_score()

    score += ote
    reasons.extend(ote_reasons)

    vwap, vwap_reasons = vwap_score()

    score += vwap
    reasons.extend(vwap_reasons)

    cvd, cvd_reasons = cvd_score()

    score += cvd
    reasons.extend(cvd_reasons)

    vp_score, vp_reasons = volume_profile_score()

    score += vp_score
    reasons.extend(vp_reasons)

    delta, delta_reasons = delta_score(state)

    score += delta
    reasons.extend(delta_reasons)

    regime, regime_reasons = regime_score(state)

    score += regime
    reasons.extend(regime_reasons)

    # -------------------------
    # Confidence Engine
    # -------------------------
    conf_score, conf_reasons = confidence_score(state, reasons)

    score += conf_score
    reasons.extend(conf_reasons)

    # -------------------------
    # Score Adjustment
    # -------------------------

    if "Bearish CHoCH" in reasons:
        score -= 2

    if "Bearish Breaker" in reasons:
        score -= 2

    if "Bearish Order Block" in reasons:
        score -= 2

    if "Bearish FVG" in reasons:
        score -= 1

    if "Bullish CHoCH" in reasons:
        score += 2

    if "Bullish Breaker" in reasons:
        score += 2

    if "Bullish Order Block" in reasons:
        score += 2

    if "Bullish FVG" in reasons:
        score += 1

    # -------------------------
    # Support / Resistance
    # -------------------------

    distance_to_support = state.price - support
    distance_to_resistance = resistance - state.price

    if distance_to_support < state.atr:
        score += 2
        reasons.append("Near Support")

    if distance_to_resistance < state.atr:
        score -= 2
        reasons.append("Near Resistance")

    # -------------------------
    # EMA
    # -------------------------
    if state.ema20 > state.ema50 > state.ema100 > state.ema200:
        score += 4
        reasons.append("Bullish EMA")

    elif state.ema20 < state.ema50 < state.ema100 < state.ema200:
        score -= 4
        reasons.append("Bearish EMA")

    # -------------------------
    # RSI
    # -------------------------
    if state.rsi < 30:
        score += 2
        reasons.append("Oversold")

    elif state.rsi > 70:
        score -= 2
        reasons.append("Overbought")

    # -------------------------
    # Volume
    # -------------------------
    if volume_signal == "HIGH VOLUME":
        score += 2
        reasons.append("High Volume")

    elif volume_signal == "LOW VOLUME":
        score -= 1
        reasons.append("Low Volume")

    # -------------------------
    # Confidence Grade
    # -------------------------

    if score >= 28:
        grade = "A+"
    elif score >= 22:
        grade = "A"
    elif score >= 16:
        grade = "B"
    elif score >= 10:
        grade = "C"
    else:
        grade = "NO TRADE"

    state.confidence = grade

    probability = 50 + score * 2

    if probability > 98:
        probability = 98

    if probability < 5:
        probability = 5

    # ==========================
    # AI Confidence Filter
    # ==========================

    if volume_signal == "LOW VOLUME":
        probability -= 10
        reasons.append("Low Confidence")

    if mtf["1h"] != mtf["15m"]:
        probability -= 10
        reasons.append("MTF Conflict")

    if probability < 60:
        decision = "⚪ NO TRADE"

    elif score >= 20:
        decision = "🟢 STRONG BUY"

    elif score >= 15:
        decision = "🟢 BUY"

    elif score >= 8:
        decision = "🟡 WATCH"

    elif score <= -20:
        decision = "🔴 STRONG SELL"

    elif score <= -15:
        decision = "🔴 SELL"

    else:
        decision = "⚪ NEUTRAL"

    state.ai_score = score
    state.confidence = grade
    state.probability = probability
    state.decision = decision

    return reasons
