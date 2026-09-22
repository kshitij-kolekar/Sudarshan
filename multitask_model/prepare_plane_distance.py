"""Stage-2 target prep: derive a per-sample road-plane distance target.

The Stage-1 physical area/volume use the camera-to-road-plane distance
`lam` (~1-3 m), NOT the cavity depth (~cm).  For an RGB-only model we need to
predict a scene-scale quantity so `geometry.py` can convert predicted mask +
cavity depth into metric area/length/width/volume.

`plane_dist_m` := mean over the GT mask footprint of the road-plane depth
                  Z_plane = Z_raw - cavity,   Z_raw in metres (depth npy is mm).

This does NOT fit any plane and does NOT touch dimension_targets_v2.csv; it
writes a small sidecar table used only as an extra regression target.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\drone\POTHOLE_TRAINING_DATASET")


def main():
    df = pd.read_csv(ROOT / "dimension_targets_v2.csv")
    df = df[df["valid"] == True].copy()                       # noqa: E712

    import cv2

    rows = []
    n_fail = 0
    for i, r in df.iterrows():
        mask = cv2.imread(str(ROOT / r["mask_path"]), cv2.IMREAD_GRAYSCALE)
        cav = np.load(ROOT / r["depth_target_path"]).astype(np.float32)
        raw = np.load(ROOT / r["depth"]).astype(np.float32)
        if mask is None:
            n_fail += 1
            continue
        m = (mask > 127) & (cav > 0.0)
        z = raw / 1000.0
        zplane = z - cav
        vals = zplane[m & np.isfinite(zplane) & (z > 0.05) & (z < 10.0)]
        if vals.size < 10:
            m2 = (mask > 127) & np.isfinite(zplane) & (z > 0.05)
            vals = zplane[m2]
        if vals.size < 10:
            n_fail += 1
            continue
        rows.append({"image": r["image"], "split": r["split"],
                     "plane_dist_m": float(np.mean(vals))})

    out = pd.DataFrame(rows)
    out = out.sort_values("image").reset_index(drop=True)
    out.to_csv(ROOT / "targets_v2" / "plane_dist_v2.csv", index=False)
    print(f"[plane_dist] wrote {len(out)} rows -> targets_v2/plane_dist_v2.csv "
          f"(failed={n_fail})")
    for sp in ["train", "val", "test"]:
        s = out[out["split"] == sp]["plane_dist_m"]
        print(f"  {sp:5s} n={len(s):4d} mean={s.mean():.3f}m  "
              f"min={s.min():.3f}  max={s.max():.3f}")


if __name__ == "__main__":
    main()