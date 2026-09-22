from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import cv2

# ============================================================
# Generate physical supervision from PothRGBD
#
# Input:
#   images/{train,val,test}/*.jpg
#   labels/{train,val,test}/*.txt   (YOLO polygon labels)
#   depths/{train,val,test}/*.npy    (uint16 depth)
#
# Output:
#   dimension_targets.csv
#   targets/{split}/{image_stem}_mask.png
#   targets/{split}/{image_stem}_cavity_depth.npy
#
# IMPORTANT:
# - Depth is treated as millimeters.
# - 0 and 65535 are invalid.
# - Depth > 3000 mm is ignored for geometry, following the
#   conservative working range used for this dataset.
# - Camera intrinsics below are provisional D415 values.
#   Replace them with exact dataset calibration if available.
# - This creates DERIVED physical targets, not manually measured
#   ground truth.
# ============================================================

ROOT = Path(r"D:\drone\POTHOLE_TRAINING_DATASET")

FX = 597.5
FY = 597.5
CX = 319.5
CY = 239.5
MAX_DEPTH_MM = 3000.0
MIN_DEPTH_MM = 50.0

# Plane fitting settings
RANSAC_ITERS = 300
PLANE_DISTANCE_M = 0.025
RANDOM_SEED = 42

rng = np.random.default_rng(RANDOM_SEED)


def read_polygon_mask(label_path, h, w):
    mask = np.zeros((h, w), dtype=np.uint8)
    if not label_path.exists():
        return mask

    lines = label_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 7:
            continue

        # YOLO segmentation: class x1 y1 x2 y2 ...
        coords = np.asarray([float(x) for x in parts[1:]], dtype=np.float32)
        if len(coords) < 6 or len(coords) % 2 != 0:
            continue

        pts = coords.reshape(-1, 2)
        pts[:, 0] = np.clip(pts[:, 0] * w, 0, w - 1)
        pts[:, 1] = np.clip(pts[:, 1] * h, 0, h - 1)
        pts = np.round(pts).astype(np.int32)

        cv2.fillPoly(mask, [pts], 1)

    return mask


def depth_to_points(depth_mm):
    h, w = depth_mm.shape
    ys, xs = np.indices((h, w))

    valid = (
        np.isfinite(depth_mm)
        & (depth_mm >= MIN_DEPTH_MM)
        & (depth_mm <= MAX_DEPTH_MM)
    )

    z = depth_mm.astype(np.float32) / 1000.0
    x = (xs.astype(np.float32) - CX) * z / FX
    y = (ys.astype(np.float32) - CY) * z / FY

    return np.stack([x, y, z], axis=-1), valid


def fit_plane(points, valid, exclude_mask):
    candidate = valid & (~exclude_mask)

    # Erode/dilate exclusion so pothole boundary doesn't contaminate road plane.
    kernel = np.ones((21, 21), np.uint8)
    dilated = cv2.dilate(exclude_mask.astype(np.uint8), kernel, iterations=1)
    candidate = valid & (~dilated.astype(bool))

    idx = np.flatnonzero(candidate)
    if len(idx) < 100:
        return None, 0

    # Limit samples for speed.
    if len(idx) > 12000:
        idx = rng.choice(idx, 12000, replace=False)

    pts = points.reshape(-1, 3)[idx]

    best_plane = None
    best_count = 0

    for _ in range(RANSAC_ITERS):
        sample = pts[rng.choice(len(pts), 3, replace=False)]
        a, b, c = sample
        n = np.cross(b - a, c - a)
        norm = np.linalg.norm(n)
        if norm < 1e-8:
            continue
        n = n / norm
        d = -np.dot(n, a)

        dist = np.abs(pts @ n + d)
        count = int(np.sum(dist < PLANE_DISTANCE_M))

        if count > best_count:
            best_count = count
            best_plane = np.array([n[0], n[1], n[2], d], dtype=np.float32)

    return best_plane, best_count


def orient_plane_toward_camera(plane):
    # We only need consistent sign for cavity depth.
    # Make the plane normal have positive Z.
    if plane is not None and plane[2] < 0:
        plane = -plane
    return plane


def plane_basis(normal):
    normal = normal / np.linalg.norm(normal)

    ref = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    if abs(np.dot(ref, normal)) > 0.9:
        ref = np.array([1.0, 0.0, 0.0], dtype=np.float32)

    u = np.cross(normal, ref)
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    v /= np.linalg.norm(v)
    return u, v


