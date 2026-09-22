"""Geometry module: converts PREDICTED mask + PREDICTED cavity depth + a
PREDICTED road-plane distance into physical length / width / area / depth /
volume.

Important scientific context:
  - These are "geometry-derived" quantities from a monocular model.
  - They are "calibration-dependent metric estimates", NOT survey-grade.
  - The camera is assumed roughly fronto-parallel to the road (no fitted plane
    at inference).  A pixel's road-plane footprint is
        dA = z_plane^2 * |rd| / (fx * fy)
    where rd is the unnormalised ray direction and z_plane is the predicted
    camera-to-road distance (~metres).  This is the Stage-1 formula evaluated
    with the road normal fixed to (0, 0, 1) and the per-pixel plane depth
    approximated by the predicted scalar plane distance.
  - The cavity depth (~cm) is the measured quantity; the plane distance
    (~m) supplies the metric scene scale.  Area therefore must use z_plane,
    NOT the cavity depth.
  - Length/width come from PCA on the predicted footprint points expressed in
    metric road-plane coordinates (X = du * z_plane, Y = dv * z_plane) with
    robust 2-98 percentile extents.
  - Volume = sum(cavity_depth_i * dA_i) over pothole pixels above the noise
    floor.
"""
from __future__ import annotations

import cv2
import numpy as np


def effective_intrinsics(cfg, W, H):
    """Scale the 640x480 intrinsics to the actual input resolution."""
    I = cfg["intrinsics"]
    sw = W / float(I["orig_w"])
    return {
        "fx": float(I["fx"]) * sw,
        "fy": float(I["fy"]) * sw,
        "cx": float(I["cx"]) * sw,
        "cy": float(I["cy"]) * sw,
    }


_EMPTY = {"length_m": np.nan, "width_m": np.nan, "area_m2": np.nan,
          "mean_depth_m": np.nan, "p90_depth_m": np.nan, "volume_m3": np.nan,
          "n_pixels": 0, "plane_dist_m": np.nan}


def predict_geometry(mask_probs, depth, plane_dist, cfg, W, H,
                     mask_threshold=0.5, noise_floor=0.003):
    """Compute physical metrics per sample.

    mask_probs:  (H, W) float in [0,1]
    depth:       (H, W) cavity depth in metres
    plane_dist:  scalar camera-to-road-plane distance in metres (predicted)
    Returns dict with length_m, width_m, area_m2, mean_depth_m,
    p90_depth_m, volume_m3, n_pixels.
    """
    if plane_dist is None or not np.isfinite(plane_dist) or plane_dist <= 0:
        out = dict(_EMPTY)
        out["success"] = False
        return out

    intri = effective_intrinsics(cfg, W, H)
    fx, fy = intri["fx"], intri["fy"]
    cx, cy = intri["cx"], intri["cy"]

    mask = (mask_probs > mask_threshold)
    n_px = int(mask.sum())
    if n_px < 10:
        out = dict(_EMPTY)
        out["n_pixels"] = n_px
        out["success"] = False
        return out

    ys, xs = np.indices((H, W))
    du = (xs.ravel().astype(np.float64) - cx) / fx
    dv = (ys.ravel().astype(np.float64) - cy) / fy
    z = depth.ravel().astype(np.float64)
    rn = np.sqrt(du ** 2 + dv ** 2 + 1.0)

    z_plane = float(plane_dist)
    pa = (z_plane ** 2) * rn / (fx * fy)     # per-pixel road-plane footprint

    m = mask.ravel()
    area = float(pa[m].sum())

    pos = m & (z > noise_floor)
    n_pos = int(pos.sum())
    if n_pos > 0:
        cav = z[pos]
        mean_depth = float(cav.mean())
        p90_depth = float(np.percentile(cav, 90))
        volume = float((cav * pa[pos]).sum())
    else:
        mean_depth = np.nan
        p90_depth = np.nan
        volume = 0.0

    # physical footprint point cloud in metric road-plane coordinates
    X = du[m] * z_plane
    Y = dv[m] * z_plane
    if X.size < 3:
        return {"length_m": np.nan, "width_m": np.nan, "area_m2": area,
                "mean_depth_m": mean_depth, "p90_depth_m": p90_depth,
                "volume_m3": volume, "n_pixels": n_px, "plane_dist_m": z_plane,
                "success": False}
    pts = np.column_stack([X, Y])
    pts -= pts.mean(axis=0)
    cov = np.cov(pts.T)
    vals, vecs = np.linalg.eigh(cov)
    axis = vecs[:, int(np.argmax(vals))]
    major = pts @ axis
    minor = pts @ np.array([-axis[1], axis[0]])
    length = float(np.percentile(major, 98) - np.percentile(major, 2))
    width = float(np.percentile(minor, 98) - np.percentile(minor, 2))
    if length < width:
        length, width = width, length

    return {
        "length_m": length,
        "width_m": width,
        "area_m2": area,
        "mean_depth_m": mean_depth,
        "p90_depth_m": p90_depth,
        "volume_m3": volume,
        "n_pixels": n_px,
        "plane_dist_m": z_plane,
        "success": bool(np.isfinite(length) and np.isfinite(width)
                        and np.isfinite(area) and np.isfinite(mean_depth)
                        and np.isfinite(volume)),
    }


