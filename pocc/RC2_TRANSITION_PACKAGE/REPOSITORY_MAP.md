# PIMES Repository Map

```
PIMES (d:\opt\pimes\)
│
├── pocc/                    ← Production Operations Command Center
│   ├── backend/             ← BOCC Dashboard (main.py + 29 templates)
│   ├── collector/           ← Data ingestion (5 workers)
│   ├── deploy.py            ← PDM (single deployment manager)
│   ├── deployment/          ← (blue-green restart scripts)
│   ├── manifests/           ← SHA256 freeze manifests
│   ├── validation/          ← PSEP, CSQ, SOQ, SEOS, OSRV, SOAP
│   │
│   ├── RC2_TRANSITION_PACKAGE/    ← All operational documentation
│   ├── PIMES_SCIENTIFIC_DATA_BOOK/ ← Scientific data book (18 sections)
│   ├── PIMES_ARCHIVE/             ← Long-term archive (v2.0.0-rc2-freeze)
│   ├── REPRODUCIBILITY_BOOK/      ← Environment + hashes + how-to
│   ├── BLIND_TEST_PACKAGE/        ← Evaluation protocol + metrics
│   ├── BLIND_TEST_LEDGER/         ← Prediction registry
│   ├── incoming/                  ← BMKG data quarantine
│   ├── production/                ← Validated waveform data
│   └── publication/               ← Paper figures, tables, methods
│
├── laws/                    ← LAWS Runtime + models
│   ├── runtime/             ← Inference engine, .venv
│   ├── priors/              ← 21 station prior distributions
│   ├── h5/                  ← Scalogram outputs
│   └── embeddings/          ← Validation embeddings
│
├── posc/                    ← Post-Operations
│   ├── osc/                 ← Campaign data + CEPSL
│   ├── csq/                 ← Scientific qualification
│   └── validation/          ← Drill simulations
│
├── data/                    ← Data directory
│   └── raw/<STATION>/       ← Per-station waveform data
│
└── initial/                 ← merge2026.csv (evaluation catalog)
```

## Key Entry Points

| Purpose | Path |
|---------|------|
| Dashboard | `pocc/backend/main.py` (port 8500) |
| Deploy | `pocc/deploy.py` |
| Documentation | `pocc/RC2_TRANSITION_PACKAGE/` |
| Scientific book | `pocc/PIMES_SCIENTIFIC_DATA_BOOK/` |
| Blind test protocol | `pocc/BLIND_TEST_PACKAGE/` |
| Prediction ledger | `pocc/BLIND_TEST_LEDGER/` |
| Incoming data | `pocc/incoming/` |
| Evidence manifest | `pocc/PIMES_SCIENTIFIC_DATA_BOOK/MASTER_EVIDENCE_MANIFEST.json` |
| Git tag | `v2.0.0-rc2-freeze` |
