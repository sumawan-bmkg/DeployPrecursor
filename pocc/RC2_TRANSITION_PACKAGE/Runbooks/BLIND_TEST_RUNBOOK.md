# WP4 — Blind Test Runbook (SOP)

**Generated:** 2026-07-16

## Pre-Conditions
- [ ] Waveform 2025-2026 placed at `/opt/pimes/data/raw/`
- [ ] `merge2026.csv` available as ground truth
- [ ] All 21 prior models present in `/opt/pimes/laws/priors/`
- [ ] All 28 station signatures present
- [ ] Server reachable at `10.20.229.43:8500`

## Step 1: Verify Data
```bash
python deploy.py doctor
```
Check: Collector RUNNING, all pages 10/10, APIs passing.

## Step 2: Check Waveform Coverage
Open `http://10.20.229.43:8500/waveform` — verify coverage bar updated.

## Step 3: Freeze Baseline
```bash
python deploy.py deploy
```
This performs: risk analysis → backup → SHA256 upload → verify → restart → health → self-test.

## Step 4: Run Inference
The collector pipeline will automatically:
1. Discover new files in `/opt/pimes/data/raw/`
2. Preprocess through CWT generator
3. Build tensors from scalograms
4. Run inference engine
5. Store predictions

## Step 5: Monitor Progress
```bash
python deploy.py watch
```
Or open `http://10.20.229.43:8500/waveform` for live status.

## Step 6: Run OSC (if not auto-running)
```bash
# OSC runs automatically via cron (hourly + daily)
# Verify: ls /opt/pimes/posc/osc/reports/daily/
```

## Step 7: Check CEPSL Integrity
```bash
curl http://10.20.229.43:8500/api/cepsl
```
Verify `archive_verified` count increasing.

## Step 8: Generate Evaluation
Compare predictions against `merge2026.csv`:
- Event-by-event matching
- Magnitude prediction vs catalog magnitude
- Timing precision
- Station coverage analysis

## Step 9: Generate Reports
```bash
python deploy.py report
```
Export prediction results to CSV for offline analysis.

## Step 10: Issue Certificate
Once evaluation passes acceptance criteria:
```bash
python deploy.py release
```
Generate release certificate with blind test results.

## Troubleshooting

| Issue | Action |
|-------|--------|
| Collector not processing | `python deploy.py restart` |
| Health check fails | `python deploy.py emergency` |
| CEPSL baseline COMPROMISED | Expected during active changes — will reset |
| Prediction errors | Check `/api/health-model` for component status |
| Server unreachable | Check network, `ping 10.20.229.43` |
