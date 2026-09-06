# dashboard/portfolio.py
import json
from datetime import datetime

def generate_portfolio_dashboard(results, output_file="portfolio.html"):
    """Generate a portfolio dashboard showing all assets and mode breakdowns."""
    
    total_assets = len(results)
    mode_stats = {}
    asset_details = []
    
    for symbol, data in results.items():
        asset_name = data.get("name", symbol)
        for mode in ["SCALP", "SWING", "CLASSIC"]:
            if mode not in mode_stats:
                mode_stats[mode] = {"BUY": 0, "SELL": 0, "WAIT": 0, "REJECT": 0, "ERROR": 0}
            decision = data.get(mode, {}).get("decision", "WAIT")
            mode_stats[mode][decision] = mode_stats[mode].get(decision, 0) + 1
            asset_details.append({
                "symbol": symbol,
                "name": asset_name,
                "mode": mode,
                "decision": decision,
                "score": data.get(mode, {}).get("score", 0),
                "grade": data.get(mode, {}).get("grade", "F"),
                "confidence": data.get(mode, {}).get("confidence", 0)
            })
    
    total_buy = sum(m["BUY"] for m in mode_stats.values())
    total_sell = sum(m["SELL"] for m in mode_stats.values())
    total_wait = sum(m["WAIT"] for m in mode_stats.values())
    total_reject = sum(m["REJECT"] for m in mode_stats.values())
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
    <meta http-equiv="refresh" content="300">
    <title>Jaguar Quant X – Portfolio</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0b0e14;
            color: #e0e4ed;
            padding: 16px;
            min-height: 100vh;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            background: linear-gradient(135deg, #141a24, #1a1f2a);
            border-radius: 12px;
            border: 1px solid #f7931a60;
            box-shadow: 0 4px 20px rgba(247,147,26,0.15);
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .logo-main {{ font-size: 26px; font-weight: 900; color: #f0f4fa; }}
        .logo-main span {{ color: #f7931a; text-shadow: 0 0 20px rgba(247,147,26,0.3); }}
        .logo-tagline {{ font-size: 11px; letter-spacing: 3px; color: #5a6272; }}
        .logo-tagline span {{ color: #f7931a; }}
        .badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; background: #252b36; color: #b0b8c8; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }}
        .card {{
            background: #141a24;
            border-radius: 12px;
            padding: 14px 16px;
            border: 1px solid #252b36;
            transition: 0.2s;
        }}
        .card:hover {{ border-color: #f7931a80; box-shadow: 0 0 25px rgba(247,147,26,0.1); }}
        .card-title {{ font-size: 10px; text-transform: uppercase; color: #8892a2; }}
        .card-value {{ font-size: 24px; font-weight: 700; color: #f0f4fa; }}
        .card-value .sub {{ font-size: 14px; color: #8892a2; margin-left: 6px; }}
        .section-title {{ font-size: 14px; font-weight: 600; color: #aab2c2; margin: 20px 0 10px 0; border-bottom: 1px solid #252b36; padding-bottom: 6px; }}
        .section-title .gold {{ color: #f7931a; }}
        .table-wrap {{ overflow-x: auto; margin-bottom: 20px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #141a24;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #252b36;
        }}
        th {{ background: #1a1f2a; color: #8892a2; font-size: 11px; text-transform: uppercase; padding: 10px 12px; text-align: left; }}
        td {{ padding: 8px 12px; border-bottom: 1px solid #1e232e; font-size: 13px; }}
        tr:hover td {{ background: #1a1f2a; }}
        .status-badge {{
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            color: #fff;
        }}
        .status-badge.buy {{ background: #2e7d32; }}
        .status-badge.sell {{ background: #c62828; }}
        .status-badge.wait {{ background: #ed6c02; }}
        .status-badge.reject {{ background: #6c757d; }}
        .status-badge.error {{ background: #e91e63; }}
        .live-dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #4caf50; animation: pulse 1.5s infinite; margin-right: 6px; }}
        @keyframes pulse {{ 0% {{ opacity:0.6; transform:scale(0.95); }} 50% {{ opacity:1; transform:scale(1.1); }} 100% {{ opacity:0.6; transform:scale(0.95); }} }}
        .flex {{ display: flex; align-items: center; gap: 6px; }}
        .footer {{ margin-top: 30px; text-align: center; font-size: 11px; color: #5a6272; border-top: 1px solid #1e232e; padding-top: 16px; }}
        .footer .gold {{ color: #f7931a; }}
        @media (max-width: 480px) {{ .grid {{ grid-template-columns: repeat(2,1fr); }} }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <div class="logo-main">JAGUAR <span>QUANTX</span></div>
            <div class="logo-tagline">DATA <span>·</span> DISCIPLINE <span>·</span> DOMINATE</div>
        </div>
        <span class="badge"><i class="fas fa-layer-group"></i> Portfolio</span>
    </div>

    <div style="display:flex; justify-content:space-between; margin-bottom:16px;">
        <div class="flex"><span class="live-dot"></span><span style="font-size:13px;color:#8892a2;">Live</span></div>
        <span style="font-size:12px;color:#5a6272;">{now}</span>
    </div>

    <div class="grid">
        <div class="card"><div class="card-title">Total Assets</div><div class="card-value">{total_assets}</div></div>
        <div class="card"><div class="card-title">Total BUY</div><div class="card-value" style="color:#4caf50;">{total_buy}</div></div>
        <div class="card"><div class="card-title">Total SELL</div><div class="card-value" style="color:#f44336;">{total_sell}</div></div>
        <div class="card"><div class="card-title">Total WAIT</div><div class="card-value" style="color:#ff9800;">{total_wait}</div></div>
        <div class="card"><div class="card-title">Total REJECT</div><div class="card-value" style="color:#6c757d;">{total_reject}</div></div>
    </div>

    <div class="section-title"><span class="gold">●</span> Breakdown by Mode</div>
    <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));">
"""
    
    for mode, stats in mode_stats.items():
        buy = stats.get("BUY", 0)
        sell = stats.get("SELL", 0)
        wait = stats.get("WAIT", 0)
        reject = stats.get("REJECT", 0)
        html += f"""
        <div class="card">
            <div class="card-title">{mode}</div>
            <div style="display:flex; gap:12px; flex-wrap:wrap; margin-top:4px;">
                <span style="color:#4caf50;">BUY {buy}</span>
                <span style="color:#f44336;">SELL {sell}</span>
                <span style="color:#ff9800;">WAIT {wait}</span>
                <span style="color:#6c757d;">REJ {reject}</span>
            </div>
        </div>
        """
    
    html += """
    </div>

    <div class="section-title"><span class="gold">●</span> Asset Details</div>
    <div class="table-wrap">
        <table>
            <thead>
                <tr><th>Asset</th><th>Mode</th><th>Decision</th><th>Score</th><th>Grade</th><th>Confidence</th></tr>
            </thead>
            <tbody>
    """
    
    for item in asset_details:
        decision = item["decision"]
        badge_class = decision.lower()
        html += f"""
        <tr>
            <td><strong>{item['name']}</strong><br><span style="font-size:11px;color:#5a6272;">{item['symbol']}</span></td>
            <td>{item['mode']}</td>
            <td><span class="status-badge {badge_class}">{decision}</span></td>
            <td>{item['score']}</td>
            <td>{item['grade']}</td>
            <td>{item['confidence']}%</td>
        </tr>
        """
    
    html += f"""
            </tbody>
        </table>
    </div>

    <div style="margin-top: 20px; text-align: center;">
        <a href="index.html" style="color:#f7931a; text-decoration: none; font-weight:600;">
            <i class="fas fa-arrow-left"></i> Back to Portal
        </a>
    </div>

    <div class="footer">
        <span class="gold">◆</span> Jaguar Quant X <span class="gold">◆</span> Portfolio Intelligence <span class="gold">◆</span> v2.0
    </div>
</div>
</body>
</html>
"""
    
    with open(output_file, "w") as f:
        f.write(html)
    print(f"✅ Portfolio dashboard saved to {output_file}")
    return output_file
