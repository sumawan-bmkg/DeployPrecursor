# PIMES RC2 Scientific Governance Resolution

**Date:** 2026-07-16
**Baseline:** v2.0.0-rc2-freeze

---

## Status

```
Engineering Phase
        CLOSED
           │
           ▼
Scientific Operational Campaign
        ACTIVE
```

---

## Engineering Charter: CLOSED

The following activities are declared complete and transitioned to maintenance-only (hotfix):

- Architecture
- Model engineering
- Deployment engineering
- Dashboard engineering
- Governance engineering
- Release engineering
- Operational tooling

Changes to the baseline are only permitted through documented hotfix processes that do not modify the scientific methodology.

---

## Scientific Charter: ACTIVE

From this point forward, all project activities must fall into exactly one category:

### Operational Evidence
- OSC hourly logs
- CEPSL archive integrity
- Collector uptime and scheduling
- API/dashboard availability
- Evidence registry integrity

### Scientific Evidence
- Blind test predictions (append-only registry)
- Waveform qualification reports
- ROC/PR/F1 evaluation metrics
- Calibration analysis
- Physics validation (H/Z, polarization, EEJ)
- Null model comparisons
- Sensitivity analysis

### Publication Evidence
- Figures and tables
- Supplementary materials
- Dissertation appendix
- Data availability statements
- Reviewer response documentation

---

## Evidence Governance Policy

> **Scientific claims are earned through verified evidence, never assumed through engineering completion.**

- No MSCM claim transitions to **Verified** without auditable, reproducible evidence
- All evidence must have complete provenance (SHA256 chain + UTC timestamps)
- All MSCM status changes must be logged and reviewable

---

## Repository Growth Policy

### Directories that grow:
```
Campaign/       ← daily logs, weekly/monthly reports
Evidence/       ← MSCM evidence files, EEJ, geomagnetic context
Blind_Test/     ← prediction registry, evaluation results
Publication/    ← figures, tables, manuscript drafts
```

### Directories frozen (hotfix only):
```
backend/        ← dashboard
deployment/     ← PDM
runtime/        ← inference engine
collector/      ← data ingestion
validation/     ← PSEP, CSQ, SOQ, SEOS, OSRV
dashboard/      ← 30 pages
```

---

## Exit Criteria

Proyek selesai hanya jika semua terpenuhi:

- **Gate A:** Engineering Baseline — **PASS**
- **Gate B:** Operational Stability — **PASS** (6 quantitative criteria, ≥14 days)
- **Gate C:** Scientific Blind Test — **PASS** (signed DQR, immutable predictions)
- **Gate D:** Publication Readiness — **PASS** (all required claims Verified or Rejected, figures, manuscript)
- **MSCM:** All claims in the paper have status **Verified** or **Rejected** — no pending claims in publication
- **Reproducibility:** All evidence can be traced from publication → MSCM → evidence file → source data via SHA256 chain

---

## ERB Resolution (2026-07-16)

| Gate | Decision |
|------|----------|
| Engineering Baseline | ✅ **APPROVED** |
| Operational Baseline | ✅ **APPROVED** |
| Scientific Protocol | ✅ **APPROVED** |
| Evidence Governance | ✅ **APPROVED** |
| Operational Campaign | 🔄 **AUTHORIZED TO CONTINUE** |
| Blind Test | ⏳ **AUTHORIZED UPON DATA QUALIFICATION** |
| Publication | ⏳ **DEFERRED UNTIL EVIDENCE COMPLETE** |

---

## Future Meeting Agenda

The question is no longer *"what feature will we build?"* but:

1. **What new evidence has been collected since the last meeting?**
2. **Has any MSCM claim changed status based on verified evidence?**
3. **Have Gate B, Gate C, or Gate D made measurable progress?**
4. **Are there any risks to the integrity of the scientific campaign?**

---

## Final Position

> **PIMES RC2 has completed the software engineering phase and entered the scientific operational campaign phase. The engineering baseline is frozen, evidence governance is approved, and the blind test methodology is established. Further project success is determined not by feature development, but by the quality of accumulated evidence, the integrity of blind test execution, and the strength of the resulting scientific analysis.**

---

## Scientific Mission Statement

> **Menghasilkan bukti ilmiah yang dapat direproduksi untuk membuktikan atau membantah hipotesis bahwa anomali geomagnetik ULF mengandung informasi prekursor gempa yang dapat dideteksi secara operasional menggunakan sistem PIMES.**

This accepts both outcomes. Scientific integrity requires it.

---

## Research Hypothesis

**H₀ (Null Hypothesis):**

> Tidak terdapat peningkatan kemampuan prediksi yang signifikan secara statistik dibandingkan baseline setelah menggunakan anomali geomagnetik ULF.

**H₁ (Alternative Hypothesis):**

> Integrasi anomali geomagnetik ULF ke dalam sistem PIMES menghasilkan peningkatan kemampuan prediksi yang signifikan secara statistik dibandingkan baseline yang telah ditentukan.

---

## Scientific Integrity Principles

**Principle 1 — Evidence precedes conclusion.**
Tidak ada kesimpulan tanpa evidence.

**Principle 2 — Reproducibility precedes publication.**
Tidak ada publikasi tanpa reproduksibilitas.

**Principle 3 — Operational success does not imply scientific validity.**
Sistem yang stabil belum tentu hipotesisnya benar.

**Principle 4 — Negative results are scientific results.**
Apabila blind test menunjukkan hipotesis tidak didukung, hasil tersebut tetap merupakan kontribusi ilmiah yang sah.

