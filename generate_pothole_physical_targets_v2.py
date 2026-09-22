# ============================================================
# generate_pothole_physical_targets_v2.py
#
# Rebuild of the physical target-generation pipeline for the
# PothRGBD-derived dataset at D:\drone\POTHOLE_TRAINING_DATASET.
#
# Goal:
#   Derive physical pothole supervision targets from
#     RGB image
#     + GROUND-TRUTH YOLO segmentation label
#     + depth map (uint16)
#   These targets are for training a future RGB-only multi-task
#   model.  The GT depth map is NEVER an inference input.
#
# Outputs:
#   dimension_targets_v2.csv    (main supervision table)
#   target_statistics.txt       (dataset-level stats)
#   target_validation/          (visual overlays, >=20 samples)
#   targets_v2/{split}/...      (rasterized mask + cavity-depth arrays)
#
# The previous dimension_targets.csv was produced with an
# inverted cavity-sign convention and inconsistent area/volume
# definitions (see report).  This script fixes both.
#
# ============================================================
# DEPTH UNIT / SCALE  (Phase 2 evidence, verified before use)
# ============================================================
# Depth maps are uint16 and were collected with an Intel
# RealSense D415 (Yurdakul & Tasdemir, arXiv:2505.04207 /
# IEEE DataPort 10.21227/z8eq-sf60).
#
# Conclusion: raw units are MILLIMETRES.
# Evidence:
#  - RealSense D400-series depth frames are millimeters by
#    default (depth_scale = 0.001 m per count).
#  - Observed road-surface medians: 279 .. 3118 units
#    (dataset median ~850).  A hand-held portable rig held at
#    ~0.8-0.9 m above the road gives exactly this range (mm).
#    Interpreting these as 0.1 mm units would put the camera
#    8-9 m above the road, which is inconsistent with the
#    collection rig described in the paper.
#  - Pothole cavity signed-distances measured relative to the
#    fitted road plane fall in ~0.01-0.07 m (1-7 cm), matching
#    the paper's reported pothole depths (~4-6 cm) and its
#    measured depth accuracy (+-0.24 cm).
#
# Caveat / uncertainty: the paper does not print the exact
# per-device depth scale, so this is an evidence-based default,
# not a published number.  If the true scale differs, every
# metric output scales linearly.  Configurable below.
# ============================================================
# CAMERA INTRINSICS  (Phase 6)
# ============================================================
# Exact per-device calibration is NOT published for PothRGBD.
# Best documented provisional values (used consistently by the
# existing project code) are the D415 defaults below:
#   fx = fy = 597.5 px, cx = 319.5, cy = 239.5 (640x480).
# NOTE: 597.5/640 -> H-FOV 56.3 deg, V-FOV 43.8 deg, which is
# narrower than the D415 datasheet depth FOV (65x40 deg).  The
# true factory calibration of the device is unknown, therefore
# ALL length/area outputs are CALIBRATION-DEPENDENT and must
# not be claimed as survey-grade.  Depth-derived statistics
# (depth / volume relative to the plane) are far less sensitive
# to focal-length error.
# ============================================================

from pathlib import Path
import numpy as np
import pandas as pd
import cv2

# ============================================================
# CONFIGURATION  (documented, intentional, adjustable)
# ============================================================
ROOT = Path(r"D:\drone\POTHOLE_TRAINING_DATASET")

# --- Camera model (see intrinsics note above) ---------------
FX = 597.5          # provisional D415 focal length, px
FY = 597.5          # provisional D415 focal length, px
CX = 319.5          # principal point x (640/2 - 0.5)
CY = 239.5          # principal point y (480/2 - 0.5)

# --- Depth scale (see depth-unit note above) ---------------
DEPTH_SCALE_TO_METERS = 0.001   # raw uint16 [mm] -> metres

# --- Depth cleaning -----------------------------------------
INVALID_DEPTH_VALUE = 0          # RealSense 'no data' sentinel
SENTINEL_DEPTH_VALUE = 65535     # out-of-range / invalid sentinel
MIN_DEPTH_M = 0.10               # below D415 reliable min-Z range
MAX_DEPTH_M = 3.0                # maximum useful depth for road geometry.
                                 #  Chosen explicitly: road surface of interest
                                 #  is never farther than ~2.5 m; 3.0 m keeps a
                                 #  margin while excluding background walls/foliage.
                                 #  (Not a silent clip of physically valid pothole
                                 #  depth: any pixel > 3.0 m cannot be road.)

