from core.market_engine import MarketEngine
from core.indicator_engine import IndicatorEngine
from core.score_engine import ScoreEngine
from strategy.smc_engine import SMCEngine
from core.brain_engine import BrainEngine
from core.probability_engine import ProbabilityEngineRunner
from core.orderblock_engine import OrderBlockEngineRunner
from core.structure_engine import StructureEngineRunner
from core.liquidity_engine import LiquidityEngineRunner
from core.fvg_engine import FVGEngineRunner
from core.premium_discount_engine import PremiumDiscountEngineRunner
from core.wyckoff_engine import WyckoffEngineRunner
from core.mss_engine import MSSEngineRunner
from core.equal_levels_engine import EqualLevelsEngineRunner


def register(registry):

    registry.register(MarketEngine())
    registry.register(IndicatorEngine())
    registry.register(ScoreEngine())
    registry.register(SMCEngine())
    registry.register(StructureEngineRunner())
    registry.register(MSSEngineRunner())
    registry.register(LiquidityEngineRunner())
    registry.register(FVGEngineRunner())
    registry.register(OrderBlockEngineRunner())
    registry.register(ProbabilityEngineRunner())
    registry.register(BrainEngine())
    registry.register(PremiumDiscountEngineRunner())
    registry.register(WyckoffEngineRunner())
    registry.register(EqualLevelsEngineRunner())
