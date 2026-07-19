"""BOCC Full Upgrade Deploy — Mission Control, 7 pages, Executive KPI, Runtime stages, Scientific hashes."""
import paramiko, base64, os, time, json

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
POCC = "/opt/pimes/pocc"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=10)

def put(path, content):
    remote = f"{POCC}/{path}"
    b64 = base64.b64encode(content.encode()).decode()
    script = f'import base64; open("{remote}","wb").write(base64.b64decode("{b64}"))'
    # Write via sftp
    with open("_tmp_up.py", "w") as f: f.write(script)
    sftp = c.open_sftp()
    sftp.put("_tmp_up.py", "/tmp/_up.py")
    sftp.close()
    c.exec_command("python3 /tmp/_up.py")
    time.sleep(0.2)
    os.remove("_tmp_up.py")
    _, o, _ = c.exec_command(f"wc -c < {remote}")
    sz = o.read().decode().strip()
    print(f"  {path.split('/')[-1]}: {sz} bytes" if sz else f"  {path.split('/')[-1]}: FAIL")

# ── 1. BOCC CSS ──
bocc_css = """
:root{--bocc-bg:#0a1628;--bocc-card:#111d36;--bocc-border:#1a2a4a;--bocc-accent:#1a73e8;--bocc-text:#e0e6f0;--bocc-muted:#8899bb;--bocc-green:#00e676;--bocc-red:#ff5252;--bocc-yellow:#ffd740;--bocc-blue:#448aff;--bocc-cyan:#18ffff}
body{background:var(--bocc-bg);color:var(--bocc-text);font-family:'Inter','Segoe UI',sans-serif;font-size:.85rem;overflow-x:hidden}
.bocc-topbar{background:linear-gradient(135deg,#0a1628 0%,#112240 100%);border-bottom:1px solid var(--bocc-border);height:48px;z-index:1030}
.bocc-sidebar{position:fixed;top:48px;left:0;bottom:0;width:180px;background:#0d1b2a;border-right:1px solid var(--bocc-border);padding-top:.5rem;overflow-y:auto;z-index:1020}
.sidebar-item{display:flex;align-items:center;gap:10px;padding:.55rem 1rem;color:var(--bocc-muted);text-decoration:none;font-size:.78rem;border-left:3px solid transparent;transition:.15s}
.sidebar-item:hover{color:var(--bocc-text);background:rgba(255,255,255,.04)}
.sidebar-item.active{color:#fff;background:rgba(26,115,232,.15);border-left-color:var(--bocc-accent);font-weight:600}
.sidebar-item i{width:18px;text-align:center;font-size:.85rem}
.sidebar-divider{border-color:var(--bocc-border);margin:.3rem .75rem}
.bocc-main{margin-left:180px;margin-top:48px;padding:1rem;min-height:calc(100vh - 48px)}
.mission-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:.75rem}
.kpi-card{background:var(--bocc-card);border:1px solid var(--bocc-border);border-radius:8px;padding:1rem;position:relative;overflow:hidden}
.kpi-card .label{font-size:.65rem;text-transform:uppercase;letter-spacing:.5px;color:var(--bocc-muted)}
.kpi-card .value{font-size:1.6rem;font-weight:700;margin:.15rem 0;font-family:'Inter',sans-serif}
.kpi-card .sub{font-size:.7rem;color:var(--bocc-muted)}
.kpi-card .icon{position:absolute;top:.75rem;right:.75rem;font-size:1.5rem;opacity:.15}
.kpi-card.green .value{color:var(--bocc-green)}.kpi-card.red .value{color:var(--bocc-red)}.kpi-card.yellow .value{color:var(--bocc-yellow)}.kpi-card.blue .value{color:var(--bocc-blue)}.kpi-card.cyan .value{color:var(--bocc-cyan)}
.stage-chain{display:flex;flex-wrap:wrap;gap:4px}
.stage-node{background:var(--bocc-card);border:1px solid var(--bocc-border);border-radius:6px;padding:.4rem .7rem;text-align:center;min-width:80px;cursor:pointer;transition:.15s}
.stage-node:hover{border-color:var(--bocc-accent);transform:translateY(-2px)}
.stage-node .s-name{font-size:.65rem;color:var(--bocc-muted);text-transform:uppercase}
.stage-node .s-status{font-size:.75rem;font-weight:600}
.section-title{font-size:.65rem;text-transform:uppercase;letter-spacing:1px;color:var(--bocc-muted);margin-bottom:.5rem;font-weight:600}
.data-table{width:100%;font-size:.75rem}
.data-table th{color:var(--bocc-muted);font-weight:500;text-transform:uppercase;font-size:.65rem;padding:.35rem .5rem;border-bottom:1px solid var(--bocc-border)}
.data-table td{padding:.35rem .5rem;border-bottom:1px solid rgba(255,255,255,.04)}
.hash-display{font-family:'Courier New',monospace;font-size:.65rem;color:var(--bocc-muted);word-break:break-all}
.log-box{background:#000c1a;color:var(--bocc-green);font-family:'Courier New',monospace;font-size:.68rem;padding:.6rem;border-radius:6px;max-height:200px;overflow-y:auto;border:1px solid var(--bocc-border)}
.badge-drift{font-size:.6rem;padding:.15rem .4rem}
@media(max-width:768px){.bocc-sidebar{width:50px}.bocc-sidebar span{display:none}.bocc-main{margin-left:50px}}
"""

