class TradeGrade:

    @staticmethod
    def calculate(technical, smc, gann, confidence):

        total = technical + smc + gann

        if total >= 180 and confidence >= 90:
            grade = "A+"
            action = "EXECUTE"

        elif total >= 150:
            grade = "A"
            action = "BUY"

        elif total >= 120:
            grade = "B"
            action = "WATCH"

        elif total >= 80:
            grade = "C"
            action = "WAIT"

        else:
            grade = "D"
            action = "NO TRADE"

        return {
            "grade": grade,
            "action": action,
            "score": total
        }
