# research/statistical_validator.py
from enum import Enum
from datetime import datetime

class Confidence(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

def confidence_level(sample_size: int) -> Confidence:
    if sample_size >= 100:
        return Confidence.HIGH
    elif sample_size >= 50:
        return Confidence.MEDIUM
    else:
        return Confidence.LOW

def format_engine_recommendation(engine_name, pos_total, pos_wins, neg_total, neg_wins, avg_contrib):
    pos_wr = (pos_wins / pos_total * 100) if pos_total > 0 else 0.0
    neg_wr = (neg_wins / neg_total * 100) if neg_total > 0 else 0.0

    sample_size = min(pos_total, neg_total) if pos_total > 0 and neg_total > 0 else max(pos_total, neg_total)
    conf = confidence_level(sample_size)

    lines = [
        f"{engine_name} Engine Contribution",
        f"  Positive: Trades: {pos_total}  Wins: {pos_wins}  Losses: {pos_total - pos_wins}  Win Rate: {pos_wr:.1f}%",
        f"  Negative: Trades: {neg_total}  Wins: {neg_wins}  Losses: {neg_total - neg_wins}  Win Rate: {neg_wr:.1f}%",
    ]
    if pos_total > 0 and neg_total > 0:
        if pos_wr > neg_wr + 10:
            rec = f"Recommendation: Increase weight for {engine_name} (avg contribution {avg_contrib:+.2f}). "
            rec += f"Win rate when positive: {pos_wr:.1f}% vs negative: {neg_wr:.1f}%"
        elif neg_wr > pos_wr + 10:
            rec = f"Recommendation: Decrease weight for {engine_name} (avg contribution {avg_contrib:+.2f}). "
            rec += f"Win rate when negative: {neg_wr:.1f}% vs positive: {pos_wr:.1f}%"
        else:
            rec = f"Recommendation: No clear directional edge for {engine_name} (positive: {pos_wr:.1f}%, negative: {neg_wr:.1f}%)"
    elif pos_total > 0 and neg_wr < 40:
        rec = f"Recommendation: {engine_name} only contributed positively with low win rate {pos_wr:.1f}%. Review scoring logic."
    elif neg_total > 0 and pos_wr < 40:
        rec = f"Recommendation: {engine_name} only contributed negatively with low win rate {neg_wr:.1f}%. Consider reducing influence."
    else:
        rec = ""
    if rec:
        lines.append(rec)
    lines.append(f"  Confidence: {conf.value}")
    return "\n".join(lines), conf, sample_size, abs(pos_wr - neg_wr) if pos_total > 0 and neg_total > 0 else 0

def format_category_recommendation(category_name, item, trades, wins, conf=None):
    losses = trades - wins
    wr = (wins / trades * 100) if trades > 0 else 0.0
    if conf is None:
        conf = confidence_level(trades)
    lines = [
        f"{category_name}: {item}",
        f"  Trades: {trades}  Wins: {wins}  Losses: {losses}  Win Rate: {wr:.1f}%",
    ]
    if wr < 40:
        lines.append(f"  Recommendation: Consider avoiding {item} (Win Rate {wr:.1f}%)")
    else:
        lines.append("  Performance is acceptable.")
    lines.append(f"  Confidence: {conf.value}")
    return "\n".join(lines), conf, trades, wr

def generate_global_summary(trades):
    closed = len(trades)
    symbols = set()
    timeframes = set()
    regimes = set()
    for t in trades:
        symbols.add(t["symbol"])
        timeframes.add(t["timeframe"])
        regimes.add(t["regime"] or "UNKNOWN")
    return f"""
  Closed Trades Analysed : {closed}
  Unique Symbols         : {', '.join(sorted(symbols))}
  Unique Timeframes      : {', '.join(sorted(timeframes))}
  Unique Regimes         : {', '.join(sorted(regimes))}
  Analysis Date          : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
