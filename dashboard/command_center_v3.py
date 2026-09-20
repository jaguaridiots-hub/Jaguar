"""
Jaguar Quant X — Command Center UI v3.

Read-only presentation layer.
Uses the canonical /dashboard/state contract.
No order placement or execution authority.
"""

from __future__ import annotations


def render_command_center_v3() -> str:
    return r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Jaguar Quant X — Command Center v3</title>

<style>
:root{
  --bg:#070b10;
  --panel:#0d141c;
  --panel2:#101923;
  --line:#233242;
  --line2:#162330;
  --text:#edf4fb;
  --muted:#8193a7;
  --cyan:#38d7ff;
  --gold:#d6b259;
  --green:#3cdaa0;
  --red:#ff6879;
  --amber:#f5ca58;
  --blue:#6ba5ff;
}

*{box-sizing:border-box}

html,body{
  margin:0;
  padding:0;
  background:var(--bg);
  color:var(--text);
  font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}

body{
  min-height:100vh;
}

button,input{
  font:inherit;
}

.shell{
  width:min(1480px,100%);
  margin:auto;
  padding:10px;
}

.topbar{
  position:sticky;
  top:7px;
  z-index:50;
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:10px;
  padding:10px 12px;
  border:1px solid var(--line);
  border-radius:15px;
  background:rgba(8,13,18,.95);
  backdrop-filter:blur(16px);
}

.brand{
  display:flex;
  align-items:center;
  gap:10px;
  min-width:0;
}

.logo{
  width:42px;
  height:42px;
  border-radius:12px;
  object-fit:cover;
  border:1px solid rgba(214,178,89,.35);
  flex:none;
}

.brand-copy{
  min-width:0;
}

.brand-title{
  font-size:14px;
  font-weight:900;
  letter-spacing:.08em;
}

.brand-sub{
  margin-top:2px;
  font-size:8px;
  color:var(--muted);
  letter-spacing:.08em;
  white-space:nowrap;
}

.statuses{
  display:flex;
  flex-wrap:wrap;
  justify-content:flex-end;
  gap:5px;
}

.badge{
  padding:6px 8px;
  border:1px solid var(--line);
  border-radius:999px;
  background:#0a1118;
  color:var(--muted);
  font-size:8px;
  font-weight:800;
  letter-spacing:.08em;
}

.badge.paper{color:var(--cyan);border-color:rgba(56,215,255,.3)}
.badge.ok{color:var(--green);border-color:rgba(60,218,160,.28)}
.badge.warn{color:var(--amber);border-color:rgba(245,202,88,.25)}
.badge.bad{color:var(--red);border-color:rgba(255,104,121,.3)}

.watchbar{
  margin-top:9px;
  display:flex;
  gap:6px;
  overflow-x:auto;
  scrollbar-width:none;
}

.watchbar::-webkit-scrollbar{display:none}

.asset{
  flex:none;
  min-width:105px;
  padding:8px 9px;
  border:1px solid var(--line2);
  border-radius:10px;
  background:#0a1017;
  color:var(--text);
  text-align:left;
}

.asset.active{
  border-color:rgba(56,215,255,.42);
  background:#0d1b24;
}

.asset-symbol{
  font-size:10px;
  font-weight:900;
}

.asset-meta{
  margin-top:2px;
  color:var(--muted);
  font-size:7px;
}

.layout{
  display:grid;
  grid-template-columns:minmax(0,1fr) 285px;
  gap:10px;
  margin-top:10px;
}

.main{
  min-width:0;
}

.card{
  border:1px solid var(--line);
  border-radius:14px;
  background:linear-gradient(180deg,#0e151d,#0a1118);
}

.hero{
  padding:14px;
}

.hero-top{
  display:flex;
  justify-content:space-between;
  gap:12px;
}

.symbol{
  color:var(--cyan);
  font-size:10px;
  font-weight:900;
  letter-spacing:.12em;
}

.price{
  margin-top:5px;
  font-size:35px;
  line-height:1;
  font-weight:950;
  letter-spacing:-.035em;
}

.market-line{
  margin-top:7px;
  color:var(--muted);
  font-size:9px;
}

.decision-wrap{
  text-align:right;
}

.decision-label{
  color:var(--gold);
  font-size:8px;
  font-weight:900;
  letter-spacing:.14em;
}

.decision{
  margin-top:2px;
  font-size:32px;
  font-weight:950;
  letter-spacing:.04em;
}

.wait{color:var(--amber)}
.buy{color:var(--green)}
.sell{color:var(--red)}
.neutral{color:var(--muted)}

.decision-context{
  margin-top:3px;
  color:var(--muted);
  font-size:8px;
}

.metrics{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:6px;
  margin-top:12px;
}

.metric{
  padding:9px 10px;
  border:1px solid var(--line2);
  border-radius:10px;
  background:#0a1016;
}

.metric-label{
  color:var(--muted);
  font-size:7px;
  font-weight:800;
  letter-spacing:.1em;
}

.metric-value{
  margin-top:4px;
  font-size:16px;
  font-weight:900;
}

.pipeline{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:6px;
  margin-top:8px;
}

.pipeline-card{
  position:relative;
  padding:9px;
  border:1px solid var(--line2);
  border-radius:10px;
  background:#0a1016;
}

.pipeline-title{
  color:var(--muted);
  font-size:7px;
  font-weight:800;
  letter-spacing:.1em;
}

.pipeline-value{
  margin-top:5px;
  font-size:11px;
  font-weight:950;
}

.arrow{
  position:absolute;
  right:-7px;
  top:50%;
  transform:translateY(-50%);
  color:var(--gold);
  z-index:2;
}

.chart-card{
  margin-top:8px;
  padding:10px;
}

.section-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:8px;
  color:var(--gold);
  font-size:8px;
  font-weight:900;
  letter-spacing:.14em;
  text-transform:uppercase;
}

