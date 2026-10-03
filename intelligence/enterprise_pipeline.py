"""
Jaguar Quant X Enterprise
Enterprise Pipeline v2.4

Canonical downstream enterprise intelligence pipeline.

Pipeline authority:

Canonical Structural Context
    ->
Institutional Score
    ->
Jaguar Brain V5
    ->
Institutional Decision Matrix
    ->
Trade Planner V2
    ->
Risk Manager V2
    ->
Execution Gateway V2

IMPORTANT:
StructuralZoneEngine is not executed here.

Canonical structural-zone intelligence is established by
Institutional Master before Institutional Confluence.

The downstream enterprise pipeline consumes the already-created
canonical structural contract.
"""

from intelligence.institutional_score import (
    InstitutionalScoreEngine,
)

from intelligence.brain_v5 import (
    JaguarBrainV5,
)

from intelligence.idm import (
    InstitutionalDecisionMatrix,
)

from intelligence.trade_planner_v2 import (
    TradePlannerV2,
)

from intelligence.risk_manager_v2 import (
    RiskManagerV2,
)

from intelligence.execution_gateway_v2 import (
    ExecutionGatewayV2,
)


class EnterprisePipeline:

    name = "Enterprise Pipeline"

    def __init__(self):

        self.engines = [

            InstitutionalScoreEngine(),

            JaguarBrainV5(),

            InstitutionalDecisionMatrix(),

            TradePlannerV2(),

            RiskManagerV2(),

            ExecutionGatewayV2(),

        ]

    def run(self, state):

        for engine in self.engines:

            state = engine.process(
                state
            )

        return state
