# ============================================================
# summarize_targets_v2.py
#
# Phase 14: dataset-level statistics for dimension_targets_v2.csv.
# Writes target_statistics.txt and prints a compact terminal summary.
# ============================================================
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"D:\drone\POTHOLE_TRAINING_DATASET")
df = pd.read_csv(ROOT / "dimension_targets_v2.csv")

METRICS = ["length_m", "width_m", "area_m2",
           "mean_depth_m", "median_depth_m", "p90_depth_m",
           "p99_depth_m", "max_depth_m", "volume_m3"]

v = df[df.valid & df.volume_m3.notna()]
n_total = len(df)
n_val = len(v)


def stat_line(col):
    s = v[col].dropna()
    return (f"{col:16s} min={s.min():.5f}  p05={s.quantile(.05):.5f}  "
            f"p25={s.quantile(.25):.5f}  median={s.median():.5f}  "
            f"mean={s.mean():.5f}  p75={s.quantile(.75):.5f}  "
            f"p95={s.quantile(.95):.5f}  max={s.max():.5f}")


lines = []
lines.append("=" * 78)
lines.append("PHYSICAL TARGET STATISTICS -- dimension_targets_v2.csv")
lines.append("Dataset root: " + str(ROOT))
lines.append("=" * 78)
lines.append(f"Total samples          : {n_total}")
lines.append(f"Valid (usable targets) : {n_val}  ({100.0*n_val/max(n_total,1):.1f}%)")
lines.append(f"Rejected               : {n_total - n_val}")
lines.append("")
for split in ["train", "val", "test"]:
    s_ = v[v.split == split]
    lines.append(f"  {split:5s}: valid {len(s_):4d} / {int((df.split==split).sum()):4d}")
lines.append("")

lines.append("-" * 78)
lines.append("Failure reasons")
lines.append("-" * 78)
fr = df.loc[~df.valid, "failure_reason"].value_counts(dropna=False)
for reason, c in fr.items():
    lines.append(f"  {c:4d}  {reason}")
lines.append("")

lines.append("-" * 78)
lines.append("Measurement statistics (valid samples)")
lines.append("-" * 78)
for m in METRICS:
    lines.append("  " + stat_line(m))
lines.append("")

lines.append("-" * 78)
lines.append("Consistency checks (volume vs footprint x mean_depth)")
lines.append("-" * 78)
ratio = v["volume_m3"] / (v["area_m2"] * v["mean_depth_m"])
lines.append(f"  volume/(area*mean_depth): p05={ratio.quantile(.05):.3f}  "
             f"median={ratio.median():.3f}  p95={ratio.quantile(.95):.3f}  "
             f"range=[{ratio.min():.3f}, {ratio.max():.3f}]")
impl = (v["area_m2"] * v["mean_depth_m"] * 1000.0)  # L
lines.append(f"  area x mean_depth (implied volume, L): median={impl.median():.1f}  "
             f"p05={impl.quantile(.05):.1f}  p95={impl.quantile(.95):.1f}")
impl2 = v["volume_m3"] * 1000.0
lines.append(f"  volume (L): median={impl2.median():.1f}  "
             f"p05={impl2.quantile(.05):.1f}  p95={impl2.quantile(.95):.1f}")
lines.append("")
lines.append("Depth sanity: median pothole depth vs documented paper range")
lines.append(f"  median mean_depth = {v.mean_depth_m.median()*100:.1f} cm "
             f"(paper reports ~4-6 cm; our shallow-end samples are sub-2cm)")
lines.append("")
lines.append("Quality of the road-plane fit:")
lines.append(f"  road_plane_inlier_ratio: min={v.road_plane_inlier_ratio.min():.3f}  "
             f"median={v.road_plane_inlier_ratio.median():.3f}")
lines.append(f"  road_plane_inliers     : min={int(v.road_plane_inliers.min())}  "
             f"median={int(v.road_plane_inliers.median())}  "
             f"max={int(v.road_plane_inliers.max())}")
lines.append("")
lines.append("Caveats and uncertainties")
lines.append(" - Intrinsics provisional D415 defaults (fx=fy=597.5 px); all lengths/areas")
lines.append("   are calibration-dependent and NOT survey-grade.")
lines.append(" - Depth units assumed mm (evidence: RealSense default, camera-height")
lines.append("   consistency, paper depth range); if the true scale differs, all")
lines.append("   metrics scale linearly.")
lines.append(" - Sub-3 mm cavity is treated as zero depth (noise floor).")

txt = "\n".join(lines)
(ROOT / "target_statistics.txt").write_text(txt, encoding="utf-8")
print(txt)
print("\nSaved:", ROOT / "target_statistics.txt")