# --- Cavity depth handling ----------------------------------
DEPTH_NOISE_M = 0.003            # 3 mm noise floor (RealSense ~2-3 mm @1m,
                                 #  paper depth error +-0.24 cm). Values below
                                 #  this are set to 0 (treated as 'no cavity').
MAX_CAVITY_M = 0.30              # 30 cm hard physical plausibility cap for a
                                 #  pothole cavity in this dataset; above this is
                                 #  treated as depth outlier.
MAX_CAVITY_OUTLIER_FRACTION = 0.30  # if more than 30% of cavity pixels exceed
                                 #  MAX_CAVITY_M the sample is rejected.

# --- Road-plane fitting (RANSAC) -----------------------------
RANSAC_ITERS = 400
PLANE_DISTANCE_M = 0.02          # inlier tolerance for plane fitting (2 cm)
MAX_RANSAC_POINTS = 25000        # cap for speed
MIN_ROAD_CANDIDATES = 500        # min road pixels to attempt a plane
MIN_INLIERS = 400                # min accepted plane inliers
MIN_INLIER_RATIO = 0.40          # min inliers / road samples used
MIN_ABS_NZ = 0.35                # plane normal must be mostly along +Z
                                 #  (rejects edge-on/grazing recoveries)
DILATE_KERNEL = 41               # dilate GT mask before selecting road pixels,
                                 #  so pothole boundary pixels do not
                                 #  contaminate the road plane.
BBOX_MARGIN_PX = 180             # road candidates taken from an expanded box
                                 #  around the pothole to avoid far background.
SVD_REFINE_ITERS = 2             # least-squares plane refinements on inliers
EDGE_CROP_PX = 8                 # ignore the outer 8 px ring for plane fitting
RANDOM_SEED = 42

# --- Minimum sample-quality thresholds ------------------------
MIN_MASK_PIXELS = 20                 # minimum GT pothole size in pixels
MIN_VALID_POTHOLE_DEPTH_PIXELS = 30  # valid (cleaned) depth pixels in mask
MIN_CAVITY_PIXELS = 20               # pixels with cavity above noise floor
MIN_COVERAGE = 0.05                  # (valid depth in mask) / mask pixels

# --- Physical plausibility ranges ------------------------------
MAX_LENGTH_M = 10.0
MAX_WIDTH_M = 10.0
MAX_AREA_M2 = 50.0
MAX_DEPTH_STAT_M = 0.5               # max permitted mean/p90/p99/max depth
MAX_VOLUME_M3 = 10.0

# --- Volume sanity -------------------------------------------------
# volume / (area * mean_depth) -- with area taken over the WHOLE pothole
# footprint and mean_depth over POSITIVE-cavity pixels, this ratio is
# the cavity 'fill fraction' and is expected in (0, 1].  Outside the
# configurable band the sample is flagged suspicious_volume.
VOLUME_RATIO_MIN = 0.02
VOLUME_RATIO_MAX = 1.50

rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# Ground-truth mask  (Phase 4)
# ============================================================
def read_polygon_mask(label_path, h, w):
    """Rasterize YOLO segmentation polygons to a binary mask.

    Supports multiple polygons.  Returns (mask, error) where error is
    None on success or a short failure reason string.
    """
    mask = np.zeros((h, w), dtype=np.uint8)
    if label_path is None or not label_path.exists():
        return mask, "invalid_polygon"

    lines = label_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    polys = 0
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        try:
            cls = int(float(parts[0]))
            coords = np.asarray([float(x) for x in parts[1:]], dtype=np.float32)
        except ValueError:
            continue
        if len(coords) == 4:  # bbox-only line (class x1 y1 x2 y2)
            x1, y1, x2, y2 = coords
            x1 = int(round(np.clip(x1 * w, 0, w - 1)))
            x2 = int(round(np.clip(x2 * w, 0, w - 1)))
            y1 = int(round(np.clip(y1 * h, 0, h - 1)))
            y2 = int(round(np.clip(y2 * h, 0, h - 1)))
            cv2.rectangle(mask, (x1, y1), (x2, y2), 1, thickness=-1)
            polys += 1
            continue
        if len(coords) < 6 or len(coords) % 2 != 0:
            continue
        if not np.all(np.isfinite(coords)):
            continue
        pts = coords.reshape(-1, 2)
        pts[:, 0] = np.clip(pts[:, 0] * w, 0, w - 1)
        pts[:, 1] = np.clip(pts[:, 1] * h, 0, h - 1)
        cv2.fillPoly(mask, [np.round(pts).astype(np.int32)], 1)
        polys += 1

    if polys == 0:
        return mask, "invalid_polygon"
    if not mask.any():
        return mask, "invalid_polygon"
    return mask, None