.meta{
  color:var(--muted);
  font-size:7px;
  letter-spacing:0;
  font-weight:600;
}

canvas{
  width:100%;
  height:285px;
  display:block;
  margin-top:7px;
  border-radius:10px;
  background:#070c11;
}

.grid2{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:8px;
  margin-top:8px;
}

details.card{
  overflow:hidden;
}

details>summary{
  list-style:none;
  cursor:pointer;
  padding:11px 12px;
  color:var(--gold);
  font-size:8px;
  font-weight:900;
  letter-spacing:.14em;
  text-transform:uppercase;
}

details>summary::-webkit-details-marker{
  display:none;
}

details>summary::after{
  content:"＋";
  float:right;
  color:var(--muted);
  font-size:12px;
}

details[open]>summary::after{
  content:"−";
}

.content{
  padding:0 12px 11px;
}

.rows{
  display:flex;
  flex-direction:column;
}

.row{
  display:grid;
  grid-template-columns:minmax(0,1fr) auto;
  gap:8px;
  padding:6px 0;
  border-bottom:1px solid rgba(255,255,255,.045);
}

.row:last-child{
  border-bottom:0;
}

.label{
  color:var(--muted);
  font-size:8px;
}

.value{
  text-align:right;
  max-width:60%;
  overflow-wrap:anywhere;
  font-size:9px;
  font-weight:800;
}

.reason{
  padding:7px 0;
  border-bottom:1px solid rgba(255,255,255,.045);
  font-size:9px;
  line-height:1.45;
}

.mtf{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:6px;
}

.mtf-card{
  padding:9px;
  border:1px solid var(--line2);
  border-radius:10px;
  background:#0a1016;
}

.mtf-title{
  margin-bottom:6px;
  color:var(--cyan);
  font-size:10px;
  font-weight:900;
}

.side{
  position:sticky;
  top:67px;
  align-self:start;
  display:flex;
  flex-direction:column;
  gap:8px;
}

.side-card{
  padding:11px;
}

.side-title{
  margin-bottom:7px;
  color:var(--gold);
  font-size:8px;
  font-weight:900;
  letter-spacing:.14em;
  text-transform:uppercase;
}

.side .row{
  padding:5px 0;
}

.ai-log{
  height:125px;
  overflow:auto;
  padding:8px;
  border:1px solid var(--line2);
  border-radius:9px;
  background:#070c11;
}

.msg{
  margin-bottom:8px;
  font-size:8px;
  line-height:1.5;
}

.msg.user{color:var(--cyan)}
.msg.bot{color:var(--text)}

.ai-form{
  display:flex;
  gap:5px;
  margin-top:6px;
}

.ai-form input{
  min-width:0;
  flex:1;
  border:1px solid var(--line);
  border-radius:8px;
  background:#080e14;
  color:var(--text);
  padding:8px;
  outline:none;
  font-size:9px;
}

.ai-form button{
  border:1px solid rgba(56,215,255,.3);
  border-radius:8px;
  background:#0c1821;
  color:var(--cyan);
  padding:8px 10px;
  font-size:8px;
  font-weight:900;
}

.banner{
  margin-top:8px;
  padding:8px;
  border:1px solid rgba(214,178,89,.25);
  border-radius:9px;
  background:rgba(214,178,89,.055);
  color:#e9d69f;
  font-size:8px;
  line-height:1.5;
}

.footer{
  padding:14px 0 4px;
  text-align:center;
  color:#596a7b;
  font-size:7px;
  letter-spacing:.1em;
}

@media(max-width:1050px){
  .layout{grid-template-columns:1fr}
  .side{
    position:static;
    display:grid;
    grid-template-columns:1fr 1fr;
  }
}

@media(max-width:700px){
  .shell{padding:7px}

  .topbar{
    position:static;
    align-items:flex-start;
  }

  .logo{width:38px;height:38px}

  .brand-title{font-size:12px}
  .brand-sub{font-size:7px;white-space:normal}

  .statuses{
    max-width:145px;
  }

  .badge{
    font-size:7px;
    padding:5px 6px;
  }

  .hero-top{
    flex-direction:column;
  }

  .decision-wrap{
    text-align:left;
  }

  .price{
    font-size:31px;
  }

  .decision{
    font-size:29px;
  }

  .metrics{
    grid-template-columns:1fr 1fr;
  }

  .pipeline{
    grid-template-columns:1fr 1fr;
  }

  .pipeline-card:nth-child(2) .arrow,
  .pipeline-card:nth-child(4) .arrow{
    display:none;
  }

  .grid2{
    grid-template-columns:1fr;
  }

  .mtf{
    grid-template-columns:1fr 1fr;
  }

  .side{
    grid-template-columns:1fr;
  }

  canvas{
    height:235px;
  }
}

@media(max-width:430px){
  .metrics{
    grid-template-columns:1fr 1fr;
  }

  .pipeline{
    grid-template-columns:1fr 1fr;
  }

  .mtf{
    grid-template-columns:1fr 1fr;
  }

  .brand-sub{
    max-width:145px;
  }

  .price{
    font-size:28px;
  }
}

.direction-long{
  color:#53e39b;
  font-weight:850;
}

.direction-short{
  color:#ff6879;
  font-weight:850;
}

.direction-neutral{
  color:#ffd35a;
  font-weight:850;
}

.row{
  grid-template-columns:minmax(90px,1fr) minmax(120px,1.5fr);
}