def geometry_from_pred_batch(masks, depths, plane_dists, cfg, W, H,
                             mask_threshold=0.5, noise_floor=0.003):
    """Batch wrapper returning lists of per-sample metric dicts."""
    out = []
    masks = np.asarray(masks)
    depths = np.asarray(depths)
    plane_dists = np.asarray(plane_dists).reshape(-1)
    for i in range(masks.shape[0]):
        pd = float(plane_dists[i]) if i < len(plane_dists) else np.nan
        out.append(predict_geometry(masks[i], depths[i], pd, cfg, W, H,
                                    mask_threshold, noise_floor))
    return out


# ---------------------------------------------------------------------------
# Stage 2.1: road-plane geometry from PREDICTED absolute metric depth.
# ---------------------------------------------------------------------------

def _unproject(du, dv, z):
    """du, dv, z: flat (N,) arrays. Returns (N,3) camera-frame points."""
    X = du * z
    Y = dv * z
    return np.column_stack([X, Y, z])


def fit_road_plane(abs_depth, mask_out, cfg, W, H):
    """Robustly fit the dominant road plane from predicted absolute depth.

    abs_depth: (H, W) metres. mask_out: boolean pothole mask.
    Returns (n, d, succeeded) with the plane n.p + d = 0 oriented so the
    pothole side (farther from camera, larger Z) is POSITIVE.

    Excludes the dilated pothole region, an edge border ring, and out-of-range
    depth so boundary pixels / far sky cannot skew the plane.
    """
    g = cfg["geometry"]
    intri = effective_intrinsics(cfg, W, H)
    fx, fy = intri["fx"], intri["fy"]
    cx, cy = intri["cx"], intri["cy"]
    crop = int(g["edge_crop"])

    ys, xs = np.indices((H, W))
    du = ((xs.astype(np.float64) - cx) / fx).ravel()
    dv = ((ys.astype(np.float64) - cy) / fy).ravel()
    z = abs_depth.ravel().astype(np.float64)

    if mask_out.ndim == 3 and mask_out.shape[0] == 1:
        mask_out = mask_out[0]
    mask = np.asarray(mask_out).ravel()

    block = np.ones((g["dilate_ks"], g["dilate_ks"]), np.uint8)
    mask_dil = cv2.dilate(mask.reshape(H, W).astype(np.uint8),
                          block, iterations=1).astype(bool).ravel()

    inner = np.zeros(H * W, bool)
    inner.reshape(H, W)[crop:H - crop, crop:W - crop] = True
    valid = (z >= 0.05) & (z <= float(cfg["data"]["abs_depth_max_m"])) & inner
    cand = valid & ~mask_dil

    if cand.sum() < int(g["min_road_candidates"]):
        return None, None, False

    pts = _unproject(du[cand], dv[cand], z[cand])
    sub = pts if len(pts) <= 30000 else pts[np.random.RandomState(0).choice(
        len(pts), 30000, replace=False)]

    tol = float(g["ransac_tol_m"])
    best_n, best_d, best_in = None, None, 0
    rng = np.random.RandomState(42)
    for _ in range(int(g["ransac_iter"])):
        id3 = rng.choice(len(sub), 3, replace=False)
        a, b, c = sub[id3]
        n = np.cross(b - a, c - a)
        nn = np.linalg.norm(n)
        if nn < 1e-9:
            continue
        n = n / nn
        d = -float(n @ a)
        n_in = int((np.abs(sub @ n + d) < tol).sum())
        if n_in > best_in:
            best_in = n_in
            best_n, best_d = n, d
    if best_n is None or best_in < int(g["min_inliers"]):
        return None, None, False

    # Total-least-squares refine on all inliers
    inl = pts[np.abs(pts @ best_n + best_d) < tol]
    if len(inl) < int(g["min_inliers"]):
        return None, None, False
    mu = inl.mean(axis=0)
    cov = np.cov((inl - mu).T)
    vals, vecs = np.linalg.eigh(cov)
    n = vecs[:, int(np.argmin(vals))]
    d = -float(n @ mu)
    if abs(n[2]) < float(g["min_abs_nz"]):
        return None, None, False

    # Orient so the pothole side (larger camera-Z) is positive
    pmask = valid & mask
    if pmask.sum() > 0:
        signed = _unproject(du[pmask], dv[pmask], z[pmask]) @ n + d
        if float(np.mean(signed)) < 0:
            n = -n
            d = -d
    return n, d, True


