from datetime import datetime, timezone

def killzone_score():
    score = 0
    reasons = []

    utc = datetime.now(timezone.utc)

    hour = utc.hour

    # London Kill Zone (07-10 UTC)
    if 7 <= hour <= 10:
        score += 2
        reasons.append("London Kill Zone")

    # New York Kill Zone (13-16 UTC)
    if 13 <= hour <= 16:
        score += 2
        reasons.append("New York Kill Zone")

    return score, reasons
