class PositionSize:

    @staticmethod
    def calculate(balance, risk_percent, entry, stop_loss):

        risk_amount = balance * (risk_percent / 100)

        stop_distance = abs(entry - stop_loss)

        if stop_distance == 0:
            return None

        quantity = risk_amount / stop_distance

        rr1 = abs((entry - stop_loss) / stop_distance)

        return {
            "balance": round(balance, 2),
            "risk_percent": risk_percent,
            "risk_amount": round(risk_amount, 2),
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "quantity": round(quantity, 6),
            "stop_distance": round(stop_distance, 2)
        }