def geometry_from_abs_depth(mask_probs, abs_depth, cfg, W, H,
                            mask_threshold=0.5, noise_floor=0.003):
    """Geometry + cavity depth from predicted absolute depth and mask.

    Fits the road plane (fit_road_plane), then:
      cavity     = signed distance of the pothole points from the plane
      area       = sum of plane footprints over valid pothole pixels
      len/width  = PCA extents of pothole points projected onto the plane
      volume     = sum(cavity * footprint)
    Returns metric dict + predicted cavity map + plane info + success flag.
    """
    empty = dict(_EMPTY)
    empty["success"] = False
    empty["cavity_map"] = None
    empty["plane_n"] = None
    empty["plane_d"] = None

    mask = np.asarray(mask_probs) > mask_threshold
    z = np.asarray(abs_depth, dtype=np.float64)
    if mask.ndim == 3 and mask.shape[0] == 1:
        mask = mask[0]

    n, d, ok = fit_road_plane(np.nan_to_num(z), mask, cfg, W, H)
    if not ok or n is None:
        return empty

    intri = effective_intrinsics(cfg, W, H)
    fx, fy = intri["fx"], intri["fy"]
    cx, cy = intri["cx"], intri["cy"]
    H0, W0 = mask.shape
    ys, xs = np.indices((H0, W0))
    du = ((xs.astype(np.float64) - cx) / fx).ravel()
    dv = ((ys.astype(np.float64) - cy) / fy).ravel()
    zf = z.ravel()
    rn = np.sqrt(du ** 2 + dv ** 2 + 1.0)

    valid = (zf >= 0.05) & (zf <= float(cfg["data"]["abs_depth_max_m"]))
    pmask = valid & mask.ravel()
    n_px = int(pmask.sum())
    if n_px < 5:
        empty["n_pixels"] = n_px
        empty["success"] = True
        return empty

    # signed cavity distance (positive = far side of the road plane)
    signed = _unproject(du[pmask], dv[pmask], zf[pmask]) @ n + d
    cavity = np.maximum(signed, 0.0)
    cavity_map = np.zeros(H0 * W0, dtype=np.float32)
    cavity_map[pmask] = cavity

    # ray-plane intersection distance (lam nrd) -> per-pixel footprint.
    # dA = lam^2 * |rd| / (fx * fy * |n.rd|)  (Stage-1 formula, per-pixel plane)
    nrd = n[0] * du[pmask] + n[1] * dv[pmask] + n[2]
    lam = np.where(np.abs(nrd) < 1e-6, np.nan, -d / nrd)

    # sanity guard: the road plane must be a plausible camera-to-road distance
    good = np.isfinite(lam) & (np.abs(lam) <= 10.0) & (np.abs(nrd) >= 0.05)
    plane_dist = float(np.median(lam[good])) if bool(good.any()) else float("nan")
    if not np.isfinite(plane_dist) or plane_dist < 0.05 or plane_dist > 10.0:
        empty["n_pixels"] = n_px
        return empty

    pa = np.where(good, lam ** 2 * rn[pmask] / (fx * fy * np.abs(nrd)), 0.0)
    valid_l = good
    area = float(pa[valid_l].sum())

    pos = (cavity > noise_floor) & valid_l
    n_pos = int(pos.sum())
    if n_pos > 0:
        cav = cavity[pos]
        mean_depth = float(cav.mean())
        p90_depth = float(np.percentile(cav, 90))
        volume = float((cav * pa[pos]).sum())
    else:
        mean_depth = np.nan
        p90_depth = np.nan
        volume = 0.0

    # length / width from the footprint projected onto the fitted plane
    pts_all = _unproject(du[pmask], dv[pmask], zf[pmask])
    pts = pts_all[valid_l]
    proj = pts - (pts @ n + d)[:, None] * n
    b1 = np.array([-n[1], n[0], 0.0]) if abs(n[2]) < 0.99 \
        else np.array([0.0, 1.0, 0.0])
    b1 = b1 / (np.linalg.norm(b1) + 1e-12)
    b2 = np.cross(n, b1)
    c1 = proj @ b1
    c2 = proj @ b2
    length = float(np.percentile(c1, 98) - np.percentile(c1, 2))
    width = float(np.percentile(c2, 98) - np.percentile(c2, 2))
    if not np.isfinite(length) or not np.isfinite(width):
        length = width = np.nan
    if length is not None and width is not None and np.isfinite(length) \
            and np.isfinite(width) and length < width:
        length, width = width, length

    return {
        "length_m": length, "width_m": width, "area_m2": area,
        "mean_depth_m": mean_depth, "p90_depth_m": p90_depth,
        "volume_m3": volume, "n_pixels": n_px, "plane_dist_m": plane_dist,
        "success": True, "cavity_map": cavity_map.reshape(H0, W0),
        "plane_n": n, "plane_d": d,
    }


def geometry_from_abs_depth_batch(mask_probs, abs_depths, cfg, W, H,
                                  mask_threshold=0.5, noise_floor=0.003):
    """Batch wrapper for geometry_from_abs_depth."""
    out = []
    for i in range(len(mask_probs)):
        out.append(geometry_from_abs_depth(mask_probs[i], abs_depths[i], cfg,
                                           W, H, mask_threshold, noise_floor))
    return out