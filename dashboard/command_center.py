"""
Jaguar Quant X — Command Center renderer.

Presentation only.
No trading authority.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from dashboard.ui_state import build_ui_state


def _esc(value: Any) -> str:
    return html.escape(str(value))


def _fmt(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def _status_class(value: str) -> str:
    value = str(value).upper()

    if value in {"READY", "APPROVED", "HEALTHY", "FILLED"}:
        return "ok"

    if value in {"WAIT", "PENDING", "INTERACTING"}:
        return "wait"

    if value in {"BLOCKED", "REJECTED", "FAILED", "HALTED"}:
        return "danger"

    return "neutral"


def render_command_center(
    state: Any,
    output_file: str = "command_center.html",
) -> str:
    ui = build_ui_state(state)

    system = ui["system"]
    market = ui["market"]
    idm = ui["idm"]
    risk = ui["risk"]
    execution = ui["execution"]
    position = ui["position"]
    audit = ui["audit"]
    freshness = ui["freshness"]

    reasons = idm.get("decision_reasons", []) or []

    if reasons:
        reason_html = "".join(
            f'<div class="reason">• {_esc(reason)}</div>'
            for reason in reasons
        )
    else:
        reason_html = '<div class="muted">No IDM decision reason recorded.</div>'

    execution_reason = execution.get("reason")
    if execution_reason:
        execution_reason_html = (
            f'<div class="gate-reason">{_esc(execution_reason)}</div>'
        )
    else:
        execution_reason_html = (
            '<div class="muted">No execution-gate reason recorded.</div>'
        )


    freshness = ui["freshness"]

    market_ready = str(
        market.get("status", "")
    ).upper() == "READY"

    idm_approved = bool(
        idm.get("approved", False)
    )

    risk_approved = bool(
        risk.get("approved", False)
    )

    execution_ready = bool(
        execution.get("ready", False)
    )

    execution_approved = bool(
        execution.get("approved", False)
    )

    authority_steps = [
        (
            "MARKET",
            "READY" if market_ready else "NOT READY",
            "ready" if market_ready else "danger",
            "✓" if market_ready else "✕",
        ),
        (
            "IDM",
            "APPROVED" if idm_approved else idm["decision"],
            "ok" if idm_approved else "wait",
            "✓" if idm_approved else "⏸",
        ),
        (
            "RISK",
            "APPROVED" if risk_approved else "REJECTED",
            "ok" if risk_approved else "rejected",
            "✓" if risk_approved else "✕",
        ),
        (
            "EXECUTION",
            "READY" if execution_ready else execution["status"],
            "ok" if execution_ready else "wait",
            "✓" if execution_ready else "⏸",
        ),
    ]

    authority_parts = [
        '<div class="authority-chain">',
        '<div class="authority-title">AUTHORITY CHAIN</div>',
    ]

    for index, step in enumerate(authority_steps):
        label = _esc(step[0])
        value = _esc(step[1])
        state_class = _esc(step[2])
        icon = _esc(step[3])

        authority_parts.append(
            '<div class="authority-step ' + state_class + '">'
            '<span class="authority-dot">' + icon + '</span>'
            '<div>'
            '<div class="authority-label">' + label + '</div>'
            '<div class="authority-value">' + value + '</div>'
            '</div>'
            '</div>'
        )

        if index < len(authority_steps) - 1:
            authority_parts.append(
                '<div class="authority-arrow">↓</div>'
            )

    trade_result = (
        "TRADE READY"
        if (
            market_ready
            and idm_approved
            and risk_approved
            and execution_ready
            and execution_approved
        )
        else "NO TRADE"
    )

    authority_parts.extend([
        '<div class="authority-arrow">↓</div>',
        '<div class="authority-result">',
        '<div class="authority-label">RESULT</div>',
        '<div class="authority-value">',
        _esc(trade_result),
        '</div>',
        '</div>',
        '</div>',
    ])

    authority_chain_html = "".join(authority_parts)

    mtf_parts = [
        '<section class="card mtf-context-card">',
        '<div class="section-title">MULTI-TIMEFRAME MARKET CONTEXT</div>',
        '<div class="mtf-grid">',
    ]

    for frame in ("15m", "1h", "4h", "1d"):
        data = ui["mtf"].get(frame, {})
        rsi_value = data.get("rsi")
        atr_value = data.get("atr")

        mtf_parts.extend([
            '<div class="mtf-frame">',
            '<div class="mtf-frame-title">' + _esc(frame) + '</div>',
            '<div class="mtf-row"><span>Trend</span><strong>' +
            _esc(data.get("trend", "UNDEFINED")) + '</strong></div>',
            '<div class="mtf-row"><span>RSI</span><strong>' +
            _esc("—" if rsi_value is None else str(round(float(rsi_value), 2))) +
            '</strong></div>',
            '<div class="mtf-row"><span>RSI Signal</span><strong>' +
            _esc(data.get("rsi_signal", "UNDEFINED")) + '</strong></div>',
            '<div class="mtf-row"><span>Volume</span><strong>' +
            _esc(data.get("volume_signal", "UNDEFINED")) + '</strong></div>',
            '<div class="mtf-row"><span>ATR</span><strong>' +
            _esc("—" if atr_value is None else str(round(float(atr_value), 2))) +
            '</strong></div>',
            '<div class="mtf-row"><span>VWAP</span><strong>' +
            _esc(data.get("vwap_signal", "UNDEFINED")) + '</strong></div>',
            '</div>',
        ])

    mtf_parts.extend([
        '</div>',
        '</section>',
    ])

    mtf_html = "".join(mtf_parts)

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jaguar Quant X — Command Center</title>

<style>
* {{
    box-sizing: border-box;
}}

html, body {{
    margin: 0;
    min-height: 100%;
}}

body {{
    background:
        radial-gradient(circle at top right, rgba(212,175,55,.08), transparent 30%),
        #05070a;
    color: #f2f4f8;
    font-family: Inter, Segoe UI, Arial, sans-serif;
}}

.shell {{
    max-width: 1450px;
    margin: 0 auto;
    padding: 22px;
}}

.topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: 18px 20px;
    border: 1px solid rgba(212,175,55,.18);
    border-radius: 16px;
    background: rgba(12,16,22,.82);
    backdrop-filter: blur(12px);
}}

.brand {{
    font-size: 25px;
    font-weight: 800;
    letter-spacing: 1.5px;
}}

.brand span {{
    color: #d4af37;
}}

.subtitle {{
    margin-top: 5px;
    color: #7f8898;
    font-size: 11px;
    letter-spacing: 2px;
}}

.mode {{
    padding: 8px 13px;
    border-radius: 999px;
    border: 1px solid rgba(0,216,255,.28);
    background: rgba(0,216,255,.08);
    color: #68ddff;
    font-size: 12px;
    font-weight: 700;
}}

.grid {{
    display: grid;
    gap: 14px;
}}

.summary {{
    grid-template-columns: repeat(4, minmax(0,1fr));
    margin-top: 14px;
}}

.two {{
    grid-template-columns: minmax(0,1.35fr) minmax(0,1fr);
    margin-top: 14px;
}}

.three {{
    grid-template-columns: repeat(3, minmax(0,1fr));
    margin-top: 14px;
}}
.structural-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0,1fr));
    gap: 10px;
    margin-top: 14px;
}}

.structural-grid .metric {{
    min-width: 0;
}}


.card {{
    background: rgba(10,14,19,.84);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 10px 35px rgba(0,0,0,.18);
}}

.label {{
    color: #7f8898;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.value {{
    margin-top: 7px;
    font-size: 25px;
    font-weight: 750;
}}

.muted {{
    color: #7f8898;
}}

.ok {{ color: #53e39b; }}
.wait {{ color: #ffd35a; }}
.danger {{ color: #ff6b6b; }}
.neutral {{ color: #c9ced8; }}

.hero {{
    min-height: 260px;
}}

.hero-head {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
}}

.decision {{
    font-size: 44px;
    font-weight: 850;
    letter-spacing: 1px;
    margin-top: 9px;
}}

.market-price {{
    font-size: 34px;
    font-weight: 800;
    margin-top: 8px;
}}

.meta {{
    color: #9099a8;
    font-size: 12px;
    margin-top: 5px;
}}

.badge {{
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    background: rgba(255,255,255,.05);
}}

.metrics {{
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 10px;
    margin-top: 22px;
}}

.metric {{
    padding: 12px;
    border-radius: 12px;
    background: rgba(255,255,255,.025);
}}

.metric-value {{
    margin-top: 5px;
    font-size: 18px;
    font-weight: 700;
}}

.section-title {{
    color: #d4af37;
    font-size: 11px;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 13px;
}}

.row {{
    display: flex;
    justify-content: space-between;
    gap: 14px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(255,255,255,.05);
}}

.row:last-child {{
    border-bottom: 0;
}}

.reason {{
    margin-top: 9px;
    line-height: 1.5;
    color: #cdd2db;
    font-size: 13px;
}}

.gate-reason {{
    margin-top: 10px;
    padding: 11px 12px;
    border-left: 3px solid #ffd35a;
    background: rgba(255,211,90,.05);
    color: #d9dde5;
    line-height: 1.45;
    font-size: 13px;
}}

.footer {{
    margin-top: 18px;
    padding: 14px 4px;
    color: #586171;
    font-size: 11px;
    text-align: center;
}}

@media (max-width: 1000px) {{
    .summary,
    .three {{
        grid-template-columns: repeat(2,minmax(0,1fr));
    }}

    .two {{
        grid-template-columns: 1fr;
    }}
}}

@media (max-width: 620px) {{
    .shell {{
        padding: 12px;
    }}

    .summary,
    .three,
    .metrics {{
        grid-template-columns: 1fr 1fr;
    }}

    .topbar,
    .hero-head {{
        flex-direction: column;
        align-items: flex-start;
    }}

    .decision {{
        font-size: 34px;
    }}
}}

        .mtf-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
        }}

        .mtf-frame {{
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 14px;
            background: rgba(255,255,255,0.025);
        }}

        .mtf-frame-title {{
            font-weight: 700;
            margin-bottom: 10px;
            letter-spacing: 0.04em;
        }}

        .mtf-row {{
            display: flex;
            justify-content: space-between;
            gap: 10px;
            padding: 6px 0;
            font-size: 0.85rem;
        }}

        .mtf-row span {{
            opacity: 0.65;
        }}

        .freshness-panel {{
            margin-top: 14px;
            padding: 12px 14px;
            border: 1px solid rgba(255,255,255,.07);
            border-radius: 14px;
            background: rgba(10,14,19,.72);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
        }}

        .freshness-left {{
            min-width: 0;
        }}

        .freshness-title {{
            color: #7f8898;
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .freshness-time {{
            margin-top: 4px;
            color: #d8dde6;
            font-size: 12px;
            white-space: nowrap;
        }}

        .freshness-badge {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 10px;
            border-radius: 999px;
            font-size: 10px;
            font-weight: 750;
            letter-spacing: .7px;
            white-space: nowrap;
        }}

        .freshness-badge.current {{
            color: #53e39b;
            background: rgba(83,227,155,.10);
            border: 1px solid rgba(83,227,155,.18);
        }}

        .freshness-badge.aging {{
            color: #ffd35a;
            background: rgba(255,211,90,.10);
            border: 1px solid rgba(255,211,90,.18);
        }}

        .freshness-badge.stale {{
            color: #ff6b6b;
            background: rgba(255,107,107,.10);
            border: 1px solid rgba(255,107,107,.18);
        }}

        .freshness-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: currentColor;
        }}

        @media (max-width: 620px) {{
            .mtf-grid {{
                grid-template-columns: 1fr;
            }}

            .freshness-panel {{
                align-items: flex-start;
                flex-direction: column;
            }}
        }}


        .authority-chain {{
            margin: 14px 0 0 0;
            padding: 16px;
            background: rgba(5,7,10,0.62);
            border: 1px solid rgba(212,175,55,0.12);
            border-radius: 16px;
        }}

        .authority-title {{
            color: #d4af37;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.4px;
            margin-bottom: 14px;
        }}

        .authority-step {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            border-radius: 10px;
            background: rgba(255,255,255,0.025);
        }}

        .authority-dot {{
            width: 27px;
            height: 27px;
            min-width: 27px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 800;
        }}

        .authority-step.ready .authority-dot,
        .authority-step.ok .authority-dot {{
            background: rgba(0,255,136,0.14);
            color: #00ff88;
        }}

        .authority-step.wait .authority-dot {{
            background: rgba(255,215,0,0.14);
            color: #ffd700;
        }}

        .authority-step.rejected .authority-dot,
        .authority-step.danger .authority-dot {{
            background: rgba(255,77,77,0.14);
            color: #ff4d4d;
        }}

        .authority-label {{
            color: #7f8898;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .authority-value {{
            color: #f5f5f5;
            font-size: 15px;
            font-weight: 700;
            margin-top: 2px;
        }}

        .authority-step.ready .authority-value,
        .authority-step.ok .authority-value {{
            color: #00ff88;
        }}

        .authority-step.wait .authority-value {{
            color: #ffd700;
        }}

        .authority-step.rejected .authority-value,
        .authority-step.danger .authority-value {{
            color: #ff6b6b;
        }}

        .authority-arrow {{
            text-align: center;
            color: #596171;
            font-size: 14px;
            line-height: 17px;
        }}

        .authority-result {{
            margin-top: 2px;
            padding: 12px;
            text-align: center;
            border-radius: 10px;
            background: rgba(108,117,125,0.08);
            border: 1px solid rgba(108,117,125,0.16);
        }}

        .authority-result .authority-value {{
            color: #aab2c2;
        }}

        .freshness-panel {{
            margin-top: 14px;
            padding: 12px 14px;
            border: 1px solid rgba(255,255,255,.07);
            border-radius: 14px;
            background: rgba(10,14,19,.72);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
        }}

        .freshness-left {{
            min-width: 0;
        }}

        .freshness-title {{
            color: #7f8898;
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .freshness-time {{
            margin-top: 4px;
            color: #d8dde6;
            font-size: 12px;
            white-space: nowrap;
        }}

        .freshness-badge {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 10px;
            border-radius: 999px;
            font-size: 10px;
            font-weight: 750;
            letter-spacing: .7px;
            white-space: nowrap;
        }}

        .freshness-badge.current {{
            color: #53e39b;
            background: rgba(83,227,155,.10);
            border: 1px solid rgba(83,227,155,.18);
        }}

        .freshness-badge.aging {{
            color: #ffd35a;
            background: rgba(255,211,90,.10);
            border: 1px solid rgba(255,211,90,.18);
        }}

        .freshness-badge.stale {{
            color: #ff6b6b;
            background: rgba(255,107,107,.10);
            border: 1px solid rgba(255,107,107,.18);
        }}

        .freshness-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: currentColor;
        }}

        @media (max-width: 620px) {{
            .authority-step,
            .authority-result {{
                width: 100%;
            }}

            .authority-arrow {{
                width: 100%;
            }}

            .freshness-panel {{
                align-items: flex-start;
                flex-direction: column;
            }}
        }}

</style>
</head>

<body>
<div class="shell">

<header class="topbar">
    <div>
        <div class="brand">JAGUAR <span>QUANT X</span></div>
        <div class="subtitle">INSTITUTIONAL TRADING INTELLIGENCE OS · COMMAND CENTER</div>
    </div>

    <div class="mode">
        ● {_esc(system["mode"])} MODE
    </div>
</header>

<section class="grid summary">
    <div class="card">
        <div class="label">System</div>
        <div class="value {_status_class(system["health"])}">
            {_esc(system["health"])}
        </div>
    </div>

    <div class="card">
        <div class="label">Market</div>
        <div class="value ok">{_esc(market["status"])}</div>
    </div>

    <div class="card">
        <div class="label">Risk</div>
        <div class="value {_status_class(risk["status"])}">
            {_esc(risk["status"])}
        </div>
    </div>

    <div class="card">
        <div class="label">Execution</div>
        <div class="value {_status_class(execution["status"])}">
            {_esc(execution["status"])}
        </div>
    </div>
</section>
    
<section class="authority-wrapper">
    {authority_chain_html}
</section>

{mtf_html}

<section class="card structural-context-card">
    <div class="section-title">STRUCTURAL CONTEXT</div>
    <div class="structural-grid">
        <div class="metric">
            <span class="label">Trend</span>
            <span class="value">{ui["structure"]["trend"]}</span>
        </div>
        <div class="metric">
            <span class="label">BOS</span>
            <span class="value">{ui["structure"]["bos"]}</span>
        </div>
        <div class="metric">
            <span class="label">CHOCH</span>
            <span class="value">{ui["structure"]["choch"]}</span>
        </div>
        <div class="metric">
            <span class="label">Direction</span>
            <span class="value">{ui["structure"]["direction"]}</span>
        </div>
        <div class="metric">
            <span class="label">Structure State</span>
            <span class="value">{ui["structure"]["state"]}</span>
        </div>
        <div class="metric">
            <span class="label">Readiness</span>
            <span class="value">{ui["structure"]["readiness"]}</span>
        </div>
        <div class="metric">
            <span class="label">Trigger</span>
            <span class="value">{ui["structure"]["trigger"]}</span>
        </div>
        <div class="metric">
            <span class="label">Zone</span>
            <span class="value">{ui["structure"]["zone_type"]}</span>
        </div>
        <div class="metric">
            <span class="label">Zone Direction</span>
            <span class="value">{ui["structure"]["zone_direction"]}</span>
        </div>
        <div class="metric">
            <span class="label">Zone Lifecycle</span>
            <span class="value">{ui["structure"]["zone_lifecycle"]}</span>
        </div>
    </div>
</section>

<section
    class="freshness-panel"
    id="freshness-panel"
    data-generated-epoch="{freshness["generated_epoch"]}"
>
    <div class="freshness-left">
        <div class="freshness-title">SNAPSHOT FRESHNESS</div>
        <div class="freshness-time">
            Generated {freshness["generated_at"]}
        </div>
    </div>

    <div
        class="freshness-badge current"
        id="freshness-badge"
    >
        <span class="freshness-dot"></span>
        <span id="freshness-status">CURRENT · 0s</span>
    </div>
</section>


<section class="grid two">

    <article class="card hero">
        <div class="hero-head">
            <div>
                <div class="label">
                    {_esc(market["symbol"])} · {_esc(market["timeframe"])}
                </div>

                <div class="market-price">
                    {_fmt(market["price"])}
                </div>

                <div class="meta">
                    Market status: {_esc(market["status"])}
                </div>
            </div>

            <div class="badge {_status_class(idm["decision"])}">
                IDM AUTHORITY
            </div>
        </div>

        <div class="decision {_status_class(idm["decision"])}">
            {_esc(idm["decision"])}
        </div>

        <div class="metrics">
            <div class="metric">
                <div class="label">Score</div>
                <div class="metric-value">{_fmt(idm["score"])}</div>
            </div>

            <div class="metric">
                <div class="label">Confidence</div>
                <div class="metric-value">{_fmt(idm["confidence"])}%</div>
            </div>

            <div class="metric">
                <div class="label">Grade</div>
                <div class="metric-value">{_esc(idm["grade"])}</div>
            </div>

            <div class="metric">
                <div class="label">Direction</div>
                <div class="metric-value">{_esc(idm["direction"])}</div>
            </div>
        </div>
    </article>

    <article class="card">
        <div class="section-title">Why IDM decided this</div>

        <div class="row">
            <span class="muted">Structure</span>
            <strong>{_esc(idm["structure"])}</strong>
        </div>

        <div class="row">
            <span class="muted">Zone</span>
            <strong>{_esc(idm["zone"])}</strong>
        </div>

        <div class="row">
            <span class="muted">Lifecycle</span>
            <strong>{_esc(idm["zone_lifecycle"])}</strong>
        </div>

        <div class="row">
            <span class="muted">Location</span>
            <strong>{_esc(idm["location"])}</strong>
        </div>

        <div class="row">
            <span class="muted">Trigger</span>
            <strong>{_esc(idm["trigger"])}</strong>
        </div>

        <div class="row">
            <span class="muted">Readiness</span>
            <strong>{_esc(idm["readiness"])}</strong>
        </div>
    </article>

</section>

<section class="grid two">

    <article class="card">
        <div class="section-title">IDM decision reason</div>
        {reason_html}
    </article>

    <article class="card">
        <div class="section-title">Execution gate</div>

        <div class="row">
            <span class="muted">Gate</span>
            <strong>{_esc(execution["gate"])}</strong>
        </div>

        <div class="row">
            <span class="muted">Ready</span>
            <strong class="{_status_class('READY' if execution['ready'] else 'BLOCKED')}">
                {_esc("YES" if execution["ready"] else "NO")}
            </strong>
        </div>

        <div class="row">
            <span class="muted">Approved</span>
            <strong class="{_status_class('APPROVED' if execution['approved'] else 'BLOCKED')}">
                {_esc("YES" if execution["approved"] else "NO")}
            </strong>
        </div>

        <div class="row">
            <span class="muted">Broker</span>
            <strong>{_esc(execution["broker"])}</strong>
        </div>

        {execution_reason_html}
    </article>

</section>

<section class="grid three">

    <article class="card">
        <div class="section-title">Risk console</div>

        <div class="row">
            <span class="muted">Approval</span>
            <strong>{_esc("APPROVED" if risk["approved"] else "REJECTED")}</strong>
        </div>

        <div class="row">
            <span class="muted">Position size</span>
            <strong>{_fmt(risk["position_size"], 4)}</strong>
        </div>

        <div class="row">
            <span class="muted">Risk %</span>
            <strong>{_fmt(risk["risk_percent"])}%</strong>
        </div>

        <div class="row">
            <span class="muted">Risk amount</span>
            <strong>{_fmt(risk["risk_amount"])}</strong>
        </div>
    </article>

    <article class="card">
        <div class="section-title">Position</div>

        <div class="row">
            <span class="muted">Status</span>
            <strong>{_esc(position["status"])}</strong>
        </div>

        <div class="row">
            <span class="muted">Side</span>
            <strong>{_esc(position["side"] or "—")}</strong>
        </div>

        <div class="row">
            <span class="muted">Quantity</span>
            <strong>{_fmt(position["quantity"], 4)}</strong>
        </div>
    </article>

    <article class="card">
        <div class="section-title">Audit identity</div>

        <div class="row">
            <span class="muted">Run ID</span>
            <strong>{_esc(audit["run_id"] or "—")}</strong>
        </div>

        <div class="row">
            <span class="muted">Decision ID</span>
            <strong>{_esc(audit["decision_id"] or "—")}</strong>
        </div>

        <div class="row">
            <span class="muted">Snapshot</span>
            <strong>{_esc(audit["timestamp"])}</strong>
        </div>
    </article>

</section>

<footer class="footer">
    JAGUAR QUANT X · READ-ONLY OPERATOR CONSOLE ·
    PAPER MODE · NO LIVE AUTHORITY
</footer>

</div>
</body>
</html>

<script>
(function () {{
    const panel = document.getElementById("freshness-panel");
    const badge = document.getElementById("freshness-badge");
    const status = document.getElementById("freshness-status");

    if (!panel || !badge || !status) {{
        return;
    }}

    const generated = Number(
        panel.dataset.generatedEpoch
    );

    if (!Number.isFinite(generated)) {{
        status.textContent = "UNKNOWN";
        badge.className = "freshness-badge stale";
        return;
    }}

    function updateFreshness() {{
        const age = Math.max(
            0,
            Date.now() / 1000 - generated
        );

        if (age < 60) {{
            status.textContent =
                "CURRENT · " + Math.floor(age) + "s";
            badge.className = "freshness-badge current";
        }} else if (age < 300) {{
            status.textContent =
                "AGING · " + Math.floor(age / 60) + "m";
            badge.className = "freshness-badge aging";
        }} else {{
            status.textContent =
                "STALE · " + Math.floor(age / 60) + "m";
            badge.className = "freshness-badge stale";
        }}
    }}

    updateFreshness();
    window.setInterval(updateFreshness, 1000);
}})();
</script>

"""

    Path(output_file).write_text(
        html_doc,
        encoding="utf-8",
    )

    return output_file