.row .value{
  min-width:0;
  max-width:none;
  overflow-wrap:anywhere;
  word-break:normal;
  white-space:normal;
}

@media(max-width:430px){
  .row{
    grid-template-columns:minmax(82px,.9fr) minmax(125px,1.6fr);
  }

  .row .value{
    max-width:none;
    text-align:right;
    white-space:normal;
    overflow-wrap:anywhere;
    word-break:normal;
  }
}


.indicator-toolbar{
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  margin:8px 0 5px;
}

.indicator-toggle{
  appearance:none;
  border:1px solid var(--line2);
  background:#0b1218;
  color:var(--muted);
  border-radius:999px;
  padding:5px 9px;
  font-size:9px;
  font-weight:900;
  letter-spacing:.04em;
  cursor:pointer;
}

.indicator-toggle.active{
  color:#eef7ff;
  border-color:rgba(56,215,255,.48);
  background:#10202a;
}

.indicator-note{
  color:var(--muted);
  font-size:8px;
  line-height:1.4;
  margin-bottom:5px;
}

.chart-legend{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:5px;
  font-size:8px;
  color:var(--muted);
}

.legend-item{
  display:inline-flex;
  align-items:center;
  gap:4px;
}

.legend-line{
  width:18px;
  height:2px;
  border-radius:2px;
  display:inline-block;
}

.coverage-card{
  margin-top:8px;
}

.session-panel{
  display:grid;
  grid-template-columns:minmax(90px,.7fr) minmax(140px,1.2fr) minmax(100px,.8fr);
  gap:6px;
  margin-bottom:9px;
}

.session-tile,
.coverage-group{
  border:1px solid var(--line2);
  background:#0a1117;
  border-radius:6px;
}

.session-tile{
  padding:9px;
}

.session-label,
.coverage-label{
  color:var(--muted);
  font-size:8px;
  font-weight:900;
  letter-spacing:.05em;
}

.session-value{
  margin-top:4px;
  font-size:13px;
  font-weight:950;
}

.session-reason{
  margin-top:4px;
  color:var(--muted);
  font-size:8px;
  line-height:1.4;
}

.coverage-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:7px;
}

.coverage-group{
  padding:9px;
}

.coverage-head{
  display:flex;
  justify-content:space-between;
  gap:8px;
  align-items:flex-start;
}

.coverage-provider{
  margin-top:2px;
  color:var(--muted);
  font-size:8px;
}

.coverage-status{
  flex:none;
  font-size:8px;
  font-weight:900;
  padding:3px 5px;
  border-radius:999px;
  border:1px solid var(--line2);
  white-space:nowrap;
}

.coverage-status.ready{
  color:#53e39b;
  border-color:rgba(83,227,155,.35);
}

.coverage-status.analysis{
  color:#ffd35a;
  border-color:rgba(255,211,90,.35);
}

.coverage-status.unavailable{
  color:#ff8e9b;
  border-color:rgba(255,104,121,.35);
}

.coverage-assets{
  display:flex;
  flex-wrap:wrap;
  gap:5px;
  margin-top:7px;
}

.coverage-asset{
  appearance:none;
  border:1px solid var(--line2);
  background:#0d171e;
  color:#dce8f2;
  border-radius:5px;
  padding:5px 7px;
  font-size:8px;
  font-weight:850;
  cursor:pointer;
}

.coverage-asset:hover{
  border-color:rgba(56,215,255,.42);
}

@media(max-width:760px){
  .coverage-grid{
    grid-template-columns:1fr;
  }

  .session-panel{
    grid-template-columns:1fr 1fr;
  }

  .session-panel .session-tile:last-child{
    grid-column:1 / -1;
  }
}

@media(max-width:430px){
  .indicator-toolbar{
    gap:4px;
  }

  .indicator-toggle{
    font-size:8px;
    padding:5px 7px;
  }

  .session-panel{
    grid-template-columns:1fr;
  }

  .session-panel .session-tile:last-child{
    grid-column:auto;
  }
}

</style>
</head>

<body>
<div class="shell">

<header class="topbar">
  <div class="brand">
    <img class="logo" src="/dashboard/assets/jaguar_quant_x_logo.png" alt="Jaguar Quant X">
    <div class="brand-copy">
      <div class="brand-title">JAGUAR QUANT X</div>
      <div class="brand-sub">INSTITUTIONAL TRADING INTELLIGENCE · READ-ONLY OPERATOR CONSOLE</div>
    </div>
  </div>

  <div class="statuses">
    <div class="badge paper" id="modeBadge">PAPER</div>
    <div class="badge" id="healthBadge">SYSTEM —</div>
    <div class="badge" id="freshBadge">FRESHNESS —</div>
  </div>
</header>

<div class="watchbar" id="watchbar"></div>

<div class="layout">

<main class="main">

<section class="card hero">
  <div class="hero-top">
    <div>
      <div class="symbol" id="symbol">—</div>
      <div class="price" id="price">—</div>
      <div class="market-line" id="marketLine">—</div>
      <div class="market-line" id="freshLine">—</div>
    </div>

    <div class="decision-wrap">
      <div class="decision-label">IDM AUTHORITY</div>
      <div class="decision wait" id="decision">WAIT</div>
      <div class="decision-context" id="decisionContext">—</div>
      <div class="decision-context" id="zoneContext">—</div>
    </div>
  </div>

  <div class="metrics">
    <div class="metric">
      <div class="metric-label">SCORE</div>
      <div class="metric-value" id="score">—</div>
    </div>
    <div class="metric">
      <div class="metric-label">CONFIDENCE</div>
      <div class="metric-value" id="confidence">—</div>
    </div>
    <div class="metric">
      <div class="metric-label">GRADE</div>
      <div class="metric-value" id="grade">—</div>
    </div>
    <div class="metric">
      <div class="metric-label">READINESS</div>
      <div class="metric-value" id="readiness">—</div>
    </div>
  </div>
