class JaguarState:

    def __init__(self):

        # -----------------------
        # Market
        # -----------------------
        self.symbol = None
        self.interval = None
        self.market = None

        # -----------------------
        # Canonical Indicators
        # -----------------------
        self.ema20 = 0.0
        self.ema50 = 0.0
        self.ema100 = 0.0
        self.ema200 = 0.0
        self.rsi = 0.0
        self.atr = 0.0
        self.volume = 0.0

        # -----------------------
        # Engine Results
        # -----------------------
        self.indicators = {}
        self.idm = {}
        self.score = {}
        self.smc = {}
        self.structure = {}
        self.liquidity = {}
        self.fvg = {}
        self.orderblock = {}
        self.session = {}
        self.regime = {}
        self.gann = {}
        self.probability = {}
        self.brain = {}
        self.trade = {}
        self.risk = {}

        # -----------------------
        # Diagnostics
        # -----------------------
        self.error = None
        self.engine_status = {}
        self.engine_time = {}

        # -----------------------
        # Final Decision
        # -----------------------
        self.signal = None
        self.confidence = 0
        self.grade = None
