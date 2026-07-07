from core.trading_kernel import TradingKernel
from indicators.indicator_engine import IndicatorEngine

from ai.score_engine import ScoreEngine
from ai.decision_engine import AIDecision
from ai.master_confluence import MasterConfluence
from ai.gann_engine import GannEngine

from strategy.market_regime import MarketRegime
from strategy.market_structure import MarketStructure
from strategy.order_block import OrderBlock
from strategy.fair_value_gap import FairValueGap
from strategy.liquidity import Liquidity
from strategy.premium_discount import PremiumDiscount
from strategy.institutional_entry import InstitutionalEntry

from strategy.gann_square import GannSquare
from strategy.gann_angles import GannAngles
from strategy.gann_time import GannTime
from strategy.gann_confluence import GannConfluence
from strategy.gann_swing import GannSwing

from strategy.risk_manager import RiskManager


class JaguarAI:

    @staticmethod
    def analyze(symbol, candles=None):

        print("=" * 60)
        print("        JAGUAR QUANT X")
        print("=" * 60)

        # --------------------------
        # Market Data
        # --------------------------

        kernel = TradingKernel(symbol)

        market = kernel.load()

        if candles is None:
            candles = market["candles"]

        price = candles[-1]["close"]

        # --------------------------
        # Technical Engine
        # --------------------------

        technical = IndicatorEngine.calculate(candles)
        regime = MarketRegime.detect(technical)
        technical["regime"] = regime

        print(technical.keys())
        print(technical)

        tech_score = ScoreEngine.calculate(technical)

        tech_decision = AIDecision.decide(tech_score)

        # --------------------------
        # Smart Money
        # --------------------------


        structure = MarketStructure.detect(candles)

        orderblock = OrderBlock.detect(candles)

        fvg = FairValueGap.detect(candles)

        liquidity = Liquidity.detect(candles)

        zone = PremiumDiscount.detect(candles)

        smc = InstitutionalEntry.analyze(
            regime,
            structure,
            orderblock,
            fvg,
            liquidity,
            zone
        )

        # --------------------------
        # Gann Engine
        # --------------------------

        square = GannSquare.calculate(price)

        angle = GannAngles.calculate(
            price,
            square["support"],
            square["resistance"]
        )

        gtime = GannTime.calculate(len(candles))

        confluence = GannConfluence.calculate(
            square,
            angle,
            gtime
        )

        gann = GannEngine.score(
            square,
            angle,
            gtime,
            confluence
        )

        # --------------------------
        # Master AI
        # --------------------------

        final = MasterConfluence.analyze(
            tech_score,
            smc,
            gann
        )

        # --------------------------
        # Risk
        # --------------------------

        risk = RiskManager.calculate(
            price,
            technical["atr"]["value"]
        )

        # --------------------------
        # Report
        # --------------------------

        print()

        print("Asset :", symbol)

        print("Price :", price)

        print()

        print("Signal :", final["signal"])

        print("Confidence :", final["confidence"], "%")

        print()

        print("Technical Score :", tech_score["score"])

        print("SMC Score :", smc["score"])

        print("Gann Score :", gann["score"])

        print()

        print("Entry :", risk["entry"])

        print("SL :", risk["sl"])

        print("TP1 :", risk["tp1"])

        print("TP2 :", risk["tp2"])

        print("TP3 :", risk["tp3"])

        print()

        print("Reasons")

        for r in final["reasons"]:

            print("✓", r)

        print("=" * 60)

        return final