</section>

<section class="pipeline">
  <div class="pipeline-card card">
    <div class="pipeline-title">MARKET DATA</div>
    <div class="pipeline-value" id="pipeMarket">—</div>
    <div class="arrow">→</div>
  </div>

  <div class="pipeline-card card">
    <div class="pipeline-title">IDM</div>
    <div class="pipeline-value" id="pipeIdm">—</div>
    <div class="arrow">→</div>
  </div>

  <div class="pipeline-card card">
    <div class="pipeline-title">RISK</div>
    <div class="pipeline-value" id="pipeRisk">—</div>
    <div class="arrow">→</div>
  </div>

  <div class="pipeline-card card">
    <div class="pipeline-title">EXECUTION</div>
    <div class="pipeline-value" id="pipeExec">—</div>
  </div>
</section>

<section class="card chart-card">
  <div class="section-head">
    <span>PRICE STRUCTURE</span>
    <span class="meta" id="chartMeta">—</span>
  </div>
  <div class="indicator-toolbar" id="indicatorToolbar">
    <button class="indicator-toggle active" data-indicator="EMA20">EMA20</button>
    <button class="indicator-toggle active" data-indicator="EMA50">EMA50</button>
    <button class="indicator-toggle active" data-indicator="EMA100">EMA100</button>
    <button class="indicator-toggle active" data-indicator="EMA200">EMA200</button>
    <button class="indicator-toggle active" data-indicator="VWAP">VWAP</button>
  </div>
  <div class="indicator-note">
    Chart overlays are calculated from the canonical candle history shown by Jaguar.
  </div>
  <canvas id="chart"></canvas>
  <div class="chart-legend" id="chartLegend"></div>
</section>


<section class="card coverage-card">
  <div class="section-head">
    <span>SESSION & MARKET COVERAGE</span>
    <span class="meta">READ-ONLY CAPABILITY MAP</span>
  </div>

  <div class="session-panel" id="sessionPanel"></div>

  <div class="coverage-grid" id="marketCoverage"></div>
</section>

<div class="grid2">

<details class="card" open>
  <summary>INSTITUTIONAL DECISION</summary>
  <div class="content" id="idmRows"></div>
</details>

<details class="card" open>
  <summary>STRUCTURE</summary>
  <div class="content" id="structureRows"></div>
</details>

<details class="card" open>
  <summary>RISK</summary>
  <div class="content" id="riskRows"></div>
</details>

<details class="card" open>
  <summary>EXECUTION CHAIN</summary>
  <div class="content">
    <div id="executionRows"></div>
    <div class="banner" id="executionReason">—</div>
  </div>
</details>

</div>

<details class="card" style="margin-top:8px" open>
  <summary>MULTI-TIMEFRAME MARKET CONTEXT</summary>
  <div class="content">
    <div class="mtf" id="mtf"></div>
  </div>
</details>

<details class="card" style="margin-top:8px" open>
  <summary>WHY JAGUAR DECIDED THIS</summary>
  <div class="content" id="reasons"></div>
</details>

</main>

<aside class="side">

<section class="card side-card">
  <div class="side-title">SYSTEM STATE</div>
  <div class="rows" id="systemRows"></div>
</section>

<section class="card side-card">
  <div class="side-title">MARKET DATA</div>
  <div class="rows" id="marketRows"></div>
</section>

<section class="card side-card">
  <div class="side-title">PORTFOLIO / BROKER</div>
  <div class="rows" id="portfolioRows"></div>
</section>

<section class="card side-card">
  <div class="side-title">AUDIT</div>
  <div class="rows" id="auditRows"></div>
</section>

<section class="card side-card">
  <div class="side-title">JAGUAR AI</div>
  <div class="ai-log" id="aiLog">
    <div class="msg bot">Jaguar AI is read-only. Ask about the current canonical snapshot.</div>
  </div>

  <form class="ai-form" id="aiForm">
    <input id="aiInput" placeholder="Ask Jaguar..." autocomplete="off">
    <button type="submit">SEND</button>
  </form>
</section>

</aside>

</div>

<div class="footer">
JAGUAR QUANT X · COMMAND CENTER V3 · READ-ONLY · NO LIVE AUTHORITY
</div>

</div>

<script>
const state={
  symbol:"BTCUSDT",
  interval:"15m",
  mode:"SWING",
  ui:null,
  candles:[],
  chartIndicators:{
    EMA20:true,
    EMA50:true,
    EMA100:true,
    EMA200:true,
    VWAP:true
  }
};


const marketGroups=[
  {
    name:"CRYPTO",
    provider:"BINANCE",
    status:"LIVE DATA",
    statusClass:"ready",
    assets:["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT"]
  },
  {
    name:"NSE",
    provider:"YAHOO_NSE · ANALYSIS",
    status:"ANALYSIS",
    statusClass:"analysis",
    assets:["RELIANCE.NS","TCS.NS","HDFCBANK.NS","^NSEI"]
  },
  {
    name:"MCX · GOLD / SILVER",
    provider:"UPSTOX",
    status:"BROKER UNAVAILABLE",
    statusClass:"unavailable",
    assets:["GOLD","GOLDM","SILVER","SILVERM"]
  },
  {
    name:"US",
    provider:"US MARKET PROVIDER",
    status:"UNAVAILABLE",
    statusClass:"unavailable",
    assets:["AAPL","MSFT","NVDA","SPY","QQQ"]
  }
];

