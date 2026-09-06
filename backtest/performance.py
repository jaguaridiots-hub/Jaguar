class Performance:

    @staticmethod
    def report(trades):

        total = len(trades)

        wins = len([t for t in trades if t["win"]])

        losses = total - wins

        profit = sum(t["profit"] for t in trades)

        gross_win = sum(t["profit"] for t in trades if t["profit"] > 0)

        gross_loss = abs(sum(t["profit"] for t in trades if t["profit"] < 0))

        pf = round(gross_win/gross_loss,2) if gross_loss else 99

        return {

            "Trades": total,

            "Wins": wins,

            "Losses": losses,

            "WinRate": round((wins/total)*100,2) if total else 0,

            "ProfitFactor": pf,

            "NetProfit": round(profit,2)

        }
