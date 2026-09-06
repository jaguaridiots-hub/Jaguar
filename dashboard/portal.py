# dashboard/portal.py – Institutional Portal
import os
from dashboard.generate import generate_dashboard
from dashboard.portfolio import generate_portfolio_dashboard
from core.orchestrator import JaguarOrchestrator
from datetime import datetime
from paper_trading import load_ledger

WATCHLIST = [
    "GC=F", "SI=F", "BTCUSDT", "ETHUSDT",
    "AAPL", "MSFT", "NVDA",
    "RELIANCE.NS", "TCS.NS",
]

MODES = ["SCALP", "SWING", "CLASSIC"]

ASSET_NAMES = {
    "GC=F": "Gold", "SI=F": "Silver",
    "BTCUSDT": "Bitcoin", "ETHUSDT": "Ethereum",
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia",
    "RELIANCE.NS": "Reliance", "TCS.NS": "TCS",
}

CURRENCY_MAP = {
    "GC=F": "$", "SI=F": "$",
    "BTCUSDT": "$", "ETHUSDT": "$",
    "AAPL": "$", "MSFT": "$", "NVDA": "$",
    "RELIANCE.NS": "₹", "TCS.NS": "₹",
}

def generate_portal():
    print("\n" + "="*70)
    print("JAGUAR QUANT X – PORTAL GENERATOR")
    print("="*70)

    results = {}
    for symbol in WATCHLIST:
        print(f"\n📊 Processing {symbol}...")
        results[symbol] = {"name": ASSET_NAMES.get(symbol, symbol)}
        for mode in MODES:
            try:
                app = JaguarOrchestrator()
                state = app.analyze(symbol, "15m", mode=mode)
                md = state.master_decision
                results[symbol][mode] = {
                    "decision": md["decision"],
                    "score": md["score"],
                    "grade": md["grade"],
                    "confidence": md["confidence"],
                    "price": state.price,
                    "reasoning": md["reasoning"][:2] if md["reasoning"] else []
                }
                filename = f"dashboard_{symbol}_{mode}.html"
                generate_dashboard(state, filename)
                print(f"  ✅ {mode}: {md['decision']} (Score: {md['score']})")
            except Exception as e:
                print(f"  ❌ Error on {symbol} {mode}: {e}")
                results[symbol][mode] = {
                    "decision": "ERROR",
                    "score": 0,
                    "grade": "F",
                    "confidence": 0,
                    "price": 0,
                    "reasoning": []
                }

    generate_portfolio_dashboard(results, "portfolio.html")
    generate_index(results)
    print("\n" + "="*70)
    print("✅ PORTAL GENERATED SUCCESSFULLY")
    print("📁 Open index.html in your browser to start.")
    print("="*70)