**Principle 5 — MSCM is the single source of scientific truth.**
Seluruh klaim ilmiah harus dapat ditelusuri kembali ke evidence yang telah diverifikasi.

---

## Definition of Success

PIMES RC2 is considered successful if:

1. Engineering baseline remains unchanged throughout the campaign.
2. Operational campaign produces complete, auditable evidence.
3. Blind test is executed per protocol without deviation.
4. All statistical analyses follow SBTP v2.0.
5. MSCM is updated only based on verified evidence.
6. Results — whether supporting or refuting the hypothesis — are fully and transparently documented.

---

## Final Position

> **PIMES RC2 has transitioned from building an operational system to conducting a scientific investigation. The software is no longer the hypothesis; it is the instrument. The evidence gathered through disciplined operation, qualified data, and blinded evaluation will determine the scientific value of the project.**

---

## Scientific Mission Statement

> **Menghasilkan bukti ilmiah yang dapat direproduksi untuk membuktikan atau membantah hipotesis bahwa anomali geomagnetik ULF mengandung informasi prekursor gempa yang dapat dideteksi secara operasional menggunakan sistem PIMES.**

This accepts both outcomes. Scientific integrity requires it.

---

## Research Hypothesis

**H₀ (Null Hypothesis):**

> Tidak terdapat peningkatan kemampuan prediksi yang signifikan secara statistik dibandingkan baseline setelah menggunakan anomali geomagnetik ULF.

**H₁ (Alternative Hypothesis):**

> Integrasi anomali geomagnetik ULF ke dalam sistem PIMES menghasilkan peningkatan kemampuan prediksi yang signifikan secara statistik dibandingkan baseline yang telah ditentukan.

---

## Scientific Integrity Principles

**Principle 1 — Evidence precedes conclusion.**
Tidak ada kesimpulan tanpa evidence.

**Principle 2 — Reproducibility precedes publication.**
Tidak ada publikasi tanpa reproduksibilitas.

**Principle 3 — Operational success does not imply scientific validity.**
Sistem yang stabil belum tentu hipotesisnya benar.

**Principle 4 — Negative results are scientific results.**
Apabila blind test menunjukkan hipotesis tidak didukung, hasil tersebut tetap merupakan kontribusi ilmiah yang sah.

**Principle 5 — MSCM is the single source of scientific truth.**
Seluruh klaim ilmiah harus dapat ditelusuri kembali ke evidence yang telah diverifikasi.

---

## Definition of Success

PIMES RC2 is considered successful if:

1. Engineering baseline remains unchanged throughout the campaign.
2. Operational campaign produces complete, auditable evidence.
3. Blind test is executed per protocol without deviation.
4. All statistical analyses follow SBTP v2.0.
5. MSCM is updated only based on verified evidence.
6. Results — whether supporting or refuting the hypothesis — are fully and transparently documented.

---

## Final Position

> **PIMES RC2 has transitioned from building an operational system to conducting a scientific investigation. The software is no longer the hypothesis; it is the instrument. The evidence gathered through disciplined operation, qualified data, and blinded evaluation will determine the scientific value of the project.**

---

## Document Hierarchy

**Level 1 — Governing Documents**
- `SCIENTIFIC_GOVERNANCE_RESOLUTION.md`
- `PROJECT_FREEZE_POLICY.md`
- `SCIENTIFIC_BASELINE_FREEZE.md`

**Level 2 — Scientific Protocols**
- SBTP v2.0 (8 protocol files)
- Statistical Validation Protocol
- Physics Validation Protocol
- Explainability Protocol
- Reproducibility Protocol

**Level 3 — Evidence**
- OSC daily logs
- CEPSL archive chain
- MSCM (18 claims)
- Evidence Atlas / Evidence Index
- Blind Test Ledger

**Level 4 — Outputs**
- Dissertation
- GJI Paper
- Executive Report
- RC2 Final Release (`v2.0.0-rc2-final`)

---

## Evidence Quality Levels

| Level | Definition | Example |
|-------|-----------|---------|
| **E0** | Raw observation | Collector output on disk |
| **E1** | Verified observation | Checksum valid, timestamp valid |
| **E2** | Qualified dataset | Passed Data Qualification Gate |
| **E3** | Scientific evidence | Used for statistical analysis |
| **E4** | Published evidence | Figure/table in paper |
| **E5** | Independent reproduction | Reproduced by external evaluator |

---

## Final ERB Resolution

> Engineering Phase: **Closed**.
> Operational Phase: **Active**.
> Scientific Campaign: **Authorized**.
> Repository Baseline: **Frozen**.
> Model Architecture: **Frozen**.
> Evaluation Protocol: **Frozen**.
> Evidence Collection: **Running**.

**Decision authority:** Evidence → MSCM → ERB → Report → Publication.

**Not:** "Model looks good" → immediate claim.

---

## Remaining Work (No Code)

These 5 documents are now complete:
1. **Scientific Evidence Index** — `Campaign/Evidence/SCIENTIFIC_EVIDENCE_INDEX.md`
2. **MSCM Coverage Report** — `Campaign/Evidence/MSCM_COVERAGE_REPORT.md`
3. **Statistical Analysis Notebook** — `Campaign/Evaluation/STATISTICAL_ANALYSIS_NOTEBOOK.md`
4. **Publication Traceability Matrix** — `Campaign/Publication/PUBLICATION_TRACEABILITY_MATRIX.md`
5. **Independent Reproduction Package** — `Campaign/Publication/INDEPENDENT_REPRODUCTION_PACKAGE.md`

They require zero code changes. They are waiting for blind test data to be filled.

---

**Signed:**
**Independent Scientific Auditor / ERB Chair**
**2026-07-16**
