"""
LAWS Phase 4 — Edge Simulator: Real-Time Shadow Mode
=====================================================
Simulates Jetson Nano edge device:
  1. Reads sequential station data
  2. POSTs 128D vectors to FastAPI
  3. Logs latency, LAI, status, magnitude
  4. Produces operational audit report

Usage:
  # Start server first (separate terminal):
  #   uvicorn laws.api.faiss_service:app --host 0.0.0.0 --port 8000
  #
  # Then run simulator:
  #   python laws/scripts/simulate_edge_stream.py

Dry-run mode (no server needed):
  python laws/scripts/simulate_edge_stream.py --dry-run
"""
import os, sys, json, time, argparse, csv
import numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

LAWS = Path("d:/multi/scalogramv3/laws")
EMB = LAWS / "embeddings"
SCRIPTS = LAWS / "scripts"
RPT = LAWS / "reports"
SCRIPTS.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# STEP 1: EDGE SIMULATOR
# ═══════════════════════════════════════════════════════════════

def load_sequential_data(station: str = "ALR", max_samples: int = 50):
    """Load sequential station data + 128D vectors."""
    proj = np.load(str(EMB / "proj_vectors.npy"))
    df = pd.read_csv(str(EMB / "val_embeddings.csv"))

    # Filter station
    mask = df['station'] == station
    df = df[mask].sort_values('date').head(max_samples).copy()
    print(f"  Station {station}: {len(df)} samples ({df['date'].min()} -> {df['date'].max()})")

    # Extract 128D vectors
    idx = df.index.values
    vectors = proj[idx]

    # Classify
    geo_labels = []
    for _, r in df.iterrows():
        kp, dst, lab = float(r['kp']), float(r['dst']), int(r['label'])
        if kp >= 5.0 or dst <= -50:
            geo_labels.append('storm')
        elif lab == 1:
            geo_labels.append('pre_earthquake')
        else:
            geo_labels.append('quiet')
    df['geo_label'] = geo_labels

    print(f"  Classes: {df['geo_label'].value_counts().to_dict()}")
    return df, vectors


def build_payload(station: str, ts: str, vec: np.ndarray, kp: float, dst: float, status: str) -> dict:
    """Build JSON payload matching API contract."""
    return {
        "station_code": station,
        "timestamp": ts,
        "environmental_factors": {
            "kp_index": float(kp),
            "dst_index": float(dst),
        },
        "latent_vector": vec.tolist(),
        "local_inference_status": status,
    }


