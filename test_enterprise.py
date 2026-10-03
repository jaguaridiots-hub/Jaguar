from intelligence.enterprise_pipeline import EnterprisePipeline
from core.market_state import MarketState

state = MarketState()

pipeline = EnterprisePipeline()

state = pipeline.run(state)

print(state.execution)
