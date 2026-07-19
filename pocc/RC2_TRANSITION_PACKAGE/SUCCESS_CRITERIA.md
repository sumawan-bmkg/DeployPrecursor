# Success Criteria — PIMES v2.0.0-rc2-final

| Stage | Completion Criteria | Evidence Required |
|-------|-------------------|-------------------|
| **Operational Campaign** | ≥14 consecutive days without critical failure | OSC reports, CEPSL ledger, daily snapshots |
| **Waveform Acquisition** | BMKG data package received, validated, moved to `production/` | Checksum manifest, metadata verification log |
| **Blind Test** | All predictions recorded in `prediction_registry.csv`, compared against `merge2026.csv` | Ledger file, evaluation report |
| **Scientific Evaluation** | Precision, recall, F1, lead time, FAR, magnitude/azimuth error, ROC, PR curve | Statistical analysis report |
| **ERB Review** | Evidence chain auditable and reproducible from source to certificate | Master Evidence Manifest, CEPSL chain |
| **Publication** | Manuscript ready for submission, all artifacts consistent | Paper draft, supplementary materials |
| **RC2 Final Release** | Tag `v2.0.0-rc2-final` published | Git tag, release certificate |

## Gate Logic

```
Operational Campaign
        ↓ PASS
Waveform Acquisition
        ↓ COMPLETE
Blind Test
        ↓ COMPLETE
Scientific Evaluation
        ↓ PASS threshold
ERB Review
        ↓ APPROVED
Publication
        ↓ SUBMITTED
RC2 Final Release
```

## Minimum Threshold for Blind Test

| Metric | Minimum |
|--------|---------|
| Recall | > 0.80 |
| Precision | > 0.70 |
| F1 | > 0.74 |
| FAR | < 0.30 |
| Lead Time | > 6h mean |
| Magnitude Error | < 0.5 |
| Availability | > 0.95 |