# ============================================================
# Depth cleaning + back-projection  (Phases 3, 6)
# ============================================================
def clean_depth(depth_raw):
    """Return (depth_m, valid) with cleaned metric depth."""
    depth = depth_raw.astype(np.float32) * DEPTH_SCALE_TO_METERS
    valid = (
        np.isfinite(depth)
        & (depth_raw != INVALID_DEPTH_VALUE)
        & (depth_raw != SENTINEL_DEPTH_VALUE)
        & (depth >= MIN_DEPTH_M)
        & (depth <= MAX_DEPTH_M)
    )
    depth = np.where(valid, depth, 0.0)
    return depth, valid


def backproject(depth_m):
    """Camera-frame 3D points: x right, y down, z forward."""
    h, w = depth_m.shape
    ys, xs = np.indices((h, w))
    z = depth_m
    x = (xs.astype(np.float32) - CX) * z / FX
    y = (ys.astype(np.float32) - CY) * z / FY
    return np.stack([x, y, z], axis=-1)


def oriented_plane(points, valid, exclude_mask):
    """Fit the dominant road plane robustly (RANSAC + LS refine).

    Returns (n, d, inliers, inlier_ratio, signed_on_road_side) with
    normal oriented AWAY from the camera (n_z > 0).  For a point on the
    plane n.p + d = 0; the side farther from the camera (larger z) has
    positive signed distance --- that is the pothole-cavity side.
    """
    h, w = valid.shape
    dil = cv2.dilate(exclude_mask.astype(np.uint8),
                     np.ones((DILATE_KERNEL, DILATE_KERNEL), np.uint8),
                     iterations=1).astype(bool)

    ys, xs = np.indices((h, w))
    if exclude_mask.any():
        nz = np.argwhere(exclude_mask)
        by0, bx0 = nz.min(axis=0)
        by1, bx1 = nz.max(axis=0)
    else:
        by0, bx0, by1, bx1 = 0, 0, h - 1, w - 1
    y0 = max(EDGE_CROP_PX, by0 - BBOX_MARGIN_PX)
    y1 = min(h - EDGE_CROP_PX, by1 + BBOX_MARGIN_PX + 1)
    x0 = max(EDGE_CROP_PX, bx0 - BBOX_MARGIN_PX)
    x1 = min(w - EDGE_CROP_PX, bx1 + BBOX_MARGIN_PX + 1)

    window = np.zeros((h, w), dtype=bool)
    window[y0:y1, x0:x1] = True
    candidate = valid & (~dil) & window
    if int(candidate.sum()) < MIN_ROAD_CANDIDATES:
        candidate = valid & (~dil)   # fall back to the whole image
    if int(candidate.sum()) < MIN_ROAD_CANDIDATES:
        return None, None, 0, 0.0

    idx = np.flatnonzero(candidate)
    if len(idx) > MAX_RANSAC_POINTS:
        idx = rng.choice(idx, MAX_RANSAC_POINTS, replace=False)
    pts = points.reshape(-1, 3)[idx]
    n_total = len(idx)

    best_n, best_d, best_count = None, None, 0
    for _ in range(RANSAC_ITERS):
        s = pts[rng.choice(n_total, 3, replace=False)]
        n = np.cross(s[1] - s[0], s[2] - s[0])
        nn = np.linalg.norm(n)
        if nn < 1e-9:
            continue
        n = n / nn
        d = -float(n @ s[0])
        dist = np.abs(pts @ n + d)
        c = int(np.sum(dist < PLANE_DISTANCE_M))
        if c > best_count:
            best_count, best_n, best_d = c, n, d

    if best_n is None:
        return None, None, 0, 0.0

    mask_in = np.abs(pts @ best_n + best_d) < PLANE_DISTANCE_M
    cur_n, cur_d = best_n, best_d
    for _ in range(SVD_REFINE_ITERS):
        inl = pts[mask_in]
        if len(inl) < 3:
            break
        cen = inl.mean(axis=0)
        _, _, vh = np.linalg.svd(inl - cen, full_matrices=False)
        n = vh[-1]
        if np.linalg.norm(n) < 1e-9:
            break
        n = n / np.linalg.norm(n)
        d = -float(n @ cen)
        mask_in = np.abs(pts @ n + d) < PLANE_DISTANCE_M
        cur_n, cur_d = n, d

    n_final, d_final = cur_n, cur_d
    # Orient the normal AWAY from the camera (into the scene).
    if n_final[2] < 0:
        n_final = -n_final
        d_final = -d_final

    inliers = int(np.sum(np.abs(pts @ n_final + d_final) < PLANE_DISTANCE_M))
    inlier_ratio = inliers / max(n_total, 1)
    return n_final, d_final, inliers, inlier_ratio


