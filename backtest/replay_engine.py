from jaguar_ai import JaguarAI

class ReplayEngine:

    @staticmethod
    def run(symbol, candles):

        results = []

        # Start after enough candles exist for indicators
        for i in range(100, len(candles)):

            history = candles[:i]

            try:
                result = JaguarAI.analyze(symbol, history)
            except Exception:
                continue

            results.append({
                "index": i,
                "price": history[-1]["close"],
                "signal": result["signal"],
                "confidence": result["confidence"]
            })

        return results
