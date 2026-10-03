# research/report_final.py
import json
from datetime import datetime

def generate_research_report(stats, engine_contrib=None, run_id=None, elapsed=0, completed=0, failed=0, output_file="research_report.html"):
    """Generate an institutional HTML research report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    overall = stats.get('overall', {})
    by_symbol = stats.get('by_symbol', {})
    by_mode = stats.get('by_mode', {})
    by_regime = stats.get('by_regime', {})
    by_asset_class = stats.get('by_asset_class', {})

    # Top 10 assets by net profit
    sorted_assets = sorted(by_symbol.items(), key=lambda x: x[1].get('net_profit', 0), reverse=True)
    top_assets = sorted_assets[:10]
    bottom_assets = sorted_assets[-10:] if len(sorted_assets) > 10 else []

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Jaguar Quant X – Research Report v1.0</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #05070A; color: #F5F5F5; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .card {{ background: rgba(5,7,10,0.6); backdrop-filter: blur(8px); border: 1px solid rgba(212,175,55,0.1); border-radius: 16px; padding: 18px 20px; margin-bottom: 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }}
            .gold {{ color: #D4AF37; }}
            .cyan {{ color: #00D8FF; }}
            .green {{ color: #00FF88; }}
            .red {{ color: #FF4D4D; }}
            .metric-value {{ font-size: 24px; font-weight: 700; color: #F5F5F5; }}
            .metric-label {{ font-size: 12px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }}
            th {{ background: rgba(212,175,55,0.08); color: #D4AF37; padding: 8px 12px; text-align: left; }}
            td {{ padding: 6px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); }}
            tr:hover td {{ background: rgba(212,175,55,0.04); }}
            .tag {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
            .tag.buy {{ background: #00FF88; color: #05070A; }}
            .tag.sell {{ background: #FF4D4D; color: #05070A; }}
            .tag.wait {{ background: #FFD700; color: #05070A; }}
            .tag.reject {{ background: #6c757d; color: #fff; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 11px; color: #5a6272; border-top: 1px solid rgba(212,175,55,0.08); padding-top: 16px; }}
            .footer .gold {{ color: #D4AF37; }}
            .section-title {{ font-size: 16px; font-weight: 600; color: #aab2c2; margin: 20px 0 10px 0; border-bottom: 1px solid rgba(212,175,55,0.08); padding-bottom: 6px; }}
            .section-title .gold {{ color: #D4AF37; }}
            .badge {{ display: inline-block; background: rgba(212,175,55,0.1); color: #D4AF37; padding: 2px 10px; border-radius: 12px; font-size: 11px; }}
            .run-info {{ color: #8892a2; font-size: 13px; }}
    </style>
    </head>
    <body>
        <div class="container">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div>
                    <h1 class="gold" style="font-size:32px; margin:0;">JAGUAR QUANT X</h1>
                    <h2 class="cyan" style="margin:0; font-weight:400;">Research Report v1.0</h2>
                </div>
                <div class="badge">Run ID: {run_id or 'N/A'}</div>
            </div>
            <div class="run-info">
                <span>Generated: {now}</span>
                <span style="margin-left:16px;">Elapsed: {elapsed:.2f}s</span>
                <span style="margin-left:16px;">Runs: {completed}</span>
                <span style="margin-left:16px;">Failed: {failed}</span>
            </div>

            <!-- Overall Performance -->
            <div class="card">
                <h3 class="gold">Overall Performance</h3>
                <div class="grid">
                    <div><div class="metric-label">Total Trades</div><div class="metric-value">{overall.get('total_trades', 0)}</div></div>
                    <div><div class="metric-label">Win Rate</div><div class="metric-value" style="color:{ '#00FF88' if overall.get('win_rate', 0) > 0.4 else '#FFD700' if overall.get('win_rate', 0) > 0.3 else '#FF4D4D' };">{overall.get('win_rate', 0)*100:.2f}%</div></div>
                    <div><div class="metric-label">Profit Factor</div><div class="metric-value" style="color:{ '#00FF88' if overall.get('profit_factor', 0) > 1.5 else '#FFD700' if overall.get('profit_factor', 0) > 1.0 else '#FF4D4D' };">{overall.get('profit_factor', 0):.2f}</div></div>
                    <div><div class="metric-label">Net Profit</div><div class="metric-value" style="color:{ '#00FF88' if overall.get('net_profit', 0) > 0 else '#FF4D4D' };">{overall.get('net_profit', 0):.2f}</div></div>
                    <div><div class="metric-label">Expectancy</div><div class="metric-value">{overall.get('expectancy', 0):.2f}</div></div>
                    <div><div class="metric-label">Sharpe Ratio</div><div class="metric-value">{overall.get('sharpe_ratio', 0):.2f}</div></div>
                    <div><div class="metric-label">Max Drawdown</div><div class="metric-value" style="color:#FF4D4D;">{overall.get('max_drawdown', 0):.2f}</div></div>
                    <div><div class="metric-label">Recovery Factor</div><div class="metric-value">{overall.get('recovery_factor', 0):.2f}</div></div>
                </div>
            </div>

            <!-- Top Assets -->
            <div class="card">
                <h3 class="gold">Top 10 Assets</h3>
                <table>
                    <tr><th>Asset</th><th>Trades</th><th>Win Rate</th><th>Profit Factor</th><th>Net Profit</th><th>Avg R</th></tr>
                    {''.join(f"<tr><td><strong>{sym}</strong></td><td>{data.get('total_trades', 0)}</td><td>{data.get('win_rate', 0)*100:.1f}%</td><td>{data.get('profit_factor', 0):.2f}</td><td style='color:{ '#00FF88' if data.get('net_profit', 0) > 0 else '#FF4D4D' };'>{data.get('net_profit', 0):.2f}</td><td>{data.get('avg_r', 0):.2f}</td></tr>" for sym, data in top_assets)}
                </table>
            </div>

            <!-- By Mode -->
            <div class="card">
                <h3 class="gold">Performance by Mode</h3>
                <table>
                    <tr><th>Mode</th><th>Trades</th><th>Win Rate</th><th>Profit Factor</th><th>Net Profit</th><th>Avg R</th></tr>
                    {''.join(f"<tr><td><strong>{mode}</strong></td><td>{data.get('total_trades', 0)}</td><td>{data.get('win_rate', 0)*100:.1f}%</td><td>{data.get('profit_factor', 0):.2f}</td><td style='color:{ '#00FF88' if data.get('net_profit', 0) > 0 else '#FF4D4D' };'>{data.get('net_profit', 0):.2f}</td><td>{data.get('avg_r', 0):.2f}</td></tr>" for mode, data in by_mode.items())}
                </table>
            </div>

            <!-- By Regime -->
            <div class="card">
                <h3 class="gold">Performance by Market Regime</h3>
                <table>
                    <tr><th>Regime</th><th>Trades</th><th>Win Rate</th><th>Profit Factor</th><th>Net Profit</th></tr>
                    {''.join(f"<tr><td><strong>{regime}</strong></td><td>{data.get('total_trades', 0)}</td><td>{data.get('win_rate', 0)*100:.1f}%</td><td>{data.get('profit_factor', 0):.2f}</td><td style='color:{ '#00FF88' if data.get('net_profit', 0) > 0 else '#FF4D4D' };'>{data.get('net_profit', 0):.2f}</td></tr>" for regime, data in by_regime.items())}
                </table>
            </div>

            <!-- Engine Contributions -->
            <div class="card">
                <h3 class="gold">Engine Contributions</h3>
                <table>
                    <tr><th>Engine</th><th>Avg Contribution</th><th>Count</th><th>Win Rate</th></tr>
                    {''.join(f"<tr><td><strong>{e.get('engine', 'Unknown')}</strong></td><td>{e.get('avg_contribution', 0):+.2f}</td><td>{e.get('count', 0)}</td><td>{e.get('win_rate', 0)*100:.1f}%</td></tr>" for e in (engine_contrib or [])[:10])}
                </table>
            </div>

            <!-- Bottom Assets -->
            {'' if not bottom_assets else f'''
            <div class="card">
                <h3 class="gold">Bottom 10 Assets</h3>
                <table>
                    <tr><th>Asset</th><th>Trades</th><th>Win Rate</th><th>Profit Factor</th><th>Net Profit</th></tr>
                    {''.join(f"<tr><td><strong>{sym}</strong></td><td>{data.get('total_trades', 0)}</td><td>{data.get('win_rate', 0)*100:.1f}%</td><td>{data.get('profit_factor', 0):.2f}</td><td style='color:{ '#00FF88' if data.get('net_profit', 0) > 0 else '#FF4D4D' };'>{data.get('net_profit', 0):.2f}</td></tr>" for sym, data in bottom_assets)}
                </table>
            </div>
            '''}

            <div class="footer">
                <span class="gold">◆</span> Jaguar Quant X <span class="gold">◆</span> Institutional Research <span class="gold">◆</span> v1.0
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_file, "w") as f:
        f.write(html)
    print(f"✅ Research report saved to {output_file}")
