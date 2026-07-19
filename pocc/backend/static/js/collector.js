/**
 * Collector Command Center — Live Dashboard JavaScript
 * Refresh every 5s, tabs, live metrics, controls.
 */
const COLLECTOR_API = '/api/collector';

// ── Main Refresh ──
async function refreshCollector() {
    try {
        const resp = await fetch(COLLECTOR_API);
        const data = await resp.json();
        if (!data) return;
        updateStatus(data);
        updateMetrics(data);
        updateQueue(data);
        updateStations(data);
        updateWorkers(data);
        updateLog(data);
        heartbeat();
    } catch (e) {
        console.error('Collector refresh error:', e);
    }
}

function updateStatus(d) {
    const s = d.scheduler || {};
    const alive = s.alive;
    const badge = document.getElementById('sbScheduler');
    if (badge) {
        badge.className = 'badge bg-' + (alive ? 'success' : 'danger') + ' fs-6 px-3 py-2';
        badge.innerHTML = '<i class="fas fa-' + (alive ? 'check-circle' : 'times-circle') + ' me-1"></i>' +
            (alive ? 'RUNNING' : 'STOPPED');
    }
    document.getElementById('sbUptime').textContent = s.uptime ? Math.floor(s.uptime / 60) + 'm' : '-';
    document.getElementById('sbStatus').textContent = d.status || 'STANDBY';
    document.getElementById('sbStations').textContent = d.remote?.stations || 0;
    document.getElementById('sbFiles').textContent = d.remote?.files || 0;
}

function updateMetrics(d) {
    const r = d.remote || {};
    const h = d.health || {};
    document.getElementById('mLatency').textContent = (r.latency || 0).toFixed(2) + 's';
    document.getElementById('mSize').textContent = (r.size_gb || 0).toFixed(1) + ' GB';
    document.getElementById('mSuccess').textContent = (h.success_rate || 0).toFixed(1) + '%';
    document.getElementById('mAvailability').textContent = ((h.availability || 0) * 100).toFixed(1) + '%';

    // Countdowns
    const q = d.queue || {};
    const w = d.workers || {};
    if (w.discovery?.last_success) {
        const last = new Date(w.discovery.last_success).getTime();
        const next = last + 300000; // 5min
        const remaining = Math.max(0, Math.floor((next - Date.now()) / 1000));
        document.getElementById('mNextDiscovery').textContent = remaining + 's';
    }
    if (w.download?.last_success) {
        const last = new Date(w.download.last_success).getTime();
        const next = last + 600000; // 10min
        const remaining = Math.max(0, Math.floor((next - Date.now()) / 1000));
        document.getElementById('mNextDownload').textContent = remaining + 's';
    }
}

function updateQueue(d) {
    const q = d.queue || {};
    const el = document.getElementById('queueBar');
    if (el) {
        const total = q.WAITING + q.RUNNING + q.SUCCESS + q.FAILED + q.RETRY || 1;
        el.innerHTML = `
            <div class="d-flex gap-2 mb-2">
                <span class="badge bg-secondary">W:${q.WAITING||0}</span>
                <span class="badge bg-info">R:${q.RUNNING||0}</span>
                <span class="badge bg-success">S:${q.SUCCESS||0}</span>
                <span class="badge bg-warning text-dark">RT:${q.RETRY||0}</span>
                <span class="badge bg-danger">F:${q.FAILED||0}</span>
                <span class="badge bg-dark">SK:${q.SKIPPED||0}</span>
            </div>
            <div class="progress" style="height:24px">
                <div class="progress-bar bg-success" style="width:${(q.SUCCESS||0)/total*100}%">${q.SUCCESS||0}</div>
                <div class="progress-bar bg-warning" style="width:${(q.RETRY||0)/total*100}%">${q.RETRY||0}</div>
                <div class="progress-bar bg-danger" style="width:${(q.FAILED||0)/total*100}%">${q.FAILED||0}</div>
            </div>`;
    }
}

function updateStations(d) {
    const details = d.remote?.station_details || {};
    const container = document.getElementById('stationGrid');
    if (!container) return;
    let html = '';
    Object.entries(details).forEach(([stn, info]) => {
        const hasFiles = (info.files_count || 0) > 0;
        const size = (info.total_size / 1e6 || 0).toFixed(1);
        html += `<div class="col-md-3 col-6 mb-2">
            <div class="p-2 border rounded ${hasFiles ? 'border-success' : 'border-secondary'}">
                <strong>${stn}</strong>
                <span class="badge bg-${hasFiles ? 'success' : 'secondary'} float-end">${hasFiles ? 'Active' : 'Empty'}</span>
                <br><small class="text-muted">${info.files_count} files / ${size} MB</small>
            </div>
        </div>`;
    });
    container.innerHTML = html || '<p class="text-muted">No station data</p>';
}

function updateWorkers(d) {
    const w = d.workers || {};
    ['discovery','download','validation','runtime','audit'].forEach(name => {
        const wd = w[name] || {};
        const status = wd.status || 'idle';
        const el = document.getElementById('w' + name.charAt(0).toUpperCase() + name.slice(1));
        if (el) {
            const cls = status === 'running' ? 'success' : status === 'error' ? 'danger' : 'secondary';
            el.innerHTML = `
                <span class="badge bg-${cls} me-2">${status}</span>
                <small class="text-muted">${wd.heartbeat ? new Date(wd.heartbeat).toLocaleTimeString() : '-'}</small>
                <br><small>dur: ${(wd.duration || 0).toFixed(2)}s · retry: ${wd.retry_count || 0}</small>`;
        }
    });
}

function updateLog(d) {
    const logEl = document.getElementById('liveLog');
    if (!logEl || !d.log) return;
    const lines = d.log.split('\n').slice(-30);
    logEl.innerHTML = lines.map(l => `<div class="text-nowrap small">${l}</div>`).join('');
    logEl.scrollTop = logEl.scrollHeight;
}

function heartbeat() {
    const hb = document.getElementById('heartbeat');
    if (hb) {
        hb.textContent = new Date().toLocaleTimeString();
        hb.classList.remove('text-danger');
        hb.classList.add('text-success');
    }
}

// ── Controls ──
async function controlCollector(action) {
    try {
        const resp = await fetch('/api/collector/control', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action})
        });
        const result = await resp.json();
        alert(action + ': ' + (result.status || 'OK'));
    } catch (e) {
        alert(action + ' failed: ' + e.message);
    }
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
    refreshCollector();
    setInterval(refreshCollector, 5000);
});
