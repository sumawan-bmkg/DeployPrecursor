"""OSC Phase 3 — Daily Report Generator."""
import json
from pathlib import Path
from .config import REPORTS, DATA, BASELINE
from .utils import now_iso, today, sf, sha256_str, ensure_dirs

def generate_daily():
    ensure_dirs()
    ts = today()
    day_log = DATA / "hourly" / f"snapshots_{ts}.jsonl"
    report_path = REPORTS / "daily" / f"report_{ts}.md"

    # Read day's snapshots
    snapshots = []
    if day_log.exists():
        for line in day_log.read_text(encoding="utf-8").strip().split("\n"):
            try: snapshots.append(json.loads(line))
            except: pass

    if not snapshots:
        (report_path).write_text(f"# Daily Report {ts}\n\nNo data collected yet.\n", encoding="utf-8")
        return

    # Compute daily stats
    healths = [sf(s.get("overall", 0)) for s in snapshots]
    ram = [sf(s.get("infrastructure", {}).get("ram_used_pct", 0)) for s in snapshots]
    pipelines = [sf(s.get("pipeline_healthy", 0)) for s in snapshots]

    avg_health = sum(healths) / len(healths)
    min_health = min(healths)
    max_health = max(healths)
    avg_ram = sum(ram) / len(ram)
    avg_pipeline = sum(pipelines) / len(pipelines)

    # Baseline comparison
    bl = {}
    try: bl = json.loads((BASELINE / "manifest.json").read_text())
    except: pass

    report = f"""# Daily Scientific Report — {ts}

Generated: {now_iso()}
Snapshots: {len(snapshots)}
Hours covered: {snapshots[0]['ts'][11:16] if snapshots else 'N/A'} — {snapshots[-1]['ts'][11:16] if snapshots else 'N/A'}

## Health Summary
| Metric | Avg | Min | Max |
|--------|-----|-----|-----|
| Overall Score | {avg_health:.1f}% | {min_health:.1f}% | {max_health:.1f}% |
| RAM Usage | {avg_ram:.1f}% | {min(ram):.1f}% | {max(ram):.1f}% |
| Pipeline Stages | {avg_pipeline:.0f} | {min(pipelines):.0f} | {max(pipelines):.0f} |

## Collector
| Metric | Value |
|--------|-------|
| Success | {snapshots[-1].get('collector', {}).get('success', 'N/A'):,} |
| Failed | {snapshots[-1].get('collector', {}).get('failed', 0):,} |
| Total | {snapshots[-1].get('collector', {}).get('total', 0):,} |

## Stability
- Health drift: {max_health - min_health:.1f}% (max-min)
- System {'STABLE' if max_health - min_health < 5 else 'UNSTABLE'}

## Report SHA256
{sha256_str(ts + avg_health.__str__())[:16]}
"""
    report_path.write_text(report, encoding="utf-8")
    print(f"  Daily report: {report_path.name} ({avg_health:.1f}% avg)")
    return {"report": report_path.name, "avg_health": avg_health, "snapshots": len(snapshots)}
