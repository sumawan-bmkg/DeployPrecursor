/* POCC — Client-side JavaScript */
let ws = null;
let theme = localStorage.getItem('pocc-theme') || 'light';

// ── Theme ──
function toggleTheme() {
    theme = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('pocc-theme', theme);
    document.getElementById('theme-icon').textContent = theme === 'dark' ? '☀️' : '🌙';
}

// ── WebSocket ──
function connectWS() {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${window.location.host}/ws`);
    ws.onopen = () => console.log('[WS] Connected');
    ws.onclose = () => { console.log('[WS] Disconnected, reconnecting...'); setTimeout(connectWS, 3000); };
    ws.onmessage = (evt) => {
        try {
            const data = JSON.parse(evt.data);
            updateDashboard(data);
        } catch(e) {}
    };
}

// ── Dashboard Update ──
function updateDashboard(data) {
    if (data.time) {
        const t = new Date(data.time);
        document.getElementById('utc-time').textContent = t.toUTCString().slice(-12, -4);
    }
    if (data.dashboard) {
        const d = data.dashboard;
        const els = {
            'cpu-val': d.system?.cpu,
            'ram-val': d.system?.ram,
            'stations-val': d.stations_total,
            'score-val': d.psep?.scientific_score,
            'pred-val': d.prediction?.probability,
        };
        Object.entries(els).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el && val !== undefined) el.textContent = typeof val === 'number' ? val.toFixed(1) : val;
        });
    }
    if (data.pipeline) {
        data.pipeline.stages?.forEach((stage, i) => {
            const node = document.getElementById(`pnode-${i}`);
            if (node) {
                const status = node.querySelector('.node-status');
                if (status) status.textContent = stage.status;
                if (stage.status === 'OK') node.classList.add('node-pass');
            }
        });
    }
}

// ── ECharts ──
function initChart(containerId, option) {
    const dom = document.getElementById(containerId);
    if (!dom) return null;
    const chart = echarts.init(dom);
    chart.setOption(option);
    window.addEventListener('resize', () => chart.resize());
    return chart;
}

// ── API Fetch ──
async function fetchAPI(endpoint) {
    try {
        const r = await fetch(endpoint);
        return await r.json();
    } catch(e) { return null; }
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
    // Set theme
    document.documentElement.setAttribute('data-theme', theme);
    document.getElementById('theme-icon').textContent = theme === 'dark' ? '☀️' : '🌙';
    // Connect WS
    connectWS();
    // Clock update
    function updateClock() {
        const now = new Date();
        const utc = now.toUTCString().slice(-12, -4);
        const wita = new Date(now.getTime() + 8*3600000);
        document.getElementById('utc-time').textContent = utc;
        document.getElementById('wita-time').textContent = wita.toISOString().slice(11, 19);
    }
    updateClock();
    setInterval(updateClock, 1000);
});