const watchlist=[
  "BTCUSDT",
  "ETHUSDT",
  "SOLUSDT",
  "BNBUSDT",
  "RELIANCE.NS",
  "TCS.NS"
];

function esc(v){
  return String(v??"").replace(/[&<>"']/g,m=>({
    "&":"&amp;",
    "<":"&lt;",
    ">":"&gt;",
    '"':"&quot;",
    "'":"&#39;"
  }[m]));
}

function fmt(v,d=2){
  if(v===null||v===undefined||Number.isNaN(Number(v))) return "—";
  return Number(v).toLocaleString(undefined,{
    minimumFractionDigits:0,
    maximumFractionDigits:d
  });
}

function cls(v){
  return String(v??"").toLowerCase().replace(/[^a-z0-9]+/g,"-")||"neutral";
}

function row(label,value){
  return `<div class="row"><div class="label">${esc(label)}</div><div class="value">${esc(value)}</div></div>`;
}

function prettyTime(v){
  if(v===null||v===undefined||v==="") return "—";
  const n=Number(v);
  if(Number.isFinite(n)&&n>100000000000){
    return new Date(n).toLocaleString();
  }
  return String(v);
}

function renderWatch(){
  const box=document.getElementById("watchbar");
  box.innerHTML=watchlist.map(s=>`
    <button class="asset ${s===state.symbol?"active":""}" data-symbol="${esc(s)}">
      <div class="asset-symbol">${esc(s)}</div>
      <div class="asset-meta">15m · SWING</div>
    </button>
  `).join("");

  box.querySelectorAll(".asset").forEach(b=>{
    b.onclick=()=>{
      state.symbol=b.dataset.symbol;
      load();
    };
  });
}

function freshnessLabel(f){
  const age=Date.now()/1000-Number(f.generated_epoch||0);
  if(age<=120) return "CURRENT";
  if(age<=600) return "AGING · "+Math.round(age/60)+"m";
  if(Number.isFinite(age)) return "STALE · "+Math.round(age/60)+"m";
  return "UNKNOWN";
}

function setPipeline(id,value){
  document.getElementById(id).textContent=value||"—";
}


function directionClass(value){
  const v=String(value||"").toUpperCase();

  if(
    v==="LONG" ||
    v==="BULLISH" ||
    v==="STRONG BULLISH"
  ){
    return "direction-long";
  }

  if(
    v==="SHORT" ||
    v==="BEARISH" ||
    v==="STRONG BEARISH"
  ){
    return "direction-short";
  }

  return "direction-neutral";
}

function directionIcon(value){
  const v=String(value||"").toUpperCase();

  if(
    v==="LONG" ||
    v==="BULLISH" ||
    v==="STRONG BULLISH"
  ){
    return "🟢";
  }

  if(
    v==="SHORT" ||
    v==="BEARISH" ||
    v==="STRONG BEARISH"
  ){
    return "🔴";
  }

  return "🟡";
}

function directionMarkup(value){
  const text=String(value||"NEUTRAL");
  return '<span class="'+directionClass(text)+'">'+
         directionIcon(text)+" "+esc(text)+
         "</span>";
}


function emaSeries(values,period){
  const out=new Array(values.length).fill(null);

  if(values.length<period){
    return out;
  }

  let sum=0;

  for(let i=0;i<period;i++){
    sum+=Number(values[i]);
  }

  let ema=sum/period;
  out[period-1]=ema;

  const k=2/(period+1);

  for(let i=period;i<values.length;i++){
    ema=(Number(values[i])-ema)*k+ema;
    out[i]=ema;
  }

  return out;
}

function vwapSeries(candles){
  const out=new Array(candles.length).fill(null);

  let pv=0;
  let vol=0;

  for(let i=0;i<candles.length;i++){
    const c=candles[i];

    const h=Number(c.high);
    const l=Number(c.low);
    const cl=Number(c.close);
    const v=Number(c.volume);

    if(
      !Number.isFinite(h) ||
      !Number.isFinite(l) ||
      !Number.isFinite(cl) ||
      !Number.isFinite(v)
    ){
      continue;
    }

    const typical=(h+l+cl)/3;

    pv+=typical*v;
    vol+=v;

    out[i]=vol>0 ? pv/vol : null;
  }

  return out;
}

function linePath(ctx,points){
  let started=false;

  ctx.beginPath();

  for(const p of points){
    if(p==null || !Number.isFinite(p.x) || !Number.isFinite(p.y)){
      started=false;
      continue;
    }

    if(!started){
      ctx.moveTo(p.x,p.y);
      started=true;
    }else{
      ctx.lineTo(p.x,p.y);
    }
  }

  ctx.stroke();
}

function directionFromTrend(value){
  const v=String(value||"").toUpperCase();

  if(v.includes("BULLISH")){
    return "BULLISH";
  }

  if(v.includes("BEARISH")){
    return "BEARISH";
  }

  return "NEUTRAL";
}

