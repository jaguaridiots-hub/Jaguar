from core.market_engine import MarketEngine
from core.indicator_engine import IndicatorEngine
from core.score_engine import ScoreEngine

from strategy.smc_engine import SMCEngine

from core.structure_engine import StructureEngineRunner
from core.mss_engine import MSSEngineRunner
from core.liquidity_engine import LiquidityEngineRunner
from core.fvg_engine import FVGEngineRunner
from core.orderblock_engine import OrderBlockEngineRunner
from core.probability_engine import ProbabilityEngineRunner
from core.premium_discount_engine import PremiumDiscountEngineRunner
from core.wyckoff_engine import WyckoffEngineRunner
from core.equal_levels_engine import EqualLevelsEngineRunner
from core.mtf_engine import MTFEngineRunner
from core.volume_profile_engine import VolumeProfileEngineRunner
from core.session_engine import SessionEngineRunner
from core.regime_engine import RegimeEngineRunner
from core.gann_engine import GannEngineRunner
from core.trade_planner_engine import TradePlannerEngineRunner
from core.risk_manager_engine import RiskManagerEngineRunner
from core.dashboard_engine import DashboardEngineRunner
from core.orderflow_engine import OrderFlowEngineRunner
from core.execution_engine import ExecutionEngineRunner
from core.decision_engine import DecisionEngineRunner
from core.probability_engine_v2 import ProbabilityEngineV2Runner
from core.trade_validator_engine import TradeValidatorEngineRunner
from strategy.master_decision_engine import MasterDecisionEngine
from strategy.execution_confirmation_engine import ExecutionConfirmationEngine
from core.orderflow_engine import OrderFlowEngineRunner
from core.confluence_engine_runner import ConfluenceEngineRunner
from core.timeframe_indicator_engine import TimeframeIndicatorEngineRunner
from core.backtest_engine import BacktestEngine
from core.execution_trigger_engine import ExecutionTriggerEngineRunner
from core.brain_engine import BrainEngine


def register(registry):

    # =====================================================
    # Foundation
    # =====================================================
    registry.register(MarketEngine())
    registry.register(IndicatorEngine())
    registry.register(ScoreEngine())

    # =====================================================
    # Smart Money
    # =====================================================
    registry.register(StructureEngineRunner())
    registry.register(MSSEngineRunner())
    registry.register(SMCEngine())
    registry.register(LiquidityEngineRunner())
    registry.register(FVGEngineRunner())
    registry.register(OrderBlockEngineRunner())
    registry.register(PremiumDiscountEngineRunner())
    registry.register(WyckoffEngineRunner())
    registry.register(EqualLevelsEngineRunner())
    registry.register(VolumeProfileEngineRunner())
    registry.register(SessionEngineRunner())

    # =====================================================
    # Multi-Timeframe
    # =====================================================
    registry.register(TimeframeIndicatorEngineRunner())
    registry.register(MTFEngineRunner())

    # =====================================================
    # Market Context
    # =====================================================
    registry.register(RegimeEngineRunner())
    registry.register(GannEngineRunner())
    registry.register(OrderFlowEngineRunner())

    # =====================================================
    # Probability (must be before Brain)
    # =====================================================
    registry.register(ProbabilityEngineV2Runner())

    # =====================================================
    # AI Brain
    # =====================================================
    registry.register(BrainEngine())
    registry.register(ConfluenceEngineRunner())

    # =====================================================
    # Trade Planning
    # =====================================================
    registry.register(TradePlannerEngineRunner())

    # =====================================================
    # Risk
    # =====================================================
    registry.register(RiskManagerEngineRunner())

    # =====================================================
    # Institutional Decision
    # =====================================================
    registry.register(DecisionEngineRunner())

    # Execution Trigger

    registry.register(ExecutionTriggerEngineRunner())

    # =====================================================
    # Execution Confirmation
    # =====================================================
    registry.register(ExecutionConfirmationEngine())

    # =====================================================
    # Trade Validator
    # =====================================================
    registry.register(TradeValidatorEngineRunner())

    # =====================================================
    # Master Decision
    # =====================================================
    registry.register(MasterDecisionEngine())

    # =====================================================
    # Execution
    # =====================================================
    registry.register(ExecutionEngineRunner())

    # =====================================================
    # Dashboard
    # =====================================================
    registry.register(DashboardEngineRunner())

    # =====================================================
    # Backtest
    # =====================================================
    registry.register(BacktestEngine(registry))
