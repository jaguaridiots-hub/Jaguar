#!/usr/bin/env python3
import sys
import copy
from core.orchestrator import JaguarOrchestrator
from dashboard.generate import generate_dashboard
from dashboard.portal import generate_portal
from dashboard.portfolio import generate_portfolio_dashboard
from validation.runner import run_validation
from validation.report import generate_report, generate_html_report

# NEW: Import audit
from core.audit import run_blackboard_audit

def run_mode(mode, symbol="BTCUSDT", debug_brain=False):
    app = JaguarOrchestrator()
    state = app.analyze(symbol, "15m", mode=mode, debug_brain=debug_brain)
    generate_dashboard(state, f"dashboard_{symbol}_{mode}.html")
    return state, app

def compare_modes(symbol="BTCUSDT"):
    modes = ["SCALP", "SWING", "CLASSIC"]
    results = {}
    for mode in modes:
        print(f"\n{'='*70}")
        print(f"RUNNING {mode} on {symbol}")
        print("="*70)
        state, _ = run_mode(mode, symbol)
        md = state.master_decision
        results[mode] = {
            "decision": md["decision"],
            "score": md["score"],
            "reasoning": md["reasoning"][-1] if md["reasoning"] else "None"
        }
        print(f"✅ {mode} -> {results[mode]['decision']} (Score: {results[mode]['score']})")
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    for mode, data in results.items():
        print(f"{mode:8} : {data['decision']} (Score: {data['score']})")
        print(f"           Reason: {data['reasoning']}")
    print("="*70)

def run_learning():
    from learning.performance_analyzer import get_performance_summary
    from learning.adaptive_config import update_config_auto
    from learning.advisor import get_llm_advice
    from dashboard.portal import WATCHLIST
    print("\n" + "="*70)
    print("JAGUAR SELF‑LEARNING ENGINE")
    print("="*70)
    print(get_performance_summary())
    if WATCHLIST:
        update_config_auto(WATCHLIST[0])
        print(f"✅ Adaptive config updated for {WATCHLIST[0]}.")
    advice = get_llm_advice()
    print("\n📈 STRATEGY ADVICE FROM LLM:")
    print(advice)

def run_optimization():
    from learning.backtest_optimizer import optimize_parameters
    from dashboard.portal import WATCHLIST
    print("\n" + "="*70)
    print("JAGUAR BACKTEST OPTIMIZER")
    print("="*70)
    if not WATCHLIST:
        print("❌ Watchlist is empty. Add assets to dashboard/portal.py.")
        return
    for symbol in WATCHLIST:
        for mode in ["SCALP", "SWING", "CLASSIC"]:
            print(f"\n🔍 Optimizing {symbol} – {mode}")
            best = optimize_parameters(symbol, mode)
            print(f"✅ Best params for {symbol} {mode}: {best}")
    print("\n💡 Optimized parameters saved to config/optimized_params.json")

def run_backtest(symbol="BTCUSDT", mode="SWING"):
    from core.backtest_engine import BacktestEngine
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    print("\n" + "="*70)
    print(f"BACKTEST: {symbol} – {mode}")
    print("="*70)
    app = JaguarOrchestrator()
    state = app.analyze(symbol, "15m", mode=mode)
    backtest_state = copy.deepcopy(state)
    backtest_state.symbol = symbol
    backtest_state.interval = "15m"
    backtest_state.mode = mode
    registry = EngineRegistry()
    register(registry)
    backtest_engine = BacktestEngine(registry)
    bus = app.bus
    backtest_engine.run(backtest_state, bus)
    result = backtest_state.backtest
    print("\n📊 PERFORMANCE SUMMARY")
    print(f"   Total Trades: {result.total_trades}")
    print(f"   Wins: {result.wins}")
    print(f"   Losses: {result.losses}")
    print(f"   Win Rate: {result.win_rate}%")
    print("="*70)

def run_validation_command(args):
    symbols = args.get("symbols", ["GC=F", "BTCUSDT"])
    modes = args.get("modes", ["SCALP", "SWING", "CLASSIC"])
    results = run_validation(symbols, modes)
    print(generate_report(symbols, modes))
    generate_html_report(symbols, modes)

