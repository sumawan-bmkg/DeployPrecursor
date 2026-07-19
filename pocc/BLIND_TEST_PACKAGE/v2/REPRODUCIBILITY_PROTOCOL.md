# Reproducibility Protocol

**Version:** 2.0
**Date:** 2026-07-16

---

## Purpose

Ensure that any researcher can reproduce the blind test results using the materials and documentation provided.

---

## 1. Environment Specification

| Component | Value | Verification |
|-----------|-------|-------------|
| OS | Ubuntu 22.04 LTS | `lsb_release -a` |
| Python | 3.12.x | `python --version` |
| PyTorch | (version from venv) | `pip show torch` |
| CUDA | (version if GPU) | `nvcc --version` |
| GPU | (model if applicable) | `nvidia-smi` |
| CPU | (model) | `lscpu` |
| RAM | (total) | `free -h` |

## 2. Environment Lock

```
pip freeze > requirements_frozen.txt
```

This file must be:
- Generated from the production `.venv`
- SHA256-logged
- Included in the publication supplementary materials
- Used for Docker/Conda environment reconstruction

## 3. Random Seeds

| Seed Type | Value | Where Set |
|-----------|-------|-----------|
| Python `random` | (value) | (location in code) |
| NumPy `np.random.seed` | (value) | (location in code) |
| PyTorch `torch.manual_seed` | (value) | (location in code) |
| CUDA `torch.cuda.manual_seed_all` | (value) | (location in code) |
| cuDNN deterministic | (True/False) | `torch.backends.cudnn.deterministic` |
| cuDNN benchmark | (True/False) | `torch.backends.cudnn.benchmark` |

## 4. Deterministic Mode

**Verification:** Run inference twice on same input. Compare outputs.

```
diff prediction_run1.csv prediction_run2.csv
```

If empty: deterministic. If non-empty: report differences and their magnitude.

**If using Bayesian inference:** Report that stochasticity is inherent in the method and provide confidence intervals rather than point predictions.

## 5. Checkpoint Hashes

| Checkpoint | Path | SHA256 |
|-----------|------|--------|
| Prior ALR | `laws/priors/prior_ALR.pt` | (hash) |
| Prior AMB | `laws/priors/prior_AMB.pt` | (hash) |
| ... (all 21) | ... | ... |
| Inference model | (path) | (hash) |

All hashes must be in `PRODUCTION_FREEZE_20260716.json`.

## 6. Dataset Hashes

| Dataset | Path | SHA256 |
|---------|------|--------|
| merge2026.csv | `initial/merge2026.csv` | (hash) |
| Cosmic features | `data/cosmic_features_v3.csv` | (hash) |
| Golden tensors | `laws/runtime/validation/golden_dataset/` | (per file) |

## 7. Configuration Hash

| Config | Hash |
|--------|------|
| deploy.py | `a083302fc70b839d` |
| main.py | `2340b3d4333073bb` |
| All .pt prior models | (hash each) |

## 8. Prediction Reproducibility

For every prediction in the registry:
- Input hash (waveform file SHA256)
- Output hash (prediction file SHA256)
- Checkpoint hash (model used)
- Config hash (deployment version)
- Environment hash (requirements_frozen.txt SHA256)
- Seed value used

## 9. Container Specification

**Recommended:** Provide Dockerfile for full environment reproduction.

```dockerfile
FROM python:3.12-slim
COPY requirements_frozen.txt .
RUN pip install -r requirements_frozen.txt
# ... (model files, data paths)
```

If Dockerfile not available, provide Conda environment.yml as alternative.

## 10. Minimum Reproducibility Checklist

- [ ] requirements_frozen.txt generated and SHA256-logged
- [ ] Random seeds documented
- [ ] Deterministic mode verified
- [ ] All checkpoint hashes in manifest
- [ ] Dataset hashes in manifest
- [ ] Inference run twice with identical results (or stochasticity documented)
- [ ] OS/hardware documented
- [ ] Python version verified
- [ ] PyTorch version verified
- [ ] CUDA version verified (if GPU)
