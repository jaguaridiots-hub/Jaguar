class TradeSimulator:

    @staticmethod
    def simulate(signals):

        trades=[]

        position=None

        for s in signals:

            if position is None:

                if s["signal"] in ["BUY","STRONG BUY"]:

                    position={
                        "entry":s["price"],
                        "index":s["index"]
                    }

            else:

                if s["signal"] in ["SELL","STRONG SELL"]:

                    exit_price=s["price"]

                    profit=exit_price-position["entry"]

                    trades.append({

                        "entry":position["entry"],

                        "exit":exit_price,

                        "profit":round(profit,2),

                        "win":profit>0

                    })

                    position=None

        return trades
