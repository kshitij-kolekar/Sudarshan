"""Validation: segmentation + absolute depth + cavity depth + dimensions +
volume metrics computed on the VALIDATION split.  RGB-only input into the model;
GT is used purely for scoring.

Two geometry paths are supported transparently:
  - MODEL B (Stage 2.1): dense absolute depth head -> road-plane fitted geometry.
  - MODEL A (Stage 2.0): scalar plane-distance head -> z_plane geometry.
The path is chosen from the model's ``abs_enabled`` flag (set False for legacy
checkpoints that predate the absolute-depth head).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

import geometry
import utils as U

sys.path.insert(0, str(Path(__file__).parent))


@torch.no_grad()
def validate(model, loader, cfg, stats, device, limit=None, total=None):
    """Returns a dict of scalar metrics for one pass over the loader."""
    from utils import (seg_metrics, mae, rmse, median_abs_err, mape,
                       unzscore, unzscore1d)

    model.eval()
    model_has_abs = bool(getattr(model, "abs_enabled", True))
    mcfg = cfg["model"]
    required = mcfg["dims"]
    plane_idx = required.index("plane_dist_m")
    abs_split = float(cfg["data"]["abs_depth_split_m"])

    tp = fp = fn = 0
    depth_pred_all, depth_gt_all = [], []
    dims_pred_all, dims_gt_all = [], []
    vol_pred_all, vol_gt_all = [], []
    abs_err = {"road": [], "pothole": [], "near": [], "far": []}
    abs_whole = []
    abs_rel = []
    plane_pred_all, plane_gt_all = [], []

    geo = {"length": [], "width": [], "area": [], "mean_d": [], "p90_d": [],
           "volume": []}
    gt = {"length": [], "width": [], "area": [], "mean_d": [], "p90_d": [],
          "volume": []}
    sanity_ratio = []
    geo_fail = 0

    mask_thr = cfg["inference"]["mask_threshold"]
    noise_floor = cfg["data"]["depth_noise_floor_m"]
    W, H = cfg["data"]["image_size"]

    count = 0
    for i, batch in enumerate(loader):
        img = batch[0].to(device)
        out = model(img)

        seg_prob = torch.sigmoid(out["seg"]).cpu()
        mask_pred = (seg_prob > mask_thr).float()
        t, f, pn = seg_metrics(batch[1].numpy(), mask_pred.numpy())
        tp += t; fp += f; fn += pn

        # ---- cavity depth (over GT-valid pothole pixels) ----
        v = batch[3].numpy() > 0
        dp = out["depth"].cpu().numpy()
        dg = batch[2].numpy()
        depth_pred_all.append(dp[v])
        depth_gt_all.append(dg[v])

        # ---- dims (regression head, original units) ----
        dim_gt_orig = unzscore(batch[4].numpy(), stats["dims"])
        dim_pred_orig = unzscore(out["dims"].cpu().numpy(), stats["dims"])
        dims_pred_all.append(dim_pred_orig)
        dims_gt_all.append(dim_gt_orig)

        vol_gt_orig = unzscore1d(batch[5].numpy(), stats["volume"])
        vol_pred_orig = unzscore1d(out["volume"].cpu().numpy(), stats["volume"])
        vol_pred_all.append(vol_pred_orig)
        vol_gt_all.append(vol_gt_orig)

        gt_mask = batch[1].numpy() > 0.5
        model_has_abs_local = model_has_abs and "abs_depth" in out
        # ---- absolute-depth bands (MODEL B only) ----
        if model_has_abs_local:
            abs_pred_np = out["abs_depth"].cpu().numpy()
            abs_gt_np = batch[6].numpy()
            vabs = batch[7].numpy() > 0
            for b in range(len(vabs)):
                m = vabs[b]
                if not bool(m.any()):
                    continue
                e = np.zeros_like(m, dtype=np.float64)          # cm
                e[m] = np.abs(abs_pred_np[b][m] - abs_gt_np[b][m]) * 100.0
                rel = np.zeros_like(m, dtype=np.float64)        # %
                rel[m] = (np.abs(abs_pred_np[b][m] - abs_gt_np[b][m])
                          / abs_gt_np[b][m] * 100.0)
                abs_whole.extend(e[m].tolist())
                abs_rel.extend(rel[m].tolist())
                abs_err["road"].extend(e[m & ~gt_mask[b]].tolist())
                abs_err["pothole"].extend(e[m & gt_mask[b]].tolist())
                nm = m & (abs_gt_np[b] <= abs_split)
                if bool(nm.any()):
                    abs_err["near"].extend(e[nm].tolist())
                nm = m & (abs_gt_np[b] > abs_split)
                if bool(nm.any()):
                    abs_err["far"].extend(e[nm].tolist())
            batch_geo = geometry.geometry_from_abs_depth_batch(
                mask_pred.numpy(), abs_pred_np, cfg, W, H, mask_thr,
                noise_floor)
            for b in range(len(batch_geo)):
                plane_pred_all.append(batch_geo[b]["plane_dist_m"])
                plane_gt_all.append(dim_gt_orig[b][plane_idx])
        else:
            plane_pred = dim_pred_orig[:, plane_idx]
            batch_geo = geometry.geometry_from_pred_batch(
                mask_pred.numpy(), out["depth"].cpu().numpy(), plane_pred, cfg,
                W, H, mask_thr, noise_floor)
            plane_pred_all.extend(plane_pred.tolist())
            plane_gt_all.extend(dim_gt_orig[:, plane_idx].tolist())

        for j, g in enumerate(batch_geo):
            geo["length"].append(g["length_m"])
            geo["width"].append(g["width_m"])
            geo["area"].append(g["area_m2"])
            geo["mean_d"].append(g["mean_depth_m"])
            geo["p90_d"].append(g["p90_depth_m"])
            geo["volume"].append(g["volume_m3"])
            gt["length"].append(dim_gt_orig[j][0])
            gt["width"].append(dim_gt_orig[j][1])
            gt["area"].append(dim_gt_orig[j][2])
            gt["mean_d"].append(dim_gt_orig[j][3])
            gt["p90_d"].append(dim_gt_orig[j][4])
            gt["volume"].append(vol_gt_orig[j][0])
            if not g.get("success", False):
                geo_fail += 1
            elif np.isfinite(g["volume_m3"]) and g["volume_m3"] > 0 \
                    and np.isfinite(g["area_m2"]) and g["area_m2"] > 0 \
                    and np.isfinite(g["mean_depth_m"]) and g["mean_depth_m"] > 0:
                sanity_ratio.append(g["volume_m3"] /
                                    (g["area_m2"] * g["mean_depth_m"]))

        count += 1
        if total and i + 1 >= total:
            break
        if limit is not None and count >= limit:
            break

    # ---- aggregate metrics ----
    dpr = np.concatenate(depth_pred_all)
    dgt = np.concatenate(depth_gt_all)
    depth_mae_m = mae(dgt, dpr)
    depth_rmse_m = rmse(dgt, dpr)
    depth_med_m = median_abs_err(dgt, dpr)

    dp_dim = np.concatenate(dims_pred_all)
    dg_dim = np.concatenate(dims_gt_all)
    dim_mae = {c: float(np.mean(np.abs(dp_dim[:, k] - dg_dim[:, k])))
               for k, c in enumerate(required)}
    dim_mape = {c: mape(dg_dim[:, k], dp_dim[:, k])
                for k, c in enumerate(required)}

    vp = np.concatenate(vol_pred_all)
    vg = np.concatenate(vol_gt_all)

    def _fin(tag, arr):
        a = np.asarray(arr, dtype=np.float64)
        g = np.asarray(gt[tag], dtype=np.float64)
        v = np.isfinite(a) & np.isfinite(g)
        if not v.any():
            return float("nan")
        return float(np.mean(np.abs(a[v] - g[v])))

    def _fmape(tag, arr):
        a = np.asarray(arr, dtype=np.float64)
        g = np.asarray(gt[tag], dtype=np.float64)
        v = np.isfinite(a) & np.isfinite(g) & (np.abs(g) > 1e-12)
        if not v.any():
            return float("nan")
        return float(np.mean(np.abs((a[v] - g[v]) / g[v]) * 100.0))

    prec, rec = precision_recall(tp, fp, fn)
    res = {
        "seg_iou": iou_score(tp, fp, fn),
        "seg_dice": dice_score(tp, fp, fn),
        "seg_precision": prec,
        "seg_recall": rec,
        "depth_mae_cm": depth_mae_m * 100.0,
        "depth_rmse_cm": depth_rmse_m * 100.0,
        "depth_med_cm": depth_med_m * 100.0,
        "dim_mae_length_m": dim_mae["length_m"],
        "dim_mae_width_m": dim_mae["width_m"],
        "dim_mae_area_m2": dim_mae["area_m2"],
        "dim_mae_mean_depth_cm": dim_mae["mean_depth_m"] * 100.0,
        "dim_mae_p90_depth_cm": dim_mae["p90_depth_m"] * 100.0,
        "dim_mae_plane_dist_m": dim_mae["plane_dist_m"],
        "dim_mape_length": dim_mape["length_m"],
        "dim_mape_width": dim_mape["width_m"],
        "dim_mape_area": dim_mape["area_m2"],
        "dim_mape_plane_dist": dim_mape["plane_dist_m"],
        "vol_reg_mae_L": float(np.mean(np.abs(vp - vg))) * 1000.0 if len(vp) else float("nan"),
        "vol_geo_mae_L": _fin("volume", np.asarray(geo["volume"])) * 1000.0,
        "vol_geo_mape": _fmape("volume", np.asarray(geo["volume"])),
        "geo_mae_length_m": _fin("length", np.asarray(geo["length"])),
        "geo_mae_width_m": _fin("width", np.asarray(geo["width"])),
        "geo_mae_area_m2": _fin("area", np.asarray(geo["area"])),
        "geo_mae_mean_depth_cm": _fin("mean_d", np.asarray(geo["mean_d"])) * 100.0,
        "geo_mae_p90_depth_cm": _fin("p90_d", np.asarray(geo["p90_d"])) * 100.0,
        "geo_failure_count": geo_fail,
        "vol_sanity_ratio_mean": float(np.mean(sanity_ratio)) if sanity_ratio else float("nan"),
        "vol_sanity_ratio_median": float(np.median(sanity_ratio)) if sanity_ratio else float("nan"),
    }

    if model_has_abs:
        pp = np.asarray(plane_pred_all, dtype=np.float64)
        pg = np.asarray(plane_gt_all, dtype=np.float64)
        mz = np.isfinite(pp) & np.isfinite(pg)
        res["plane_dist_mae_m"] = float(
            np.mean(np.abs(pp[mz] - pg[mz]))) if mz.any() else float("nan")
        res["plane_dist_mape"] = float(
            np.mean(np.abs((pp[mz] - pg[mz]) / np.abs(pg[mz])) * 100.0)
        ) if mz.any() else float("nan")
        ae = np.asarray(abs_whole)
        ar = np.asarray(abs_rel)
        res["abs_depth_mae_cm"] = float(ae.mean()) if len(ae) else float("nan")
        res["abs_depth_rmse_cm"] = float(
            np.sqrt((ae ** 2).mean())) if len(ae) else float("nan")
        res["abs_depth_med_cm"] = float(
            np.median(ae)) if len(ae) else float("nan")
        res["abs_depth_mape"] = float(ar.mean()) if len(ar) else float("nan")
        for name, key in [("road", "abs_road"), ("pothole", "abs_pothole"),
                          ("near", "abs_near"), ("far", "abs_far")]:
            vals = abs_err[name]
            res[f"{key}_mae_cm"] = float(
                np.mean(vals)) if vals else float("nan")
            res[f"{key}_n"] = int(len(vals)) if vals else 0
    return res


def precision_recall(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return p, r


def iou_score(tp, fp, fn):
    d = tp + fp + fn
    return tp / d if d > 0 else 0.0


def dice_score(tp, fp, fn):
    d = 2 * tp + fp + fn
    return 2 * tp / d if d > 0 else 0.0


if __name__ == "__main__":
    # standalone: python validate.py --checkpoint checkpoints/best.pt
    import argparse

    import dataset as D
    import model as M

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--checkpoint", default="checkpoints/best.pt")
    ap.add_argument("--split", default="val")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    cfg = U.load_config(args.config)
    ckpt = U.load_checkpoint(Path(args.checkpoint))
    assert "target_stats" in ckpt, "checkpoint missing normalization statistics"

    ds = D.MultiTaskPotholeDataset(cfg, args.split, use_aug=False)
    ds.set_dim_stats(ckpt["target_stats"])
    loader = torch.utils.data.DataLoader(
        ds, batch_size=int(cfg["train"]["batch_size"]), shuffle=False,
        num_workers=0)

    model = M.build_model(cfg)
    has_abs = any(k.startswith("abs_head") for k in ckpt["state_dict"])
    if not has_abs:
        model.remove_abs_head()
    model.load_state_dict(ckpt["state_dict"], strict=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    total = args.limit if args.limit else len(ds)
    res = validate(model, loader, cfg, ckpt["target_stats"], device,
                   total=total)
    for k, vv in res.items():
        print(f"{k:26s} {vv:.4f}" if isinstance(vv, float) else f"{k:26s} {vv}")