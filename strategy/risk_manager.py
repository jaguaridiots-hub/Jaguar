class RiskManager:

    @staticmethod
    def calculate(price, atr):

        stop_loss = price - atr * 2

        tp1 = price + atr * 2
        tp2 = price + atr * 4
        tp3 = price + atr * 6

        rr = round((tp2-price)/(price-stop_loss),2)

        return {
            "entry": round(price,2),
            "sl": round(stop_loss,2),
            "tp1": round(tp1,2),
            "tp2": round(tp2,2),
            "tp3": round(tp3,2),
            "rr": rr
        }
