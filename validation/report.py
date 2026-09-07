# validation/report.py
from .analytics import compute_backtest_metrics, compute_engine_contributions

def generate_validation_report(symbols, modes):
    """Generate a comprehensive validation report."""
    lines = []
    lines.append("="*80)
    lines.append("JAGUAR QUANT X – VALIDATION REPORT")
    lines.append("="*80)

    for symbol in symbols:
        for mode in modes:
            lines.append(f"\n📊 {symbol} | {mode}")
            metrics = compute_backtest_metrics(symbol, mode)
            if not metrics:
                lines.append("   No closed trades.")
                continue
            lines.append(f"   Total Trades        : {metrics['total_trades']}")
            lines.append(f"   Win Rate            : {metrics['win_rate']:.2%}")
            lines.append(f"   Profit Factor       : {metrics['profit_factor']:.2f}")
            lines.append(f"   Net Profit          : {metrics['net_profit']:.2f}")
            lines.append(f"   Average R           : {metrics['avg_r']:.2f}")
            lines.append(f"   Expectancy          : {metrics['expectancy']:.2f}")
            lines.append(f"   Sharpe Ratio        : {metrics['sharpe_ratio']:.2f}")
            lines.append(f"   Sortino Ratio       : {metrics['sortino_ratio']:.2f}")
            lines.append(f"   Max Drawdown        : {metrics['max_drawdown']:.2f}")
            lines.append(f"   Recovery Factor     : {metrics['recovery_factor']:.2f}")

            contribs = compute_engine_contributions(symbol, mode)
            if contribs:
                lines.append("   Engine Contributions (avg):")
                for c in contribs[:5]:
                    lines.append(f"      {c['engine']:15}: {c['avg_contribution']:+.2f}")

    lines.append("\n" + "="*80)
    return "\n".join(lines)

def generate_report(symbols, modes):
    """
    Backward-compatible wrapper for jaguar.py.
    """
    return generate_validation_report(symbols, modes)

def generate_html_report(symbols, modes, output_file="validation_report.html"):
    """Generate an HTML report."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Jaguar Quant X – Validation Report</title></head>
    <body>
        <h1>Jaguar Quant X – Validation Report</h1>
        <p>Report generated for {symbols} across {modes}</p>
        <p>Detailed metrics will be displayed here.</p>
    </body>
    </html>
    """
    with open(output_file, "w") as f:
        f.write(html)
    print(f"✅ HTML report saved to {output_file}")
