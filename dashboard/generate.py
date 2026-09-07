# dashboard/generate.py – Institutional AI Command Center (FINAL)
import json
from datetime import datetime
from string import Template
from paper_trading import load_ledger, get_open_trades, get_closed_trades

CURRENCY_MAP = {
    "GC=F": "$", "SI=F": "$",
    "BTCUSDT": "$", "ETHUSDT": "$",
    "AAPL": "$", "MSFT": "$", "NVDA": "$",
    "RELIANCE.NS": "₹", "TCS.NS": "₹", "NIFTY": "₹",
}

def generate_dashboard(state, output_file="dashboard.html"):
    # ---- DIAGNOSTIC ----
    print("PASSED STATE ID :", id(state))
    passed_dec = getattr(state, "master_decision", None)
    print("PASSED DECISION :", passed_dec.get("decision") if passed_dec else None)
    # ---- end diagnostic ----

    md = state.master_decision if hasattr(state, "master_decision") else {}
    trade = state.trade_plan if hasattr(state, "trade_plan") else {}
    risk = state.risk if hasattr(state, "risk") else {}
    components = md.get("components", {})

    # ---- DIAGNOSTIC: DASHBOARD INPUT ----
    print("\n========== DASHBOARD INPUT ==========")
    print("STATE ID :", id(state))
    print("MASTER DECISION RAW:")
    print(md)
    print("====================================\n")
    # -----------------------------------------

    decision = md.get("decision", "WAIT")
    score = md.get("score", 0)
    grade = md.get("grade", "F")
    confidence = md.get("confidence", 0)
    priority = md.get("priority", "LOW")
    execution = md.get("execution", "BLOCKED")
    reasons = md.get("reasons", [])
    reasoning = md.get("reasoning", [])

    entry = trade.get("entry", "N/A") if trade else "N/A"
    stop = trade.get("stop", "N/A") if trade else "N/A"
    tp1 = trade.get("tp1", "N/A") if trade else "N/A"
    tp2 = trade.get("tp2", "N/A") if trade else "N/A"
    tp3 = trade.get("tp3", "N/A") if trade else "N/A"
    risk_reward = trade.get("risk_reward", "N/A") if trade else "N/A"

    capital = risk.get("capital", 100000)
    position_size = risk.get("position_size", 0)
    exposure = risk.get("exposure", 0)
    risk_status = risk.get("status", "NO TRADE")
    risk_percent = risk.get("risk_percent", 1.0)

    ai_score = components.get("ai_score", 0)
    prob_score = components.get("prob_score", 0)
    smc = components.get("smc_signal", "NEUTRAL")
    regime = components.get("regime", "NEUTRAL")
    structure = components.get("structure", "NEUTRAL")

    symbol = getattr(state, "symbol", "BTCUSDT")
    mode = getattr(state, "mode", "SWING")
    price = getattr(state, "price", 0)
    high = getattr(state, "high", 0)
    low = getattr(state, "low", 0)
    volume = getattr(state, "volume", 0)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    currency = CURRENCY_MAP.get(symbol, "$")

    ledger = load_ledger()
    balance = ledger.get("balance", 100000)
    total_trades = ledger.get("total_trades", 0)
    wins = ledger.get("wins", 0)
    win_rate = round(wins / total_trades * 100, 2) if total_trades > 0 else 0
    net_profit = balance - 100000

    open_trades = get_open_trades()
    closed_trades = get_closed_trades()
    open_count = len(open_trades)
    closed_count = len(closed_trades)
    total_profit = sum(p["pnl"] for p in closed_trades if p["pnl"] > 0)
    total_loss = sum(p["pnl"] for p in closed_trades if p["pnl"] < 0)
    profit_count = len([p for p in closed_trades if p["pnl"] > 0])
    loss_count = len([p for p in closed_trades if p["pnl"] < 0])

    unrealized_pnl = sum(
        (price - p["entry"]) * p["quantity"] if p["side"] == "BUY" else (p["entry"] - price) * p["quantity"]
        for p in open_trades if p["symbol"] == symbol
    )

    asset_name = {
        "GC=F": "Gold", "SI=F": "Silver", "BTCUSDT": "Bitcoin",
        "ETHUSDT": "Ethereum", "AAPL": "Apple", "MSFT": "Microsoft",
        "NVDA": "Nvidia", "RELIANCE.NS": "Reliance", "TCS.NS": "TCS"
    }.get(symbol, symbol)

    # ---- SMC Flags ----
    smc_flags = {
        "BOS": "✅" if structure in ["BREAKOUT", "BOS_CONFIRMED"] else "❌",
        "CHoCH": "✅" if getattr(state, "structure", {}).get("choch", {}).get("signal") == "BULLISH" else "❌",
        "Liquidity": "✅" if getattr(state, "liquidity_engine", {}).get("sweep", False) else "❌",
        "Order Block": "✅" if getattr(state, "order_block_engine", {}).get("active", False) else "❌",
        "FVG": "✅" if getattr(state, "fvg_engine", {}).get("active", False) else "❌",
    }
    if not any(v == "✅" for v in smc_flags.values()):
        smc_flags["Liquidity"] = "✅" if getattr(state, "liquidity", {}).get("sweep", False) else "❌"
        smc_flags["Order Block"] = "✅" if getattr(state, "order_block", {}).get("active", False) else "❌"
        smc_flags["FVG"] = "✅" if getattr(state, "fvg", {}).get("active", False) else "❌"

    # ---- Build open rows ----
    open_rows = ""
    if open_trades:
        for p in open_trades:
            sym_curr = CURRENCY_MAP.get(p["symbol"], "$")
            pnl = (price - p["entry"]) * p["quantity"] if p["side"] == "BUY" else (p["entry"] - price) * p["quantity"]
            color = "#00FF88" if pnl >= 0 else "#FF4D4D"
            open_rows += f"""
            <tr>
                <td>{p["symbol"]}</td>
                <td>{p["side"]}</td>
                <td>{sym_curr}{p["entry"]:.2f}</td>
                <td>{p["quantity"]:.4f}</td>
                <td>{sym_curr}{p["stop"]:.2f}</td>
                <td>{sym_curr}{p["tp"]:.2f}</td>
                <td id="price_{p["symbol"]}">{currency}{price:.2f}</td>
                <td style="color:{color};">{currency}{pnl:.2f}</td>
            </tr>
            """
    else:
        open_rows = '<tr><td colspan="8" style="text-align:center;color:#9CA3AF;">No open positions</td></tr>'

    closed_rows = ""
    if closed_trades:
        for p in closed_trades:
            sym_curr = CURRENCY_MAP.get(p["symbol"], "$")
            color = "#00FF88" if p["pnl"] >= 0 else "#FF4D4D"
            result_label = "WIN" if p["pnl"] >= 0 else "LOSS"
            closed_rows += f"""
            <tr>
                <td>{p["symbol"]}</td>
                <td>{p["side"]}</td>
                <td>{sym_curr}{p["entry"]:.2f}</td>
                <td>{sym_curr}{p["exit"]:.2f}</td>
                <td>{p["quantity"]:.4f}</td>
                <td style="color:{color};">{currency}{p["pnl"]:.2f}</td>
                <td><span class="tag {result_label.lower()}">{result_label}</span></td>
            </tr>
            """
    else:
        closed_rows = '<tr><td colspan="7" style="text-align:center;color:#9CA3AF;">No closed trades</td></tr>'

    # ---- State JSON ----
    state_json = json.dumps({
        "symbol": symbol,
        "asset_name": asset_name,
        "decision": decision,
        "score": score,
        "grade": grade,
        "confidence": confidence,
        "priority": priority,
        "execution": execution,
        "reasons": reasons,
        "reasoning": reasoning,
        "entry": entry,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "risk_reward": risk_reward,
        "capital": capital,
        "position_size": position_size,
        "exposure": exposure,
        "risk_status": risk_status,
        "risk_percent": risk_percent,
        "ai_score": ai_score,
        "prob_score": prob_score,
        "smc": smc,
        "regime": regime,
        "structure": structure,
        "mode": mode,
        "price": price,
        "high": high,
        "low": low,
        "volume": volume,
        "balance": balance,
        "total_trades": total_trades,
        "win_rate": win_rate,
        "net_profit": net_profit,
        "unrealized_pnl": unrealized_pnl,
        "open_trades": open_trades,
        "closed_trades": closed_trades,
        "total_profit": total_profit,
        "total_loss": total_loss,
        "profit_count": profit_count,
        "loss_count": loss_count,
        "smc_flags": smc_flags,
        "currency": currency,
    })

    # ---- Prepare data ----
    decision_bg = "#00FF88" if decision in ["BUY", "SELL"] else "#6c757d"
    hero_decision = "ENTER LONG" if decision == "BUY" else "ENTER SHORT" if decision == "SELL" else "WAIT" if decision == "WAIT" else "NO TRADE"
    hero_sub = "High Probability Opportunity" if decision in ["BUY", "SELL"] else "Awaiting Clear Signal"
    first_reason = reasoning[0] if reasoning else "No specific reasoning."
    ai_brain_items = "\n".join(f'<li style="padding:4px 0; font-size:14px; color:#E5E7EB; border-bottom:1px solid rgba(255,255,255,0.04);"><span style="color:#D4AF37;">▸</span> {r}</li>' for r in reasoning[:5])
    if not reasoning:
        ai_brain_items = '<li style="color:#9CA3AF;">No AI analysis available.</li>'
    smc_badges = "\n".join(f'<span class="smc-badge {"active" if flag=="✅" else "inactive"}">{name} {flag}</span>' for name, flag in smc_flags.items())
    risk_color = "#00FF88" if risk_status == "SAFE" else "#FF4D4D"
    win_color = "#00FF88" if win_rate >= 50 else "#FF4D4D"
    profit_color = "#00FF88" if net_profit >= 0 else "#FF4D4D"
    upnl_color = "#00FF88" if unrealized_pnl >= 0 else "#FF4D4D"
    reason_items = "\n".join(f'<li>{r}</li>' for r in reasoning)
    reasons_str = ", ".join(reasons)

    # ---- DIAGNOSTIC: HTML VALUES ----
    print("\n========== HTML VALUES ==========")
    print("decision   =", decision)
    print("score      =", score)
    print("confidence =", confidence)
    print("reasoning  =", reasoning)
    print("trade      =", trade)
    print("risk       =", risk)
    print("=================================\n")
    # -----------------------------------------

    # ---- HTML Template ----
    template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
    <meta http-equiv="refresh" content="60">
    <title>Jaguar Quant X – $asset_name</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family: 'Inter', sans-serif; background: #05070A; color: #F5F5F5; padding:16px; min-height:100vh; }
        .container { max-width: 1200px; margin:0 auto; }
        .gold { color:#D4AF37; }
        .cyan { color:#00D8FF; }
        .green { color:#00FF88; }
        .red { color:#FF4D4D; }
        .badge { display:inline-block; padding:2px 12px; border-radius:20px; font-size:11px; font-weight:600; }
        .badge.buy { background:#00FF88; color:#05070A; }
        .badge.sell { background:#FF4D4D; color:#05070A; }
        .badge.wait { background:#FFD700; color:#05070A; }
        .badge.reject { background:#6c757d; color:#fff; }
        .header { display:flex; align-items:center; justify-content:space-between; padding:12px 24px; background:rgba(5,7,10,0.8); backdrop-filter:blur(12px); border:1px solid rgba(212,175,55,0.2); border-radius:16px; margin-bottom:20px; flex-wrap:wrap; gap:12px; }
        .logo-main { font-size:24px; font-weight:900; letter-spacing:1px; }
        .logo-main span { color:#D4AF37; }
        .logo-tagline { font-size:10px; color:#9CA3AF; letter-spacing:2px; }
        .logo-tagline span { color:#D4AF37; }
        .nav { display:flex; gap:16px; flex-wrap:wrap; }
        .nav a { color:#9CA3AF; text-decoration:none; font-size:13px; font-weight:500; padding:4px 0; border-bottom:2px solid transparent; transition:0.2s; }
        .nav a:hover, .nav a.active { color:#D4AF37; border-bottom-color:#D4AF37; }
        .hero { background:linear-gradient(145deg,rgba(212,175,55,0.06),rgba(0,216,255,0.03)); border:1px solid rgba(212,175,55,0.2); border-radius:20px; padding:24px 28px; margin-bottom:24px; position:relative; overflow:hidden; }
        .hero-decision { font-size:28px; font-weight:700; color:#D4AF37; text-shadow:0 0 40px rgba(212,175,55,0.15); }
        .hero-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:16px; margin-top:16px; }
        .hero-item .label { font-size:10px; text-transform:uppercase; color:#9CA3AF; letter-spacing:0.5px; }
        .hero-item .value { font-size:22px; font-weight:700; }
        .hero-reason { font-size:14px; color:#9CA3AF; margin-top:12px; line-height:1.5; }
        .card { background:rgba(5,7,10,0.6); backdrop-filter:blur(8px); border:1px solid rgba(212,175,55,0.1); border-radius:16px; padding:18px 20px; transition:0.2s; }
        .card:hover { border-color:rgba(212,175,55,0.3); }
        .card-title { font-size:11px; text-transform:uppercase; color:#9CA3AF; letter-spacing:0.5px; margin-bottom:6px; }
        .card-value { font-size:20px; font-weight:600; color:#F5F5F5; }
        .grid-2 { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:20px; }
        .grid-3 { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; margin-bottom:20px; }
        .grid-4 { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:16px; margin-bottom:20px; }
        .smc-badge { display:inline-flex; align-items:center; gap:4px; padding:4px 14px; border-radius:20px; font-size:12px; font-weight:600; background:rgba(0,216,255,0.06); border:1px solid rgba(0,216,255,0.1); color:#00D8FF; }
        .smc-badge.active { background:rgba(0,255,136,0.1); border-color:#00FF88; color:#00FF88; }
        .smc-badge.inactive { opacity:0.3; }
        .trade-table { width:100%; border-collapse:collapse; font-size:13px; background:rgba(5,7,10,0.4); border-radius:12px; overflow:hidden; }
        .trade-table th { background:rgba(212,175,55,0.08); color:#9CA3AF; font-size:10px; text-transform:uppercase; padding:8px 12px; text-align:left; }
        .trade-table td { padding:6px 12px; border-bottom:1px solid rgba(255,255,255,0.04); }
        .trade-table tr:hover td { background:rgba(212,175,55,0.04); }
        .tag { display:inline-block; padding:1px 8px; border-radius:10px; font-size:10px; font-weight:600; }
        .tag.win { background:#00FF88; color:#05070A; }
        .tag.loss { background:#FF4D4D; color:#05070A; }
        .chart-container { background:rgba(5,7,10,0.4); border-radius:16px; padding:16px; border:1px solid rgba(212,175,55,0.08); margin-bottom:20px; }
        .chart-container canvas { width:100% !important; height:180px !important; }
        .reason-list { list-style:none; padding:0; }
        .reason-list li { padding:4px 0; font-size:13px; color:#E5E7EB; border-bottom:1px solid rgba(255,255,255,0.04); }
        .reason-list li::before { content:"▸ "; color:#D4AF37; }
        .footer { margin-top:30px; text-align:center; font-size:11px; color:#9CA3AF; border-top:1px solid rgba(212,175,55,0.08); padding-top:16px; }
        .status-dot { display:inline-block; width:10px; height:10px; border-radius:50%; animation:pulse 1.5s infinite; margin-right:6px; background:#00FF88; }
        @keyframes pulse { 0%{opacity:0.6;transform:scale(0.95)} 50%{opacity:1;transform:scale(1.1)} 100%{opacity:0.6;transform:scale(0.95)} }
        .flex { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
        .chat-toggle { position:fixed; bottom:20px; right:20px; width:60px; height:60px; border-radius:50%; background:linear-gradient(135deg,#D4AF37,#B8960F); border:none; color:#05070A; font-size:28px; box-shadow:0 4px 30px rgba(212,175,55,0.4); cursor:pointer; z-index:1000; transition:0.3s; display:flex; align-items:center; justify-content:center; }
        .chat-toggle:hover { transform:scale(1.05); box-shadow:0 4px 40px rgba(212,175,55,0.6); }
        .chat-panel { position:fixed; bottom:90px; right:20px; width:360px; max-width:calc(100vw - 40px); max-height:480px; background:rgba(5,7,10,0.9); backdrop-filter:blur(16px); border:1px solid rgba(212,175,55,0.2); border-radius:16px; box-shadow:0 8px 40px rgba(0,0,0,0.8); z-index:999; display:none; flex-direction:column; overflow:hidden; }
        .chat-panel.open { display:flex; }
        .chat-header { padding:12px 16px; background:rgba(212,175,55,0.06); border-bottom:1px solid rgba(212,175,55,0.1); font-weight:600; color:#F5F5F5; display:flex; justify-content:space-between; align-items:center; }
        .chat-header i { color:#D4AF37; }
        .chat-header .close { background:none; border:none; color:#9CA3AF; font-size:18px; cursor:pointer; }
        .chat-messages { flex:1; overflow-y:auto; padding:12px 16px; max-height:280px; }
        .chat-message { margin-bottom:10px; padding:8px 12px; border-radius:12px; max-width:85%; font-size:13px; line-height:1.4; }
        .chat-message.user { background:rgba(0,216,255,0.1); color:#F5F5F5; align-self:flex-end; margin-left:auto; border-bottom-right-radius:4px; }
        .chat-message.bot { background:rgba(212,175,55,0.08); color:#F5F5F5; align-self:flex-start; border-left:2px solid #D4AF37; border-bottom-left-radius:4px; }
        .chat-input-area { display:flex; align-items:center; padding:8px 12px; border-top:1px solid rgba(212,175,55,0.1); background:rgba(0,0,0,0.2); gap:8px; }
        .chat-input-area input { flex:1; background:rgba(255,255,255,0.04); border:1px solid rgba(212,175,55,0.1); border-radius:20px; padding:8px 14px; color:#F5F5F5; font-size:13px; outline:none; }
        .chat-input-area input:focus { border-color:#D4AF37; }
        .chat-input-area button { background:#D4AF37; border:none; color:#05070A; width:36px; height:36px; border-radius:50%; font-size:16px; cursor:pointer; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .chat-input-area button.mic { background:rgba(255,255,255,0.05); color:#F5F5F5; }
        .chat-input-area button.mic.listening { background:#FF4D4D; animation:pulse 0.8s infinite; }
        @media (max-width:640px) {
            .hero-decision { font-size:22px; }
            .header { flex-direction:column; align-items:flex-start; }
            .nav { width:100%; justify-content:space-around; }
        }
    </style>
</head>
<body>
<div class="container">

    <!-- HEADER -->
    <div class="header">
        <div>
            <div class="logo-main">JAGUAR <span>QUANT X</span></div>
            <div class="logo-tagline">DATA <span>·</span> DISCIPLINE <span>·</span> DOMINATE</div>
        </div>
        <div class="flex">
            <span class="badge buy" style="background:$decision_bg;">$decision</span>
            <span class="badge" style="background:rgba(212,175,55,0.2);color:#D4AF37;">$symbol</span>
            <span class="badge" style="background:rgba(0,216,255,0.15);color:#00D8FF;">$mode</span>
            <span class="status-dot"></span>
            <span style="font-size:12px;color:#9CA3AF;">$now</span>
        </div>
    </div>

    <!-- NAV -->
    <div class="nav" style="margin-bottom:20px;">
        <a href="index.html" class="active">Dashboard</a>
        <a href="#">Markets</a>
        <a href="#">Scanner</a>
        <a href="portfolio.html">Portfolio</a>
        <a href="#">AI Brain</a>
    </div>

    <!-- HERO -->
    <div class="hero">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
            <div>
                <div style="font-size:12px; color:#9CA3AF; letter-spacing:2px;">MASTER DECISION</div>
                <div class="hero-decision">$hero_decision</div>
                <div style="font-size:14px; color:#9CA3AF; margin-top:4px;">$hero_sub</div>
            </div>
            <div class="hero-grid">
                <div class="hero-item"><div class="label">Confidence</div><div class="value cyan">$confidence%</div></div>
                <div class="hero-item"><div class="label">Probability</div><div class="value gold">$score%</div></div>
                <div class="hero-item"><div class="label">Risk</div><div class="value green">$risk_status</div></div>
                <div class="hero-item"><div class="label">Regime</div><div class="value" style="font-size:18px;">$regime</div></div>
            </div>
        </div>
        <div class="hero-reason"><strong>Reason:</strong> $first_reason</div>
    </div>

    <!-- AI BRAIN -->
    <div class="card" style="margin-bottom:20px; border-left:2px solid #00D8FF;">
        <div class="card-title" style="color:#00D8FF;"><i class="fas fa-brain"></i> AI BRAIN EXPLANATION</div>
        <ul style="list-style:none; padding:0; margin-top:8px;">
            $ai_brain_items
        </ul>
    </div>

    <!-- SMC -->
    <div class="card" style="margin-bottom:20px;">
        <div class="card-title"><i class="fas fa-layer-group"></i> SMART MONEY STRUCTURE</div>
        <div class="flex" style="gap:8px; margin-top:6px;">
            $smc_badges
        </div>
        <div style="margin-top:6px; font-size:12px; color:#9CA3AF;">
            <span class="smc-badge active">✅ Active</span>
            <span class="smc-badge inactive">❌ Inactive</span>
        </div>
    </div>

    <!-- PRICE -->
    <div class="grid-3">
        <div class="card"><div class="card-title">Price</div><div class="card-value" id="livePrice">$currency$price</div></div>
        <div class="card"><div class="card-title">High / Low</div><div class="card-value">$currency$high / $currency$low</div></div>
        <div class="card"><div class="card-title">Volume</div><div class="card-value">$volume</div></div>
    </div>

    <!-- TRADE PLAN & RISK -->
    <div class="grid-2">
        <div class="card">
            <div class="card-title"><i class="fas fa-bullseye"></i> TRADE PLAN</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px 12px; margin-top:6px; font-size:14px;">
                <span style="color:#9CA3AF;">Entry</span><span>$currency$entry</span>
                <span style="color:#9CA3AF;">Stop Loss</span><span>$currency$stop</span>
                <span style="color:#9CA3AF;">TP1</span><span>$currency$tp1</span>
                <span style="color:#9CA3AF;">TP2</span><span>$currency$tp2</span>
                <span style="color:#9CA3AF;">TP3</span><span>$currency$tp3</span>
                <span style="color:#9CA3AF;">R/R</span><span>$risk_reward</span>
            </div>
        </div>
        <div class="card">
            <div class="card-title"><i class="fas fa-shield-alt"></i> RISK DASHBOARD</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px 12px; margin-top:6px; font-size:14px;">
                <span style="color:#9CA3AF;">Capital</span><span>$currency$capital</span>
                <span style="color:#9CA3AF;">Risk %</span><span>$risk_percent%</span>
                <span style="color:#9CA3AF;">Position</span><span>$position_size</span>
                <span style="color:#9CA3AF;">Exposure</span><span>$currency$exposure</span>
                <span style="color:#9CA3AF;">Status</span><span style="color:$risk_color;">$risk_status</span>
            </div>
        </div>
    </div>

    <!-- PERFORMANCE -->
    <div class="grid-4">
        <div class="card"><div class="card-title">Total Trades</div><div class="card-value">$total_trades</div></div>
        <div class="card"><div class="card-title">Win Rate</div><div class="card-value" style="color:$win_color;">$win_rate%</div></div>
        <div class="card"><div class="card-title">Net Profit</div><div class="card-value" style="color:$profit_color;">$currency$net_profit</div></div>
        <div class="card"><div class="card-title">Unrealized P&L</div><div class="card-value" style="color:$upnl_color;">$currency$unrealized_pnl</div></div>
    </div>

    <!-- OPEN POSITIONS -->
    <div class="card" style="margin-bottom:20px;">
        <div class="card-title"><i class="fas fa-folder-open"></i> OPEN POSITIONS ($open_count)</div>
        <div style="overflow-x:auto;">
            <table class="trade-table">
                <thead><tr><th>Symbol</th><th>Side</th><th>Entry</th><th>Qty</th><th>Stop</th><th>TP</th><th>Current</th><th>P&L</th></tr></thead>
                <tbody>$open_rows</tbody>
            </table>
        </div>
    </div>

    <!-- CLOSED TRADES -->
    <div class="card" style="margin-bottom:20px;">
        <div class="card-title"><i class="fas fa-history"></i> CLOSED TRADES ($closed_count)</div>
        <div style="overflow-x:auto;">
            <table class="trade-table">
                <thead><tr><th>Symbol</th><th>Side</th><th>Entry</th><th>Exit</th><th>Qty</th><th>P&L</th><th>Result</th></tr></thead>
                <tbody>$closed_rows</tbody>
            </table>
        </div>
    </div>

    <!-- COMPONENTS -->
    <div class="grid-4" style="margin-bottom:20px;">
        <div class="card"><div class="card-title">AI</div><div class="card-value">$ai_score</div></div>
        <div class="card"><div class="card-title">Probability</div><div class="card-value">$prob_score</div></div>
        <div class="card"><div class="card-title">SMC</div><div class="card-value" style="font-size:16px;">$smc</div></div>
        <div class="card"><div class="card-title">Regime</div><div class="card-value" style="font-size:16px;">$regime</div></div>
    </div>

    <!-- CHART -->
    <div class="chart-container">
        <canvas id="componentChart"></canvas>
    </div>

    <!-- REASONING -->
    <div class="card" style="margin-bottom:20px;">
        <div class="card-title"><i class="fas fa-list-ul"></i> REASONING</div>
        <ul class="reason-list">$reason_items</ul>
        <div style="margin-top:8px; font-size:12px; color:#9CA3AF;"><strong>Reasons:</strong> $reasons_str</div>
    </div>

    <!-- FOOTER -->
    <div class="footer">
        <span class="gold">◆</span> Jaguar Quant X <span class="gold">◆</span> Institutional Trading Intelligence OS <span class="gold">◆</span> v2.0
    </div>
</div>

<!-- CHAT -->
<button class="chat-toggle" id="chatToggle"><i class="fas fa-comment-dots"></i></button>
<div class="chat-panel" id="chatPanel">
    <div class="chat-header">
        <span><i class="fas fa-brain"></i> Jaguar Brain X</span>
        <button class="close" id="chatClose"><i class="fas fa-times"></i></button>
    </div>
    <div class="chat-messages" id="chatMessages">
        <div class="chat-message bot">🐆 Good Morning. I'm your Jaguar Brain. Ask me about $asset_name or the market.</div>
    </div>
    <div class="chat-input-area">
        <input type="text" id="chatInput" placeholder="Type your question..." autocomplete="off">
        <button class="mic" id="micButton"><i class="fas fa-microphone"></i></button>
        <button id="sendButton"><i class="fas fa-paper-plane"></i></button>
    </div>
</div>

<script>
    const state = $state_json;
    const chatToggle = document.getElementById('chatToggle');
    const chatPanel = document.getElementById('chatPanel');
    const chatClose = document.getElementById('chatClose');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const micButton = document.getElementById('micButton');

    chatToggle.addEventListener('click', () => chatPanel.classList.toggle('open'));
    chatClose.addEventListener('click', () => chatPanel.classList.remove('open'));

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `chat-message ${sender}`;
        div.textContent = text;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function getBotResponse(q) {
        const lq = q.toLowerCase();
        if (lq.includes('signal') || lq.includes('decision')) {
            return `The current signal for ${state.asset_name} is **${state.decision}** (Score: ${state.score}, Grade: ${state.grade}). Confidence: ${state.confidence}%.`;
        } else if (lq.includes('score') || lq.includes('grade')) {
            return `Score: ${state.score}/100, Grade: ${state.grade}, Confidence: ${state.confidence}%.`;
        } else if (lq.includes('entry') || lq.includes('stop') || lq.includes('tp') || lq.includes('trade plan')) {
            return `Trade Plan: Entry ${state.entry}, Stop Loss ${state.stop}, TP1 ${state.tp1}, TP2 ${state.tp2}, TP3 ${state.tp3}, R/R ${state.risk_reward}.`;
        } else if (lq.includes('risk') || lq.includes('position') || lq.includes('exposure')) {
            return `Risk: ${state.risk_status}, Position Size ${state.position_size.toFixed(4)}, Exposure ${state.exposure.toFixed(2)}, Capital ${state.capital.toFixed(2)}.`;
        } else if (lq.includes('why') || lq.includes('reason')) {
            return `Reasoning: ${state.reasoning.join('. ')}`;
        } else if (lq.includes('components') || lq.includes('ai') || lq.includes('smc')) {
            return `Components: AI ${state.ai_score}, Probability ${state.prob_score}, SMC ${state.smc}, Regime ${state.regime}, Structure ${state.structure}.`;
        } else {
            return `I can help with signal, score, trade plan, risk, reasoning, components, or paper trading. What would you like to know?`;
        }
    }

    async function askLLM(question) {
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 3000);
            const resp = await fetch('http://localhost:8082/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, context: state }),
                signal: controller.signal
            });
            clearTimeout(timeout);
            if (!resp.ok) throw new Error('Server error');
            const data = await resp.json();
            return data.reply;
        } catch (e) {
            return null;
        }
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;
        addMessage(text, 'user');
        chatInput.value = '';
        let reply = getBotResponse(text);
        if (reply.includes("I can help with") || reply.includes("What would you like")) {
            const llmReply = await askLLM(text);
            if (llmReply) reply = llmReply;
            else reply = "⚠️ LLM server unavailable. " + getBotResponse(text);
        }
        addMessage(reply, 'bot');
        speak(reply);
    }

    // voice
    let recognition = null;
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.lang = 'en-US';
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.onresult = (e) => {
            chatInput.value = e.results[0][0].transcript;
            sendMessage();
            micButton.classList.remove('listening');
            micButton.innerHTML = '<i class="fas fa-microphone"></i>';
        };
        recognition.onerror = () => {
            micButton.classList.remove('listening');
            micButton.innerHTML = '<i class="fas fa-microphone"></i>';
        };
    }
    micButton.addEventListener('click', () => {
        if (!recognition) { alert('Voice not supported'); return; }
        if (recognition.started) {
            recognition.stop();
            micButton.classList.remove('listening');
            micButton.innerHTML = '<i class="fas fa-microphone"></i>';
            return;
        }
        recognition.start();
        micButton.classList.add('listening');
        micButton.innerHTML = '<i class="fas fa-stop"></i>';
    });

    function speak(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.lang = 'en-US';
            u.rate = 0.9;
            u.pitch = 1.0;
            window.speechSynthesis.speak(u);
        }
    }

    chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
    sendButton.addEventListener('click', sendMessage);

    // live price
    function updatePrice() {
        const symbol = state.symbol;
        const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}`;
        fetch(url).then(r => r.json()).then(d => {
            const price = d.chart.result[0].meta.regularMarketPrice;
            document.getElementById('livePrice').innerHTML = `${state.currency || '$'}${price.toFixed(2)}`;
        }).catch(() => {});
    }
    setInterval(updatePrice, 10000);

    // chart
    const ctx = document.getElementById('componentChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['AI', 'Probability', 'SMC', 'Regime', 'Structure', 'Score'],
            datasets: [{
                label: 'Score / Signal',
                data: [$ai_score, $prob_score, ${10 if smc=='BULLISH' else -10 if smc=='BEARISH' else 0}, ${10 if regime=='BULLISH' else -10 if regime=='BEARISH' else 0}, ${10 if structure=='BREAKOUT' else -5 if structure=='CONSOLIDATION' else 0}, $score],
                backgroundColor: ['#D4AF37', '#00D8FF', '#00FF88', '#FFD700', '#FF4D4D', '#9CA3AF'],
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#9CA3AF' } },
                x: { grid: { display: false }, ticks: { color: '#9CA3AF' } }
            }
        }
    });
</script>
</body>
</html>
""")

    # ---- Render ----
    html = template.safe_substitute(
        asset_name=asset_name,
        decision=decision,
        decision_bg=decision_bg,
        symbol=symbol,
        mode=mode,
        now=now,
        hero_decision=hero_decision,
        hero_sub=hero_sub,
        confidence=confidence,
        score=score,
        risk_status=risk_status,
        regime=regime,
        first_reason=first_reason,
        ai_brain_items=ai_brain_items,
        smc_badges=smc_badges,
        currency=currency,
        price=f"{price:.2f}",
        high=f"{high:.2f}",
        low=f"{low:.2f}",
        volume=f"{volume:.2f}",
        entry=entry,
        stop=stop,
        tp1=tp1,
        tp2=tp2,
        tp3=tp3,
        risk_reward=risk_reward,
        capital=f"{capital:,.2f}",
        risk_percent=risk_percent,
        position_size=f"{position_size:.4f}",
        exposure=f"{exposure:,.2f}",
        risk_color=risk_color,
        total_trades=total_trades,
        win_rate=win_rate,
        win_color=win_color,
        net_profit=f"{net_profit:,.2f}",
        profit_color=profit_color,
        unrealized_pnl=f"{unrealized_pnl:,.2f}",
        upnl_color=upnl_color,
        open_rows=open_rows,
        closed_rows=closed_rows,
        open_count=open_count,
        closed_count=closed_count,
        ai_score=ai_score,
        prob_score=prob_score,
        smc=smc,
        reason_items=reason_items,
        reasons_str=reasons_str,
        state_json=state_json,
    )

    # ---- FINAL HTML VALUES ----
    # (already printed above, but we keep the earlier print)

    with open(output_file, "w") as f:
        f.write(html)

    print(f"✅ Institutional dashboard saved: {output_file}")
    return output_file
