"""ST-LAF smoke test — runs all components end-to-end."""
import sys, os, numpy as np

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    # 1. TemporalBuffer
    from app.models.temporal_buffer import TemporalBuffer
    buf = TemporalBuffer(window_size=5)
    for i in range(12):
        proj = np.random.randn(128).astype(np.float64)
        proj /= np.linalg.norm(proj)
        buf.push('ALR', proj)
        buf.push('SCN', proj * 0.5)
    win = buf.get_window('ALR')
    assert win.shape == (5, 128), f"Expected (5,128), got {win.shape}"
    assert buf.station_count() == 2
    print("1. TemporalBuffer: OK")

    # 2. SpatialFuser
    from app.models.spatial_fuser import SpatialFuser
    fuser = SpatialFuser()
    projections = {
        'ALR': np.random.randn(128).astype(np.float64),
        'SCN': np.random.randn(128).astype(np.float64),
        'GTO': np.random.randn(128).astype(np.float64),
    }
    fused = fuser.fuse(projections)
    assert fused['n_stations'] == 3
    assert fused['cluster_radius'] > 0
    print("2. SpatialFuser: OK")

    # 3. ActivityEstimator
    from app.models.activity_estimator import ActivityEstimator
    est = ActivityEstimator()
    result = est.estimate(
        temporal_raw={'ALR': 1.5, 'SCN': 0.8},
        spatial_fused=fused,
        baseline_prior=None,
    )
    assert 0 <= result['activity_index'] <= 100
    assert result['system_status'] in ['QUIET', 'MONITOR', 'REVIEW', 'ALERT']
    assert set(result['components'].keys()) == {'temporal', 'spatial', 'baseline'}
    print("3. ActivityEstimator: OK")

    # 4. Pipeline end-to-end
    from app.pipeline import ingest, ingest_batch, get_state, reset_state
    reset_state()
    for i in range(6):
        proj = np.random.randn(128).astype(np.float32)
        proj /= np.linalg.norm(proj)
        r = ingest('ALR', proj)
    r2 = ingest_batch({
        'ALR': np.random.randn(128).astype(np.float32),
        'SCN': np.random.randn(128).astype(np.float32),
        'GTO': np.random.randn(128).astype(np.float32),
    })
    state = get_state()
    assert 0 <= r2['activity_index'] <= 100
    assert state['stations_active'] >= 3
    print(f"4. Pipeline: activity={r2['activity_index']}, status={r2['system_status']}, active={state['stations_active']}")

    # 5. Regression: deterministic output for same input
    reset_state()
    rng = np.random.RandomState(42)
    ref = None
    for i in range(20):
        p = rng.randn(128).astype(np.float32)
        p /= np.linalg.norm(p)
        station = ['ALR', 'SCN', 'GTO', 'PLU'][i % 4]
        r = ingest(station, p)
        if i == 19:
            ref = r['activity_index']
    reset_state()
    rng2 = np.random.RandomState(42)
    for i in range(20):
        p = rng2.randn(128).astype(np.float32)
        p /= np.linalg.norm(p)
        station = ['ALR', 'SCN', 'GTO', 'PLU'][i % 4]
        r = ingest(station, p)
        if i == 19:
            assert abs(r['activity_index'] - ref) < 1e-10, \
                f"Non-deterministic: {r['activity_index']} != {ref}"
    print("5. Determinism: OK")

    print()
    print("ALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