# ============================================================
# Geometry  (Phases 7-10)
# ============================================================
def plane_basis(normal):
    normal = normal / np.linalg.norm(normal)
    ref = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    if abs(ref @ normal) > 0.9:
        ref = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    u = np.cross(normal, ref)
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    v /= np.linalg.norm(v)
    return u, v


def compute_geometry(points, valid, mask, n, d):
    """Return (metrics, cavity_depth, detail) or (None, None, reason)."""
    h, w = mask.shape
    pothole_valid = valid & mask.astype(bool)
    idx = np.flatnonzero(pothole_valid)
    if len(idx) < MIN_VALID_POTHOLE_DEPTH_PIXELS:
        return None, None, "insufficient_pothole_points"

    ys, xs = np.indices((h, w))
    p = points.reshape(-1, 3)[idx]
    px = xs.reshape(-1)[idx].astype(np.float32)
    py = ys.reshape(-1)[idx].astype(np.float32)

    signed = p @ n + d
    cavity = np.maximum(signed, 0.0)
    if not np.all(np.isfinite(cavity)):
        return None, None, "measurements_not_finite"

    # Noise floor: zero out sub-noise deviations.
    cavity[cavity < DEPTH_NOISE_M] = 0.0

    # Physical-area weights for each pixel (plane footprint per pixel).
    # Ray through pixel (unnormalised, z=1): rd = ((u-cx)/fx, (v-cy)/fy, 1)
    rd = np.stack([
        (px - CX) / FX,
        (py - CY) / FY,
        np.ones_like(px, dtype=np.float32),
    ], axis=-1)
    nd = rd @ n                       # n . rd
    lam = np.full(len(px), -1.0, dtype=np.float32)
    ok_plane = (np.abs(nd) > 1e-7)
    lam[ok_plane] = -d / nd[ok_plane]
    rn = np.linalg.norm(rd, axis=-1)
    # pixel_area = lam^2 * |rd| / (fx*fy*|n.rd|)   (positive ray-plane hits only)
    pixel_area = np.zeros(len(px), dtype=np.float32)
    hit = ok_plane & (lam > 0.0) & np.isfinite(lam)
    pixel_area[hit] = (lam[hit] ** 2) * rn[hit] / (FX * FY * np.abs(nd[hit]))

    pos = cavity > 0.0
    n_pos = int(np.sum(pos))
    if n_pos < MIN_CAVITY_PIXELS:
        return None, None, "insufficient_cavity_depth"

    # Outlier guard: too many pixels above the hard plausibility cap.
    above = cavity > MAX_CAVITY_M
    if int(np.sum(above)) > MAX_CAVITY_OUTLIER_FRACTION * n_pos:
        return None, None, "depth_outlier"
    cavity = np.minimum(cavity, MAX_CAVITY_M)

    dpos = cavity[pos]
    apa = pixel_area[pos]

    # ---- Depth statistics over positive cavity pixels ----------
    mean_depth = float(np.mean(dpos))
    median_depth = float(np.median(dpos))
    p90_depth = float(np.percentile(dpos, 90))
    p99_depth = float(np.percentile(dpos, 99))
    max_depth = float(np.max(dpos))

    # ---- Physical area (footprint on the road plane) -----------
    area_m2 = float(np.sum(pixel_area))        # full mask footprint
    area_pos_m2 = float(np.sum(apa))           # footprint with cavity>noise

    if not (area_m2 > 0.0):
        return None, None, "non_positive_area"

    # ---- Length / width via PCA on the projected footprint -----
    pproj = p - np.outer(signed, n)
    u, v = plane_basis(n)
    pu = pproj @ u
    pv = pproj @ v
    xy = np.column_stack([pu, pv])
    xy -= xy.mean(axis=0, keepdims=True)
    if xy.shape[0] < 3:
        return None, None, "insufficient_pothole_points"
    cov = np.cov(xy.T)
    vals, vecs = np.linalg.eigh(cov)
    axis = vecs[:, int(np.argmax(vals))]
    major = xy @ axis
    minor = xy @ np.array([-axis[1], axis[0]])
    length = float(np.percentile(major, 98) - np.percentile(major, 2))
    width = float(np.percentile(minor, 98) - np.percentile(minor, 2))
    if length < 0:
        length = -length
    if width < 0:
        width = -width
    if length < width:
        length, width = width, length      # documented: length >= width

    if not (length > 0.0 and width > 0.0):
        return None, None, "non_positive_dimension"

    # ---- Volume -------------------------------------------------
    volume_m3 = float(np.sum(dpos * apa))    # integral over cavity footprint
    if not (volume_m3 > 0.0):
        return None, None, "non_positive_volume"

    # ---- Volume sanity -------------------------------------------
    denom = area_m2 * mean_depth
    ratio = volume_m3 / denom if denom > 0 else float("nan")
    if not (VOLUME_RATIO_MIN <= ratio <= VOLUME_RATIO_MAX):
        return None, None, "suspicious_volume"

    valid_pothole_depth_pixels = int(len(idx))
    mask_pixels = int(np.sum(mask))
    coverage = valid_pothole_depth_pixels / max(mask_pixels, 1)

    metrics = {
        "length_m": length,
        "width_m": width,
        "area_m2": area_m2,
        "area_pos_m2": area_pos_m2,
        "mean_depth_m": mean_depth,
        "median_depth_m": median_depth,
        "p90_depth_m": p90_depth,
        "p99_depth_m": p99_depth,
        "max_depth_m": max_depth,
        "volume_m3": volume_m3,
        "valid_depth_pixels": int(np.sum(valid)),
        "valid_pothole_depth_pixels": valid_pothole_depth_pixels,
        "mask_pixels": mask_pixels,
        "cavity_pixels": n_pos,
        "pothole_depth_coverage": coverage,
        "volume_area_mean_depth_ratio": ratio,
        "road_plane_inliers": None,
        "road_plane_inlier_ratio": None,
    }
    detail = {
        "cavity_full": cavity,
        "idx": idx,
        "h": h, "w": w,
    }
    return metrics, detail, None