def compute_geometry(points, valid, mask, plane):
    if plane is None:
        return None

    pothole_valid = valid & mask.astype(bool)
    idx = np.flatnonzero(pothole_valid)

    if len(idx) < 30:
        return None

    p = points.reshape(-1, 3)[idx]

    n = plane[:3]
    d = plane[3]

    # Signed distance to road plane.
    signed = p @ n + d

    # Pothole cavity is on the road-interior side.
    # Since normal has +Z, lower-than-road points have negative distance.
    cavity_depth = np.maximum(-signed, 0.0)

    # Robustly ignore tiny negative/positive noise.
    cavity_depth[cavity_depth < 0.003] = 0.0

    # Keep robust percentiles for dimensions.
    positive = cavity_depth[cavity_depth > 0]

    if len(positive) < 10:
        return None

    u, v = plane_basis(n)

    # Project points onto road plane for footprint dimensions.
    projected = p - np.outer(signed, n)
    pu = projected @ u
    pv = projected @ v

    # PCA on projected footprint.
    xy = np.column_stack([pu, pv])
    xy -= xy.mean(axis=0, keepdims=True)

    cov = np.cov(xy.T)
    vals, vecs = np.linalg.eigh(cov)
    axis = vecs[:, np.argmax(vals)]

    major = xy @ axis
    minor = xy @ np.array([-axis[1], axis[0]])

    # Robust extent: 2nd to 98th percentile reduces outlier sensitivity.
    length = np.percentile(major, 98) - np.percentile(major, 2)
    width = np.percentile(minor, 98) - np.percentile(minor, 2)

    # Approximate local physical pixel area from camera geometry.
    z = p[:, 2]
    pixel_area = (z * z) / (FX * FY)

    area = float(np.sum(pixel_area))

    # Volume from cavity depth integrated over physical footprint.
    volume = float(np.sum(cavity_depth * pixel_area))

    return {
        "valid_pothole_pixels": int(len(p)),
        "length_m": float(abs(length)),
        "width_m": float(abs(width)),
        "area_m2": area,
        "mean_depth_m": float(np.mean(positive)),
        "median_depth_m": float(np.median(positive)),
        "p90_depth_m": float(np.percentile(positive, 90)),
        "p99_depth_m": float(np.percentile(positive, 99)),
        "max_depth_m": float(np.max(positive)),
        "volume_m3": volume,
    }, cavity_depth, idx


rows = []

for split in ["train", "val", "test"]:
    image_dir = ROOT / "images" / split
    label_dir = ROOT / "labels" / split
    depth_dir = ROOT / "depths" / split
    target_dir = ROOT / "targets" / split
    target_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(image_dir.glob("*"))
    images = [p for p in images if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]

    print(f"\n{split}: {len(images)} images")

    for i, image_path in enumerate(images, 1):
        stem = image_path.stem
        label_path = label_dir / f"{stem}.txt"
        depth_path = depth_dir / f"{stem}.npy"

        # Handle datasets where depth filenames have a modality suffix.
        if not depth_path.exists():
            candidates = list(depth_dir.glob(f"{stem}*.npy"))
            if candidates:
                depth_path = candidates[0]

        try:
            image = np.asarray(Image.open(image_path).convert("RGB"))
            h, w = image.shape[:2]

            depth = np.load(depth_path)

            if depth.shape != (h, w):
                raise ValueError(f"depth shape {depth.shape} != image {(h,w)}")

            mask = read_polygon_mask(label_path, h, w)

            points, valid = depth_to_points(depth)

            plane, plane_inliers = fit_plane(points, valid, mask)
            plane = orient_plane_toward_camera(plane)

            geometry = compute_geometry(points, valid, mask, plane)

            if geometry is None:
                rows.append({
                    "split": split,
                    "image": image_path.name,
                    "status": "FAILED_GEOMETRY",
                    "plane_inliers": plane_inliers,
                })
                continue

            metrics, cavity_depth, idx = geometry

            # Full-size cavity depth target, meters, zero outside valid pothole.
            target_depth = np.zeros((h, w), dtype=np.float32)
            flat = target_depth.reshape(-1)
            flat[idx] = cavity_depth.astype(np.float32)

            mask_path = target_dir / f"{stem}_mask.png"
            depth_target_path = target_dir / f"{stem}_cavity_depth.npy"

            Image.fromarray((mask * 255).astype(np.uint8)).save(mask_path)
            np.save(depth_target_path, target_depth)

            rows.append({
                "split": split,
                "image": image_path.name,
                "status": "OK",
                "plane_inliers": plane_inliers,
                "valid_pothole_pixels": metrics["valid_pothole_pixels"],
                "length_m": metrics["length_m"],
                "width_m": metrics["width_m"],
                "area_m2": metrics["area_m2"],
                "mean_depth_m": metrics["mean_depth_m"],
                "median_depth_m": metrics["median_depth_m"],
                "p90_depth_m": metrics["p90_depth_m"],
                "p99_depth_m": metrics["p99_depth_m"],
                "max_depth_m": metrics["max_depth_m"],
                "volume_m3": metrics["volume_m3"],
                "mask_path": str(mask_path.relative_to(ROOT)),
                "depth_target_path": str(depth_target_path.relative_to(ROOT)),
            })

        except Exception as e:
            rows.append({
                "split": split,
                "image": image_path.name,
                "status": "ERROR",
                "error": str(e),
            })

        if i % 100 == 0 or i == len(images):
            print(f"  processed {i}/{len(images)}")

df = pd.DataFrame(rows)
out = ROOT / "dimension_targets.csv"
df.to_csv(out, index=False)

print("\n" + "=" * 70)
print("PHYSICAL TARGET GENERATION COMPLETE")
print("=" * 70)
print("Total rows:", len(df))
print("OK:", int((df["status"] == "OK").sum()))
print("Failed geometry:", int((df["status"] == "FAILED_GEOMETRY").sum()))
print("Errors:", int((df["status"] == "ERROR").sum()))

ok = df[df["status"] == "OK"]
if len(ok):
    print("\nDerived target ranges:")
    for col in [
        "length_m", "width_m", "area_m2",
        "mean_depth_m", "max_depth_m", "volume_m3"
    ]:
        print(
            f"{col:18s}: "
            f"min={ok[col].min():.5f}, "
            f"median={ok[col].median():.5f}, "
            f"max={ok[col].max():.5f}"
        )

print("\nSaved:")
print(out)
print("\nNOTE: These are geometry-derived supervision targets.")
print("They must be sanity-checked before model training.")
