# LAWS Phase 1 - Latent Representation Audit Report

**Generated:** 2026-06-29 13:28:56
**Model:** V8 SupCon (MultiTaskScalogramV3_v8)
**Checkpoint:** `laws/checkpoints/v8_supcon_best.pth`
**Dataset:** val split (1700 samples)
**Device:** cpu

---

## 1. Dataset Statistics

| Metric | Value |
|--------|-------|
| Total val samples | 1700 |
| Quiet (label=0, Kp<5) | 72 |
| Storm (Kp>=5) | 333 |
| Pre-earthquake (label=1) | 1295 |
| Kp range | [1.0, 8.7] |
| Storm days in val | 333 |
| Mag range (class 1) | [4.71, 6.54] |

## 2. Clustering Metrics (128D Latent Space)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Silhouette (cosine) | -0.40885597467422485 | >0.5 = well-separated clusters |
| Silhouette (euclidean) | -0.20314790308475494 | >0.5 = well-separated clusters |
| Davies-Bouldin Index | 3.2648734519020537 | lower is better |
| Trustworthiness (k=15) | 1.0 | >0.9 = local structure preserved |

## 3. Inter-Class Centroid Distances

| Pair | Cosine Distance | Euclidean Distance |
|------|-----------------|-------------------|
| Quiet <-> Storm | 0.0013 | 0.0515 |
| Quiet <-> Pre-earthquake | 0.0007 | 0.0380 |
| Storm <-> Pre-earthquake | 0.0022 | 0.0657 |

## 4. Geophysical Separation Evaluation

### Q1: Are geomagnetic storm anomalies (Kp >= 5) fully separated from lithospheric anomalies?

- **FINDING:** Poor separation (silhouette < 0.25). Heavy cluster overlap.
- Storm <-> Pre-earthquake centroid cosine distance: 0.0022
  => Possible confusion (distance < 0.3)

### Q2: Is Quiet-day embedding variance significantly lower than Pre-earthquake variance?

- **FINDING:** Pre-earthquake variance is 5.8x higher than Quiet. Latent space captures increased geophysical activity before earthquakes.
- Quiet variance (mean across dims): 0.000022
- Pre-earthquake variance: 0.000129

### Q3: Is there evidence of magnitude-based sub-clustering within earthquake embeddings?

| Magnitude Tier | Count | Visual Separation |
|----------------|-------|-------------------|
| M5.0-M5.5 | 407 | See UMAP/t-SNE figure |
| M5.6-M6.0 | 616 | See UMAP/t-SNE figure |
| M>6.0 | 494 | See UMAP/t-SNE figure |

**Magnitude-Embedding Correlation:**
- UMAP Dim 1 vs Magnitude: r=-0.172, p=0.0000
- UMAP Dim 2 vs Magnitude: r=-0.115, p=0.0000
- **FINDING:** Weak correlation - magnitude ordering not strongly encoded.

## 5. Conclusions

### Key Results

| Target Criterion | Value | Verdict |
|-----------------|-------|---------|
| Storm <-> Pre-earthquake separation | Silhouette cosine: -0.40885597467422485 | Overlapping |
| Quiet stability | Variance ratio: 5.795762538909912 | High stability |
| Magnitude ordering in embedding | r1=-0.17233803012446652, r2=-0.11521186612853485 | Weak |

### Output Files

| File | Description |
|------|-------------|
| `embeddings/proj_vectors.npy` | - |
| `embeddings/v_fusion_vectors.npy` | - |
| `embeddings/val_embeddings.csv` | - |
| `figures/01_umap_latent_space.png` | - |
| `figures/02_tsne_latent_space.png` | - |
| `figures/03_embedding_norms.png` | - |