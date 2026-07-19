import torch, os
from pathlib import Path

prior_dir = Path("d:/multi/scalogramv3/laws/priors")
for f in sorted(prior_dir.glob("prior_*.pt")):
    p = torch.load(f, map_location="cpu")
    meta_file = f.with_suffix(".txt").name.replace("prior_", "prior_").replace(".pt", "_metadata.txt")
    meta_path = prior_dir / meta_file
    meta = meta_path.read_text().strip() if meta_path.exists() else "N/A"
    shape = p.shape if hasattr(p, "shape") else "scalar"
    dtype = p.dtype if hasattr(p, "dtype") else "N/A"
    print(f"{f.stem:20s} shape={str(shape):20s} dtype={str(dtype):10s} sum={p.sum():.4f} nan={torch.isnan(p).sum().item()} inf={torch.isinf(p).sum().item()} | {meta}")
print(f"\nTotal prior files: {len(list(prior_dir.glob('prior_*.pt')))}")