function render(){
  const u=state.ui||{};
  const sys=u.system||{};
  const fresh=u.freshness||{};
  const market=u.market||{};
  const idm=u.idm||{};
  const st=u.structure||{};
  const risk=u.risk||{};
  const exe=u.execution||{};
  const mtf=u.mtf||{};
  const portfolio=u.portfolio||{};
  const audit=u.audit||{};

  const freshness=freshnessLabel(fresh);

  const mode=String(sys.mode||"UNKNOWN").toUpperCase();

  document.getElementById("modeBadge").textContent="EXECUTION · "+mode;
  document.getElementById("modeBadge").className="badge "+(mode==="PAPER"?"paper":"bad");

  document.getElementById("healthBadge").textContent="SYSTEM · "+(sys.health||"UNKNOWN");
  document.getElementById("healthBadge").className="badge "+(sys.health==="HEALTHY"?"ok":"bad");

  document.getElementById("freshBadge").textContent="FRESHNESS · "+freshness;
  document.getElementById("freshBadge").className="badge "+
    (freshness==="CURRENT"?"ok":freshness.startsWith("AGING")?"warn":"bad");

  document.getElementById("symbol").textContent=market.symbol||state.symbol;
  document.getElementById("price").textContent=fmt(market.price,2);

  document.getElementById("marketLine").textContent=
    `${market.status||"UNKNOWN"} · ${market.timeframe||state.interval} · ${state.mode}`;

  document.getElementById("freshLine").textContent=
    `Snapshot ${freshness} · ${fresh.generated_at||"—"}`;

  const decision=String(idm.decision||"WAIT").toUpperCase();
  const decisionEl=document.getElementById("decision");
  decisionEl.textContent=decision;
  decisionEl.className="decision "+cls(decision);

  const headlineDirection=idm.direction||"NEUTRAL";
  const decisionContext=document.getElementById("decisionContext");
  decisionContext.innerHTML=
    directionIcon(headlineDirection)+" "+
    esc(headlineDirection)+" · Priority "+esc(idm.priority||"—");
  decisionContext.className=
    "decision-context "+directionClass(headlineDirection);

  document.getElementById("zoneContext").textContent=
    `${idm.zone||"NONE"} · ${idm.zone_lifecycle||"UNKNOWN"} · ${idm.location||"UNKNOWN"}`;

  document.getElementById("score").textContent=fmt(idm.score);
  document.getElementById("confidence").textContent=fmt(idm.confidence)+"%";
  document.getElementById("grade").textContent=idm.grade||"—";
  document.getElementById("readiness").textContent=idm.readiness||"—";

  setPipeline("pipeMarket",market.status||"UNKNOWN");
  setPipeline("pipeIdm",idm.decision||"WAIT");
  setPipeline("pipeRisk",risk.status||"UNKNOWN");
  setPipeline("pipeExec",exe.mode||"UNKNOWN");

  document.getElementById("chartMeta").textContent=
    `${state.candles.length} candles · ${market.timeframe||state.interval}`;

  document.getElementById("idmRows").innerHTML=[
    row("Decision",idm.decision),
    row("Approved",idm.approved?"YES":"NO"),
    row("Direction",directionMarkup(idm.direction)),
    row("Score",fmt(idm.score)),
    row("Confidence",fmt(idm.confidence)+"%"),
    row("Grade",idm.grade),
    row("Priority",idm.priority),
    row("Readiness",idm.readiness),
    row("Trigger",idm.trigger),
    row("Confirmed",idm.trigger_confirmed?"YES":"NO")
  ].join("");

  document.getElementById("structureRows").innerHTML=[
    row("Trend",st.trend),
    row("BOS",st.bos),
    row("CHoCH",st.choch),
    row("Direction",directionMarkup(st.direction)),
    row("State",st.state),
    row("Readiness",st.readiness),
    row("Trigger",st.trigger),
    row("Zone",st.zone_type),
    row("Zone Direction",directionMarkup(st.zone_direction)),
    row("Lifecycle",st.zone_lifecycle)
  ].join("");

  document.getElementById("riskRows").innerHTML=[
    row("Approved",risk.approved?"YES":"NO"),
    row("Status",risk.status),
    row("Position",fmt(risk.position_size,4)),
    row("Risk %",fmt(risk.risk_percent)+"%"),
    row("Risk Amount",fmt(risk.risk_amount)),
    row("Exposure",fmt(risk.exposure)),
    row("Reason",risk.reason||"—")
  ].join("");

  document.getElementById("executionRows").innerHTML=[
    row("Mode",exe.mode),
    row("Ready",exe.ready?"YES":"NO"),
    row("Approved",exe.approved?"YES":"NO"),
    row("Status",exe.status),
    row("Gate",exe.gate),
    row("Broker",exe.broker),
    row("Authorization",exe.authorization_id??"NONE")
  ].join("");

  document.getElementById("executionReason").textContent=
    exe.reason||"No execution reason recorded.";

  const reasons=Array.isArray(idm.decision_reasons)?idm.decision_reasons:[];

  document.getElementById("reasons").innerHTML=
    reasons.length
      ? reasons.map(x=>`<div class="reason">• ${esc(x)}</div>`).join("")
      : `<div class="reason">No IDM decision reason recorded.</div>`;

  document.getElementById("mtf").innerHTML=["15m","1h","4h","1d"].map(tf=>{
    const a=mtf[tf]||{};
    return `
      <div class="mtf-card">
        <div class="mtf-title">${tf}</div>
        ${row("Trend",directionMarkup(a.trend))}
        ${row("RSI",a.rsi==null?"—":Number(a.rsi).toFixed(2))}
        ${row("Signal",a.rsi_signal)}
        ${row("Volume",a.volume_signal)}
        ${row("ATR",a.atr==null?"—":Number(a.atr).toFixed(2))}
        ${row("Volatility",a.atr_volatility)}
        ${row("VWAP",a.vwap_signal)}
      </div>
    `;
  }).join("");

  document.getElementById("systemRows").innerHTML=[
    row("Health",sys.health),
    row("Execution Mode",sys.mode),
    row("Authority","READ-ONLY"),
    row("Live Authority","NONE")
  ].join("");

  document.getElementById("marketRows").innerHTML=[
    row("Symbol",market.symbol),
    row("Timeframe",market.timeframe),
    row("Price",fmt(market.price)),
    row("Status",market.status),
    row("Market Time",prettyTime(fresh.market_timestamp)),
    row("Freshness",freshness)
  ].join("");

  const broker=portfolio.broker||{};
  const account=portfolio.account||{};
  const rec=portfolio.reconciliation||{};

  document.getElementById("portfolioRows").innerHTML=[
    row("Portfolio",portfolio.status),
    row("Equity",portfolio.equity??"—"),
    row("Cash",portfolio.available_cash??"—"),
    row("Broker",broker.status||"—"),
    row("Account",account.status||"—"),
    row("Reconciliation",rec.status||"—")
  ].join("");

  document.getElementById("auditRows").innerHTML=[
    row("Run ID",audit.run_id??"NONE"),
    row("Decision ID",audit.decision_id??"NONE"),
    row("Timestamp",audit.timestamp||"—")
  ].join("");

  renderSession();
  renderMarkets();
  renderChart();
  renderWatch();
}

