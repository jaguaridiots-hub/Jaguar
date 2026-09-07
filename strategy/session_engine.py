from datetime import datetime


class SessionEngine:

    def run(self, state, bus):


        now = datetime.utcnow()

        hour = now.hour

        session = "CLOSED"
        score = 0
        reasons = []

        if 0 <= hour < 7:
            session = "ASIA"
            score = 5
            reasons.append("Asian Session")

        elif 7 <= hour < 13:
            session = "LONDON"
            score = 15
            reasons.append("London Session")

        elif 13 <= hour < 17:
            session = "LONDON_NEWYORK"
            score = 25
            reasons.append("London-New York Overlap")

        elif 17 <= hour < 22:
            session = "NEWYORK"
            score = 10
            reasons.append("New York Session")

        else:
            session = "CLOSED"
            score = -10
            reasons.append("Market Quiet")

        state.session = {
            "session": session,
            "score": score,
            "reasons": reasons
        }


        return state
