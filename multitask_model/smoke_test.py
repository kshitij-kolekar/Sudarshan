"""Smoke test (steps 1-8 of the Stage-2 first-implementation checklist):
  1 build dataset loader, 2 build model, 3 load one training sample,
  4 forward pass, 5 verify output shapes, 6 run all losses,
  7 one optimizer step, 8 confirm GPU memory usage.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).parent))

import dataset as D
import geometry as G
import losses as L
import model as M
import utils as U

cfg = U.load_config(Path(__file__).parent / "config.yaml")
U.set_seed(cfg["seed"])
device = "cuda" if torch.cuda.is_available() else "cpu"

print("[1] building dataset loader...")
df = U.load_targets_df(cfg["data"]["root"])
df = df[(df["valid"] == True) & (df["split"] == "train")]                # noqa: E712
dim_cols = list(cfg["model"]["dims"]) + list(cfg["model"]["dims_aux"])
stats = U.compute_target_stats(df[dim_cols].to_numpy(np.float64),
                               df["volume_m3"].to_numpy(np.float64))
ds = D.MultiTaskPotholeDataset(cfg, "train", use_aug=True)
ds.set_dim_stats(stats)
print("    dataset size:", len(ds))

print("[2] building model...")
try:
    model = M.build_model(cfg)
    pretrained = model.backbone.pretrained_source
except Exception as e:
    print("    pretrained failed, random init:", e)
    cfg["model"]["pretrained"] = False
    model = M.build_model(cfg)
    pretrained = "random-init"
model.to(device)
print(f"    params={model.count_params()/1e6:.2f}M  "
      f"weights={M.model_size_bytes(model)/1e6:.2f}MB  source={pretrained}")

print("[3] loading one training sample...")
img, mask, depth, valid, dims, vol, abs_depth, valid_abs = ds[0]
print(f"    img{tuple(img.shape)} mask{tuple(mask.shape)} depth{tuple(depth.shape)} "
      f"valid{tuple(valid.shape)} dims{tuple(dims.shape)} vol{tuple(vol.shape)}")
print(f"    abs_depth{tuple(abs_depth.shape)} valid_abs{tuple(valid_abs.shape)}")
print(f"    abs depth range: {abs_depth.min().item():.3f}..{abs_depth.max().item():.3f} m "
      f"valid_abs px: {int(valid_abs.sum())}  mask px: {int(mask.sum())}")

print("[4] forward pass...")
t0 = time.time()
with torch.no_grad():
    out = model(img.unsqueeze(0).to(device))
torch.cuda.synchronize() if device == "cuda" else None
print(f"    forward time: {(time.time()-t0)*1000:.0f} ms")

print("[5] output shapes / ranges:")
for k, v in out.items():
    print(f"    {k:7s} {tuple(v.shape)}  min={v.min().item():+.3f} max={v.max().item():+.3f}")
print(f"    cavity depth pred range: {out['depth'].min().item():.4f}.."
      f"{out['depth'].max().item():.4f} m")
print(f"    abs depth pred range:    {out['abs_depth'].min().item():.4f}.."
      f"{out['abs_depth'].max().item():.4f} m  "
      f"(head max={cfg['data']['abs_depth_max_m']})")
seg_prob = torch.sigmoid(out["seg"])
print(f"    seg prob range:   {seg_prob.min().item():.4f}..{seg_prob.max().item():.4f}")

print("[6] running all losses...")
criterion = L.MultiTaskLoss(cfg)
batch = (img.unsqueeze(0).to(device), mask.unsqueeze(0).to(device),
         depth.unsqueeze(0).to(device), valid.unsqueeze(0).to(device),
         dims.unsqueeze(0).to(device), vol.unsqueeze(0).to(device),
         abs_depth.unsqueeze(0).to(device),
         valid_abs.unsqueeze(0).to(device))
out = model(batch[0])
lossd = criterion(out, batch, len(cfg["model"]["dims"]))
for k, v in lossd.items():
    print(f"    {k:7s} {v.item():.5f}")

print("[7] one optimizer step...")
optim = torch.optim.AdamW(model.parameters(), lr=1e-4)
optim.zero_grad(set_to_none=True)
lossd["total"].backward()
gn = torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
optim.step()
print(f"    grad norm (pre-clip) = {gn.item():.4f}  [optimizer step OK]")

print("[8] GPU memory:")
if device == "cuda":
    print(f"    allocated={torch.cuda.memory_allocated()/1e6:.0f} MB  "
          f"reserved={torch.cuda.memory_reserved()/1e6:.0f} MB  "
          f"max_allocated={torch.cuda.max_memory_allocated()/1e6:.0f} MB")
else:
    print("    no CUDA device")

print("[9] road-plane geometry from predicted abs depth...")
seg_np = (torch.sigmoid(out["seg"]) > 0.5)[0].detach().cpu().numpy()
abs_np = out["abs_depth"][0].detach().cpu().numpy()
W, H = cfg["data"]["image_size"]
t0 = time.time()
res_g = G.geometry_from_abs_depth(seg_np, abs_np, cfg, W, H)
dt_g = time.time() - t0
print(f"    success={res_g['success']}  t={dt_g*1000:.0f} ms  "
      f"n_px={res_g['n_pixels']}")
if res_g["success"]:
    print(f"    len={res_g['length_m']:.3f}m w={res_g['width_m']:.3f}m "
          f"area={res_g['area_m2']:.4f}m^2 vol={res_g['volume_m3']*1000:.1f}L "
          f"plane={res_g['plane_dist_m']:.3f}m "
          f"mean_d={res_g['mean_depth_m']*100:.1f}cm")
else:
    print("    (geometry fit failed for this tiny smoke sample - expected "
          "early in training)")

print("\nSMOKE TEST STEPS 1-9 PASSED")
