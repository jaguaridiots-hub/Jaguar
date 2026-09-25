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




.confidence-breakdown{
  margin-top:8px;
}
.confidence-summary{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:8px;
}
.confidence-tile{
  border:1px solid var(--border,#263041);
  border-radius:9px;
  padding:9px;
  min-width:0;
}
.confidence-label{
  font-size:10px;
  letter-spacing:.08em;
  opacity:.65;
  margin-bottom:5px;
}
.confidence-value{
  font-weight:800;
  font-size:16px;
}
.confidence-note{
  font-size:11px;
  opacity:.7;
  margin-top:3px;
}
.confidence-engines{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:6px;
  margin-top:8px;
}
.confidence-engine{
  border:1px solid var(--border,#263041);
  border-radius:8px;
  padding:8px;
}
.confidence-engine-head{
  display:flex;
  justify-content:space-between;
  gap:8px;
  font-weight:700;
}
.confidence-engine-meta{
  font-size:11px;
  opacity:.7;
  margin-top:3px;
  line-height:1.35;
}
.confidence-method{
  margin-top:8px;
  font-size:11px;
  opacity:.65;
}
@media(max-width:700px){
  .confidence-summary{
    grid-template-columns:1fr 1fr;
  }
  .confidence-engines{
    grid-template-columns:1fr;
  }
}
@media(max-width:430px){
  .confidence-summary{
    grid-template-columns:1fr;
  }
}

.decision-gate{
  border:1px solid var(--border,#263041);
  border-radius:12px;
  padding:10px;
  margin-top:8px;
}
.decision-gate-grid{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:8px;
}
.gate-block{
  min-width:0;
  border:1px solid var(--border,#263041);
  border-radius:9px;
  padding:9px;
}
.gate-label{
  font-size:10px;
  letter-spacing:.08em;
  opacity:.65;
  margin-bottom:5px;
}
.gate-value{
  font-weight:700;
  word-break:break-word;
}
.gate-reason{
  margin-top:9px;
  line-height:1.4;
  opacity:.9;
}
.gate-list{
  margin:5px 0 0 16px;
  padding:0;
}
.gate-condition{
  margin-top:4px;
}
.gate-authorized{
  font-weight:800;
}
.gate-blocked{
  font-weight:800;
}
.mtf-sufficiency{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:8px;
  margin-bottom:8px;
}
.mtf-suff-tile{
  border:1px solid var(--border,#263041);
  border-radius:9px;
  padding:8px;
}
.mtf-suff-value{
  font-weight:800;
  font-size:16px;
}
.mtf-suff-note{
  font-size:11px;
  opacity:.7;
  margin-top:3px;
}
@media(max-width:700px){
  .decision-gate-grid{
    grid-template-columns:1fr 1fr;
  }
  .mtf-sufficiency{
    grid-template-columns:1fr 1fr;
  }
}
@media(max-width:430px){
  .decision-gate-grid{
    grid-template-columns:1fr;
  }
  .mtf-sufficiency{
    grid-template-columns:1fr;
  }
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

  /* Mobile: MTF cards must be fully readable.
     Keep multi-column layout only on wider screens. */
  .mtf{
    grid-template-columns:1fr;
  }

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
    grid-template-columns:1fr;
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
    grid-template-columns:1fr;
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
    grid-template-columns:1fr;
  }

  .pipeline{
    grid-template-columns:1fr 1fr;
  }

  .mtf{
    grid-template-columns:1fr;
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


/* CANONICAL FIBONACCI UI */
.fibonacci-card{
  margin-top:8px;
}

.fib-summary{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:6px;
  margin-bottom:8px;
}

.fib-summary-tile{
  padding:9px;
  border:1px solid var(--line2);
  border-radius:9px;
  background:#0a1016;
}

.fib-summary-label{
  color:var(--muted);
  font-size:7px;
  font-weight:900;
  letter-spacing:.1em;
}

.fib-summary-value{
  margin-top:4px;
  font-size:11px;
  font-weight:950;
}

.fib-level-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:8px;
}

.fib-level-panel{
  padding:9px;
  border:1px solid var(--line2);
  border-radius:9px;
  background:#0a1016;
}

.fib-level-title{
  color:var(--gold);
  font-size:8px;
  font-weight:900;
  letter-spacing:.12em;
  margin-bottom:5px;
}

.fib-level{
  display:grid;
  grid-template-columns:64px 1fr;
  gap:7px;
  padding:4px 0;
  border-bottom:1px solid rgba(255,255,255,.045);
  font-size:8px;
}

.fib-level:last-child{
  border-bottom:0;
}

.fib-ratio{
  color:var(--muted);
  font-weight:800;
}

.fib-price{
  text-align:right;
  font-weight:900;
}

.fib-reasons{
  margin-top:7px;
  color:var(--muted);
  font-size:8px;
  line-height:1.5;
}

.fib-premium{
  color:#ffd35a;
}

.fib-discount{
  color:#53e39b;
}

.fib-bullish{
  color:#53e39b;
}

.fib-bearish{
  color:#ff6879;
}

.fib-neutral{
  color:#ffd35a;
}

@media(max-width:700px){
  .fib-summary{
    grid-template-columns:1fr 1fr;
  }

  .fib-summary-tile:last-child{
    grid-column:1 / -1;
  }

  .fib-level-grid{
    grid-template-columns:1fr;
  }
}

@media(max-width:430px){
  .fib-summary{
    grid-template-columns:1fr;
  }

  .fib-summary-tile:last-child{
    grid-column:auto;
  }
}



/* R25_DASHBOARD_TABS_HARDENING_START */
.r24-tab:focus-visible{
  outline:2px solid var(--cyan);
  outline-offset:2px;
}

.r24-tab[aria-selected="false"]{
  opacity:.78;
}

.r24-tab[aria-selected="true"]{
  opacity:1;
}
/* R25_DASHBOARD_TABS_HARDENING_END */

/* R24_DASHBOARD_TABS_UI_START */
.r24-tabs{
  margin-top:10px;
  display:flex;
  gap:6px;
  overflow-x:auto;
  scrollbar-width:none;
  padding:4px;
  border:1px solid var(--line);
  border-radius:12px;
  background:#0a1017;
}

.r24-tabs::-webkit-scrollbar{
  display:none;
}

.r24-tab{
  flex:1 0 auto;
  min-width:92px;
  padding:9px 12px;
  border:1px solid transparent;
  border-radius:9px;
  background:transparent;
  color:var(--muted);
  font-size:9px;
  font-weight:900;
  letter-spacing:.08em;
  cursor:pointer;
}

.r24-tab:hover{
  border-color:var(--line);
  color:var(--text);
}

.r24-tab.r24-active{
  border-color:rgba(56,215,255,.38);
  background:#0d1b24;
  color:var(--cyan);
}

.r24-tab-panel{
  min-width:0;
  display:none !important;
}

.r24-tab-hidden{
  display:none !important;
}

@media (max-width:720px){
  .r24-tabs{
    gap:4px;
    padding:3px;
  }

  .r24-tab{
    min-width:82px;
    padding:8px 9px;
    font-size:8px;
  }
}
/* R24_DASHBOARD_TABS_UI_END */

/* R19_SCANNER_UI_START */
.scanner-card{
  overflow:hidden;
}

.scanner-toolbar{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  margin-bottom:10px;
}

.scanner-symbol{
  min-width:180px;
  padding:8px 10px;
  border:1px solid var(--line, #26303b);
  border-radius:8px;
  background:rgba(255,255,255,.02);
  color:inherit;
  font:inherit;
}

.scanner-action{
  padding:8px 12px;
  border:1px solid var(--line, #26303b);
  border-radius:8px;
  background:rgba(255,255,255,.03);
  color:inherit;
  cursor:pointer;
  font:inherit;
}

.scanner-action:hover{
  background:rgba(255,255,255,.07);
}

.scanner-action:disabled{
  opacity:.55;
  cursor:wait;
}

.scanner-status{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  margin-bottom:12px;
}

.scanner-pill{
  display:inline-flex;
  align-items:center;
  padding:4px 8px;
  border-radius:999px;
  border:1px solid rgba(255,255,255,.12);
  font-size:11px;
  font-weight:800;
  letter-spacing:.04em;
}

.scanner-pill.current{
  border-color:rgba(60,218,160,.28);
}

.scanner-pill.degraded{
  border-color:rgba(245,202,88,.28);
}

.scanner-pill.unavailable{
  border-color:rgba(255,104,121,.3);
}

.scanner-note{
  margin:4px 0 12px;
  font-size:10px;
  opacity:.6;
}

.scanner-error{
  margin:6px 0 10px;
  font-size:11px;
  line-height:1.5;
  opacity:.75;
}

.scanner-list{
  display:grid;
  gap:8px;
}

.scanner-item{
  padding:12px;
  border:1px solid rgba(255,255,255,.07);
  border-radius:9px;
  background:rgba(255,255,255,.015);
}

.scanner-item-head{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap:10px;
}

.scanner-item-symbol{
  font-size:13px;
  font-weight:800;
}

.scanner-item-direction{
  font-size:12px;
  font-weight:900;
  letter-spacing:.05em;
}

.scanner-metrics{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:8px;
  margin-top:10px;
}

.scanner-metric{
  min-width:0;
  padding:8px;
  border:1px solid rgba(255,255,255,.05);
  border-radius:7px;
}

.scanner-metric-label{
  font-size:9px;
  opacity:.55;
  letter-spacing:.06em;
}

.scanner-metric-value{
  margin-top:3px;
  font-size:12px;
  font-weight:800;
}

.scanner-evidence{
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  margin-top:10px;
}

.scanner-evidence-chip{
  padding:4px 7px;
  border-radius:6px;
  border:1px solid rgba(255,255,255,.08);
  font-size:9px;
  opacity:.8;
}

.scanner-candidate-only{
  margin-top:10px;
  font-size:9px;
  font-weight:800;
  letter-spacing:.08em;
  opacity:.55;
}

.scanner-empty{
  padding:20px 12px;
  border:1px dashed rgba(255,255,255,.10);
  border-radius:9px;
  text-align:center;
  font-size:12px;
  opacity:.7;
}

@media(max-width:700px){
  .scanner-symbol{
    min-width:0;
    flex:1 1 160px;
  }

  .scanner-action{
    flex:1 1 140px;
  }

  .scanner-metrics{
    grid-template-columns:repeat(2,minmax(0,1fr));
  }

  .scanner-item-head{
    flex-direction:column;
  }
}
/* R19_SCANNER_UI_END */



/* R23_SCANNER_ALERT_CONTEXT_UI_START */
.scanner-alert-context-card{
  margin-top:16px;
}
.scanner-alert-context-toolbar{
  display:grid;
  grid-template-columns:minmax(150px,1fr) auto auto;
  gap:10px;
  align-items:center;
  margin-bottom:12px;
}
.scanner-alert-context-action{
  min-height:38px;
}
.scanner-alert-context-status{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
  margin-bottom:12px;
}
.scanner-alert-context-list{
  display:grid;
  gap:12px;
}
.scanner-alert-context-item{
  border:1px solid rgba(255,255,255,.08);
  border-radius:12px;
  padding:14px;
}
.scanner-alert-context-news{
  display:grid;
  gap:8px;
  margin-top:12px;
}
.scanner-alert-context-news-item{
  padding:10px;
  border-radius:10px;
  background:rgba(255,255,255,.025);
}
.scanner-alert-context-boundary{
  letter-spacing:.08em;
  font-size:.72rem;
  text-transform:uppercase;
}
@media (max-width:760px){
  .scanner-alert-context-toolbar{
    grid-template-columns:1fr;
  }
  .scanner-alert-context-action{
    width:100%;
  }
}
/* R23_SCANNER_ALERT_CONTEXT_UI_END */
/* R21_SCANNER_ALERT_UI_START */
.scanner-alert-card{
  overflow:hidden;
}

.scanner-alert-toolbar{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  margin-bottom:10px;
}

.scanner-alert-symbol{
  min-width:180px;
  padding:8px 10px;
  border:1px solid var(--line, #26303b);
  border-radius:8px;
  background:rgba(255,255,255,.02);
  color:inherit;
  font:inherit;
}

.scanner-alert-action{
  padding:8px 12px;
  border:1px solid var(--line, #26303b);
  border-radius:8px;
  background:rgba(255,255,255,.03);
  color:inherit;
  cursor:pointer;
}

.scanner-alert-action:disabled{
  opacity:.55;
  cursor:wait;
}

.scanner-alert-status{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  margin-bottom:10px;
}

.scanner-alert-status-pill{
  display:inline-flex;
  align-items:center;
  padding:4px 8px;
  border-radius:999px;
  border:1px solid rgba(255,255,255,.12);
  font-size:11px;
  font-weight:800;
}

.scanner-alert-status-pill.current{
  border-color:rgba(60,218,160,.28);
}

.scanner-alert-status-pill.degraded{
  border-color:rgba(245,202,88,.25);
}

.scanner-alert-status-pill.unavailable{
  border-color:rgba(255,104,121,.3);
}

.scanner-alert-list{
  display:grid;
  gap:8px;
}

.scanner-alert-item{
  padding:12px;
  border:1px solid rgba(255,255,255,.06);
  border-radius:9px;
  background:rgba(255,255,255,.015);
}

.scanner-alert-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:8px;
  flex-wrap:wrap;
}

.scanner-alert-title{
  font-size:13px;
  font-weight:800;
}

.scanner-alert-meta{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:6px;
  font-size:10px;
  opacity:.7;
}

.scanner-alert-explanation{
  margin-top:8px;
  font-size:11px;
  line-height:1.5;
  opacity:.82;
}

.scanner-alert-badge{
  display:inline-flex;
  align-items:center;
  padding:3px 7px;
  border-radius:999px;
  border:1px solid rgba(255,255,255,.12);
  font-size:10px;
  font-weight:800;
}

.scanner-alert-empty{
  padding:20px 12px;
  border:1px dashed rgba(255,255,255,.10);
  border-radius:9px;
  text-align:center;
  font-size:12px;
  opacity:.7;
}

@media (max-width:700px){
  .scanner-alert-symbol{
    min-width:0;
    flex:1 1 130px;
  }

  .scanner-alert-action{
    width:100%;
  }
}
/* R21_SCANNER_ALERT_UI_END */


<!-- R21_SCANNER_ALERT_UI_START -->
<details class="card scanner-alert-card">
  <summary>
    <span>JAGUAR SCANNER ALERTS</span>
    <span class="meta">CONTEXTUAL ALERTS · READ-ONLY</span>
  </summary>

  <div class="content">
    <div class="scanner-alert-toolbar">
      <select
        class="scanner-alert-symbol"
        id="scannerAlertSymbol"
        aria-label="Scanner alert symbol"
      >
        <option value="">CURRENT SYMBOL</option>
        <option value="BTCUSDT">BTCUSDT</option>
        <option value="ETHUSDT">ETHUSDT</option>
        <option value="BNBUSDT">BNBUSDT</option>
        <option value="SOLUSDT">SOLUSDT</option>
        <option value="XRPUSDT">XRPUSDT</option>
        <option value="DOGEUSDT">DOGEUSDT</option>
        <option value="ADAUSDT">ADAUSDT</option>
        <option value="LINKUSDT">LINKUSDT</option>
        <option value="AVAXUSDT">AVAXUSDT</option>
        <option value="XAUUSD">XAUUSD</option>
      </select>

      <button
        class="scanner-alert-action"
        id="scannerAlertScanSymbol"
        type="button"
      >
        SCAN ALERTS
      </button>

      <button
        class="scanner-alert-action"
        id="scannerAlertScanWatchlist"
        type="button"
      >
        SCAN WATCHLIST ALERTS
      </button>
    </div>

    <div
      class="scanner-alert-status"
      id="scannerAlertStatus"
    ></div>

    <div class="scanner-alert-list" id="scannerAlertList">
      <div class="scanner-alert-empty">
        Alert scanner idle. Run an alert scan to discover contextual alerts.
      </div>
    </div>
  </div>
</details>
<!-- R21_SCANNER_ALERT_UI_END -->




/* R21_SCANNER_ALERT_UI_START */
let r21ScannerAlerts = null;

function scannerAlertStatusClass(status){
  const normalized=String(
    status||"UNAVAILABLE"
  ).toUpperCase();

  if(normalized==="CURRENT"){
    return "current";
  }

  if(normalized==="DEGRADED"){
    return "degraded";
  }

  return "unavailable";
}

function renderScannerAlerts(){
  const statusEl=document.getElementById(
    "scannerAlertStatus"
  );

  const listEl=document.getElementById(
    "scannerAlertList"
  );

  if(!statusEl || !listEl){
    return;
  }

  const result=r21ScannerAlerts;

  if(!result){
    statusEl.innerHTML="";
    listEl.innerHTML=
      '<div class="scanner-alert-empty">'+
      'Alert scanner idle. Run an alert scan to discover contextual alerts.'+
      '</div>';
    return;
  }

  const status=String(
    result.status||"UNAVAILABLE"
  ).toUpperCase();

  statusEl.innerHTML=
    '<span class="scanner-alert-status-pill '+
    scannerAlertStatusClass(status)+
    '">'+
    status+
    '</span>'+
    '<span class="meta">'+
    'SCANNED '+
    Number(result.scanned_symbols||0)+
    ' · ALERTS '+
    Number(result.alert_count||0)+
    '</span>';

  if(
    Array.isArray(result.errors) &&
    result.errors.length
  ){
    statusEl.innerHTML+=
      '<span class="meta">'+
      'ERRORS '+
      result.errors.length+
      '</span>';
  }

  const alerts=Array.isArray(result.alerts)
    ? result.alerts
    : [];

  if(!alerts.length){
    listEl.innerHTML=
      '<div class="scanner-alert-empty">'+
      'No contextual scanner alerts found.'+
      '</div>';
    return;
  }

  listEl.innerHTML=alerts.map(
    alert=>{
      const priority=String(
        alert.priority||"MEDIUM"
      ).toUpperCase();

      const direction=String(
        alert.direction||"NEUTRAL"
      ).toUpperCase();

      const factors=Array.isArray(
        alert.dominant_factors
      )
        ? alert.dominant_factors.join(", ")
        : "n/a";

      return `
        <article class="scanner-alert-item">
          <div class="scanner-alert-head">
            <div class="scanner-alert-title">
              ${alert.symbol||"UNKNOWN"}
              · ${direction}
              · ${alert.setup||"CONFLUENCE"}
            </div>

            <span class="scanner-alert-badge">
              ${priority}
            </span>
          </div>

          <div class="scanner-alert-meta">
            <span>TF ${alert.timeframe||"n/a"}</span>
            <span>STATE ${alert.state||"n/a"}</span>
            <span>CONF ${Number(alert.confidence||0)}</span>
            <span>CONFLUENCE ${Number(alert.confluence_score||0)}</span>
            <span>CONFLICTS ${Number(alert.conflict_count||0)}</span>
          </div>

          <div class="scanner-alert-meta">
            <span>FACTORS ${factors}</span>
          </div>

          <div class="scanner-alert-explanation">
            ${alert.explanation||"No explanation available."}
          </div>
        </article>
      `;
    }
  ).join("");
}

async function loadScannerAlerts(symbol=null){
  const symbolEl=document.getElementById(
    "scannerAlertSymbol"
  );

  const scanSymbolEl=document.getElementById(
    "scannerAlertScanSymbol"
  );

  const scanWatchlistEl=document.getElementById(
    "scannerAlertScanWatchlist"
  );

  let activeSymbol=symbol;

  if(activeSymbol===null){
    activeSymbol=
      symbolEl && symbolEl.value
        ? String(symbolEl.value).trim()
        : String(state.symbol||"").trim();
  }

  const buttons=[
    scanSymbolEl,
    scanWatchlistEl
  ].filter(Boolean);

  buttons.forEach(button=>{
    button.disabled=true;
  });

  if(scanSymbolEl){
    scanSymbolEl.textContent="SCANNING…";
  }

  if(scanWatchlistEl){
    scanWatchlistEl.textContent="SCANNING…";
  }

  try{
    const url=
      activeSymbol
        ? `/scanner/alerts?symbol=${encodeURIComponent(activeSymbol)}`
        : "/scanner/alerts";

    const response=await fetch(
      url,
      {cache:"no-store"}
    );

    if(!response.ok){
      throw new Error(
        `HTTP ${response.status}`
      );
    }

    r21ScannerAlerts=await response.json();

    renderScannerAlerts();
  }catch(error){
    r21ScannerAlerts={
      status:"UNAVAILABLE",
      scanned_symbols:0,
      alert_count:0,
      alerts:[],
      errors:[
        {
          error:String(
            error &&
            error.message
              ? error.message
              : error
          )
        }
      ]
    };

    renderScannerAlerts();
  }finally{
    buttons.forEach(button=>{
      button.disabled=false;
    });

    if(scanSymbolEl){
      scanSymbolEl.textContent="SCAN ALERTS";
    }

    if(scanWatchlistEl){
      scanWatchlistEl.textContent=
        "SCAN WATCHLIST ALERTS";
    }
  }
}

function initScannerAlertControls(){
  const symbolEl=document.getElementById(
    "scannerAlertSymbol"
  );

  const scanSymbolEl=document.getElementById(
    "scannerAlertScanSymbol"
  );

  const scanWatchlistEl=document.getElementById(
    "scannerAlertScanWatchlist"
  );

  if(scanSymbolEl){
    scanSymbolEl.onclick=()=>{
      const symbol=
        symbolEl && symbolEl.value
          ? String(symbolEl.value).trim()
          : String(state.symbol||"").trim();

      loadScannerAlerts(symbol);
    };
  }

  if(scanWatchlistEl){
    scanWatchlistEl.onclick=()=>{
      if(symbolEl){
        symbolEl.value="";
      }

      loadScannerAlerts("");
    };
  }

  renderScannerAlerts();
}
/* R21_SCANNER_ALERT_UI_END */





/* R18_NEWS_UI_START */
.news-card{
  overflow:hidden;
}

.news-toolbar{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  margin-bottom:10px;
}

.news-filter{
  min-width:150px;
  padding:8px 10px;
  border:1px solid var(--line, #26303b);
  border-radius:8px;
  background:rgba(255,255,255,.02);
  color:inherit;
  font:inherit;
}

.news-refresh{
  margin-left:auto;
  padding:8px 12px;
  border:1px solid var(--line, #26303b);
  border-radius:8px;
  background:rgba(255,255,255,.03);
  color:inherit;
  cursor:pointer;
}

.news-refresh:hover{
  background:rgba(255,255,255,.07);
}

.news-status{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  margin-bottom:12px;
}

.news-status-pill{
  display:inline-flex;
  align-items:center;
  padding:4px 8px;
  border-radius:999px;
  border:1px solid rgba(255,255,255,.12);
  font-size:11px;
  font-weight:800;
  letter-spacing:.04em;
}

.news-status-pill.current{
  border-color:rgba(60,218,160,.28);
}

.news-status-pill.cached{
  border-color:rgba(245,202,88,.25);
}

.news-status-pill.unavailable{
  border-color:rgba(255,104,121,.3);
}

.news-error{
  margin:6px 0 10px;
  font-size:11px;
  line-height:1.5;
  opacity:.75;
}

.news-list{
  display:grid;
  gap:8px;
}

.news-item{
  display:grid;
  grid-template-columns:minmax(0,1fr) auto;
  gap:10px;
  padding:11px 12px;
  border:1px solid rgba(255,255,255,.06);
  border-radius:9px;
  background:rgba(255,255,255,.015);
}

.news-item-main{
  min-width:0;
}

.news-title{
  font-size:13px;
  line-height:1.45;
  font-weight:700;
}

.news-meta{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:5px;
  font-size:10px;
  opacity:.65;
}

.news-link{
  align-self:center;
  white-space:nowrap;
  font-size:11px;
  text-decoration:none;
}

.news-empty{
  padding:20px 12px;
  border:1px dashed rgba(255,255,255,.10);
  border-radius:9px;
  text-align:center;
  font-size:12px;
  opacity:.7;
}

@media (max-width:700px){
  .news-filter{
    min-width:0;
    flex:1 1 130px;
  }

  .news-refresh{
    margin-left:0;
    width:100%;
  }

  .news-item{
    grid-template-columns:1fr;
  }

  .news-link{
    align-self:start;
  }
}
/* R18_NEWS_UI_END */


<!-- R19_SCANNER_UI_START -->
<details class="card scanner-card">
  <summary>
    <span>JAGUAR SCANNER</span>
    <span class="meta">CANDIDATE DISCOVERY · READ-ONLY</span>
  </summary>

  <div class="content">
    <div class="scanner-toolbar">
      <select
        class="scanner-symbol"
        id="scannerSymbol"
        aria-label="Scanner symbol"
      >
        <option value="">CURRENT SYMBOL</option>
        <option value="BTCUSDT">BTCUSDT</option>
        <option value="ETHUSDT">ETHUSDT</option>
        <option value="BNBUSDT">BNBUSDT</option>
        <option value="SOLUSDT">SOLUSDT</option>
        <option value="XRPUSDT">XRPUSDT</option>
        <option value="DOGEUSDT">DOGEUSDT</option>
        <option value="ADAUSDT">ADAUSDT</option>
        <option value="LINKUSDT">LINKUSDT</option>
        <option value="AVAXUSDT">AVAXUSDT</option>
        <option value="XAUUSD">XAUUSD</option>
      </select>

      <button
        class="scanner-action"
        id="scannerScanSymbol"
        type="button"
      >
        SCAN SYMBOL
      </button>

      <button
        class="scanner-action"
        id="scannerScanWatchlist"
        type="button"
      >
        SCAN WATCHLIST
      </button>
    </div>

    <div class="scanner-status" id="scannerStatus"></div>

    <div class="scanner-note">
      Scanner discovers candidates only. IDM remains the canonical decision authority.
    </div>

    <div class="scanner-error" id="scannerError"></div>

    <div class="scanner-list" id="scannerList">
      <div class="scanner-empty">
        Scanner idle. Run a scan to discover candidates.
      </div>
    </div>
  </div>
</details>
<!-- R19_SCANNER_UI_END -->

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
    <div class="badge" id="dataQualityBadge">DATA —</div>
  </div>
</header>

<div class="watchbar" id="watchbar"></div>

<!-- R24_DASHBOARD_TABS_UI_START -->
<!-- R25_DASHBOARD_TABS_HARDENING_START -->
<nav
  class="r24-tabs"
  id="r24DashboardTabs"
  role="tablist"
  aria-label="Command Center sections"
>
  <button
    type="button"
    role="tab"
    class="r24-tab r24-active"
    id="r24-tab-overview"
    data-r24-tab="overview"
    aria-selected="true"
    aria-controls="r24-panel-overview"
    tabindex="0"
  >OVERVIEW</button>

  <button
    type="button"
    role="tab"
    class="r24-tab"
    id="r24-tab-market"
    data-r24-tab="market"
    aria-selected="false"
    aria-controls="r24-panel-market"
    tabindex="-1"
  >MARKET</button>

  <button
    type="button"
    role="tab"
    class="r24-tab"
    id="r24-tab-scanner"
    data-r24-tab="scanner"
    aria-selected="false"
    aria-controls="r24-panel-scanner"
    tabindex="-1"
  >SCANNER</button>

  <button
    type="button"
    role="tab"
    class="r24-tab"
    id="r24-tab-news"
    data-r24-tab="news"
    aria-selected="false"
    aria-controls="r24-panel-news"
    tabindex="-1"
  >NEWS</button>

  <button
    type="button"
    role="tab"
    class="r24-tab"
    id="r24-tab-system"
    data-r24-tab="system"
    aria-selected="false"
    aria-controls="r24-panel-system"
    tabindex="-1"
  >SYSTEM</button>
</nav>
<!-- R25_DASHBOARD_TABS_HARDENING_END -->

<div class="r24-tab-panel" id="r24-panel-overview" data-r24-panel="overview" role="tabpanel" aria-labelledby="r24-tab-overview" tabindex="0">
</div>
<div class="r24-tab-panel" id="r24-panel-market" data-r24-panel="market" role="tabpanel" aria-labelledby="r24-tab-market" tabindex="0">
</div>
<div class="r24-tab-panel" id="r24-panel-scanner" data-r24-panel="scanner" role="tabpanel" aria-labelledby="r24-tab-scanner" tabindex="0">
</div>
<div class="r24-tab-panel" id="r24-panel-news" data-r24-panel="news" role="tabpanel" aria-labelledby="r24-tab-news" tabindex="0">
</div>
<div class="r24-tab-panel" id="r24-panel-system" data-r24-panel="system" role="tabpanel" aria-labelledby="r24-tab-system" tabindex="0">
</div>
<!-- R24_DASHBOARD_TABS_UI_END -->


<div class="layout">

<main class="main">

<section class="card hero">
  <div class="hero-top">
    <div>
      <div class="symbol" id="symbol">—</div>
      <div class="price" id="price">—</div>
      <div class="market-line" id="marketLine">—</div>
      <div class="market-line" id="freshLine">—</div>
      <div class="market-line" id="dataQualityLine">—</div>
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
    <button class="indicator-toggle active" data-indicator="FIB_RETR">FIB RET</button>
    <button class="indicator-toggle active" data-indicator="FIB_EXT">FIB EXT</button>
  </div>
  <div class="indicator-note">
    EMA/VWAP overlays use canonical candle history. Fibonacci overlays use canonical Fibonacci metadata only.
  </div>
  <canvas id="chart"></canvas>
  <div class="chart-legend" id="chartLegend"></div>
</section>

<section class="card fibonacci-card">
  <div class="section-head">
    <span>FIBONACCI STRUCTURE</span>
    <span class="meta">CANONICAL ENGINE</span>
  </div>

  <div class="content" id="fibonacciPanel"></div>
</section>


<section class="card coverage-card">
  <div class="section-head">
    <span>SESSION & MARKET COVERAGE</span>
    <span class="meta">READ-ONLY CAPABILITY MAP</span>
  </div>

  <div class="session-panel" id="sessionPanel"></div>

  <div class="coverage-grid" id="marketCoverage"></div>
</section>

<section class="card decision-gate">
  <div class="section-head">
    <span>JAGUAR DECISION GATE</span>
    <span class="meta">DECISION · REASON · BLOCKER · NEXT CONDITION</span>
  </div>

  <div class="decision-gate-grid">
    <div class="gate-block">
      <div class="gate-label">DECISION</div>
      <div class="gate-value" id="gateDecision">—</div>
    </div>

    <div class="gate-block">
      <div class="gate-label">AUTHORIZATION</div>
      <div class="gate-value" id="gateAuthorization">—</div>
    </div>

    <div class="gate-block">
      <div class="gate-label">PRIMARY BLOCKER</div>
      <div class="gate-value" id="gateBlocker">—</div>
    </div>

    <div class="gate-block">
      <div class="gate-label">BLOCKER STATUS</div>
      <div class="gate-value" id="gateBlockerStatus">—</div>
    </div>
  </div>

  <div class="gate-reason">
    <div class="gate-label">WHY</div>
    <div id="gateReason">—</div>
  </div>

  <div class="gate-reason">
    <div class="gate-label">NEXT REQUIRED CONDITIONS</div>
    <div id="gateConditions">—</div>
  </div>
</section>

<section class="card decision-gate">
  <div class="section-head">
    <span>MTF DATA SUFFICIENCY</span>
    <span class="meta">DATA COVERAGE ≠ MARKET DIRECTION</span>
  </div>
  <div class="mtf-sufficiency" id="mtfSufficiency"></div>
</section>


<section class="card thesis-invalidation-card">
  <div class="section-head">
    <span>THESIS / INVALIDATION</span>
    <span class="meta">CANONICAL DIRECTIONAL EVIDENCE</span>
  </div>
  <div class="thesis-invalidation" id="thesisInvalidation"></div>
</section>

<section class="card what-change-card">
  <div class="section-head">
    <span>WHAT WOULD CHANGE DECISION</span>
    <span class="meta">CANONICAL DECISION TRANSITION</span>
  </div>
  <div class="what-would-change" id="whatWouldChange"></div>
</section>

<section class="card trade-setup-card">
  <div class="section-head">
    <span>TRADE SETUP</span>
    <span class="meta">CANONICAL SETUP STATE</span>
  </div>
  <div class="trade-setup" id="tradeSetup"></div>
</section>

<section class="card confidence-breakdown">
  <div class="section-head">
    <span>CONFIDENCE BREAKDOWN</span>
    <span class="meta">CANONICAL EVIDENCE PROVENANCE</span>
  </div>

  <div class="confidence-summary" id="confidenceSummary"></div>

  <div class="confidence-engines" id="confidenceEngines"></div>

  <div class="confidence-method" id="confidenceMethod"></div>
</section>



/* R19_SCANNER_UI_START */
function scannerStatusClass(status){
  const normalized=String(
    status||"UNAVAILABLE"
  ).toUpperCase();

  if(normalized==="CURRENT"){
    return "current";
  }

  if(normalized==="DEGRADED"){
    return "degraded";
  }

  return "unavailable";
}

function scannerDirectionClass(direction){
  const value=String(
    direction||"NEUTRAL"
  ).toUpperCase();

  if(value==="LONG"){
    return "long";
  }

  if(value==="SHORT"){
    return "short";
  }

  return "neutral";
}

function renderScanner(){
  const snapshot=state.scanner||{};

  const status=String(
    snapshot.status||"UNAVAILABLE"
  ).toUpperCase();

  const candidates=Array.isArray(
    snapshot.candidates
  )
    ? snapshot.candidates
    : [];

  const statusEl=document.getElementById(
    "scannerStatus"
  );

  const errorEl=document.getElementById(
    "scannerError"
  );

  const listEl=document.getElementById(
    "scannerList"
  );

  if(!statusEl || !errorEl || !listEl){
    return;
  }

  const scanned=Number(
    snapshot.scanned_symbols||0
  );

  const count=Number(
    snapshot.candidate_count||0
  );

  statusEl.innerHTML=
    `<span class="scanner-pill ${scannerStatusClass(status)}">`+
    `STATUS · ${esc(status)}`+
    `</span>`+
    `<span class="scanner-pill">`+
    `SCANNED · ${fmt(scanned,0)}`+
    `</span>`+
    `<span class="scanner-pill">`+
    `CANDIDATES · ${fmt(count,0)}`+
    `</span>`;

  errorEl.textContent=
    Array.isArray(snapshot.errors) &&
    snapshot.errors.length
      ? snapshot.errors.map(
          error=>String(
            error.error||"Scanner provider error"
          )
        ).join(" · ")
      : "";

  if(!candidates.length){
    listEl.innerHTML=
      `<div class="scanner-empty">`+
      (
        status==="UNAVAILABLE"
          ? "Scanner unavailable or no valid market data is available."
          : "No scanner candidates meet the current discovery gates."
      )+
      `</div>`;

    return;
  }

  listEl.innerHTML=candidates.map(candidate=>{
    const symbol=esc(
      String(candidate.symbol||"—")
    );

    const direction=esc(
      String(candidate.direction||"NEUTRAL")
    );

    const score=fmt(
      candidate.score,
      0
    );

    const confidence=fmt(
      candidate.confidence,
      0
    )+"%";

    const structure=candidate.structure||{};
    const quality=candidate.data_quality||{};

    const structureTrend=esc(
      String(structure.trend||"NEUTRAL")
    );

    const bos=esc(
      String(structure.bos||"NEUTRAL")
    );

    const mtf=quality.mtf||{};
    const mtfValues=Object.values(mtf);

    const primaryTrend=
      mtf.primary
        ? String(mtf.primary)
        : "";

    const aligned=primaryTrend
      ? mtfValues.filter(
          value=>String(value)===primaryTrend
        ).length
      : 0;

    const dataQuality=fmt(
      quality.quality,
      0
    )+"%";

    const evidence=Array.isArray(
      candidate.evidence
    )
      ? candidate.evidence
      : [];

    const chips=evidence.slice(0,8).map(item=>{
      const name=esc(
        String(item.name||"—")
      );

      const signal=esc(
        String(item.signal||"NEUTRAL")
      );

      return `
        <span class="scanner-evidence-chip">
          ${name} · ${signal}
        </span>
      `;
    }).join("");

    return `
      <article class="scanner-item">
        <div class="scanner-item-head">
          <div>
            <div class="scanner-item-symbol">
              ${symbol}
            </div>

            <div class="meta">
              ${esc(String(candidate.timeframe||"15m"))}
              ·
              ${structureTrend}
            </div>
          </div>

          <span class="scanner-pill scanner-item-direction ${scannerDirectionClass(direction)}">
            ${direction}
          </span>
        </div>

        <div class="scanner-metrics">
          <div class="scanner-metric">
            <div class="scanner-metric-label">
              SCORE
            </div>
            <div class="scanner-metric-value">
              ${score}
            </div>
          </div>

          <div class="scanner-metric">
            <div class="scanner-metric-label">
              CONFIDENCE
            </div>
            <div class="scanner-metric-value">
              ${confidence}
            </div>
          </div>

          <div class="scanner-metric">
            <div class="scanner-metric-label">
              DATA QUALITY
            </div>
            <div class="scanner-metric-value">
              ${dataQuality}
            </div>
          </div>

          <div class="scanner-metric">
            <div class="scanner-metric-label">
              MTF ALIGNMENT
            </div>
            <div class="scanner-metric-value">
              ${fmt(aligned,0)}/${fmt(mtfValues.length,0)}
            </div>
          </div>
        </div>

        <div class="scanner-evidence">
          <span class="scanner-evidence-chip">
            STRUCTURE · ${structureTrend}
          </span>

          <span class="scanner-evidence-chip">
            BOS · ${bos}
          </span>

          ${chips}
        </div>

        <div class="scanner-candidate-only">
          SCANNER CANDIDATE ONLY · NOT EXECUTION AUTHORIZATION
        </div>
      </article>
    `;
  }).join("");
}

async function loadScanner(symbol=null){
  const symbolEl=document.getElementById(
    "scannerSymbol"
  );

  const scanSymbolEl=document.getElementById(
    "scannerScanSymbol"
  );

  const scanWatchlistEl=document.getElementById(
    "scannerScanWatchlist"
  );

  let activeSymbol=symbol;

  if(activeSymbol===null){
    activeSymbol=
      symbolEl && symbolEl.value
        ? String(symbolEl.value).trim()
        : String(state.symbol||"").trim();
  }

  const buttons=[
    scanSymbolEl,
    scanWatchlistEl
  ].filter(Boolean);

  buttons.forEach(button=>{
    button.disabled=true;
  });

  if(scanSymbolEl){
    scanSymbolEl.textContent="SCANNING…";
  }

  if(scanWatchlistEl){
    scanWatchlistEl.textContent="SCANNING…";
  }

  try{
    const url=
      activeSymbol
        ? `/scanner?symbol=${encodeURIComponent(activeSymbol)}`
        : "/scanner";

    const response=await fetch(
      url,
      {cache:"no-store"}
    );

    const data=await response.json();

    if(!response.ok){
      throw new Error(
        data.detail||("HTTP "+response.status)
      );
    }

    state.scanner=data;
    renderScanner();

  }catch(error){
    state.scanner={
      status:"UNAVAILABLE",
      generated_at:Date.now(),
      scanned_symbols:0,
      candidate_count:0,
      candidates:[],
      errors:[
        {
          symbol:activeSymbol||"",
          timeframe:"",
          error:String(error)
        }
      ]
    };

    renderScanner();

  }finally{
    buttons.forEach(button=>{
      button.disabled=false;
    });

    if(scanSymbolEl){
      scanSymbolEl.textContent="SCAN SYMBOL";
    }

    if(scanWatchlistEl){
      scanWatchlistEl.textContent="SCAN WATCHLIST";
    }
  }
}

function initScannerControls(){
  const symbolEl=document.getElementById(
    "scannerSymbol"
  );

  const scanSymbolEl=document.getElementById(
    "scannerScanSymbol"
  );

  const scanWatchlistEl=document.getElementById(
    "scannerScanWatchlist"
  );

  if(scanSymbolEl){
    scanSymbolEl.onclick=()=>{
      const symbol=
        symbolEl && symbolEl.value
          ? String(symbolEl.value).trim()
          : String(state.symbol||"").trim();

      loadScanner(symbol);
    };
  }

  if(scanWatchlistEl){
    scanWatchlistEl.onclick=()=>{
      if(symbolEl){
        symbolEl.value="";
      }

      loadScanner("");
    };
  }

  renderScanner();
}
/* R19_SCANNER_UI_END */



<!-- R23_SCANNER_ALERT_CONTEXT_UI_START -->
<details class="card scanner-alert-context-card">
  <summary>
    <span>JAGUAR ALERT CONTEXT</span>
    <span class="meta">CONTEXT ONLY · READ-ONLY</span>
  </summary>

  <div class="content">
    <div class="scanner-alert-context-toolbar">
      <select
        class="scanner-alert-context-symbol"
        id="scannerAlertContextSymbol"
        aria-label="Scanner alert context symbol"
      >
        <option value="">CURRENT SYMBOL</option>
        <option value="BTCUSDT">BTCUSDT</option>
        <option value="ETHUSDT">ETHUSDT</option>
        <option value="BNBUSDT">BNBUSDT</option>
        <option value="SOLUSDT">SOLUSDT</option>
        <option value="XRPUSDT">XRPUSDT</option>
        <option value="DOGEUSDT">DOGEUSDT</option>
        <option value="ADAUSDT">ADAUSDT</option>
        <option value="LINKUSDT">LINKUSDT</option>
        <option value="AVAXUSDT">AVAXUSDT</option>
        <option value="XAUUSD">XAUUSD</option>
      </select>

      <button
        class="scanner-alert-context-action"
        id="scannerAlertContextScanSymbol"
        type="button"
      >
        LOAD CONTEXT
      </button>

      <button
        class="scanner-alert-context-action"
        id="scannerAlertContextScanWatchlist"
        type="button"
      >
        LOAD WATCHLIST CONTEXT
      </button>
    </div>

    <div
      class="scanner-alert-context-status"
      id="scannerAlertContextStatus"
    ></div>

    <div
      class="scanner-alert-context-list"
      id="scannerAlertContextList"
    >
      <div class="scanner-alert-empty">
        Alert context idle. Load context to inspect related news.
      </div>
    </div>
  </div>
</details>
<!-- R23_SCANNER_ALERT_CONTEXT_UI_END -->
<!-- R18_NEWS_UI_START -->
<section class="card news-card">
  <div class="section-head">
    <span>JAGUAR NEWS</span>
    <span class="meta" id="newsMeta">READ-ONLY MARKET CONTEXT</span>
  </div>

  <div class="news-toolbar">
    <select class="news-filter" id="newsSymbolFilter" aria-label="News symbol">
      <option value="">All symbols</option>
      <option value="BTCUSDT">BTCUSDT</option>
      <option value="ETHUSDT">ETHUSDT</option>
      <option value="SOLUSDT">SOLUSDT</option>
      <option value="BNBUSDT">BNBUSDT</option>
      <option value="XRPUSDT">XRPUSDT</option>
      <option value="RELIANCE.NS">RELIANCE.NS</option>
      <option value="TCS.NS">TCS.NS</option>
      <option value="HDFCBANK.NS">HDFCBANK.NS</option>
      <option value="^NSEI">^NSEI</option>
      <option value="GOLD">GOLD</option>
      <option value="SILVER">SILVER</option>
      <option value="AAPL">AAPL</option>
      <option value="MSFT">MSFT</option>
      <option value="NVDA">NVDA</option>
      <option value="SPY">SPY</option>
      <option value="QQQ">QQQ</option>
    </select>

    <select class="news-filter" id="newsCategoryFilter" aria-label="News category">
      <option value="MARKET">Market</option>
      <option value="MACRO">Macro</option>
      <option value="CRYPTO">Crypto</option>
      <option value="NSE">NSE</option>
      <option value="MCX">MCX</option>
      <option value="US">US Markets</option>
    </select>

    <button class="news-refresh" id="newsRefresh" type="button">
      REFRESH NEWS
    </button>
  </div>

  <div class="news-status" id="newsStatus"></div>
  <div class="news-error" id="newsError"></div>
  <div class="news-list" id="newsList">
    <div class="news-empty">Loading news…</div>
  </div>
</section>
<!-- R18_NEWS_UI_END -->

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
  news:null,
  scanner:null,
  chartIndicators:{
    EMA20:true,
    EMA50:true,
    EMA100:true,
    EMA200:true,
    VWAP:true,
    FIB_RETR:true,
    FIB_EXT:true
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

function rowMarkup(label,markup){
  return `<div class="row"><div class="label">${esc(label)}</div><div class="value">${markup}</div></div>`;
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
  const dataQuality=u.data_quality||{};
  const market=u.market||{};
  const idm=u.idm||{};
  const st=u.structure||{};
  const risk=u.risk||{};
  const exe=u.execution||{};
  const mtf=u.mtf||{};
const mtfSuff=u.mtf_sufficiency||{};
const decisionGate=u.decision_gate||{};
const confidence=u.confidence_breakdown||{};


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

  const qualityStatus=String(
    dataQuality.status||"UNKNOWN"
  ).toUpperCase();

  const qualityOk=Boolean(
    dataQuality.integrity_ok
  );

  const qualityReason=String(
    dataQuality.reason||""
  ).trim();

  document.getElementById(
    "dataQualityBadge"
  ).textContent="DATA · "+qualityStatus;

  document.getElementById(
    "dataQualityBadge"
  ).className="badge "+
    (
      qualityOk
        ? "ok"
        : qualityStatus==="UNKNOWN"
          ? "warn"
          : "bad"
    );

  document.getElementById(
    "dataQualityLine"
  ).textContent =
    `Data Quality ${qualityStatus} · `+
    `Candles ${dataQuality.candle_count ?? "—"} · `+
    `Gaps ${dataQuality.gap_count ?? 0}`+
    (qualityReason ? ` · ${qualityReason}` : "");

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

  const idmMissing=Array.isArray(idm.missing)
    ? idm.missing.join(", ")
    : (idm.missing||"—");

  document.getElementById("gateDecision").textContent =
  decisionGate.decision || idm.decision || "WAIT";

document.getElementById("gateAuthorization").textContent =
  decisionGate.authorization ||
  (idm.approved ? "AUTHORIZED" : "BLOCKED");

document.getElementById("gateBlocker").textContent =
  decisionGate.blocker || "NONE";

document.getElementById("gateBlockerStatus").textContent =
  decisionGate.blocker_status || "CLEAR";

document.getElementById("gateReason").textContent =
  decisionGate.reason || "—";

const gateConditions =
  decisionGate.next_conditions || [];

document.getElementById("gateConditions").innerHTML =
  gateConditions.length
    ? `<ul class="gate-list">${gateConditions.map(
        x => `<li class="gate-condition">${
          esc(String(x))
        }</li>`
      ).join("")}</ul>`
    : "No additional condition identified.";

document.getElementById("mtfSufficiency").innerHTML = `
  <div class="mtf-suff-tile">
    <div class="gate-label">STATUS</div>
    <div class="mtf-suff-value">${esc(
      String(mtfSuff.status || "UNKNOWN")
    )}</div>
    <div class="mtf-suff-note">${esc(
      String(mtfSuff.impact || "—")
    )}</div>
  </div>

  <div class="mtf-suff-tile">
    <div class="gate-label">COVERAGE</div>
    <div class="mtf-suff-value">${
      Number(mtfSuff.available_count || 0)
    }/${Number(mtfSuff.required_count || 0)}</div>
    <div class="mtf-suff-note">timeframes available</div>
  </div>

  <div class="mtf-suff-tile">
    <div class="gate-label">AVAILABLE</div>
    <div class="mtf-suff-value">${esc(
      (mtfSuff.available || []).join(", ") || "NONE"
    )}</div>
    <div class="mtf-suff-note">usable MTF context</div>
  </div>

  <div class="mtf-suff-tile">
    <div class="gate-label">UNAVAILABLE</div>
    <div class="mtf-suff-value">${esc(
      (mtfSuff.unavailable || []).join(", ") || "NONE"
    )}</div>
    <div class="mtf-suff-note">missing MTF context</div>
  </div>
`;


  // ----------------------------------------------------------
  // THESIS / INVALIDATION
  // Presentation-only canonical evidence.
  // ----------------------------------------------------------

  const thesis =
    u.thesis_invalidation || {};

  const thesisSupport =
    Array.isArray(
      thesis.supporting_evidence
    )
      ? thesis.supporting_evidence
      : [];

  const thesisWeakening =
    Array.isArray(
      thesis.weakening_evidence
    )
      ? thesis.weakening_evidence
      : [];

  const thesisGates =
    Array.isArray(
      thesis.canonical_invalidation_gates
    )
      ? thesis.canonical_invalidation_gates
      : [];

  const activeInvalidation =
    Array.isArray(
      thesis.active_invalidation
    )
      ? thesis.active_invalidation
      : [];

  const thesisList = values =>
    values.length
      ? `<ul class="gate-list">${values.map(
          x => `<li class="gate-condition">${
            esc(String(x))
          }</li>`
        ).join("")}</ul>`
      : "None recorded.";

  document.getElementById(
    "thesisInvalidation"
  ).innerHTML = `
    <div class="rows">
      ${row(
        "Direction",
        thesis.direction || "NEUTRAL"
      )}

      ${row(
        "Thesis Status",
        thesis.status || "UNDEFINED"
      )}

      ${row(
        "Setup",
        thesis.setup || "UNKNOWN"
      )}

      ${row(
        "Direction Relationship",
        thesis.direction_relationship || "UNKNOWN"
      )}
    </div>

    <div class="gate-reason">
      <div class="gate-label">SUPPORTING EVIDENCE</div>
      ${thesisList(thesisSupport)}
    </div>

    <div class="gate-reason">
      <div class="gate-label">CURRENT WEAKENING EVIDENCE</div>
      ${thesisList(thesisWeakening)}
    </div>

    <div class="gate-reason">
      <div class="gate-label">CANONICAL INVALIDATION GATES</div>
      ${thesisList(thesisGates)}
    </div>

    <div class="gate-reason">
      <div class="gate-label">ACTIVE INVALIDATION</div>
      ${thesisList(activeInvalidation)}
    </div>
  `;

  // ----------------------------------------------------------
  // WHAT WOULD CHANGE DECISION
  // Presentation-only canonical evidence.
  // ----------------------------------------------------------

  const whatWouldChange =
    u.what_would_change || {};

  const requiredConditions =
    Array.isArray(
      whatWouldChange.required_conditions
    )
      ? whatWouldChange.required_conditions
      : [];

  const decisionReasons =
    Array.isArray(
      whatWouldChange.decision_reasons
    )
      ? whatWouldChange.decision_reasons
      : [];

  const confirmationReasons =
    Array.isArray(
      whatWouldChange.execution_confirmation_reasons
    )
      ? whatWouldChange.execution_confirmation_reasons
      : [];

  const conflicts =
    Array.isArray(
      whatWouldChange.conflicts
    )
      ? whatWouldChange.conflicts
      : [];

  const conditionList =
    requiredConditions.length
      ? `<ul class="gate-list">${requiredConditions.map(
          x => `<li class="gate-condition">${
            esc(String(x))
          }</li>`
        ).join("")}</ul>`
      : "No additional transition condition recorded.";

  const decisionReasonList =
    decisionReasons.length
      ? `<ul class="gate-list">${decisionReasons.map(
          x => `<li class="gate-condition">${
            esc(String(x))
          }</li>`
        ).join("")}</ul>`
      : "None recorded.";

  const confirmationReasonList =
    confirmationReasons.length
      ? `<ul class="gate-list">${confirmationReasons.map(
          x => `<li class="gate-condition">${
            esc(String(x))
          }</li>`
        ).join("")}</ul>`
      : "None recorded.";

  const conflictList =
    conflicts.length
      ? `<ul class="gate-list">${conflicts.map(
          x => `<li class="gate-condition">${
            esc(String(x))
          }</li>`
        ).join("")}</ul>`
      : "None recorded.";

  document.getElementById("whatWouldChange").innerHTML = `
    <div class="rows">
      ${row(
        "Current Decision",
        whatWouldChange.current_decision || "WAIT"
      )}

      ${row(
        "Authorization",
        whatWouldChange.current_authorization || "BLOCKED"
      )}

      ${row(
        "Structural Readiness",
        whatWouldChange.structural_readiness || "UNKNOWN"
      )}

      ${row(
        "Trigger Status",
        whatWouldChange.trigger_status || "UNKNOWN"
      )}

      ${row(
        "Trigger Confirmed",
        whatWouldChange.trigger_confirmed
          ? "YES"
          : "NO"
      )}

      ${row(
        "Execution Confirmation",
        whatWouldChange.execution_confirmation || "WAIT"
      )}

      ${row(
        "Execution Confirmed",
        whatWouldChange.execution_confirmation_confirmed
          ? "YES"
          : "NO"
      )}
    </div>

    <div class="gate-reason">
      <div class="gate-label">REQUIRED CONDITIONS</div>
      ${conditionList}
    </div>

    <div class="gate-reason">
      <div class="gate-label">CURRENT DECISION REASONS</div>
      ${decisionReasonList}
    </div>

    <div class="gate-reason">
      <div class="gate-label">EXECUTION EVIDENCE</div>
      ${confirmationReasonList}
    </div>

    <div class="gate-reason">
      <div class="gate-label">CURRENT CONFLICTS</div>
      ${conflictList}
    </div>
  `;

  // ----------------------------------------------------------
  // TRADE SETUP
  // Presentation-only canonical setup state.
  // ----------------------------------------------------------

  const tradeSetup =
    u.trade_setup || {};

  document.getElementById("tradeSetup").innerHTML = `
    <div class="rows">
      ${row(
        "Status",
        tradeSetup.status || "UNKNOWN"
      )}
      ${rowMarkup(
        "Direction",
        directionMarkup(
          tradeSetup.direction || "NEUTRAL"
        )
      )}
      ${row(
        "Setup Type",
        tradeSetup.setup_type || "UNKNOWN"
      )}
      ${row(
        "Zone",
        tradeSetup.zone || "NONE"
      )}
      ${row(
        "Zone Status",
        tradeSetup.zone_status || "UNKNOWN"
      )}
      ${row(
        "Zone Lifecycle",
        tradeSetup.zone_lifecycle || "UNKNOWN"
      )}
      ${row(
        "Location",
        tradeSetup.location || "UNKNOWN"
      )}
      ${row(
        "Readiness",
        tradeSetup.readiness || "UNKNOWN"
      )}
      ${row(
        "Trigger",
        tradeSetup.trigger || "NONE"
      )}
      ${row(
        "Trigger Confirmed",
        tradeSetup.trigger_confirmed
          ? "YES"
          : "NO"
      )}
      ${row(
        "Execution Confirmation",
        tradeSetup.execution_confirmation || "WAIT"
      )}
      ${row(
        "Risk",
        tradeSetup.risk_status || "UNKNOWN"
      )}
      ${row(
        "Execution",
        tradeSetup.execution_status || "WAIT"
      )}
      ${row(
        "Execution Ready",
        tradeSetup.execution_ready
          ? "YES"
          : "NO"
      )}
    </div>
  `;

  // ----------------------------------------------------------
  // CONFIDENCE BREAKDOWN
  // Presentation-only. Values come from canonical Jaguar
  // evidence already exposed by the UI state.
  // No composite confidence is calculated here.
  // ----------------------------------------------------------

  const confidenceMtf =
    confidence.mtf || {};

  document.getElementById("confidenceSummary").innerHTML = `
    <div class="rows">
      ${row(
        "IDM Confidence",
        confidence.idm_confidence == null
          ? "—"
          : fmt(confidence.idm_confidence) + "%"
      )}

      ${row(
        "Institutional Confidence",
        confidence.institutional_confidence == null
          ? "—"
          : fmt(confidence.institutional_confidence) + "%"
      )}

      ${row(
        "Institutional Score",
        confidence.institutional_score == null
          ? "—"
          : fmt(confidence.institutional_score)
      )}

      ${row(
        "Probability",
        confidence.probability == null
          ? "—"
          : fmt(confidence.probability)
      )}

      ${row(
        "State Confidence Grade",
        confidence.grade || "—"
      )}

      ${row(
        "Context Confidence Grade",
        confidence.context_grade || "—"
      )}

      ${row(
        "MTF Confidence",
        confidenceMtf.confidence == null
          ? "—"
          : fmt(confidenceMtf.confidence) + "%"
      )}

      ${row(
        "MTF Bias",
        confidenceMtf.bias || "—"
      )}

      ${row(
        "MTF Alignment",
        confidenceMtf.alignment == null
          ? "—"
          : fmt(confidenceMtf.alignment, 0)
      )}

      ${row(
        "MTF Score",
        confidenceMtf.score == null
          ? "—"
          : fmt(confidenceMtf.score)
      )}
    </div>
  `;

  const confidenceEngines =
    confidence.engines &&
    typeof confidence.engines === "object"
      ? confidence.engines
      : {};

  const confidenceEngineRows =
    Object.entries(confidenceEngines)
      .sort((a, b) =>
        String(a[0]).localeCompare(String(b[0]))
      )
      .map(([name, evidence]) => {
        const item =
          evidence &&
          typeof evidence === "object"
            ? evidence
            : {};

        const percent =
          item.confidence_percent == null
            ? "—"
            : fmt(item.confidence_percent) + "%";

        const signal =
          item.signal || "NEUTRAL";

        const score =
          item.score == null
            ? "—"
            : fmt(item.score);

        return `
          <div class="confidence-engine">
            <div class="section-head">
              <span>${esc(name)}</span>
              <span class="meta">${esc(signal)}</span>
            </div>

            ${row("Confidence", percent)}
            ${row("Score", score)}
          </div>
        `;
      })
      .join("");

  document.getElementById("confidenceEngines").innerHTML =
    confidenceEngineRows ||
    `<div class="banner">No canonical engine confidence evidence available.</div>`;

  document.getElementById("confidenceMethod").innerHTML =
    `<div class="banner">${esc(
      confidence.method ||
      "Canonical evidence only; no derived composite confidence."
    )}</div>`;

document.getElementById("idmRows").innerHTML=[
    row("Decision",idm.decision),
    row("Approved",idm.approved?"YES":"NO"),
    rowMarkup("Direction",directionMarkup(idm.direction)),
    row("Score",fmt(idm.score)),
    row("Confidence",fmt(idm.confidence)+"%"),
    row("Institutional Grade",idm.grade),
    row("Priority",idm.priority),
    row("Setup",idm.setup||"—"),
    row("Readiness",idm.readiness),
    row("Trigger",idm.trigger),
    row("Confirmed",idm.trigger_confirmed?"YES":"NO"),
    row("Missing",idmMissing)
  ].join("");

  document.getElementById("structureRows").innerHTML=[
    row("Trend",st.trend),
    row("BOS",st.bos||"NEUTRAL"),
    row("BOS Score",fmt(st.bos_score)),
    row("BOS Confidence",fmt(st.bos_confidence)+"%"),
    row("BOS Reason",st.bos_reason||"—"),
    row("CHoCH",st.choch||"NEUTRAL"),
    row("CHoCH Score",fmt(st.choch_score)),
    row("CHoCH Confidence",fmt(st.choch_confidence)+"%"),
    row("CHoCH Reason",st.choch_reason||"—"),
    rowMarkup("Direction",directionMarkup(st.direction)),
    row("State",st.state),
    row("Readiness",st.readiness),
    row("Trigger",st.trigger),
    row("Zone",st.zone_type),
    rowMarkup("Zone Direction",directionMarkup(st.zone_direction)),
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
        ${rowMarkup("Trend",directionMarkup(a.trend))}
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
  renderFibonacci();
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

  const fibMetadata=state.ui?.fibonacci?.metadata||{};
  const fibRetracements=fibMetadata.retracements||{};
  const fibExtensions=fibMetadata.extensions||{};

  const fibRetracementValues=Object.values(fibRetracements)
    .map(Number)
    .filter(Number.isFinite);

  const fibExtensionValues=Object.values(fibExtensions)
    .map(Number)
    .filter(Number.isFinite);

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


  if(state.chartIndicators.FIB_RETR){
    finiteValues.push(...fibRetracementValues);
  }

  if(state.chartIndicators.FIB_EXT){
    finiteValues.push(...fibExtensionValues);
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

  const drawFibLevels=(levels,style,dash)=>{
    ctx.save();
    ctx.strokeStyle=style;
    ctx.lineWidth=Math.max(1,dpr);
    ctx.setLineDash(dash);

    for(const value of Object.values(levels)){
      const n=Number(value);

      if(!Number.isFinite(n)){
        continue;
      }

      const y=yOf(n);

      if(y<top || y>top+plotH){
        continue;
      }

      ctx.beginPath();
      ctx.moveTo(left,y);
      ctx.lineTo(left+plotW,y);
      ctx.stroke();
    }

    ctx.restore();
  };

  if(state.chartIndicators.FIB_RETR){
    drawFibLevels(fibRetracements,"rgba(214,178,89,.70)",[6*dpr,4*dpr]);
  }

  if(state.chartIndicators.FIB_EXT){
    drawFibLevels(fibExtensions,"rgba(167,139,250,.70)",[2*dpr,4*dpr]);
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
    ["VWAP","#53e39b"],
    ["FIB_RETR","#d6b259"],
    ["FIB_EXT","#a78bfa"]
  ].filter(x=>state.chartIndicators[x[0]])
   .map(x=>`
     <span class="legend-item">
       <span class="legend-line" style="background:${x[1]}"></span>
       ${x[0]}
     </span>
   `)
   .join("");
}


function fibLevelClass(value){
  const v=String(value||"").toUpperCase();

  if(v.includes("PREMIUM")){
    return "fib-premium";
  }

  if(v.includes("DISCOUNT")){
    return "fib-discount";
  }

  if(v.includes("BULLISH")){
    return "fib-bullish";
  }

  if(v.includes("BEARISH")){
    return "fib-bearish";
  }

  return "fib-neutral";
}

function renderFibonacci(){
  const box=document.getElementById("fibonacciPanel");
  if(!box){
    return;
  }

  const fib=state.ui?.fibonacci;

  if(!fib){
    box.innerHTML='<div class="banner">Canonical Fibonacci data unavailable.</div>';
    return;
  }

  const metadata=fib.metadata||{};
  const retracements=metadata.retracements||{};
  const extensions=metadata.extensions||{};
  const reasons=Array.isArray(fib.reasons)?fib.reasons:[];

  const renderLevels=(levels)=>{
    const entries=Object.entries(levels);

    if(!entries.length){
      return '<div class="fib-reasons">No canonical levels available.</div>';
    }

    return entries.map(([ratio,value])=>`
      <div class="fib-level">
        <div class="fib-ratio">${esc(ratio)}%</div>
        <div class="fib-price">${fmt(value,2)}</div>
      </div>
    `).join("");
  };

  box.innerHTML=`
    <div class="fib-summary">
      <div class="fib-summary-tile">
        <div class="fib-summary-label">STATUS</div>
        <div class="fib-summary-value ${fibLevelClass(fib.status)}">
          ${esc(fib.status||"UNKNOWN")}
        </div>
      </div>

      <div class="fib-summary-tile">
        <div class="fib-summary-label">ZONE</div>
        <div class="fib-summary-value ${fibLevelClass(fib.zone)}">
          ${esc(fib.zone||"UNKNOWN")}
        </div>
      </div>

      <div class="fib-summary-tile">
        <div class="fib-summary-label">SIGNAL</div>
        <div class="fib-summary-value ${fibLevelClass(fib.signal)}">
          ${esc(fib.signal||"NEUTRAL")}
        </div>
      </div>
    </div>

    <div class="fib-level-grid">
      <div class="fib-level-panel">
        <div class="fib-level-title">RETRACEMENTS</div>
        ${renderLevels(retracements)}
      </div>

      <div class="fib-level-panel">
        <div class="fib-level-title">EXTENSIONS</div>
        ${renderLevels(extensions)}
      </div>
    </div>

    <div class="fib-reasons">
      ${reasons.length
        ? reasons.map(reason=>`• ${esc(reason)}`).join("<br>")
        : "No Fibonacci reasons reported."
      }
    </div>
  `;
}

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


/* R23_SCANNER_ALERT_CONTEXT_UI_START */
let r23ScannerAlertContexts = null;

function renderScannerAlertContext(){
  const statusEl=document.getElementById(
    "scannerAlertContextStatus"
  );

  const listEl=document.getElementById(
    "scannerAlertContextList"
  );

  if(!statusEl || !listEl){
    return;
  }

  const result=r23ScannerAlertContexts;

  if(!result){
    statusEl.innerHTML="";
    listEl.innerHTML=
      '<div class="scanner-alert-empty">'+
      'Alert context idle. Load context to inspect related news.'+
      '</div>';
    return;
  }

  const status=String(
    result.status||"UNAVAILABLE"
  ).toUpperCase();

  const authority=String(
    result.authority||
    "SCANNER_ALERT_CONTEXT_ONLY"
  );

  statusEl.innerHTML=
    '<span class="scanner-alert-status-pill">'+
    status+
    '</span>'+
    '<span class="meta">CONTEXTS '+
    Number(result.context_count||0)+
    ' · ALERTS '+
    Number(result.alert_count||0)+
    '</span>'+
    '<span class="meta scanner-alert-context-boundary">'+
    authority+
    '</span>';

  const contexts=
    Array.isArray(result.contexts)
      ? result.contexts
      : [];

  if(!contexts.length){
    listEl.innerHTML=
      '<div class="scanner-alert-empty">'+
      'No alert context available.'+
      '</div>';
    return;
  }

  listEl.innerHTML=contexts.map(
    context=>{
      const alert=context.alert||{};

      const related=
        Array.isArray(context.related_items)
          ? context.related_items
          : [];

      const newsHtml=related.length
        ? related.map(
            item=>`
              <article class="scanner-alert-context-news-item">
                <div>
                  <strong>
                    ${item.publisher||"Unknown publisher"}
                  </strong>
                </div>
                <div>${item.title||"Untitled"}</div>
                <div class="meta">
                  ${item.published_at||"n/a"}
                  · ${item.relevance||"n/a"}
                  · ${item.match_reason||"n/a"}
                </div>
              </article>
            `
          ).join("")
        : '<div class="scanner-alert-empty">No related news.</div>';

      return `
        <article class="scanner-alert-context-item">
          <div class="scanner-alert-head">
            <div class="scanner-alert-title">
              ${alert.symbol||"UNKNOWN"}
              · ${alert.direction||"NEUTRAL"}
              · ${alert.setup||"CONFLUENCE"}
            </div>

            <span class="scanner-alert-badge">
              ${alert.priority||"MEDIUM"}
            </span>
          </div>

          <div class="scanner-alert-meta">
            <span>
              TF ${alert.timeframe||"n/a"}
            </span>
            <span>
              STATE ${alert.state||"n/a"}
            </span>
            <span>
              CONF ${Number(alert.confidence||0)}
            </span>
            <span>
              CONFLUENCE ${
                Number(alert.confluence_score||0)
              }
            </span>
          </div>

          <div class="scanner-alert-explanation">
            ${alert.explanation||
              "No explanation available."}
          </div>

          <div class="scanner-alert-context-news">
            <div class="meta">
              NEWS ${context.news_status||"UNKNOWN"}
              · ${context.news_provider||"NONE"}
              · ${
                context.news_cached
                  ? "CACHED"
                  : "CURRENT"
              }
            </div>

            <div>
              ${
                context.context_summary||
                "No context summary available."
              }
            </div>

            ${newsHtml}
          </div>
        </article>
      `;
    }
  ).join("");
}

async function loadScannerAlertContext(
  symbol=null,
  refresh=false
){
  const symbolEl=document.getElementById(
    "scannerAlertContextSymbol"
  );

  const scanSymbolEl=document.getElementById(
    "scannerAlertContextScanSymbol"
  );

  const scanWatchlistEl=document.getElementById(
    "scannerAlertContextScanWatchlist"
  );

  let activeSymbol=symbol;

  if(activeSymbol===null){
    activeSymbol=
      symbolEl && symbolEl.value
        ? String(symbolEl.value).trim()
        : String(state.symbol||"").trim();
  }

  const buttons=[
    scanSymbolEl,
    scanWatchlistEl
  ].filter(Boolean);

  buttons.forEach(button=>{
    button.disabled=true;
  });

  if(scanSymbolEl){
    scanSymbolEl.textContent="LOADING…";
  }

  if(scanWatchlistEl){
    scanWatchlistEl.textContent="LOADING…";
  }

  try{
    const params=new URLSearchParams();

    if(activeSymbol){
      params.set(
        "symbol",
        activeSymbol
      );
    }

    params.set(
      "limit",
      "5"
    );

    params.set(
      "refresh",
      refresh ? "true" : "false"
    );

    const response=await fetch(
      `/scanner/alert-context?${params.toString()}`,
      {cache:"no-store"}
    );

    if(!response.ok){
      throw new Error(
        `HTTP ${response.status}`
      );
    }

    r23ScannerAlertContexts=
      await response.json();

    renderScannerAlertContext();

  }catch(error){
    r23ScannerAlertContexts={
      status:"UNAVAILABLE",
      generated_at:0,
      scanned_symbols:0,
      candidate_count:0,
      alert_count:0,
      context_count:0,
      contexts:[],
      errors:[
        {
          error:String(
            error && error.message
              ? error.message
              : error
          )
        }
      ],
      authority:
        "SCANNER_ALERT_CONTEXT_ONLY"
    };

    renderScannerAlertContext();

  }finally{
    buttons.forEach(button=>{
      button.disabled=false;
    });

    if(scanSymbolEl){
      scanSymbolEl.textContent=
        "LOAD CONTEXT";
    }

    if(scanWatchlistEl){
      scanWatchlistEl.textContent=
        "LOAD WATCHLIST CONTEXT";
    }
  }
}

function initScannerAlertContextControls(){
  const symbolEl=document.getElementById(
    "scannerAlertContextSymbol"
  );

  const scanSymbolEl=document.getElementById(
    "scannerAlertContextScanSymbol"
  );

  const scanWatchlistEl=document.getElementById(
    "scannerAlertContextScanWatchlist"
  );

  if(scanSymbolEl){
    scanSymbolEl.onclick=()=>{
      const symbol=
        symbolEl && symbolEl.value
          ? String(symbolEl.value).trim()
          : String(state.symbol||"").trim();

      loadScannerAlertContext(
        symbol,
        false
      );
    };
  }

  if(scanWatchlistEl){
    scanWatchlistEl.onclick=()=>{
      if(symbolEl){
        symbolEl.value="";
      }

      loadScannerAlertContext(
        "",
        false
      );
    };
  }

  renderScannerAlertContext();
}
/* R23_SCANNER_ALERT_CONTEXT_UI_END */
/* R26_DASHBOARD_TAB_STATE_START */
const R26_TAB_STORAGE_KEY="jaguarQuantXActiveDashboardTab";

const R26_VALID_TABS=new Set([
  "overview",
  "market",
  "scanner",
  "news",
  "system"
]);

function readR26ActiveTab(){
  try{
    const stored=sessionStorage.getItem(
      R26_TAB_STORAGE_KEY
    );

    if(
      stored &&
      R26_VALID_TABS.has(stored)
    ){
      return stored;
    }
  }catch(_error){
    // Browser storage may be unavailable.
  }

  return "overview";
}

function persistR26ActiveTab(name){
  if(!R26_VALID_TABS.has(name)){
    return;
  }

  try{
    sessionStorage.setItem(
      R26_TAB_STORAGE_KEY,
      name
    );
  }catch(_error){
    // Browser storage may be unavailable.
  }
}
/* R26_DASHBOARD_TAB_STATE_END */

/* R24_DASHBOARD_TABS_UI_START */
/* R25_DASHBOARD_TABS_HARDENING_START */
function initR24DashboardTabs(){
  const tabRoot=document.getElementById("r24DashboardTabs");
  if(!tabRoot)return;

  const tabs=[
    {
      name:"overview",
      selectors:[
        ".hero",
        ".pipeline",
        ".decision-gate",
        ".thesis-invalidation-card",
        ".what-change-card",
        ".trade-setup-card",
        ".confidence-breakdown"
      ]
    },
    {
      name:"market",
      selectors:[
        ".chart-card",
        ".fibonacci-card",
        ".coverage-card",
        ".mtf-card"
      ]
    },
    {
      name:"scanner",
      selectors:[
        ".scanner-card",
        ".scanner-alert-card",
        ".scanner-alert-context-card"
      ]
    },
    {
      name:"news",
      selectors:[
        ".news-card"
      ]
    },
    {
      name:"system",
      selectors:[
        ".side-card"
      ]
    }
  ];

  const assigned=new Set();

  tabs.forEach(group=>{
    group.selectors.forEach(selector=>{
      document.querySelectorAll(selector).forEach(el=>{
        if(assigned.has(el))return;
        assigned.add(el);
        el.dataset.r24Route=group.name;
        el.classList.add("r24-routed-content");
      });
    });
  });

  const routed=[...document.querySelectorAll(".r24-routed-content")];
  const buttons=[...tabRoot.querySelectorAll(".r24-tab")];

  function activate(name, focusButton=false, persist=true){
    tabs.forEach(group=>{
      const button=tabRoot.querySelector(
        `[data-r24-tab="${group.name}"]`
      );

      if(button){
        const active=group.name===name;

        button.classList.toggle(
          "r24-active",
          active
        );

        button.setAttribute(
          "aria-selected",
          active ? "true" : "false"
        );

        button.setAttribute(
          "tabindex",
          active ? "0" : "-1"
        );

        if(active && focusButton){
          button.focus();
        }
      }
    });

    routed.forEach(el=>{
      el.classList.toggle(
        "r24-tab-hidden",
        el.dataset.r24Route!==name
      );
    });

    document.querySelectorAll("[data-r24-panel]").forEach(panel=>{
      const active=panel.dataset.r24Panel===name;
      panel.hidden=!active;
    });

    if(persist){
      persistR26ActiveTab(name);
    }
  }

  buttons.forEach((button,index)=>{
    button.onclick=()=>{
      activate(
        button.dataset.r24Tab||"overview"
      );
    };

    button.onkeydown=event=>{
      let nextIndex=index;

      if(event.key==="ArrowRight"){
        nextIndex=(index+1)%buttons.length;
      }else if(event.key==="ArrowLeft"){
        nextIndex=(index-1+buttons.length)%buttons.length;
      }else if(event.key==="Home"){
        nextIndex=0;
      }else if(event.key==="End"){
        nextIndex=buttons.length-1;
      }else if(event.key==="Enter"||event.key===" "){
        event.preventDefault();
        activate(
          button.dataset.r24Tab||"overview",
          true
        );
        return;
      }else{
        return;
      }

      event.preventDefault();

      const nextButton=buttons[nextIndex];
      if(!nextButton)return;

      activate(
        nextButton.dataset.r24Tab||"overview",
        true
      );
    };
  });

  const initialTab=readR26ActiveTab();
  activate(initialTab,false,false);
}

/* R24_DASHBOARD_TABS_UI_END */
/* R25_DASHBOARD_TABS_HARDENING_END */
/* R18_NEWS_UI_START */
function newsTimestamp(value){
  if(!value){
    return "—";
  }

  const date=new Date(value);

  if(Number.isNaN(date.getTime())){
    return String(value);
  }

  return date.toLocaleString();
}

function renderNews(){
  const snapshot=state.news||{};
  const status=String(snapshot.status||"UNAVAILABLE").toUpperCase();
  const provider=String(snapshot.provider||"NONE");
  const cached=Boolean(snapshot.cached);
  const items=Array.isArray(snapshot.items)?snapshot.items:[];

  const statusEl=document.getElementById("newsStatus");
  const errorEl=document.getElementById("newsError");
  const listEl=document.getElementById("newsList");
  const metaEl=document.getElementById("newsMeta");

  if(!statusEl || !errorEl || !listEl || !metaEl){
    return;
  }

  let statusClass="unavailable";

  if(status==="CURRENT"){
    statusClass="current";
  }else if(status==="CACHED"){
    statusClass="cached";
  }

  statusEl.innerHTML=
    `<span class="news-status-pill ${statusClass}">STATUS · ${esc(status)}</span>`+
    `<span class="news-status-pill">SOURCE · ${esc(provider)}</span>`+
    `<span class="news-status-pill">${cached?"CACHED":"CURRENT"}</span>`;

  metaEl.textContent=
    `${provider} · ${items.length} item${items.length===1?"":"s"}`;

  errorEl.textContent=
    snapshot.error
      ? String(snapshot.error)
      : "";

  if(!items.length){
    listEl.innerHTML=
      `<div class="news-empty">${
        status==="UNAVAILABLE"
          ? "News providers unavailable and no cached news is available."
          : "No news items available for this filter."
      }</div>`;
    return;
  }

  listEl.innerHTML=items.map(item=>{
    const publisher=esc(String(item.publisher||item.source||"—"));
    const title=esc(String(item.title||"Untitled"));
    const category=esc(String(item.category||"MARKET"));
    const published=esc(newsTimestamp(item.published_at));
    const source=esc(String(item.source||publisher));
    const url=String(item.url||"");

    return `
      <article class="news-item">
        <div class="news-item-main">
          <div class="news-title">${title}</div>
          <div class="news-meta">
            <span>${publisher}</span>
            <span>${source}</span>
            <span>${category}</span>
            <span>${published}</span>
          </div>
        </div>
        ${
          /^https?:\/\//i.test(url)
            ? `<a class="news-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer">OPEN ↗</a>`
            : ""
        }
      </article>
    `;
  }).join("");
}

async function loadNews(refresh=false){
  const symbolEl=document.getElementById("newsSymbolFilter");
  const categoryEl=document.getElementById("newsCategoryFilter");
  const refreshEl=document.getElementById("newsRefresh");

  const symbol=
    symbolEl
      ? String(symbolEl.value||"").trim()
      : "";

  const category=
    categoryEl
      ? String(categoryEl.value||"MARKET").trim()
      : "MARKET";

  if(symbolEl && !symbolEl.value && state.symbol){
    const option=[...symbolEl.options].find(
      option=>option.value===state.symbol
    );

    if(option){
      symbolEl.value=state.symbol;
    }
  }

  const activeSymbol=
    symbolEl
      ? String(symbolEl.value||"").trim()
      : "";

  if(refreshEl){
    refreshEl.disabled=true;
    refreshEl.textContent="REFRESHING…";
  }

  try{
    const params=new URLSearchParams();

    if(activeSymbol){
      params.set("symbol",activeSymbol);
    }

    params.set("category",category);
    params.set("limit","20");
    params.set("refresh",refresh ? "true" : "false");

    const response=await fetch(
      `/news?${params.toString()}`,
      {cache:"no-store"}
    );

    const data=await response.json();

    if(!response.ok){
      throw new Error(
        data.detail || ("HTTP "+response.status)
      );
    }

    state.news=data;
    renderNews();

  }catch(error){
    state.news={
      status:"UNAVAILABLE",
      provider:"NONE",
      cached:false,
      items:[],
      error:String(error)
    };

    renderNews();

  }finally{
    if(refreshEl){
      refreshEl.disabled=false;
      refreshEl.textContent="REFRESH NEWS";
    }
  }
}

function initNewsControls(){
  const symbolEl=document.getElementById("newsSymbolFilter");
  const categoryEl=document.getElementById("newsCategoryFilter");
  const refreshEl=document.getElementById("newsRefresh");

  if(symbolEl){
    symbolEl.onchange=()=>{
      loadNews(true);
    };
  }

  if(categoryEl){
    categoryEl.onchange=()=>{
      loadNews(true);
    };
  }

  if(refreshEl){
    refreshEl.onclick=()=>{
      loadNews(true);
    };
  }

  loadNews(false);
}
/* R18_NEWS_UI_END */


async function load(){
  try{
    const url=
      `/dashboard/state?symbol=${encodeURIComponent(state.symbol)}`+
      `&interval=${encodeURIComponent(state.interval)}`;

    const r=await fetch(url,{cache:"no-store"});
    if(!r.ok) throw new Error("HTTP "+r.status);

    const d=await r.json();

    if(!d||!d.ui) throw new Error("Invalid dashboard state");


    state.ui=d.ui;
    state.candles=Array.isArray(d.candles)?d.candles:[];

    render();
  }catch(e){
    document.getElementById("healthBadge").textContent="SYSTEM · ERROR";
    document.getElementById("healthBadge").className="badge bad";
    document.getElementById("freshBadge").textContent="FRESHNESS · ERROR";
    document.getElementById("freshBadge").className="badge bad";
    document.getElementById("dataQualityBadge").textContent="DATA · ERROR";
    document.getElementById("dataQualityBadge").className="badge bad";
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
initR24DashboardTabs();
initIndicatorControls();
initNewsControls();
initScannerAlertControls();
    initScannerAlertContextControls();
initScannerControls();
load();
setInterval(load,10000);
</script>
</body>
</html>"""