def run_research_command(args):
    from research.suite import run_research_suite
    symbol = None
    mode = None
    asset_class = None
    if "--symbol" in args:
        idx = args.index("--symbol")
        if len(args) > idx + 1:
            symbol = args[idx + 1]
    if "--mode" in args:
        idx = args.index("--mode")
        if len(args) > idx + 1:
            mode = args[idx + 1].upper()
    if "--asset-class" in args:
        idx = args.index("--asset-class")
        if len(args) > idx + 1:
            asset_class = args[idx + 1]
    run_research_suite(symbol, mode, asset_class)

def main():
    args = sys.argv[1:]
    mode = "SWING"
    symbol = "BTCUSDT"

    # ---- NEW: Blackboard Audit ----
    if "--blackboard-audit" in args:
        run_blackboard_audit()
        return

    # ---- Score Contribution Report ----
    if "--score-report" in args:
        from research.score_analysis import print_full_report
        print_full_report()
        return

    # ---- Research Campaign (single mode) ----
    if "--research-run" in args:
        sym = symbol
        md = mode
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                sym = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                md = args[idx + 1].upper()
        from research.suite import run_research_campaign
        run_research_campaign(symbol=sym, mode=md)
        return

    # ---- Research All Modes (SCALP + SWING + CLASSIC) ----
    if "--research-all-modes" in args:
        sym = symbol
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                sym = args[idx + 1]
        from research.suite import run_all_modes_campaign
        run_all_modes_campaign(symbol=sym)
        return

    # ---- Research Suite ----
    if "--research" in args:
        run_research_command(args)
        return

    # ---- Validation mode ----
    if "--validate" in args:
        symbols = []
        modes = []
        if "--symbols" in args:
            idx = args.index("--symbols")
            if len(args) > idx + 1:
                symbols = args[idx + 1].split(",")
        if "--modes" in args:
            idx = args.index("--modes")
            if len(args) > idx + 1:
                modes = args[idx + 1].split(",")
        if not symbols:
            symbols = ["GC=F", "BTCUSDT"]
        if not modes:
            modes = ["SCALP", "SWING", "CLASSIC"]
        run_validation_command({"symbols": symbols, "modes": modes})
        return

    # ---- Backtest mode (isolated) ----
    if "--backtest" in args:
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        run_backtest(symbol, mode)
        return

    # ---- Portal generation ----
    if "--portal" in args:
        generate_portal()
        return
    if "--portfolio" in args:
        generate_portal()
        return

    # ---- Self‑learning ----
    if "--learn" in args:
        run_learning()
        return

    # ---- Parameter optimization (existing) ----
    if "--optimize" in args:
        run_optimization()
        return

    # ---- Optimize Structure ----
    if "--optimize-structure" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.optimize_structure import run_optimize_structure
        run_optimize_structure(symbol, mode)
        return

    # ---- Optimization Advisor (evidence-based) ----
    if "--optimize-report" in args:
        from research.optimization_advisor import print_optimization_report
        print_optimization_report()
        return

    # ---- Calibration Report ----
    if "--calibration-report" in args:
        from research.evidence_calibration import print_calibration_report
        print_calibration_report()
        return

    # ---- Score Audit ----
    if "--score-audit" in args:
        from research.score_discrimination_audit import print_score_audit_report
        print_score_audit_report()
        return

    # ---- Engine Variability Audit ----
    if "--engine-audit" in args:
        from research.engine_variability_audit import print_engine_audit
        print_engine_audit()
        return

    # ---- Persistence Audit ----
    if "--persistence-audit" in args:
        import tempfile, os
        from research.recorder import set_audit_log_path
        from research.suite import run_research_campaign
        from research.persistence_audit import compare_and_report

        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()

        log_path = os.path.join(tempfile.gettempdir(), f"jaguar_audit_{symbol}_{mode}.jsonl")
        set_audit_log_path(log_path)
        print(f"🔍 Audit log will be saved to {log_path}")
        run_id = run_research_campaign(symbol=symbol, mode=mode)
        compare_and_report(run_id, log_path)
        return

    # ---- Replay Explainability ----
    if "--replay-explain" in args:
        from research.replay_explainability import generate_explainability_report
        run_id = None
        if "--run-id" in args:
            idx = args.index("--run-id")
            if len(args) > idx + 1:
                run_id = args[idx + 1]
        generate_explainability_report(run_id=run_id)
        return

    # ---- Integrity Audit ----
    if "--audit-integrity" in args:
        from research.integrity_audit import audit_run
        run_id = None
        if "--run-id" in args:
            idx = args.index("--run-id")
            if len(args) > idx + 1:
                run_id = args[idx + 1]
        if not run_id:
            print("Please specify --run-id <uuid>")
        else:
            audit_run(run_id)
        return

    # ---- Research Report ----
    if "--research-report" in args:
        from research.research_report import generate_research_report, campaign_list, campaign_compare
        run_id = None
        if "--run-id" in args:
            idx = args.index("--run-id")
            if len(args) > idx + 1:
                run_id = args[idx + 1]
        if "--compare" in args:
            comp = campaign_compare()
            print("Campaign Comparison:")
            for rid, perf in comp.items():
                print(f"  {rid[:8]}...: Trades {perf['total']} WinRate {perf['win_rate']:.1f}% PF {perf['profit_factor']:.2f} Expect {perf['expectancy']:.2f} DD {perf['max_drawdown']:.2f}")
        else:
            generate_research_report(run_id=run_id)
        return

    # ---- Research Validation Report ----
    if "--research-validate" in args:
        from research.research_report import generate_validation_report
        generate_validation_report()
        return

    # ---- Trade Forensics ----
    if "--trade-forensics" in args:
        from research.trade_forensics import run_trade_forensics
        run_trade_forensics(args)
        return

    # ---- Replay Input Trace Audit ----
    if "--replay-trace" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.replay_input_trace import run_input_trace
        run_input_trace(symbol, mode)
        return

    # ---- Verify Replay Trace Samples ----
    if "--verify-trace" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.replay_sample_verification import verify_trace
        verify_trace(symbol, mode)
        return

    # ---- Indicator State Provenance Audit ----
    if "--indicator-provenance" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.indicator_provenance_audit import run_indicator_provenance
        run_indicator_provenance(symbol, mode)
        return

    # ---- Replay Slice Audit ----
    if "--slice-audit" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.replay_slice_audit import run_slice_audit
        run_slice_audit(symbol, mode)
        return

    # ---- Indicator Input Audit ----
    if "--indicator-input-audit" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.indicator_input_audit import run_indicator_input_audit
        run_indicator_input_audit(symbol, mode)
        return

    # ---- Brain Calibration Report ----
    if "--brain-calibration" in args:
        from research.brain_calibration_report import generate_brain_calibration_report
        run_id = None
        if "--run-id" in args:
            idx = args.index("--run-id")
            if len(args) > idx + 1:
                run_id = args[idx + 1]
        generate_brain_calibration_report(run_id=run_id)
        return

    # ---- Staged Brain Prototype (now experimental simulation) ----
    if "--staged-brain" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.experimental_brain import run_experimental_brain
        run_experimental_brain(symbol, mode)
        return

    # ---- Staged Brain Unblocked (bypass execution gates for research) ----
    if "--staged-brain-unblocked" in args:
        symbol = "GC=F"
        mode = "SWING"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()

        from strategy.staged_brain import StagedBrain
        from research.suite import run_research_campaign
        from strategy.execution_trigger_engine import ExecutionTriggerEngine
        from strategy.execution_confirmation_engine import ExecutionConfirmationEngine

        original_trigger = ExecutionTriggerEngine.analyze
        original_confirm_run = ExecutionConfirmationEngine.run

        def patched_trigger(state):
            original_trigger(state)
            if hasattr(state, "execution_trigger"):
                state.execution_trigger["confirmed"] = True
                state.execution_trigger["reasons"] = []
                state.execution_trigger["signal"] = "BUY"
            return state.execution_trigger if hasattr(state, "execution_trigger") else {}

        def patched_confirm(self, state, bus):
            original_confirm_run(self, state, bus)
            if hasattr(state, "execution_confirmation"):
                state.execution_confirmation["confirmed"] = True
                state.execution_confirmation["reasons"] = []
                state.execution_confirmation["signal"] = "STRONG"
            return state

        ExecutionTriggerEngine.analyze = patched_trigger
        ExecutionConfirmationEngine.run = patched_confirm

        try:
            brain = StagedBrain(probability_threshold=0.55)
            run_research_campaign(symbol=symbol, mode=mode, brain_instance=brain)
        finally:
            ExecutionTriggerEngine.analyze = original_trigger
            ExecutionConfirmationEngine.run = original_confirm_run
        return

    # ---- Regime Diagnostic ----
    if "--regime-diagnostic" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.regime_diagnostic import run_regime_diagnostic
        run_regime_diagnostic(symbol, mode)
        return

    # ---- Regime Audit ----
    if "--regime-audit" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.regime_audit import run_regime_audit
        run_regime_audit(symbol, mode)
        return

    # ---- Regime Input Audit ----
    if "--regime-input-audit" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.regime_input_audit import run_regime_input_audit
        run_regime_input_audit(symbol, mode)
        return

    # ---- Feature Predictiveness Audit ----
    if "--feature-predictiveness-audit" in args:
        from research.feature_predictiveness_audit import run_feature_predictiveness_audit
        run_feature_predictiveness_audit()
        return

    # ---- Engine Activation Audit ----
    if "--engine-activation-audit" in args:
        from research.engine_activation_audit import run_engine_activation_audit
        run_engine_activation_audit()
        return

    # ---- Dead Engine Diagnostic ----
    if "--dead-engine-diagnostic" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.dead_engine_diagnostic import run_dead_engine_diagnostic
        run_dead_engine_diagnostic(symbol, mode)
        return

    # ---- Staged Brain Analysis ----
    if "--staged-brain-analyze" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.staged_brain_analysis import run_staged_brain_analysis
        run_staged_brain_analysis(symbol, mode)
        return

    # ---- Staged Brain V2 ----
    if "--staged-brain-v2" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.staged_brain_v2 import run_staged_brain_v2
        run_staged_brain_v2(symbol, mode)
        return

    # ---- Staged Brain V3 ----
    if "--staged-brain-v3" in args:
        from research.staged_brain_v3 import run_staged_brain_v3
        run_staged_brain_v3()
        return

    # ---- Generate Validation Campaigns ----
    if "--research-generate-validation" in args:
        from research.generate_validation import generate_validation_campaigns
        generate_validation_campaigns()
        return

    # ---- Brain Optimizer ----
    if "--brain-optimize" in args:
        if "--generate-profiles" in args:
            from research.brain_optimizer import generate_profiles
            generate_profiles()
        elif "--validate-profiles" in args:
            from research.brain_optimizer import validate_profiles
            validate_profiles()
        elif "--walk-forward" in args:
            from research.brain_optimizer import walk_forward_validation
            walk_forward_validation()
        elif "--diagnose-walk-forward" in args:
            from research.brain_optimizer import diagnose_walk_forward
            diagnose_walk_forward()
        elif "--compare-runs" in args:
            from research.brain_optimizer import compare_campaigns
            compare_campaigns()
        else:
            from research.brain_optimizer import run_brain_optimizer
            run_brain_optimizer()
        return

    # ---- Brain Interaction Analysis ----
    if "--brain-interaction-analysis" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.brain_interaction import run_brain_interaction_analysis
        run_brain_interaction_analysis(symbol, mode)
        return

    # ---- Trade Data Audit ----
    if "--audit-trade-data" in args:
        from research.audit_trade_data import audit_trade_timestamps
        audit_trade_timestamps()
        return

    # ---- Trade Lifecycle Audit ----
    if "--audit-trade-lifecycle" in args:
        from research.audit_trade_lifecycle import audit_trade_lifecycle
        audit_trade_lifecycle()
        return

    # ---- Market Data Audit ----
    if "--audit-market-data" in args:
        symbol = "GC=F"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        from research.audit_market_data import run_market_audit
        run_market_audit(symbol=symbol)
        return

    # ---- Replay Input Audit ----
    if "--audit-replay-input" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.audit_replay_input import run_replay_input_audit
        run_replay_input_audit(symbol, mode)
        return

    # ---- Trade Accounting Audit ----
    if "--audit-trade-accounting" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.audit_trade_accounting import run_accounting_audit
        run_accounting_audit(symbol, mode)
        return

    # ---- Execution Gate Audit ----
    if "--audit-execution-gate" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.audit_execution_gate import run_execution_gate_audit
        run_execution_gate_audit(symbol, mode)
        return

    # ---- Audit Candidate Setups ----
    if "--audit-candidate-setups" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.audit_candidate_setups import run_candidate_audit
        run_candidate_audit(symbol, mode)
        return

    # ---- Execution Gates Audit ----
    if "--audit-execution-gates" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.audit_execution_gates import run_execution_gates_audit
        run_execution_gates_audit(symbol, mode)
        return

    # ---- Threshold Impact Analysis ----
    if "--threshold-impact-analysis" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.threshold_impact_analysis import run_threshold_impact_analysis
        run_threshold_impact_analysis(symbol, mode)
        return

    # ---- Brain Miscalibration Analysis ----
    if "--brain-miscalibration-analysis" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.brain_miscalibration_analysis import run_brain_miscalibration_analysis
        run_brain_miscalibration_analysis(symbol, mode)
        return

    # ---- Engine Ablation Framework ----
    if "--engine-ablation" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.engine_ablation import run_engine_ablation
        run_engine_ablation(symbol, mode)
        return

    # ---- Brain Logistic Comparison ----
    if "--brain-logistic" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.brain_logistic import run_brain_logistic
        run_brain_logistic(symbol, mode)
        return

    # ---- Brain Logistic Validate ----
    if "--brain-logistic-validate" in args:
        from research.brain_logistic_validate import run_brain_logistic_validate
        run_brain_logistic_validate()
        return

    # ---- Decision Quality Audit ----
    if "--decision-quality-audit" in args:
        symbol = "GC=F"
        mode = "SCALP"
        if "--symbol" in args:
            idx = args.index("--symbol")
            if len(args) > idx + 1:
                symbol = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if len(args) > idx + 1:
                mode = args[idx + 1].upper()
        from research.decision_quality_audit import run_decision_quality_audit
        run_decision_quality_audit(symbol, mode)
        return

    # ---- Diagnose Logistic Validation ----
    if "--diagnose-logistic-validation" in args:
        from research.diagnose_logistic_validation import run_diagnose_logistic_validation
        run_diagnose_logistic_validation()
        return

    # ---- Logistic Training Audit ----
    if "--logistic-training-audit" in args:
        from research.logistic_training_audit import run_logistic_training_audit
        run_logistic_training_audit()
        return

    # ---- Dataset Quality Audit ----
    if "--dataset-quality-audit" in args:
        from research.dataset_quality_audit import run_dataset_quality_audit
        run_dataset_quality_audit()
        return

    # ---- Research Dataset Audit ----
    if "--research-audit" in args:
        from research.research_audit import run_research_audit
        run_research_audit()
        return

    # ---- Parse mode and symbol for normal runs ----
    if "--mode" in args:
        idx = args.index("--mode")
        if len(args) > idx + 1:
            mode = args[idx + 1].upper()
    if "--symbol" in args:
        idx = args.index("--symbol")
        if len(args) > idx + 1:
            symbol = args[idx + 1]

    if "--compare" in args:
        compare_modes(symbol)
    else:
        debug_brain = "--debug-brain" in args
        print(f"Running {mode} mode on {symbol}")
        state, app = run_mode(mode, symbol, debug_brain=debug_brain)
        print(f"\n========== JAGUAR ({mode}) ==========")
        from report.console_report import print_report
        print_report(state)
        print("\nEvents:")
        for e in app.events():
            print(e)

if __name__ == "__main__":
    main()