# ── 2. Base HTML ──
base_html = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{% block title %}BOCC — BMKG Operational Control Center{% endblock %}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link href="/static/css/bocc.css" rel="stylesheet"></head><body>
<nav class="navbar navbar-dark bocc-topbar fixed-top px-3"><div class="container-fluid">
<div class="d-flex align-items-center gap-3">
<img src="/static/img/logo_bmkg.svg" height="28" alt="BMKG">
<span class="navbar-brand mb-0 fs-5 fw-bold">BOCC</span>
<span class="badge bg-light text-dark fs-7">{{ version }}</span></div>
<div class="d-flex align-items-center gap-3">
<span id="liveTime" class="text-light small"></span>
<span id="overallHealth" class="badge bg-success fs-7 px-3">OPERATIONAL</span></div></div></nav>
<div class="bocc-sidebar"><div class="sidebar-menu">
<a href="/" class="sidebar-item{% if active_page=='overview' %} active{% endif %}" data-page="overview"><i class="fas fa-rocket"></i><span>Overview</span></a>
<a href="/collector" class="sidebar-item{% if active_page=='collector' %} active{% endif %}" data-page="collector"><i class="fas fa-download"></i><span>Collector</span></a>
<a href="/runtime" class="sidebar-item{% if active_page=='runtime' %} active{% endif %}" data-page="runtime"><i class="fas fa-microchip"></i><span>Runtime</span></a>
<a href="/scientific" class="sidebar-item{% if active_page=='scientific' %} active{% endif %}" data-page="scientific"><i class="fas fa-flask"></i><span>Scientific</span></a>
<a href="/burnin" class="sidebar-item{% if active_page=='burnin' %} active{% endif %}" data-page="burnin"><i class="fas fa-fire"></i><span>Burn-in</span></a>
<a href="/psep" class="sidebar-item{% if active_page=='psep' %} active{% endif %}" data-page="psep"><i class="fas fa-balance-scale"></i><span>PSEP</span></a>
<a href="/release" class="sidebar-item{% if active_page=='release' %} active{% endif %}" data-page="release"><i class="fas fa-tags"></i><span>Release</span></a>
<hr class="sidebar-divider">
<a href="/executive" class="sidebar-item{% if active_page=='executive' %} active{% endif %}" data-page="executive"><i class="fas fa-chart-pie"></i><span>Executive</span></a>
<a href="/governance" class="sidebar-item{% if active_page=='governance' %} active{% endif %}" data-page="governance"><i class="fas fa-shield-alt"></i><span>Governance</span></a>
<a href="/stations" class="sidebar-item{% if active_page=='stations' %} active{% endif %}" data-page="stations"><i class="fas fa-satellite-dish"></i><span>Stations</span></a>
<a href="/system" class="sidebar-item{% if active_page=='system' %} active{% endif %}" data-page="system"><i class="fas fa-cogs"></i><span>System</span></a>
</div></div>
<div class="bocc-main">{% block content %}{% endblock %}</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
function uc(){var n=new Date;document.getElementById('liveTime').textContent=n.toLocaleString('id-ID',{timeZone:'Asia/Makassar',hour12:false})}
setInterval(uc,1000);uc();
setTimeout(function(){fetch('/api/health').then(r=>r.json()).then(d=>{var h=document.getElementById('overallHealth');if(d.status==='OK'){h.textContent='OPERATIONAL';h.className='badge bg-success fs-7 px-3'}else{h.textContent='DEGRADED';h.className='badge bg-warning text-dark fs-7 px-3'}}).catch(function(){document.getElementById('overallHealth').textContent='OFFLINE'})},2000);
</script>
{% block scripts %}{% endblock %}</body></html>"""

# ── 3. Dashboard → Mission Overview ──
overview_html = """{% extends 'base.html' %}{% block title %}Mission Overview — BOCC{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
<h4 class="mb-0 fw-bold"><i class="fas fa-rocket me-2 text-primary"></i>Mission Overview</h4>
<small class="text-muted">Today's Operational Status</small></div>
<div class="mission-grid" id="missionGrid">
<div class="kpi-card blue"><div class="label">Overall Health</div><div class="value" id="ovHealth">-</div><div class="sub">System Status</div><i class="fas fa-heartbeat icon"></i></div>
<div class="kpi-card green"><div class="label">Scientific Score</div><div class="value" id="ovScore">-</div><div class="sub">PSEP Score</div><i class="fas fa-flask icon"></i></div>
<div class="kpi-card cyan"><div class="label">Collector</div><div class="value" id="ovCollector">-</div><div class="sub">Last: --</div><i class="fas fa-download icon"></i></div>
<div class="kpi-card blue"><div class="label">Runtime</div><div class="value" id="ovRuntime">-</div><div class="sub">Pipeline</div><i class="fas fa-microchip icon"></i></div>
<div class="kpi-card green"><div class="label">Burn-in</div><div class="value" id="ovBurnin">-</div><div class="sub" id="ovBurninSub">Cycle</div><i class="fas fa-fire icon"></i></div>
<div class="kpi-card yellow"><div class="label">Shadow Mode</div><div class="value" id="ovShadow">-</div><div class="sub" id="ovShadowSub">Day</div><i class="fas fa-moon icon"></i></div>
<div class="kpi-card blue"><div class="label">Stations Online</div><div class="value" id="ovStations">-</div><div class="sub">of 22 expected</div><i class="fas fa-satellite-dish icon"></i></div>
<div class="kpi-card green"><div class="label">Release Gate</div><div class="value" id="ovRelease">-</div><div class="sub">Phase</div><i class="fas fa-tags icon"></i></div>
</div>
<div class="row mt-3">
<div class="col-md-7"><div class="section-title">Today's Pipeline</div>
<div class="stage-chain" id="pipelineChain"><div class="stage-node"><div class="s-name">Reader</div><div class="s-status text-muted">-</div></div><i class="fas fa-chevron-right align-self-center text-muted"></i>
<div class="stage-node"><div class="s-name">PC3</div><div class="s-status text-muted">-</div></div><i class="fas fa-chevron-right align-self-center text-muted"></i>
<div class="stage-node"><div class="s-name">Tensor</div><div class="s-status text-muted">-</div></div><i class="fas fa-chevron-right align-self-center text-muted"></i>
<div class="stage-node"><div class="s-name">Inference</div><div class="s-status text-muted">-</div></div><i class="fas fa-chevron-right align-self-center text-muted"></i>
<div class="stage-node"><div class="s-name">Fusion</div><div class="s-status text-muted">-</div></div><i class="fas fa-chevron-right align-self-center text-muted"></i>
<div class="stage-node"><div class="s-name">Alert</div><div class="s-status text-muted">-</div></div></div></div>
<div class="col-md-5"><div class="section-title">Prediction Today</div>
<div class="kpi-card cyan"><div class="label">Active Predictions</div><div class="value" id="ovPredCount">-</div><div class="sub" id="ovPredTime">-</div><i class="fas fa-chart-line icon"></i></div></div></div>
<div class="row mt-3"><div class="col-12">
<div class="section-title">Live Log</div>
<div id="liveLog" class="log-box" style="max-height:150px">Waiting for data...</div></div></div>
{% endblock %}
{% block scripts %}
<script>
function refreshOverview(){fetch('/api/overview').then(r=>r.json()).then(d=>{
document.getElementById('ovHealth').textContent=d.health||'-';
document.getElementById('ovScore').textContent=d.scientific_score||'-';
document.getElementById('ovCollector').textContent=d.collector||'-';
document.getElementById('ovRuntime').textContent=d.runtime||'-';
document.getElementById('ovBurnin').textContent=d.burnin_cycle||'-';document.getElementById('ovBurninSub').textContent=d.burnin_status||'';
document.getElementById('ovShadow').textContent=d.shadow_day||'-';document.getElementById('ovShadowSub').textContent=d.shadow_status||'';
document.getElementById('ovStations').textContent=d.stations_online||'-';
document.getElementById('ovRelease').textContent=d.release_gate||'-';
document.getElementById('ovPredCount').textContent=d.prediction_count||'-';
document.getElementById('ovPredTime').textContent=d.prediction_time||'';
if(d.log){document.getElementById('liveLog').innerHTML=d.log.split('\\n').slice(-15).map(l=>'<div>'+l+'</div>').join('')}
}).catch(function(){})}
refreshOverview();setInterval(refreshOverview,10000);
</script>{% endblock %}"""

# ── Deploy ──
files = [
    ("static/css/bocc.css", bocc_css),
    ("templates/base.html", base_html),
    ("templates/dashboard.html", overview_html),
]

for rel, content in files:
    put(rel, content)

# Update main.py to add bocc CSS + overview API
put("backend/main.py", open(r"d:\opt\pimes\pocc\backend\main.py", encoding="utf-8").read())

# Restart
c.exec_command("pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 1")
c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > pocc.log 2>&1 </dev/null &")
time.sleep(5)

# Verify
_, o, _ = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/ 2>/dev/null")
print(f"\nDASHBOARD: {o.read().decode().strip()}")
_, o, _ = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/governance 2>/dev/null")
print(f"GOVERNANCE: {o.read().decode().strip()}")
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/health 2>/dev/null | head -c 80")
print(f"HEALTH: {o.read().decode().strip()}")

c.close()
print("\nBOCC Phase 1 complete!")
