"""
Register all 15 engines.
"""
from core.engine_registry import EngineRegistry

# Import all engine runners (adjust paths if necessary)
from strategy.yahoo_market_engine import YahooMarketEngine
from core.timeframe_indicator_engine import TimeframeIndicatorEngineRunner
from strategy.smc_engine import SMCEngine
from core.structure_engine import StructureEngineRunner
from core.wyckoff_engine import WyckoffEngineRunner
from core.liquidity_engine import LiquidityEngineRunner
from core.fvg_engine import FVGEngineRunner
from core.orderblock_engine import OrderBlockEngineRunner
from core.orderflow_engine import OrderFlowEngineRunner
from core.volume_profile_engine import VolumeProfileEngineRunner
from core.session_engine import SessionEngineRunner
from core.mtf_engine import MTFEngineRunner
from core.regime_engine import RegimeEngineRunner
from core.gann_engine import GannEngineRunner
from core.equal_levels_engine import EqualLevelsEngineRunner
from core.premium_discount_engine import PremiumDiscountEngineRunner
from core.mss_engine import MSSEngineRunner

def register(registry: EngineRegistry):
    """Register all engines."""
    registry.register(YahooMarketEngine())
    registry.register(TimeframeIndicatorEngineRunner())
    registry.register(StructureEngineRunner())
    registry.register(SMCEngine())
    registry.register(WyckoffEngineRunner())
    registry.register(LiquidityEngineRunner())
    registry.register(FVGEngineRunner())
    registry.register(OrderBlockEngineRunner())
    registry.register(OrderFlowEngineRunner())
    registry.register(VolumeProfileEngineRunner())
    registry.register(SessionEngineRunner())
    registry.register(MTFEngineRunner())
    registry.register(RegimeEngineRunner())
    registry.register(GannEngineRunner())
    registry.register(EqualLevelsEngineRunner())
    registry.register(PremiumDiscountEngineRunner())
    registry.register(MSSEngineRunner())
