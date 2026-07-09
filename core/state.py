class JaguarState:

    def __init__(self):

        self.symbol = None
        self.interval = "15m"

        # Market Data
        self.market = {}
        self.market_current = None

        # Engines
        self.indicators = None
        self.ai = None
        self.risk = None

        self.smc = {}
        self.structure = {}
        self.mss = {}
        self.volume_profile = None
        self.equal_levels = {}
        self.liquidity = {}
        self.fvg = {}
        self.premium_discount = {}
        self.wyckoff = {}
        self.orderblock = {}
        self.orderflow = {}
        self.execution = {}
        self.probability = {}
        self.mtf = {}
        self.session = {}

        # New Enterprise Engines
        self.regime = {}
        self.orderflow = {}

        self.trade_plan = {}
        self.decision = {}
        self.risk_manager = {}
        self.gann = {}
        self.dashboard = {}

        self.brain = {}
