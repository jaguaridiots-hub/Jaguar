class BacktestEngine:

    def __init__(self):

        self.total_trades = 0
        self.wins = 0
        self.losses = 0

        self.gross_profit = 0
        self.gross_loss = 0

        self.balance = 100000

    def add_trade(self, pnl):

        self.total_trades += 1

        self.balance += pnl

        if pnl > 0:

            self.wins += 1
            self.gross_profit += pnl

        else:

            self.losses += 1
            self.gross_loss += abs(pnl)

    def report(self):

        if self.total_trades == 0:

            return {
                "Trades":0,
                "WinRate":0,
                "ProfitFactor":0,
                "Balance":self.balance
            }

        winrate = round(
            self.wins/self.total_trades*100,
            2
        )

        if self.gross_loss == 0:
            pf = 999
        else:
            pf = round(
                self.gross_profit/self.gross_loss,
                2
            )

        return {

            "Trades":self.total_trades,

            "Wins":self.wins,

            "Losses":self.losses,

            "WinRate":winrate,

            "ProfitFactor":pf,

            "Balance":round(self.balance,2)

        }
