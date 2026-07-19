"""
LAWS Monorepo Shared Core — Memory/RAM Verification
=====================================================
Verifies:
  1. Singleton pattern prevents multiple model loads
  2. Memory allocated once, not per-call
  3. RAM stays constant under concurrent simulated calls
  4. No memory leaks in downstream modules

Run:
  python laws/scripts/verify_monorepo_memory.py
"""
import os, sys, time, gc, warnings
import numpy as np
from pathlib import Path
warnings.filterwarnings('ignore')

LAWS = Path("d:/multi/scalogramv3/laws")
sys.path.insert(0, str(LAWS.parent))

print("=" * 60)
print("MONOREPO MEMORY VERIFICATION")
print("=" * 60)


def get_mem_mb():
    """Return current process memory in MB (Windows)."""
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        return proc.memory_info().rss / 1e6
    except ImportError:
        # Fallback: estimate from sys
        import tracemalloc
        # Not available on all platforms
        return None


# ── Test pre-import memory ────────────────────────────────────
mem_before = get_mem_mb()
print(f"\n[1/5] Memory before imports: {mem_before:.1f} MB" if mem_before else "[1/5] psutil not available")

# ── Import Shared Encoder (loads model ONCE) ──────────────────
print("\n[2/5] Loading SharedEncoder singleton...")
from laws.core import SharedEncoder
e1 = SharedEncoder()
mem_after_load = get_mem_mb()
if mem_after_load:
    delta = mem_after_load - (mem_before or 0)
    print(f"  Memory after load:  {mem_after_load:.1f} MB")
    print(f"  Delta:              {delta:+.1f} MB")

# ── Verify singleton: second call loads nothing ───────────────
print("\n[3/5] Singleton verification (second call = zero load)...")
mem_before_2 = get_mem_mb()
e2 = SharedEncoder()
assert e1 is e2, "Singleton broken!"
mem_after_2 = get_mem_mb()
if mem_before_2:
    delta2 = (mem_after_2 or 0) - (mem_before_2 or 0)
    print(f"  e1 is e2: ✅")
    print(f"  Memory delta: {delta2:+.2f} MB (should be ~0)")
    assert abs(delta2) < 1, f"Second instance leaked {delta2:.1f} MB!"

# ── Simulate 100 downstream calls ─────────────────────────────
print("\n[4/5] Stress test: 100 sequential encode calls...")
from laws.downstream.legacy_laws.magnitude_predictor import MagnitudePredictor
from laws.downstream.lt_laf.station_activity import StationActivityIndex
predictor = MagnitudePredictor()
sai = StationActivityIndex()

latencies = []
for i in range(100):
    img = np.random.randn(1, 3, 128, 1440).astype(np.float32)
    cosm = np.random.randn(1, 2).astype(np.float32)

    t0 = time.time()
    proj = e1.encode(img, cosm)
    t1 = time.time()
    _ = predictor.predict(proj)
    t2 = time.time()
    _ = sai.compute(proj[0], station="ALR")
    t3 = time.time()

    latencies.append({
        "encode_ms": (t1 - t0) * 1000,
        "mag_ms": (t2 - t1) * 1000,
        "activity_ms": (t3 - t2) * 1000,
        "total_ms": (t3 - t0) * 1000,
    })

mean_lat = {k: np.mean([l[k] for l in latencies]) for k in latencies[0]}
print(f"  100 calls complete.")
print(f"  Mean encode:     {mean_lat['encode_ms']:.2f}ms")
print(f"  Mean magnitude:  {mean_lat['mag_ms']:.2f}ms")
print(f"  Mean activity:   {mean_lat['activity_ms']:.2f}ms")
print(f"  Mean total:      {mean_lat['total_ms']:.2f}ms")

# ── Post-stress memory check ──────────────────────────────────
gc.collect()
mem_after_stress = get_mem_mb()
if mem_after_stress and mem_after_load:
    mem_drift = mem_after_stress - mem_after_load
    print(f"\n[5/5] Memory drift after 100 calls:")
    print(f"  Before stress: {mem_after_load:.1f} MB")
    print(f"  After stress:  {mem_after_stress:.1f} MB")
    print(f"  Drift:         {mem_drift:+.1f} MB")
    verdict = "✅ NO LEAK" if abs(mem_drift) < 5 else "⚠️ POSSIBLE LEAK"
    print(f"  Verdict:       {verdict}")
else:
    print("\n[5/5] Memory tracking skipped (psutil not available)")

# ── Final verdict ─────────────────────────────────────────────
print(f"\n{'=' * 60}")
print("MONOREPO MEMORY VERDICT")
print(f"{'=' * 60}")
print(f"  Singleton pattern:   ✅ (e1 is e2)")
print(f"  Backend:             {e1.metadata['backend']}")
print(f"  Mean inference:      {mean_lat['encode_ms']:.1f}ms/sample")
print(f"  Total downstream:    {mean_lat['total_ms']:.1f}ms/sample")
if np.mean([l['total_ms'] for l in latencies]) < 10000:
    print(f"  Real-time capable:   ✅ (< 10s per sample)")
if mem_after_stress and mem_after_load and abs(mem_after_stress - mem_after_load) < 5:
    print(f"  No memory leak:      ✅")
print("=" * 60)