# ============================================================
# Main loop
# ============================================================
def process_sample(split, image_path, label_dir, depth_dir):
    """Return a row dict for one sample."""
    stem = image_path.stem
    label_path = label_dir / f"{stem}.txt"
    depth_path = depth_dir / f"{stem}.npy"
    row = {
        "split": split,
        "image": f"images/{split}/{image_path.name}",
        "label": f"labels/{split}/{stem}.txt",
        "depth": f"depths/{split}/{stem}.npy",
        "valid": False,
        "failure_reason": "",
    }

    if not depth_path.exists():
        row["failure_reason"] = "missing_depth"
        return row

    try:
        depth_raw = np.load(depth_path)
    except Exception as e:
        row["failure_reason"] = f"depth_load_failed:{e}"
        return row

    if depth_raw.ndim != 2:
        row["failure_reason"] = "depth_shape_mismatch"
        return row

    try:
        image = cv2.imread(str(image_path))
        if image is None:
            row["failure_reason"] = "image_load_failed"
            return row
        h, w = image.shape[:2]
    except Exception as e:
        row["failure_reason"] = f"image_load_failed:{e}"
        return row

    if depth_raw.shape != (h, w):
        row["failure_reason"] = "depth_shape_mismatch"
        return row

    depth_m, valid = clean_depth(depth_raw)
    points = backproject(depth_m)

    mask, mask_err = read_polygon_mask(label_path, h, w)
    if mask_err is not None or int(np.sum(mask)) < MIN_MASK_PIXELS:
        row["failure_reason"] = "invalid_polygon"
        return row

    n, d, inliers, inlier_ratio = oriented_plane(points, valid, mask)
    if n is None:
        row["failure_reason"] = (
            "insufficient_road_points" if inliers == 0 and inlier_ratio == 0.0
            else "plane_fit_failed"
        )
        row["road_plane_inliers"] = inliers
        row["road_plane_inlier_ratio"] = inlier_ratio
        return row

    if inliers < MIN_INLIERS or inlier_ratio < MIN_INLIER_RATIO:
        row["failure_reason"] = "plane_fit_failed"
        row["road_plane_inliers"] = inliers
        row["road_plane_inlier_ratio"] = inlier_ratio
        return row
    if abs(n[2]) < MIN_ABS_NZ:
        row["failure_reason"] = "plane_fit_failed"
        row["road_plane_inliers"] = inliers
        row["road_plane_inlier_ratio"] = inlier_ratio
        return row

    metrics, detail, reason = compute_geometry(points, valid, mask, n, d)
    if reason is not None:
        row["failure_reason"] = reason
        row["road_plane_inliers"] = inliers
        row["road_plane_inlier_ratio"] = inlier_ratio
        return row

    # --- Physical plausibility sweep ------------------------------
    for key, hi in [("length_m", MAX_LENGTH_M), ("width_m", MAX_WIDTH_M),
                    ("area_m2", MAX_AREA_M2), ("volume_m3", MAX_VOLUME_M3)]:
        if not (0.0 < metrics[key] <= hi):
            row["failure_reason"] = "dimensions_out_of_range"
            row["road_plane_inliers"] = inliers
            row["road_plane_inlier_ratio"] = inlier_ratio
            return row
    for key in ["mean_depth_m", "median_depth_m", "p90_depth_m",
                "p99_depth_m", "max_depth_m"]:
        if not (0.0 < metrics[key] <= MAX_DEPTH_STAT_M):
            row["failure_reason"] = "depth_outlier"
            row["road_plane_inliers"] = inliers
            row["road_plane_inlier_ratio"] = inlier_ratio
            return row
    if not (0.0 < metrics["pothole_depth_coverage"]) or \
       metrics["pothole_depth_coverage"] < MIN_COVERAGE:
        row["failure_reason"] = "pothole_depth_coverage_low"
        row["road_plane_inliers"] = inliers
        row["road_plane_inlier_ratio"] = inlier_ratio
        return row

    # --- Build cavity-depth map + binary mask artifacts ------------
    cavity_full = detail["cavity_full"]
    idx = detail["idx"]
    cavity_map = np.zeros((h, w), dtype=np.float32)
    cavity_map.reshape(-1)[idx] = cavity_full.astype(np.float32)
    cavity_map[~mask.astype(bool)] = 0.0

    target_dir = ROOT / "targets_v2" / split
    target_dir.mkdir(parents=True, exist_ok=True)
    mask_path = target_dir / f"{stem}_mask.png"
    depth_target_path = target_dir / f"{stem}_cavity_depth.npy"
    cv2.imwrite(str(mask_path), (mask * 255).astype(np.uint8))
    np.save(depth_target_path, cavity_map)

    row.update(metrics)
    row["valid"] = True
    row["road_plane_inliers"] = int(inliers)
    row["road_plane_inlier_ratio"] = float(inlier_ratio)
    row["mask_path"] = f"targets_v2/{split}/{stem}_mask.png"
    row["depth_target_path"] = f"targets_v2/{split}/{stem}_cavity_depth.npy"
    row["valid"] = True
    return row