function renderChart(){
  const canvas=document.getElementById("chart");
  const rect=canvas.getBoundingClientRect();
  const dpr=window.devicePixelRatio||1;

  const width=Math.max(1,Math.floor(rect.width*dpr));
  const height=Math.max(240,Math.floor(320*dpr));

  canvas.width=width;
  canvas.height=height;

  const ctx=canvas.getContext("2d");
  if(!ctx){
    return;
  }

  ctx.clearRect(0,0,width,height);

  const candles=Array.isArray(state.candles)?state.candles:[];

  if(!candles.length){
    ctx.fillStyle="#8193a7";
    ctx.font=`${12*dpr}px system-ui`;
    ctx.fillText("No canonical candle data available",14*dpr,24*dpr);
    return;
  }

  const visibleCount=Math.min(160,candles.length);
  const visibleStart=candles.length-visibleCount;
  const visible=candles.slice(visibleStart);

  const closes=candles.map(c=>Number(c.close));

  const series={
    EMA20:emaSeries(closes,20),
    EMA50:emaSeries(closes,50),
    EMA100:emaSeries(closes,100),
    EMA200:emaSeries(closes,200),
    VWAP:vwapSeries(candles)
  };

  const finiteValues=[];

  for(const c of visible){
    for(const key of ["high","low"]){
      const n=Number(c[key]);
      if(Number.isFinite(n)){
        finiteValues.push(n);
      }
    }
  }

  for(const name of ["EMA20","EMA50","EMA100","EMA200","VWAP"]){
    if(!state.chartIndicators[name]){
      continue;
    }

    for(let i=visibleStart;i<candles.length;i++){
      const n=series[name][i];
      if(Number.isFinite(n)){
        finiteValues.push(n);
      }
    }
  }

  if(!finiteValues.length){
    return;
  }

  let min=Math.min(...finiteValues);
  let max=Math.max(...finiteValues);

  if(min===max){
    min-=1;
    max+=1;
  }

  const pad=(max-min)*0.08;
  min-=pad;
  max+=pad;

  const left=10*dpr;
  const right=8*dpr;
  const top=10*dpr;
  const bottom=18*dpr;

  const plotW=Math.max(1,width-left-right);
  const plotH=Math.max(1,height-top-bottom);

  const xStep=plotW/visibleCount;
  const candleW=Math.max(1.5*dpr,xStep*.56);

  const yOf=(price)=>{
    return top+(max-price)/(max-min)*plotH;
  };

  // Grid
  ctx.strokeStyle="rgba(122,151,171,.12)";
  ctx.lineWidth=1*dpr;

  for(let i=0;i<=5;i++){
    const y=top+(plotH/5)*i;
    ctx.beginPath();
    ctx.moveTo(left,y);
    ctx.lineTo(left+plotW,y);
    ctx.stroke();
  }

  // Candles
  for(let i=0;i<visible.length;i++){
    const c=visible[i];

    const o=Number(c.open);
    const h=Number(c.high);
    const l=Number(c.low);
    const cl=Number(c.close);

    if(![o,h,l,cl].every(Number.isFinite)){
      continue;
    }

    const x=left+i*xStep+xStep/2;

    const yo=yOf(o);
    const yh=yOf(h);
    const yl=yOf(l);
    const yc=yOf(cl);

    const rising=cl>=o;

    ctx.strokeStyle=rising
      ? "rgba(83,227,155,.95)"
      : "rgba(255,104,121,.95)";

    ctx.fillStyle=rising
      ? "rgba(83,227,155,.90)"
      : "rgba(255,104,121,.90)";

    ctx.lineWidth=Math.max(1,dpr);

    ctx.beginPath();
    ctx.moveTo(x,yh);
    ctx.lineTo(x,yl);
    ctx.stroke();

    const bodyY=Math.min(yo,yc);
    const bodyH=Math.max(1*dpr,Math.abs(yc-yo));

    ctx.fillRect(
      x-candleW/2,
      bodyY,
      candleW,
      bodyH
    );
  }

  const indicatorColors={
    EMA20:"#ffd35a",
    EMA50:"#38d7ff",
    EMA100:"#a78bfa",
    EMA200:"#ff8e9b",
    VWAP:"#53e39b"
  };

  const pointsFor=(name)=>{
    const arr=series[name];

    return visible.map((_,i)=>{
      const globalIndex=visibleStart+i;
      const value=arr[globalIndex];

      if(!Number.isFinite(value)){
        return null;
      }

      return {
        x:left+i*xStep+xStep/2,
        y:yOf(value)
      };
    });
  };

  for(const name of ["EMA20","EMA50","EMA100","EMA200","VWAP"]){
    if(!state.chartIndicators[name]){
      continue;
    }

    ctx.strokeStyle=indicatorColors[name];
    ctx.lineWidth=1.5*dpr;
    linePath(ctx,pointsFor(name));
  }

  // Right-side price marker.
  ctx.fillStyle="#9fb1c1";
  ctx.font=`${8*dpr}px system-ui`;
  ctx.textAlign="right";
  ctx.fillText(
    fmt(max,2),
    width-right,
    top+8*dpr
  );
  ctx.fillText(
    fmt(min,2),
    width-right,
    height-bottom
  );

  ctx.textAlign="left";

  // Legend.
  document.getElementById("chartLegend").innerHTML=[
    ["EMA20","#ffd35a"],
    ["EMA50","#38d7ff"],
    ["EMA100","#a78bfa"],
    ["EMA200","#ff8e9b"],
    ["VWAP","#53e39b"]
  ].filter(x=>state.chartIndicators[x[0]])
   .map(x=>`
     <span class="legend-item">
       <span class="legend-line" style="background:${x[1]}"></span>
       ${x[0]}
     </span>
   `)
   .join("");
}

