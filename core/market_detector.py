class MarketDetector:

    @staticmethod
    def detect(symbol):

        symbol = symbol.upper()

        # India
        if symbol.endswith(".NS"):
            return "NSE"

        if symbol.endswith(".BO"):
            return "BSE"

        # MCX
        mcx = {
            "GOLD",
            "SILVER",
            "CRUDEOIL",
            "NATURALGAS",
            "COPPER",
            "ZINC",
            "LEAD",
            "NICKEL",
            "ALUMINIUM"
        }

        if symbol in mcx:
            return "MCX"

        # Forex
        forex = {
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "USDCHF",
            "AUDUSD",
            "NZDUSD",
            "USDCAD",
            "XAUUSD",
            "XAGUSD"
        }

        if symbol in forex:
            return "FOREX"

        # Crypto
        if symbol.endswith("USDT"):
            return "CRYPTO"

        # US Stocks
        return "US"

