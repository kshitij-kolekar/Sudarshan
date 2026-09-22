# ============================================================
# visualize_targets_v2.py
#
# Phase 13: visual validation of the v2 physical targets.
# Builds 2x2 validation panels for a representative sample
# (>=20 images) into the target_validation/ folder:
#
#   [1] RGB + GT pothole mask overlay
#   [2] raw depth map colorised (mm)
#   [3] cavity-depth map above the fitted road plane (metres)
#   [4] measurement summary text (length/width/area/depth/volume)
#
# A human/expert must still eyeball these panels, but every
# metric printed is exactly the value stored in
# dimension_targets_v2.csv, so any discrepancy is a bug.
# ============================================================
from pathlib import Path
import numpy as np
import pandas as pd
import cv2

import sys

ROOT = Path(r"D:\drone\POTHOLE_TRAINING_DATASET")
sys.path.insert(0, str(ROOT))
import generate_pothole_physical_targets_v2 as g
OUT = ROOT / "target_validation"
OUT.mkdir(parents=True, exist_ok=True)

FX, FY, CX, CY = 597.5, 597.5, 319.5, 239.5
DEPTH_SCALE = 0.001


def depth_color(depth_raw):
    d = np.clip(depth_raw.astype(np.float32) * DEPTH_SCALE, 0.0, 2.5)
    nz = d.max()
    if nz > 0:
        d = d / nz
    c = (cv2.applyColorMap((d * 255).astype(np.uint8), cv2.COLORMAP_JET))
    c[depth_raw == 0] = (0, 0, 0)
    return c


def panel_info(img, lines):
    out = img.copy()
    y = 18
    for ln in lines:
        cv2.putText(out, ln, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (255, 255, 255), 1, cv2.LINE_AA)
        y += 20
    return out


def draw_mask(img, mask):
    out = img.copy()
    contour, _ = cv2.findContours((mask * 255).astype(np.uint8),
                                  cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(out, contour, -1, (0, 255, 0), 2)
    return out


def cavity_color(cavity):
    v = cavity.copy()
    pos = v > 0
    if pos.any():
        top = float(np.percentile(v[pos], 99))
    else:
        top = 1.0
    top = max(top, 0.005)
    v = np.clip(v, 0.0, top) / top
    c = cv2.applyColorMap((v * 255).astype(np.uint8), cv2.COLORMAP_JET)
    c[cavity <= 0] = (0, 0, 0)
    return c, top


def main():
    df = pd.read_csv(ROOT / "dimension_targets_v2.csv")
    sel = []

    v = df[df.valid]
    n_sel = 0
    # largest / smallest, deepest / shallowest, failed reasons
    for label, sub in [("largest_area", v.nlargest(6, "area_m2")),
                       ("smallest_area", v[v.area_m2 >= 0.01].nsmallest(6, "area_m2")),
                       ("deepest", v.nlargest(6, "p90_depth_m")),
                       ("shallowest", v[v.area_m2 >= 0.01].nsmallest(6, "p90_depth_m"))]:
        for _, r in sub.iterrows():
            sel.append((r, label))
    # ensure a few failed samples are also shown
    for _, r in df[~df.valid].iterrows():
        sel.append((r, "FAILED")) 

    # dedupe by image, keep first
    seen = set()
    final = []
    for r, label in sel:
        if r.image not in seen:
            seen.add(r.image)
            final.append((r, label))
    final = final[:40]
    print(f"Building {len(final)} validation panels...")

    for r, label in final:
        split = r.split
        stem = Path(r.image).stem
        img = cv2.imread(str(ROOT / r.image))
        if r.valid and pd.notna(r.mask_path):
            mask = cv2.imread(str(ROOT / r.mask_path), cv2.IMREAD_GRAYSCALE) > 0
            cavity = np.load(ROOT / r.depth_target_path).astype(np.float32)
        else:
            h, w = img.shape[:2]
            mask, _ = g.read_polygon_mask(ROOT / r.label, h, w)
            mask = mask.astype(bool)
            cavity = np.zeros((h, w), dtype=np.float32)

        top = None
        if r.valid:
            p1 = draw_mask(img, mask)
            depth = np.load(ROOT / r.depth)
            p2 = depth_color(depth)
            pc, top = cavity_color(cavity)
        else:
            p1 = draw_mask(img, mask)
            depth = np.load(ROOT / r.depth)
            p2 = depth_color(depth)
            pc = cavity_color(cavity)[0]

        lines = []
        lines.append(f"split={split}  sample={stem}")
        lines.append(f"bucket={label}")
        if r.valid:
            lines.append(f"length={r.length_m:.3f} m   width={r.width_m:.3f} m")
            lines.append(f"area={r.area_m2:.4f} m2")
            lines.append(f"mean_depth={r.mean_depth_m*100:.1f} cm  "
                         f"p90={r.p90_depth_m*100:.1f} cm  "
                         f"max={r.max_depth_m*100:.1f} cm")
            lines.append(f"volume={r.volume_m3*1000:.0f} L  "
                         f"fill_ratio={r.volume_area_mean_depth_ratio:.2f}")
            lines.append(f"coverage={r.pothole_depth_coverage:.2f}  "
                         f"plane_inliers={r.road_plane_inliers}")
        else:
            lines.append(f"FAILED: {r.failure_reason}")

        p1 = panel_info(p1, lines[:4])
        p2 = panel_info(p2, ["raw depth (m, JET)"])
        pc = panel_info(pc, [
            (f"cavity top(p99)={top*100:.1f} cm" if top else "cavity map"),
        ])

        canvas = np.zeros((2 * 480, 2 * 640, 3), dtype=np.uint8)
        canvas[:480, :640] = p1
        canvas[:480, 640:1280] = p2
        canvas[480:960, :640] = pc
        canvas[480:960, 640:1280] = panel_info(img, lines)

        dst = OUT / f"{stem}_{label}.png"
        cv2.imwrite(str(dst), canvas)
        print("  wrote", dst.name)

    print(f"Done: {len(final)} panels in {OUT}")


if __name__ == "__main__":
    main()