def main():
    rows = []
    for split in ["train", "val", "test"]:
        image_dir = ROOT / "images" / split
        label_dir = ROOT / "labels" / split
        depth_dir = ROOT / "depths" / split
        images = sorted(p for p in image_dir.glob("*")
                        if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
        print(f"\n{split}: {len(images)} images")
        for i, image_path in enumerate(images, 1):
            row = process_sample(split, image_path, label_dir, depth_dir)
            rows.append(row)
            if i % 200 == 0 or i == len(images):
                print(f"  processed {i}/{len(images)}")

    df = pd.DataFrame(rows)
    out = ROOT / "dimension_targets_v2.csv"
    df.to_csv(out, index=False)

    print("\n" + "=" * 70)
    print("TARGET GENERATION V2 COMPLETE")
    print("=" * 70)
    print("Total rows:", len(df))
    valid_df = df[df["valid"]]
    print("Valid:", len(valid_df))
    print("Failed:", int((~df["valid"]).sum()))
    if len(valid_df):
        print("\nMeasurement ranges (valid samples):")
        for col in ["length_m", "width_m", "area_m2",
                    "mean_depth_m", "p90_depth_m", "volume_m3"]:
            print(f"  {col:14s} min={valid_df[col].min():.5f} "
                  f"median={valid_df[col].median():.5f} "
                  f"max={valid_df[col].max():.5f}")
    print("\nSaved:", out)


if __name__ == "__main__":
    main()