def simulate_edge_stream(station: str = "ALR", max_samples: int = 50,
                         api_url: str = "http://localhost:8000/api/v1/magnitude-assistance",
                         dry_run: bool = False):
    """Main simulation loop."""
    print(f"\n{'='*60}")
    print(f"LAWS EDGE SIMULATOR (Shadow Mode)")
    print(f"{'='*60}")
    print(f"Station:      {station}")
    print(f"Samples:      {max_samples}")
    print(f"API URL:      {api_url}")
    print(f"Dry-run:      {dry_run}")
    print(f"{'='*60}\n")

    # Load data
    df, vectors = load_sequential_data(station, max_samples)
    n = len(df)

    if n == 0:
        print("[FAIL] No data for station", station)
        return

    # Log buffer
    log = []

    # Pre-compute synthetic timestamps (one per minute)
    base_ts = datetime(2026, 6, 29, 14, 0, 0)

    if not dry_run:
        import urllib.request
        import urllib.error

    print(f"{'Idx':>4}  {'Date':>10}  {'Label':>4}  {'Mag':>5}  {'Geo':>15}  "
          f"{'LAI':>7}  {'Status':>8}  {'EstMag':>6}  {'Conf':>5}  {'Lat(ms)':>8}")
    print("-" * 90)

    for i in range(n):
        row = df.iloc[i]
        vec = vectors[i]

        # Build payload
        ts_str = base_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        base_ts = base_ts.replace(minute=(base_ts.minute + 1) % 60)
        if base_ts.minute == 0:
            base_ts = base_ts.replace(hour=base_ts.hour + 1)

        payload = build_payload(
            station=station,
            ts=ts_str,
            vec=vec,
            kp=float(row['kp']),
            dst=float(row['dst']),
            status="REVIEW" if row['geo_label'] != 'quiet' else "QUIET"
        )

        log_entry = {
            'idx': i,
            'date': int(row['date']),
            'label': int(row['label']),
            'actual_mag': float(row['mag']),
            'kp': float(row['kp']),
            'geo_label': row['geo_label'],
            'timestamp': ts_str,
        }

        if dry_run:
            # Echo payload w/o server call
            log_entry['latency_ms'] = 0.0
            log_entry['lai'] = 0.0
            log_entry['system_status'] = 'DRY_RUN'
            log_entry['estimated_mag'] = 0.0
            log_entry['confidence'] = 0.0
            log_entry['status_code'] = 200

            print(f"{i:>4}  {row['date']:>10}  {row['label']:>4}  {float(row['mag']):>5.2f}  "
                  f"{row['geo_label']:>15}  {'DRY':>7}  {'RUN':>8}")
        else:
            try:
                t0 = time.time()
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    api_url,
                    data=data,
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp_data = json.loads(resp.read().decode('utf-8'))
                latency_ms = (time.time() - t0) * 1000

                lai = resp_data.get('lithosphere_activity_index', {})
                mag = resp_data.get('magnitude_assistance', {})
                status_code = resp.status

                log_entry['latency_ms'] = round(latency_ms, 3)
                log_entry['lai'] = lai.get('mahalanobis_distance', -1)
                log_entry['system_status'] = lai.get('system_status', '?')
                log_entry['estimated_mag'] = mag.get('estimated_magnitude', -1)
                log_entry['confidence'] = mag.get('confidence_margin', -1)
                log_entry['status_code'] = status_code

                print(f"{i:>4}  {row['date']:>10}  {row['label']:>4}  {float(row['mag']):>5.2f}  "
                      f"{row['geo_label']:>15}  {log_entry['lai']:>7.3f}  "
                      f"{log_entry['system_status']:>8}  {log_entry['estimated_mag']:>6.2f}  "
                      f"{log_entry['confidence']:>5.2f}  {latency_ms:>8.3f}")

            except urllib.error.URLError as e:
                log_entry['latency_ms'] = -1
                log_entry['system_status'] = 'CONN_ERR'
                log_entry['estimated_mag'] = -1
                log_entry['lai'] = -1
                log_entry['status_code'] = 0
                print(f"{i:>4}  {row['date']:>10}  {row['label']:>4}  {float(row['mag']):>5.2f}  "
                      f"{row['geo_label']:>15}  {'ERR':>7}  {'CONN':>8}  {'-':>6}  {'-':>5}  "
                      f"{'FAIL':>8}")

        log.append(log_entry)
        time.sleep(0.1)  # simulate 100ms between edge calls

    # ═══════════════════════════════════════════════════════════
    # STEP 2: LOGGING & STATE TRACKING
    # ═══════════════════════════════════════════════════════════

    log_df = pd.DataFrame(log)
    log_path = SCRIPTS / "edge_simulation_log.csv"
    log_df.to_csv(log_path, index=False)
    print(f"\n  [OK] Log saved: {log_path}")

    # Summary stats
    if not dry_run and log_df['status_code'].iloc[0] != 0:
        # ═══════════════════════════════════════════════════════
        # STEP 3: SHADOW MODE AUDIT REPORT
        # ═══════════════════════════════════════════════════════
        report = []
        report.append("# LAWS Phase 4 — Shadow Mode Audit Report")
        report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Station:** {station}")
        report.append(f"**Samples:** {n}")
        report.append(f"**API:** {api_url}")
        report.append("")

        successes = log_df[log_df['status_code'] == 200]
        failures = log_df[log_df['status_code'] != 200]
        n_ok = len(successes)

        # Latency
        mean_lat = successes['latency_ms'].mean()
        p95_lat = successes['latency_ms'].quantile(0.95)
        max_lat = successes['latency_ms'].max()
        min_lat = successes['latency_ms'].min()

        report.append("## 1. API Latency (Client-Side)")
        report.append("")
        report.append("| Metric | Value |")
        report.append("|--------|-------|")
        report.append(f"| Requests sent | {n} |")
        report.append(f"| Successful | {n_ok} |")
        report.append(f"| Failed | {len(failures)} |")
        report.append(f"| Mean latency | {mean_lat:.3f} ms |")
        report.append(f"| P95 latency | {p95_lat:.3f} ms |")
        report.append(f"| Max latency | {max_lat:.3f} ms |")
        report.append(f"| Min latency | {min_lat:.3f} ms |")
        report.append("")

        # Status transition analysis (flickering)
        statuses = successes['system_status'].tolist()
        transitions = sum(1 for i in range(1, len(statuses)) if statuses[i] != statuses[i-1])
        report.append("## 2. System Status Stability")
        report.append("")
        report.append("| Metric | Value |")
        report.append("|--------|-------|")
        report.append(f"| Unique statuses seen | {list(pd.unique(statuses))} |")
        report.append(f"| Status transitions | {transitions} |")
        report.append(f"| Flicker rate | {transitions / max(1, len(statuses)) * 100:.1f}% |")
        report.append("")

        if transitions / max(1, len(statuses)) > 0.5:
            report.append("⚠️ **High flicker rate** — status oscillates frequently. Consider hysteresis in `get_status()`.")
        else:
            report.append("✅ **Stable status progression** — threshold levels respond correctly to activity.")
        report.append("")

        # Magnitude stability
        mags = successes['estimated_mag'].values
        actual_mags = successes['actual_mag'].values
        mag_diff = np.abs(mags[:-1] - mags[1:])  # minute-to-minute jump
        mean_jump = mag_diff.mean()
        max_jump = mag_diff.max()
        mae_actual = np.abs(mags - actual_mags).mean()

        report.append("## 3. Magnitude Estimation Stability")
        report.append("")
        report.append("| Metric | Value |")
        report.append("|--------|-------|")
        report.append(f"| Minute-to-minute mean jump | {mean_jump:.4f} mag units |")
        report.append(f"| Minute-to-minute max jump | {max_jump:.4f} mag units |")
        report.append(f"| MAE vs actual magnitude | {mae_actual:.4f} |")
        report.append(f"| Estimated range | [{mags.min():.2f}, {mags.max():.2f}] |")
        report.append(f"| Actual range | [{actual_mags.min():.2f}, {actual_mags.max():.2f}] |")
        report.append("")

        if mean_jump > 0.3:
            report.append("⚠️ **Unstable magnitude — jumps > 0.3 between minutes.** FAISS neighbours may be sensitive to daily variations.")
        elif mean_jump > 0.15:
            report.append("📊 **Moderate magnitude fluctuation.** Acceptable for alerting with confidence bounds.")
        else:
            report.append("✅ **Stable magnitude estimation.** FAISS k-NN provides consistent minute-to-minute estimates.")
        report.append("")

        # Per-status summary
        report.append("## 4. Per-Status Summary")
        report.append("")
        report.append("| Status | N | Mean LAI | Mean Est Mag |")
        report.append("|--------|---|----------|--------------|")
        for st in ['QUIET', 'MONITOR', 'REVIEW', 'ALERT']:
            sub = successes[successes['system_status'] == st]
            if len(sub) > 0:
                report.append(f"| {st} | {len(sub)} | {sub['lai'].mean():.3f} | {sub['estimated_mag'].mean():.3f} |")

        report.append("")
        report.append("## 5. Edge Timing Simulation")
        report.append("")
        report.append(f"| Parameter | Value |")
        report.append("|--------|-------|")
        report.append(f"| Simulated interval | 60s (1 minute) |")
        report.append(f"| Inter-request delay | 100ms |")
        report.append(f"| Total wall time | ~{n * 0.1:.1f}s (plus network) |")

        report_path = RPT / "10_SHADOW_MODE_AUDIT.md"
        with open(str(report_path), 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        print(f"  [OK] Report saved: {report_path}")

        # Print quick summary
        print(f"\n{'='*60}")
        print(f"SHADOW MODE SUMMARY")
        print(f"{'='*60}")
        print(f"  API Latency:      mean={mean_lat:.3f}ms, p95={p95_lat:.3f}ms")
        print(f"  Status Transitions: {transitions}/{n_ok} ({transitions/max(1,n_ok)*100:.1f}%)")
        print(f"  Mag Stability:    mean_jump={mean_jump:.4f}, max_jump={max_jump:.4f}")
        print(f"  Log:              {log_path}")
        print(f"  Report:           {report_path}")
    else:
        # Print dry-run summary
        print(f"\n{'='*60}")
        print(f"DRY-RUN SUMMARY (no server call)")
        print(f"{'='*60}")
        print(f"  Station: {station}, samples: {n}")
        print(f"  To run live, start server then call without --dry-run")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LAWS Edge Simulator')
    parser.add_argument('--station', default='ALR', help='Station code')
    parser.add_argument('--max-samples', type=int, default=50, help='Samples to process')
    parser.add_argument('--api-url', default='http://localhost:8000/api/v1/magnitude-assistance')
    parser.add_argument('--dry-run', action='store_true', help='Skip server calls')
    args = parser.parse_args()

    simulate_edge_stream(
        station=args.station,
        max_samples=args.max_samples,
        api_url=args.api_url,
        dry_run=args.dry_run,
    )
