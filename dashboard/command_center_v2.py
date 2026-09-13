"""
Jaguar Quant X — Command Center V2.
Presentation only. No trading authority.
"""

from __future__ import annotations


def render_command_center_v2() -> str:
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#05070a">
<title>Jaguar Quant X — Command Center</title>
<style>
:root{
--bg:#05070a;--panel:#0b1016;--line:rgba(255,255,255,.08);
--gold:#d4af37;--cyan:#62dcff;--green:#53e39b;--yellow:#ffd35a;
--red:#ff6b6b;--text:#edf1f7;--muted:#7f8999;--muted2:#596373
}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--bg);color:var(--text);
font-family:Inter,Segoe UI,Roboto,Arial,sans-serif}
body{background:
radial-gradient(circle at 90% -10%,rgba(212,175,55,.10),transparent 30%),
radial-gradient(circle at -10% 35%,rgba(0,216,255,.05),transparent 28%),var(--bg)}
button,input,select{font:inherit}
button{cursor:pointer}
.shell{max-width:1500px;margin:auto;padding:14px}
.brand-logo{width:48px;height:48px;display:block;object-fit:cover;border-radius:50%;
border:1px solid rgba(212,175,55,.42);box-shadow:0 0 18px rgba(212,175,55,.12)}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:14px;
padding:14px 16px;border:1px solid rgba(212,175,55,.20);border-radius:18px;
background:rgba(9,13,18,.94);backdrop-filter:blur(18px)}
.brand-wrap{display:flex;align-items:center;gap:11px;min-width:0}
.brand-mark{width:42px;height:42px;display:grid;place-items:center;border:1px solid rgba(212,175,55,.35);
border-radius:12px;background:linear-gradient(145deg,rgba(212,175,55,.16),rgba(0,216,255,.04))}
.brand{font-size:21px;font-weight:900;letter-spacing:1.3px;white-space:nowrap}
.brand span{color:var(--gold)}
.subtitle{font-size:9px;letter-spacing:2px;color:var(--muted);margin-top:3px}
.top-actions{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.pill{display:inline-flex;align-items:center;gap:6px;padding:7px 10px;border-radius:999px;
font-size:9px;font-weight:800;letter-spacing:.6px;border:1px solid var(--line);
background:rgba(255,255,255,.035);color:var(--text)}
.pill.paper{color:var(--cyan);border-color:rgba(98,220,255,.25);background:rgba(98,220,255,.07)}
.dot{width:7px;height:7px;border-radius:50%;background:currentColor}
.select{background:var(--panel);color:var(--text);border:1px solid var(--line);
border-radius:10px;padding:9px 11px;outline:none}
.toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:11px}
.layout{display:grid;grid-template-columns:210px minmax(0,1fr) 310px;gap:13px;margin-top:13px}
.card{background:rgba(9,14,20,.92);border:1px solid var(--line);border-radius:16px;
padding:15px;box-shadow:0 10px 32px rgba(0,0,0,.18)}
.section-title{font-size:10px;color:var(--gold);font-weight:850;letter-spacing:1.3px;
text-transform:uppercase;margin-bottom:11px}
.watchlist{display:flex;flex-direction:column;gap:6px}
.asset{width:100%;text-align:left;padding:10px;border:1px solid transparent;border-radius:10px;
background:rgba(255,255,255,.025);color:var(--text)}
.asset.active{border-color:rgba(212,175,55,.45);background:rgba(212,175,55,.08)}
.asset-symbol{font-size:12px;font-weight:800}
.asset-name{font-size:10px;color:var(--muted);margin-top:2px}
.asset-state{font-size:8px;color:var(--muted2);margin-top:5px}
.main{min-width:0}
.hero{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:15px}
.symbol-line{font-size:10px;color:var(--muted);letter-spacing:1px}
.symbol{color:var(--text);font-size:18px;font-weight:850;margin-left:5px}
.price{font-size:38px;font-weight:900;margin-top:4px}
.direction{margin-top:4px;font-size:11px;font-weight:800}
.meta{font-size:10px;color:var(--muted);margin-top:4px}
.hero-side{text-align:right}
.decision{font-size:32px;font-weight:900;color:var(--yellow)}
.decision.ok{color:var(--green)} .decision.danger{color:var(--red)}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:14px;grid-column:1/-1}
.stat{padding:10px;border-radius:11px;background:rgba(255,255,255,.025)}
.stat-label{font-size:8px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px}
.stat-value{font-size:16px;font-weight:800;margin-top:4px}
.ok{color:var(--green)} .wait{color:var(--yellow)} .danger{color:var(--red)} .neutral{color:#d8dde7}
.chart-wrap{margin-top:13px;padding:12px;border-radius:15px;background:rgba(255,255,255,.018);
border:1px solid var(--line)}
.chart-head{display:flex;justify-content:space-between;align-items:center;gap:8px}
.chart-meta{font-size:9px;color:var(--muted)}
.chart{width:100%;height:300px;display:block;margin-top:6px}
.mini-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:13px}
.row{display:flex;justify-content:space-between;gap:9px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.row:last-child{border-bottom:0}
.row span{color:var(--muted);font-size:10px}
.row strong{font-size:10px;text-align:right;overflow-wrap:anywhere}
.mtf{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
.mtf-frame{border:1px solid var(--line);border-radius:11px;padding:10px;background:rgba(255,255,255,.018);min-width:0}
.mtf-title{font-size:11px;font-weight:850;margin-bottom:5px}
.fresh{display:flex;justify-content:space-between;align-items:center;gap:9px;margin-top:10px;padding:9px 11px;
border-radius:11px;border:1px solid var(--line);background:rgba(255,255,255,.02)}
.fresh-badge{padding:5px 8px;border-radius:999px;font-size:8px;font-weight:850}
.fresh-current{color:var(--green);background:rgba(83,227,155,.08)}
.fresh-aging{color:var(--yellow);background:rgba(255,211,90,.08)}
.fresh-stale{color:var(--red);background:rgba(255,107,107,.08)}
.ai-messages{height:330px;overflow:auto}
.msg{padding:9px 10px;border-radius:11px;margin:7px 0;font-size:10px;line-height:1.45;white-space:pre-wrap}
.msg.bot{background:rgba(212,175,55,.07);border-left:2px solid var(--gold)}
.msg.user{background:rgba(98,220,255,.07);border-right:2px solid var(--cyan)}
.ai-form{display:flex;gap:6px;margin-top:8px}
.ai-input{flex:1;min-width:0;background:rgba(255,255,255,.035);color:var(--text);
border:1px solid var(--line);border-radius:10px;padding:9px 10px}
.send{border:1px solid rgba(212,175,55,.35);background:rgba(212,175,55,.10);color:var(--gold);
border-radius:10px;padding:0 11px;font-weight:850}
.gate{margin-top:8px;padding:9px;border-radius:10px;background:rgba(255,211,90,.05);
border-left:3px solid var(--yellow);font-size:10px;line-height:1.45}
.footer{margin:13px 2px 4px;text-align:center;color:var(--muted2);font-size:8px}
@media(max-width:1100px){.layout{grid-template-columns:185px minmax(0,1fr)}.right{grid-column:1/-1}}
@media(max-width:760px){
.shell{padding:9px}.topbar{padding:11px}.brand{font-size:17px}.layout{grid-template-columns:1fr}
.left{order:2}.main{order:1}.right{order:3;grid-column:auto}
.watchlist{flex-direction:row;overflow-x:auto}.asset{min-width:100px}
.hero{grid-template-columns:1fr}.hero-side{text-align:left}.price{font-size:31px}
.decision{font-size:27px}.stats{grid-template-columns:1fr 1fr}.mini-grid{grid-template-columns:1fr}
.mtf{grid-template-columns:1fr 1fr}.chart{height:245px}}
@media(max-width:430px){.mtf{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="shell">
<header class="topbar">
<div class="brand-wrap">
<img class="brand-logo" src="/dashboard/assets/jaguar_quant_x_logo.png"
alt="Jaguar Quant X logo" width="48" height="48" decoding="async">
<div><div class="brand">JAGUAR <span>QUANT X</span></div>
<div class="subtitle">INSTITUTIONAL TRADING INTELLIGENCE</div></div>
</div>
<div class="top-actions">
<span class="pill paper" id="executionModePill"><span class="dot"></span> EXECUTION —</span>
<span class="pill" id="healthPill">SYSTEM —</span>
<button class="pill" id="refreshButton">↻ Refresh</button>
</div>
</header>

<div class="toolbar">
<select id="intervalSelect" class="select"><option>5m</option><option selected>15m</option><option>1h</option><option>4h</option><option>1d</option></select>
<select id="modeSelect" class="select"><option>SCALP</option><option selected>SWING</option><option>CLASSIC</option></select>
<span class="pill">READ-ONLY OPERATOR CONSOLE</span>
</div>

<div class="layout">
<aside class="left card"><div class="section-title">MARKETS</div><div id="watchlist" class="watchlist"></div></aside>

<main class="main">
<section class="card hero">
<div><div class="symbol-line"><span class="symbol" id="symbol">BTCUSDT</span> · <span id="timeframe">15m</span></div>
<div class="price" id="price">—</div><div class="direction" id="direction">Loading…</div>
<div class="meta" id="marketMeta">Canonical Jaguar analysis</div></div>
<div class="hero-side"><div class="section-title">IDM AUTHORITY</div>
<div class="decision" id="decision">WAIT</div><div class="meta" id="grade">Grade —</div></div>
<div class="stats">
<div class="stat"><div class="stat-label">Score</div><div class="stat-value" id="score">—</div></div>
<div class="stat"><div class="stat-label">Confidence</div><div class="stat-value" id="confidence">—</div></div>
<div class="stat"><div class="stat-label">Risk</div><div class="stat-value" id="riskStatus">—</div></div>
<div class="stat"><div class="stat-label">Execution</div><div class="stat-value" id="executionStatus">—</div></div>
</div>
</section>

<section class="chart-wrap"><div class="chart-head">
<div class="section-title" style="margin:0">PRICE STRUCTURE</div><div class="chart-meta" id="candleMeta">Candles —</div>
</div><canvas id="chart" class="chart"></canvas></section>

<section class="mini-grid">
<div class="card"><div class="section-title">STRUCTURE</div><div id="structureRows"></div></div>
<div class="card"><div class="section-title">RISK / EXECUTION</div><div id="riskRows"></div></div>
</section>

<section class="card" style="margin-top:13px"><div class="section-title">MULTI-TIMEFRAME MARKET CONTEXT</div><div id="mtf" class="mtf"></div></section>

<section class="fresh"><div><div style="font-size:8px;color:var(--muted);text-transform:uppercase">Canonical Snapshot</div>
<div id="freshTime" style="font-size:9px;margin-top:3px">—</div></div><div id="freshBadge" class="fresh-badge fresh-current">CURRENT</div></section>

<section class="card" style="margin-top:13px"><div class="section-title">WHY JAGUAR DECIDED THIS</div><div id="reasons"></div></section>
</main>

<aside class="right">
<section class="card"><div style="display:flex;justify-content:space-between;align-items:center">
<div class="section-title" style="margin:0">JAGUAR AI</div><div style="color:var(--cyan);font-size:8px">READ-ONLY</div></div>
<div class="ai-messages" id="aiMessages"><div class="msg bot">Jaguar AI is connected to the canonical analysis boundary. Ask about the selected market.</div></div>
<form id="aiForm" class="ai-form"><input id="aiInput" class="ai-input" autocomplete="off" placeholder="Ask Jaguar about this setup…"><button class="send" type="submit">Send</button></form>
</section>

<section class="card" style="margin-top:13px"><div class="section-title">EXECUTION GATE</div><div id="gateRows"></div><div id="gateReason"></div></section>
</aside>
</div>
<div class="footer">JAGUAR QUANT X · READ-ONLY OPERATOR CONSOLE · <span id="footerExecutionMode">EXECUTION —</span> · NO LIVE AUTHORITY</div>
</div>

<script>
const WATCHLIST=[
["BTCUSDT","Bitcoin"],["ETHUSDT","Ethereum"],["SOLUSDT","Solana"],
["BNBUSDT","BNB"],["RELIANCE.NS","Reliance"],["TCS.NS","TCS"]];
const s={symbol:"BTCUSDT",interval:"15m",mode:"SWING",ui:null,candles:[]};
function esc(v){return String(v??"—").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));}
function fmt(v,d=2){const n=Number(v);return Number.isFinite(n)?n.toLocaleString(undefined,{minimumFractionDigits:d,maximumFractionDigits:d}):"—";}
function cls(v){const x=String(v||"").toUpperCase();if(["READY","APPROVED","HEALTHY"].includes(x))return"ok";if(["WAIT","PENDING"].includes(x))return"wait";if(["BLOCKED","REJECTED","FAILED"].includes(x))return"danger";return"neutral";}
function row(a,b){return '<div class="row"><span>'+esc(a)+'</span><strong>'+esc(b)+'</strong></div>';}
function watch(){const e=document.getElementById("watchlist");e.innerHTML=WATCHLIST.map(([a,n])=>'<button class="asset '+(a===s.symbol?"active":"")+'" data-s="'+esc(a)+'"><div class="asset-symbol">'+esc(a)+'</div><div class="asset-name">'+esc(n)+'</div><div class="asset-state">'+(a===s.symbol?"SELECTED":"VIEW ANALYSIS")+'</div></button>').join("");e.querySelectorAll(".asset").forEach(b=>b.onclick=()=>{s.symbol=b.dataset.s;load();});}
function chart(){const c=document.getElementById("chart"),r=c.getBoundingClientRect(),d=devicePixelRatio||1;c.width=Math.max(1,Math.floor(r.width*d));c.height=Math.max(1,Math.floor(r.height*d));const x=c.getContext("2d");x.scale(d,d);x.clearRect(0,0,r.width,r.height);const data=s.candles.slice(-120);if(data.length<2){x.fillStyle="#596373";x.font="12px Arial";x.fillText("No canonical candle data available",12,22);return;}const hi=data.map(a=>+a.high).filter(Number.isFinite),lo=data.map(a=>+a.low).filter(Number.isFinite);const max=Math.max(...hi),min=Math.min(...lo),range=Math.max(max-min,1),pl=8,pt=12,pb=22,pw=r.width-pl-8,ph=r.height-pt-pb,step=pw/data.length,bw=Math.max(2,step*.55),y=v=>pt+(max-v)/range*ph;x.strokeStyle="rgba(255,255,255,.045)";for(let i=1;i<5;i++){const gy=pt+ph*i/5;x.beginPath();x.moveTo(pl,gy);x.lineTo(r.width-8,gy);x.stroke();}data.forEach((a,i)=>{const o=+a.open,h=+a.high,l=+a.low,cl=+a.close;if(![o,h,l,cl].every(Number.isFinite))return;const px=pl+i*step+step/2,up=cl>=o;x.strokeStyle=x.fillStyle=up?"#53e39b":"#ff6b6b";x.beginPath();x.moveTo(px,y(h));x.lineTo(px,y(l));x.stroke();const top=Math.min(y(o),y(cl)),bh=Math.max(1,Math.abs(y(o)-y(cl)));x.fillRect(px-bw/2,top,bw,bh);});}
function render(){const u=s.ui||{},m=u.market||{},i=u.idm||{},st=u.structure||{},r=u.risk||{},e=u.execution||{},mt=u.mtf||{},f=u.freshness||{};document.getElementById("symbol").textContent=m.symbol||s.symbol;document.getElementById("timeframe").textContent=m.timeframe||s.interval;document.getElementById("price").textContent=fmt(m.price);document.getElementById("direction").textContent="Market status: "+(m.status||"—")+" · "+(i.direction||"NEUTRAL");document.getElementById("marketMeta").textContent="Profile "+s.mode+" · Priority "+(i.priority||"—");const de=document.getElementById("decision");de.textContent=i.decision||"WAIT";de.className="decision "+cls(i.decision);document.getElementById("grade").textContent="Grade "+(i.grade||"—");document.getElementById("score").textContent=fmt(i.score);document.getElementById("confidence").textContent=fmt(i.confidence)+"%";document.getElementById("riskStatus").textContent=r.status||"UNKNOWN";document.getElementById("riskStatus").className="stat-value "+cls(r.status);document.getElementById("executionStatus").textContent=e.status||"WAIT";document.getElementById("executionStatus").className="stat-value "+cls(e.status);document.getElementById("structureRows").innerHTML=[row("Trend",st.trend),row("BOS",st.bos),row("CHoCH",st.choch),row("Direction",st.direction),row("State",st.state),row("Readiness",st.readiness),row("Trigger",st.trigger),row("Zone",st.zone_type),row("Zone Direction",st.zone_direction),row("Lifecycle",st.zone_lifecycle)].join("");document.getElementById("riskRows").innerHTML=[row("Approved",r.approved?"YES":"NO"),row("Position",fmt(r.position_size,4)),row("Risk %",fmt(r.risk_percent)+"%"),row("Risk Amount",fmt(r.risk_amount)),row("Exposure",fmt(r.exposure)),row("Broker",e.broker),row("Gate",e.gate)].join("");document.getElementById("mtf").innerHTML=["15m","1h","4h","1d"].map(t=>{const a=mt[t]||{};return '<div class="mtf-frame"><div class="mtf-title">'+t+'</div>'+row("Trend",a.trend)+row("RSI",a.rsi==null?"—":Number(a.rsi).toFixed(2))+row("RSI Signal",a.rsi_signal)+row("Volume",a.volume_signal)+row("ATR",a.atr==null?"—":Number(a.atr).toFixed(2))+row("VWAP",a.vwap_signal)+'</div>';}).join("");const reasons=Array.isArray(i.decision_reasons)?i.decision_reasons:[];document.getElementById("reasons").innerHTML=reasons.length?reasons.map(v=>'<div class="reason">• '+esc(v)+'</div>').join(""):'<div class="reason">No IDM decision reason recorded.</div>';document.getElementById("gateRows").innerHTML=[row("Gate",e.gate),row("Ready",e.ready?"YES":"NO"),row("Approved",e.approved?"YES":"NO"),row("Broker",e.broker)].join("");document.getElementById("gateReason").innerHTML=e.reason?'<div class="gate">'+esc(e.reason)+'</div>':"";document.getElementById("freshTime").textContent=f.generated_at||"—";const age=Date.now()/1000-Number(f.generated_epoch||0),b=document.getElementById("freshBadge");if(age<=120){b.textContent="CURRENT";b.className="fresh-badge fresh-current";}else if(age<=600){b.textContent="AGING · "+Math.round(age/60)+"m";b.className="fresh-badge fresh-aging";}else{b.textContent="STALE · "+Math.round(age/60)+"m";b.className="fresh-badge fresh-stale";}const system=u.system||{};const executionMode=String(system.mode||"UNKNOWN").toUpperCase();const modePill=document.getElementById("executionModePill");modePill.textContent="EXECUTION · "+executionMode;modePill.className="pill "+(executionMode==="PAPER"?"paper":executionMode==="LIVE"?"danger":"");document.getElementById("healthPill").textContent="SYSTEM "+(system.health||"UNKNOWN");document.getElementById("candleMeta").textContent=s.candles.length+" candles · "+s.interval;document.getElementById("footerExecutionMode").textContent="EXECUTION · "+executionMode;watch();chart();}
async function load(){watch();try{const u="/dashboard/state?symbol="+encodeURIComponent(s.symbol)+"&interval="+encodeURIComponent(s.interval)+"&mode="+encodeURIComponent(s.mode);const r=await fetch(u,{cache:"no-store"});if(!r.ok)throw new Error("HTTP "+r.status);const d=await r.json();if(!d||!d.ui)throw new Error("Invalid dashboard state");s.ui=d.ui;s.candles=Array.isArray(d.candles)?d.candles:[];render();}catch(e){document.getElementById("marketMeta").textContent="Dashboard refresh failed: "+e.message;document.getElementById("healthPill").textContent="SYSTEM ERROR";}}
async function ask(q){q=q.trim();if(!q)return;const box=document.getElementById("aiMessages");box.insertAdjacentHTML("beforeend",'<div class="msg user">'+esc(q)+'</div>');const p=document.createElement("div");p.className="msg bot";p.textContent="Jaguar AI is analysing the canonical snapshot…";box.appendChild(p);box.scrollTop=box.scrollHeight;try{const r=await fetch("/assistant/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:q,symbol:s.symbol,interval:s.interval,mode:s.mode})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"HTTP "+r.status);p.textContent=d.reply||"No response.";}catch(e){p.textContent="Assistant unavailable: "+e.message;}box.scrollTop=box.scrollHeight;}
document.getElementById("intervalSelect").onchange=e=>{s.interval=e.target.value;load();};
document.getElementById("modeSelect").onchange=e=>{s.mode=e.target.value;load();};
document.getElementById("refreshButton").onclick=load;
document.getElementById("aiForm").onsubmit=e=>{e.preventDefault();const i=document.getElementById("aiInput"),q=i.value;i.value="";ask(q);};
addEventListener("resize",chart);addEventListener("load",load);setInterval(load,60000);
</script>
</body>
</html>"""
