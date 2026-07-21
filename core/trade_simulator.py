from core.trade import Trade


class TradeSimulator:
    """
    Simulates trade outcomes using historical candles.
    """

    def simulate(self, trade: Trade, candles):

        if not candles:
            trade.status = "OPEN"
            return trade

        for candle in candles:

            high = candle.get("high", 0)
            low = candle.get("low", 0)

            if trade.direction == "BUY":

                if low <= trade.stop_loss:
                    trade.status = "LOSS"
                    trade.exit_price = trade.stop_loss
                    return trade

                if high >= trade.take_profit_2:
                    trade.status = "WIN"
                    trade.exit_price = trade.take_profit_2
                    return trade

                if high >= trade.take_profit_1:
                    trade.status = "WIN"
                    trade.exit_price = trade.take_profit_1
                    return trade

            elif trade.direction == "SELL":

                if high >= trade.stop_loss:
                    trade.status = "LOSS"
                    trade.exit_price = trade.stop_loss
                    return trade

                if low <= trade.take_profit_2:
                    trade.status = "WIN"
                    trade.exit_price = trade.take_profit_2
                    return trade

                if low <= trade.take_profit_1:
                    trade.status = "WIN"
                    trade.exit_price = trade.take_profit_1
                    return trade

        trade.status = "OPEN"
        return trade