function load(){
  try{
    const url=
      `/dashboard/state?symbol=${encodeURIComponent(state.symbol)}`+
      `&interval=${encodeURIComponent(state.interval)}`+
      `&mode=${encodeURIComponent(state.mode)}`;

    const r=await fetch(url,{cache:"no-store"});
    if(!r.ok) throw new Error("HTTP "+r.status);

    const d=await r.json();

    if(!d||!d.ui) throw new Error("Invalid dashboard state");


function renderSession(){
  const box=document.getElementById("sessionPanel");
  if(!box){
    return;
  }

  const s=(state.ui&&state.ui.session)||{};
  const name=s.session||"UNAVAILABLE";
  const score=Number(s.score||0);
  const reasons=Array.isArray(s.reasons)?s.reasons:[];

  const sessionClass=
    name==="UNAVAILABLE"
      ? "coverage-status unavailable"
      : "coverage-status analysis";

  box.innerHTML=`
    <div class="session-tile">
      <div class="session-label">SESSION</div>
      <div class="session-value">${esc(name)}</div>
    </div>

    <div class="session-tile">
      <div class="session-label">SESSION SCORE</div>
      <div class="session-value">${Number.isFinite(score)?score:"—"}</div>
    </div>

    <div class="session-tile">
      <div class="session-label">ENGINE STATUS</div>
      <div class="${sessionClass}">
        ${esc(s.status||"UNAVAILABLE")}
      </div>
      <div class="session-reason">
        ${esc(reasons.join(" · ")||"No session reason available.")}
      </div>
    </div>
  `;
}

function renderMarkets(){
  const box=document.getElementById("marketCoverage");
  if(!box){
    return;
  }

  box.innerHTML=marketGroups.map(group=>`
    <div class="coverage-group">
      <div class="coverage-head">
        <div>
          <div class="coverage-label">${esc(group.name)}</div>
          <div class="coverage-provider">${esc(group.provider)}</div>
        </div>
        <span class="coverage-status ${esc(group.statusClass)}">
          ${esc(group.status)}
        </span>
      </div>

      <div class="coverage-assets">
        ${group.assets.map(symbol=>`
          <button
            class="coverage-asset"
            data-symbol="${esc(symbol)}"
            title="Load ${esc(symbol)}"
          >${esc(symbol)}</button>
        `).join("")}
      </div>
    </div>
  `).join("");

  box.querySelectorAll(".coverage-asset").forEach(btn=>{
    btn.onclick=()=>{
      state.symbol=btn.dataset.symbol;
      load();
    };
  });
}

function initIndicatorControls(){
  const toolbar=document.getElementById("indicatorToolbar");
  if(!toolbar){
    return;
  }

  toolbar.querySelectorAll(".indicator-toggle").forEach(btn=>{
    btn.onclick=()=>{
      const name=btn.dataset.indicator;

      state.chartIndicators[name]=!state.chartIndicators[name];

      btn.classList.toggle(
        "active",
        !!state.chartIndicators[name]
      );

      renderChart();
    };
  });
}


    state.ui=d.ui;
    state.candles=Array.isArray(d.candles)?d.candles:[];

    render();
  }catch(e){
    document.getElementById("healthBadge").textContent="SYSTEM · ERROR";
    document.getElementById("healthBadge").className="badge bad";
    document.getElementById("freshBadge").textContent="FRESHNESS · ERROR";
    document.getElementById("freshBadge").className="badge bad";
    console.error(e);
  }
}

document.getElementById("aiForm").addEventListener("submit",async e=>{
  e.preventDefault();

  const input=document.getElementById("aiInput");
  const q=input.value.trim();

  if(!q)return;

  const log=document.getElementById("aiLog");

  log.insertAdjacentHTML(
    "beforeend",
    `<div class="msg user">You: ${esc(q)}</div>`
  );

  input.value="";

  try{
    const r=await fetch("/assistant/chat",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        question:q,
        symbol:state.symbol,
        interval:state.interval,
        mode:state.mode
      })
    });

    const d=await r.json();

    if(!r.ok)throw new Error(d.detail||("HTTP "+r.status));

    log.insertAdjacentHTML(
      "beforeend",
      `<div class="msg bot">Jaguar: ${esc(d.reply||"No response.")}</div>`
    );
  }catch(err){
    log.insertAdjacentHTML(
      "beforeend",
      `<div class="msg bot">Assistant unavailable: ${esc(err.message)}</div>`
    );
  }

  log.scrollTop=log.scrollHeight;
});

window.addEventListener("resize",()=>{
  if(state.ui)renderChart();
});

renderWatch();
initIndicatorControls();
load();
setInterval(load,10000);
</script>
</body>
</html>"""
