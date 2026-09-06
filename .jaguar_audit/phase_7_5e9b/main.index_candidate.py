from core.kernel import JaguarKernel
from core.logger import JaguarLogger
from core.registry import ModuleRegistry
from core.event_bus import EventBus
from engine.trade_manager import TradeManager
from engine.position_manager import PositionManager
from engine.trade_journal import TradeJournal
from engine.performance import Performance
from engine.live_feed import LiveFeed
import time
from engine.state_manager import save, load, clear
from market.live_loader import update_state
SYMBOL = 'BTCUSDT'
TIMEFRAME = '15m'
print('=' * 50)
print('              JAGUAR QUANT X v2.0')
print('=' * 50)
log = JaguarLogger()
log.info('Starting Jaguar Quant X...')
kernel = JaguarKernel()
kernel.initialize(SYMBOL, TIMEFRAME)
registry = ModuleRegistry()
modules = ['Kernel', 'Market Data', 'Indicators', 'Gann Engine', 'SMC Engine', 'AI Brain', 'Probability Engine', 'Risk Engine', 'Trade Engine']
for module in modules:
    registry.register(module)
registry.show()
bus = EventBus()
bus.publish('startup', 'All Systems Online')
print('\n' + '=' * 50)
print('Jaguar Quant X Ready To Trade')
print('=' * 50)
state = kernel.get_state()
state = update_state(state, SYMBOL)
candles = state.market['candles']
latest = candles[-1]
print('\n========= LIVE MARKET =========')
print('Symbol     :', state.symbol)
print('Timeframe  :', state.timeframe)
print('Price      :', state.price)
print('High       :', latest['high'])
print('Low        :', latest['low'])
print('Volume     :', state.volume)
print('\nMarket State')
print(state.summary())
from indicators.indicator_engine import update_market_state
state = update_market_state(state)
print('\nIndicators')
print('-------------------------')
print('EMA20 :', state.ema20)
print('EMA50 :', state.ema50)
print('EMA100:', state.ema100)
print('EMA200:', state.ema200)
print('RSI   :', state.rsi)
print('ATR   :', state.atr)
print('Volume:', state.volume)
from engine.institutional_master import analyze as institutional_master
report = institutional_master(state)
print(report)
context = report.get('context', report.get('decision', {}))
enterprise = report.get('enterprise', {})
plan = report.get('plan', {})
context_direction = context.get('direction', 'NEUTRAL')
context_decision = context.get('decision', 'WAIT')
context_grade = context.get('confidence', 'D')
context_probability = context.get('probability', 0)
context_score = context.get('score', 0)
print('\n========== MARKET CONTEXT ==========')
print('Bias          :', context_direction)
print('Setup Status  :', context_decision)
print('Context Grade :', context_grade)
print('Probability   :', f'{context_probability}%')
print('Context Score :', context_score)
execution = enterprise.get('execution', {})
enterprise_approved = enterprise.get('approved', False)
print('\n========== ENTERPRISE DECISION ==========')
print('Score         :', enterprise.get('score', 0))
print('Grade         :', enterprise.get('grade', 'F'))
print('Confidence    :', enterprise.get('confidence', 0))
print('IDM Decision  :', enterprise.get('decision', 'WAIT'))
print('Priority      :', enterprise.get('priority', 'LOW'))
print('Approved      :', enterprise_approved)
print('Execution     :', execution.get('status', 'WAIT'))
print('Ready         :', execution.get('ready', False))
print('Reason        :', execution.get('reason', ''))
engines = report.get('engines', {})
gann = engines.get('Gann', {})
gann_metadata = gann.get('metadata', {})
support = gann_metadata.get('support')
resistance = gann_metadata.get('resistance')
print('\n====== SUPPORT / RESISTANCE ======')
support_display = round(support, 2) if isinstance(support, (int, float)) else 'N/A'
resistance_display = round(resistance, 2) if isinstance(resistance, (int, float)) else 'N/A'
print('Support   :', support_display)
print('Resistance:', resistance_display)
performance = Performance()
journal = TradeJournal()
position = PositionManager()
manager = TradeManager()
position_loaded = load(position)
if position_loaded:
    print('\nExisting trade state loaded.')
trade_status = {'Action': 'NO TRADE', 'StopLoss': 0, 'BreakEven': False, 'Trailing': False}
execution_ready = execution.get('ready', False)
if plan and plan.get('Direction') and execution_ready:
    trade_status = manager.manage(state, plan)
    journal.save(state, plan)
    if position.position == 'NONE':
        direction = plan.get('Direction', '')
        if 'BUY' in direction:
            position.open_trade('LONG', plan['Entry'], plan['StopLoss'], plan['TP1'])
            save(position)
        elif 'SELL' in direction:
            position.open_trade('SHORT', plan['Entry'], plan['StopLoss'], plan['TP1'])
            save(position)
if position.position != 'NONE':
    print('\n========== POSITION ACTIVE ==========')
    try:
        while position.position != 'NONE':
            state = update_state(state, SYMBOL)
            position.update(state.price)
            save(position)
            trade_status = manager.manage(state, plan)
            new_stop = trade_status.get('StopLoss')
            if isinstance(new_stop, (int, float)) and new_stop > 0:
                position.update_stop_loss(new_stop)
            status = position.status()
            print('\n===== LIVE MARKET =====')
            print('Symbol :', state.symbol)
            print('Price  :', state.price)
            print('High   :', state.high)
            print('Low    :', state.low)
            print('Volume :', state.volume)
            print('PnL    :', status.get('PnL', 0))
            print('Action :', trade_status.get('Action', 'WAIT'))
            print('Stop Loss :', trade_status.get('StopLoss', 0))
            print('BreakEven :', trade_status.get('BreakEven', False))
            print('Trailing :', trade_status.get('Trailing', False))
            if trade_status.get('Action') in ('EXIT', 'STOP LOSS'):
                position.close_trade()
                clear()
                print('\nTrade Closed')
                break
            time.sleep(5)
    except KeyboardInterrupt:
        print('\nStopping active trade monitor...')
else:
    print('\nNo Position')
print('Action      :', trade_status.get('Action', 'NO TRADE'))
print('Stop Loss   :', trade_status.get('StopLoss', 0))
print('Break Even  :', trade_status.get('BreakEven', False))
print('Trailing SL :', trade_status.get('Trailing', False))
stats = performance.summary()
print('Total Trades :', stats.get('Trades', 0))
print('Wins         :', stats.get('Wins', 0))
print('Losses       :', stats.get('Losses', 0))
print('Win Rate     :', f"{stats.get('WinRate', 0)}%")
reasons = context.get('reasons', [])
unique_reasons = list(dict.fromkeys(reasons))
for reason in unique_reasons:
    print('✓', reason)
idm_reasons = state.idm.get('reasons', [])
for reason in idm_reasons:
    print('•', reason)