def generate_index(results):
    total_buy = sum(1 for s in results for m in MODES if results[s].get(m, {}).get("decision") == "BUY")
    total_sell = sum(1 for s in results for m in MODES if results[s].get(m, {}).get("decision") == "SELL")
    total_wait = sum(1 for s in results for m in MODES if results[s].get(m, {}).get("decision") == "WAIT")
    total_reject = sum(1 for s in results for m in MODES if results[s].get(m, {}).get("decision") == "REJECT")
    total_signals = len(results) * len(MODES)

    ledger = load_ledger()
    balance = ledger.get("balance", 0)
    open_positions = [p for p in ledger.get("positions", []) if p.get("status") == "OPEN"]
    total_trades = ledger.get("total_trades", 0)
    wins = ledger.get("wins", 0)
    win_rate = round(wins / total_trades * 100, 2) if total_trades > 0 else 0

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build open positions table rows
    open_rows = ""
    if open_positions:
        for p in open_positions[:20]:  # limit to 20 for display
            curr = CURRENCY_MAP.get(p["symbol"], "$")
            open_rows += f"<tr><td>{p['symbol']}</td><td>{p['side']}</td><td>{curr}{p['entry']:.2f}</td><td>{p['quantity']:.4f}</td><td>OPEN</td></tr>"
        if len(open_positions) > 20:
            open_rows += f"<tr><td colspan='5' style='text-align:center;color:#9CA3AF;'>... and {len(open_positions)-20} more</td></tr>"
    else:
        open_rows = "<tr><td colspan='5' style='text-align:center;color:#9CA3AF;'>No open positions</td></tr>"

    # Build asset grid
    asset_cards = ""
    for symbol, data in results.items():
        name = data["name"]
        decision = data.get("SCALP", {}).get("decision", "WAIT")
        score = data.get("SCALP", {}).get("score", 0)
        price = data.get("SCALP", {}).get("price", 0)
        currency = CURRENCY_MAP.get(symbol, "$")
        badge_class = decision.lower()
        swing = data.get("SWING", {}).get("decision", "WAIT")
        classic = data.get("CLASSIC", {}).get("decision", "WAIT")
        asset_cards += f"""
        <a href="dashboard_{symbol}_SCALP.html" class="asset-card">
            <div class="asset-name">{name}</div>
            <div class="asset-symbol">{symbol}</div>
            <div class="asset-price">{currency}{price:.2f}</div>
            <div class="asset-decision">
                <span class="status-badge {badge_class}">{decision}</span>
                <span style="font-size:12px; color:#8892a2; margin-left:6px;">Score {score}</span>
            </div>
            <div style="margin-top:6px; font-size:11px; color:#5a6272;">
                <span>SWING: {swing}</span>
                <span style="margin-left:8px;">CLASSIC: {classic}</span>
            </div>
        </a>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
    <meta http-equiv="refresh" content="300">
    <title>Jaguar Quant X – Portal</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #05070A; color: #F5F5F5; padding:16px; min-height:100vh; }}
        .container {{ max-width: 1200px; margin:0 auto; }}
        .glass {{ background: rgba(5,7,10,0.65); backdrop-filter:blur(12px); border:1px solid rgba(212,175,55,0.15); border-radius:16px; }}
        .gold {{ color:#D4AF37; }}
        .cyan {{ color:#00D8FF; }}
        .green {{ color:#00FF88; }}
        .red {{ color:#FF4D4D; }}
        .badge {{ display:inline-block; padding:2px 12px; border-radius:20px; font-size:11px; font-weight:600; }}
        .badge.buy {{ background:#00FF88; color:#05070A; }}
        .badge.sell {{ background:#FF4D4D; color:#05070A; }}
        .badge.wait {{ background:#FFD700; color:#05070A; }}
        .badge.reject {{ background:#6c757d; color:#fff; }}
        .header {{ display:flex; align-items:center; justify-content:space-between; padding:12px 24px; background:rgba(5,7,10,0.8); backdrop-filter:blur(12px); border:1px solid rgba(212,175,55,0.2); border-radius:16px; margin-bottom:20px; flex-wrap:wrap; gap:12px; }}
        .logo-main {{ font-size:24px; font-weight:900; letter-spacing:1px; }}
        .logo-main span {{ color:#D4AF37; }}
        .logo-tagline {{ font-size:10px; color:#9CA3AF; letter-spacing:2px; }}
        .logo-tagline span {{ color:#D4AF37; }}
        .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-bottom:20px; }}
        .card {{ background:rgba(5,7,10,0.6); backdrop-filter:blur(8px); border:1px solid rgba(212,175,55,0.1); border-radius:16px; padding:14px 16px; transition:0.2s; }}
        .card:hover {{ border-color:rgba(212,175,55,0.3); }}
        .card-title {{ font-size:10px; text-transform:uppercase; color:#9CA3AF; letter-spacing:0.5px; margin-bottom:4px; }}
        .card-value {{ font-size:20px; font-weight:600; color:#F5F5F5; }}
        .section-title {{ font-size:14px; font-weight:600; color:#aab2c2; margin:20px 0 10px 0; border-bottom:1px solid rgba(212,175,55,0.1); padding-bottom:6px; }}
        .section-title .gold {{ color:#D4AF37; }}
        .asset-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; margin-bottom:20px; }}
        .asset-card {{ background:rgba(5,7,10,0.6); backdrop-filter:blur(8px); border-radius:16px; padding:14px 16px; border:1px solid rgba(212,175,55,0.1); transition:0.2s; text-decoration:none; color:#F5F5F5; }}
        .asset-card:hover {{ border-color:rgba(212,175,55,0.3); transform:translateY(-3px); box-shadow:0 8px 30px rgba(212,175,55,0.05); }}
        .asset-name {{ font-size:16px; font-weight:600; }}
        .asset-symbol {{ font-size:11px; color:#9CA3AF; }}
        .asset-price {{ font-size:18px; font-weight:700; margin:4px 0; }}
        .asset-decision {{ font-size:13px; margin-top:6px; }}
        .status-badge {{ padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600; color:#05070A; display:inline-block; }}
        .status-badge.buy {{ background:#00FF88; }}
        .status-badge.sell {{ background:#FF4D4D; }}
        .status-badge.wait {{ background:#FFD700; }}
        .status-badge.reject {{ background:#6c757d; color:#fff; }}
        .status-badge.error {{ background:#e91e63; color:#fff; }}
        .trade-table {{ width:100%; border-collapse:collapse; font-size:13px; background:rgba(5,7,10,0.4); border-radius:12px; overflow:hidden; }}
        .trade-table th {{ background:rgba(212,175,55,0.08); color:#9CA3AF; font-size:10px; text-transform:uppercase; padding:8px 12px; text-align:left; }}
        .trade-table td {{ padding:6px 12px; border-bottom:1px solid rgba(255,255,255,0.04); }}
        .trade-table tr:hover td {{ background:rgba(212,175,55,0.04); }}
        .footer {{ margin-top:30px; text-align:center; font-size:11px; color:#9CA3AF; border-top:1px solid rgba(212,175,55,0.08); padding-top:16px; }}
        .flex {{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; }}
        .status-dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; animation:pulse 1.5s infinite; margin-right:6px; background:#00FF88; }}
        @keyframes pulse {{ 0%{{opacity:0.6;transform:scale(0.95)}} 50%{{opacity:1;transform:scale(1.1)}} 100%{{opacity:0.6;transform:scale(0.95)}} }}
        @media (max-width:640px) {{ .asset-grid {{ grid-template-columns:1fr 1fr; }} .grid {{ grid-template-columns:1fr 1fr; }} .header {{ flex-direction:column; align-items:flex-start; }} }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <div class="logo-main">JAGUAR <span>QUANT X</span></div>
            <div class="logo-tagline">DATA <span>·</span> DISCIPLINE <span>·</span> DOMINATE</div>
        </div>
        <div>
            <span class="badge" style="background:rgba(212,175,55,0.2);color:#D4AF37;"><i class="fas fa-sync-alt"></i> Auto-refresh 5m</span>
            <span class="badge" style="background:rgba(0,216,255,0.15);color:#00D8FF;"><i class="fas fa-layer-group"></i> Portal</span>
        </div>
    </div>

    <div style="display:flex; justify-content:space-between; margin-bottom:16px;">
        <div class="flex"><span class="status-dot"></span><span style="font-size:13px;color:#9CA3AF;">Live</span></div>
        <span style="font-size:12px;color:#5a6272;">{now}</span>
    </div>

    <div class="grid">
        <div class="card"><div class="card-title">Total Signals</div><div class="card-value">{total_signals}</div></div>
        <div class="card"><div class="card-title">BUY</div><div class="card-value" style="color:#00FF88;">{total_buy}</div></div>
        <div class="card"><div class="card-title">SELL</div><div class="card-value" style="color:#FF4D4D;">{total_sell}</div></div>
        <div class="card"><div class="card-title">WAIT</div><div class="card-value" style="color:#FFD700;">{total_wait}</div></div>
        <div class="card"><div class="card-title">REJECT</div><div class="card-value" style="color:#6c757d;">{total_reject}</div></div>
    </div>

    <div class="section-title"><span class="gold">●</span> Paper Trading</div>
    <div class="grid">
        <div class="card"><div class="card-title">Balance</div><div class="card-value">${balance:,.2f}</div></div>
        <div class="card"><div class="card-title">Open Positions</div><div class="card-value">{len(open_positions)}</div></div>
        <div class="card"><div class="card-title">Total Trades</div><div class="card-value">{total_trades}</div></div>
        <div class="card"><div class="card-title">Win Rate</div><div class="card-value">{win_rate}%</div></div>
    </div>

    <div class="section-title"><span class="gold">●</span> Open Positions</div>
    <div style="overflow-x:auto; margin-bottom:20px;">
        <table class="trade-table">
            <thead><tr><th>Symbol</th><th>Side</th><th>Entry</th><th>Qty</th><th>Status</th></tr></thead>
            <tbody>{open_rows}</tbody>
        </table>
    </div>

    <div class="section-title"><span class="gold">●</span> Portfolio</div>
    <div style="margin-bottom:16px;">
        <a href="portfolio.html" style="color:#D4AF37; text-decoration:none; font-weight:600;">
            <i class="fas fa-chart-pie"></i> View full portfolio breakdown
        </a>
    </div>

    <div class="section-title"><span class="gold">●</span> Assets</div>
    <div class="asset-grid">
        {asset_cards}
    </div>

    <div class="footer">
        <span class="gold">◆</span> Jaguar Quant X <span class="gold">◆</span> Institutional Trading Intelligence OS <span class="gold">◆</span> v2.0
    </div>
</div>
</body>
</html>"""
    with open("index.html", "w") as f:
        f.write(html)
    print("✅ Main index.html generated.")
