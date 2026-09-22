"""Final TEST evaluation - RGB-ONLY.

The model receives only the RGB image.  GT depth/mask are loaded only AFTER
the forward pass, purely for scoring.  Reports segmentation, absolute/cavity
depth, plane-distance, dimension, geometry and volume metrics, and compares
segmentation quality against the existing YOLOv8n-seg baseline (recorded from
its own evaluation; NOT directly comparable).

Usage:
    python test.py                                # Model B (current best)
    python test.py --checkpoint checkpoints/stage2_modelA_best.pt
    python test.py --ablate                       # Model A vs Model B
    python test.py --split val --limit 12 --save  # quick sanity + visuals
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))

import dataset as D
import geometry as GE
import model as M
import utils as U
import validate as V

# Recorded from the existing YOLOv8n-seg evaluation (Stage-1 model). NOT retrained.
YOLO_BASELINE = {
    "Box Precision": 0.858, "Box Recall": 0.894,
    "Box mAP50": 0.906, "Box mAP50-95": 0.631,
    "Mask Precision": 0.912, "Mask Recall": 0.944,
    "Mask mAP50": 0.970, "Mask mAP50-95": 0.643,
}


def _load_model_for_ckpt(cfg, ckpt):
    model = M.build_model(cfg)
    has_abs = any(k.startswith("abs_head") for k in ckpt["state_dict"])
    if not has_abs:
        model.remove_abs_head()
    model.load_state_dict(ckpt["state_dict"], strict=True)
    return model


def _make_loader(cfg, ckpt, split, limit=None):
    ds = D.MultiTaskPotholeDataset(cfg, split, use_aug=False)
    ds.set_dim_stats(ckpt["target_stats"])
    loader = torch.utils.data.DataLoader(
        ds, batch_size=int(cfg["train"]["batch_size"]), shuffle=False,
        num_workers=0)
    return ds, loader


def _print_model(split, res, has_abs):
    print(f"\n================ TEST {split.upper()}  (RGB-ONLY) ================")
    print(f"Segmentation  IoU={res['seg_iou']:.4f}  Dice={res['seg_dice']:.4f}  "
          f"P={res['seg_precision']:.3f}  R={res['seg_recall']:.3f}")
    print(f"Cavity depth (GT-valid px)  MAE={res['depth_mae_cm']:.2f}cm  "
          f"RMSE={res['depth_rmse_cm']:.2f}cm  medAbs={res['depth_med_cm']:.2f}cm")
    if has_abs:
        print("Absolute metric depth (valid px):")
        print(f"  MAE={res['abs_depth_mae_cm']:.2f}cm  "
              f"RMSE={res['abs_depth_rmse_cm']:.2f}cm  "
              f"medAbs={res['abs_depth_med_cm']:.2f}cm  "
              f"MAPE={res['abs_depth_mape']:.1f}%")
        print("  banded MAE:  road=" + (f"{res['abs_road_mae_cm']:.2f}cm"
                                        if 'abs_road_mae_cm' in res else "n/a")
              + "  pothole=" + (f"{res['abs_pothole_mae_cm']:.2f}cm"
                                if 'abs_pothole_mae_cm' in res else "n/a")
              + "  near=" + (f"{res['abs_near_mae_cm']:.2f}cm"
                             if 'abs_near_mae_cm' in res else "n/a")
              + "  far=" + (f"{res['abs_far_mae_cm']:.2f}cm"
                            if 'abs_far_mae_cm' in res else "n/a"))
    print("Dimensions (regression head, MAE):")
    print(f"  length={res['dim_mae_length_m']:.3f}m  width={res['dim_mae_width_m']:.3f}m  "
          f"area={res['dim_mae_area_m2']:.4f}m^2")
    print(f"  mean_depth={res['dim_mae_mean_depth_cm']:.2f}cm  "
          f"p90_depth={res['dim_mae_p90_depth_cm']:.2f}cm")
    print(f"  MAPE%: len={res['dim_mape_length']:.1f}  w={res['dim_mape_width']:.1f}  "
          f"area={res['dim_mape_area']:.1f}")
    if has_abs:
        print(f"  plane_dist (reg head) MAE={res['dim_mae_plane_dist_m']:.3f}m")
        print(f"  plane_dist (fitted)   MAE={res['plane_dist_mae_m']:.3f}m "
              f"MAPE={res['plane_dist_mape']:.1f}%")
    else:
        print(f"  plane_dist MAE={res['dim_mae_plane_dist_m']:.3f}m "
              f"MAPE={res['dim_mape_plane_dist']:.1f}%")
    print("Geometry-derived (predicted mask + depth, MAE):")
    print(f"  length={res['geo_mae_length_m']:.3f}m  width={res['geo_mae_width_m']:.3f}m  "
          f"area={res['geo_mae_area_m2']:.4f}m^2")
    print(f"  mean_depth={res['geo_mae_mean_depth_cm']:.2f}cm  "
          f"p90_depth={res['geo_mae_p90_depth_cm']:.2f}cm")
    print("Volume (geometry-derived from predicted mask+depth):")
    print(f"  MAE={res['vol_geo_mae_L']:.3f}L  MAPE={res['vol_geo_mape']:.1f}%   "
          f"(direct regression MAE={res['vol_reg_mae_L']:.3f}L)")
    print(f"Geometry failures={res['geo_failure_count']}  "
          f"volume/(area*mean) sanity mean={res['vol_sanity_ratio_mean']:.3f} "
          f"median={res['vol_sanity_ratio_median']:.3f}")

    print("\n--------------- baseline comparison (segment) ----------------")
    print("NOTE: YOLO metrics are detection/generalization mAP; ours are spatial")
    print("per-pixel IoU/Dice at threshold 0.5. Quantities are NOT directly")
    print("comparable; shown for cross-reference only.")
    print("YOLOv8n-seg (existing): "
          f"maskP={YOLO_BASELINE['Mask Precision']:.3f} "
          f"maskR={YOLO_BASELINE['Mask Recall']:.3f} "
          f"mask_mAP50={YOLO_BASELINE['Mask mAP50']:.3f} "
          f"mask_mAP50-95={YOLO_BASELINE['Mask mAP50-95']:.3f}")
    print("MultiTask  (ours):      "
          f"maskP={res['seg_precision']:.3f} "
          f"maskR={res['seg_recall']:.3f} "
          f"IoU={res['seg_iou']:.4f} Dice={res['seg_dice']:.4f}")


def run_test():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--checkpoint", default="checkpoints/best.pt")
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ablate", action="store_true",
                    help="Model A (stage2) vs Model B (dense abs depth)")
    ap.add_argument("--save", action="store_true", help="save per-sample outputs")
    args = ap.parse_args()

    cfg = U.load_config(args.config)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    out_dir = Path(__file__).parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.ablate:
        jobs = [("stage2_modelA_best.pt", "modelA"), ("best.pt", "modelB")]
    else:
        jobs = [(str(Path(args.checkpoint).name), "final")]

    results = {}
    for ckpt_name, tag in jobs:
        ckpt_path = Path(__file__).parent / "checkpoints" / ckpt_name
        if not ckpt_path.exists():
            ckpt_path = Path(ckpt_name)
        if not ckpt_path.exists():
            print(f"[test] {ckpt_path} not found - skipping {tag}")
            continue
        ckpt = U.load_checkpoint(ckpt_path)
        has_abs = any(k.startswith("abs_head") for k in ckpt["state_dict"])
        ds, loader = _make_loader(cfg, ckpt, args.split, args.limit)
        model = _load_model_for_ckpt(cfg, ckpt).to(device).eval()
        n_params = model.count_params()

        print(f"\n[test] {tag}: {ckpt_path}  split={args.split} n={len(ds)} "
              f"RGB-ONLY inference (depth/mask loaded post-hoc for scoring)  "
              f"params={n_params/1e6:.2f}M")
        t0 = time.time()
        res = V.validate(model, loader, cfg, ckpt["target_stats"], device,
                         total=args.limit)
        dt = time.time() - t0
        res["_tag"] = tag
        res["_checkpoint"] = str(ckpt_path)
        res["_has_abs"] = has_abs
        res["_params"] = n_params
        res["_infer_s"] = dt
        results[tag] = res
        _print_model(args.split, res, has_abs)

        if args.save:
            save_per_sample(cfg, model, ds, device, ckpt["target_stats"],
                            out_dir / f"test_vis_{tag}", has_abs)

    U.save_json({"args": vars(args), "results": results,
                 "yolo_baseline": YOLO_BASELINE},
                out_dir / f"test_results_{args.split}.json")
    with open(out_dir / f"test_results_{args.split}.txt", "w",
              encoding="utf-8") as f:
        for tag, res in results.items():
            f.write(f"=== {tag} ===\n")
            for k, v in res.items():
                if isinstance(v, bool) or k == "_tag" or k == "_checkpoint":
                    f.write(f"{k}: {v}\n")
                elif isinstance(v, float):
                    f.write(f"{k}: {v:.5f}\n")
            f.write("\n")
    print(f"[test] results -> {out_dir}")


def save_per_sample(cfg, model, ds, device, stats, visdir, has_abs=True):
    visdir.mkdir(parents=True, exist_ok=True)
    mask_thr = cfg["inference"]["mask_threshold"]
    noise = cfg["data"]["depth_noise_floor_m"]
    W, H = cfg["data"]["image_size"]
    n = 0
    for i in range(len(ds)):
        img_t, mask_gt, depth_gt, valid, dims, vol, abs_depth, valid_abs = ds[i]
        img = (img_t * torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
               + torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)).clamp(0, 1)
        with torch.no_grad():
            out = model(img_t.unsqueeze(0).to(device))
        seg_prob = torch.sigmoid(out["seg"]).cpu().squeeze(0).squeeze(0).numpy()
        mask_pred = (seg_prob > mask_thr).astype(np.uint8)
        depth_pred = out["depth"].cpu().squeeze(0).squeeze(0).numpy()
        dims_pred = U.unzscore(out["dims"].cpu().numpy(), stats["dims"])[0]
        if has_abs:
            abs_pred = out["abs_depth"].cpu().squeeze(0).squeeze(0).numpy()
            geo = GE.geometry_from_abs_depth(seg_prob, abs_pred, cfg, W, H,
                                             mask_thr, noise)
        else:
            plane_idx = cfg["model"]["dims"].index("plane_dist_m")
            geo = GE.predict_geometry(seg_prob, depth_pred, dims_pred[plane_idx],
                                      cfg, W, H, mask_thr, noise)
        rgb = (img.permute(1, 2, 0).numpy() * 255).astype(np.uint8)
        rgb = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        cont, _ = cv2.findContours(mask_pred.copy(), cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(rgb, cont, -1, (0, 255, 0), 2)
        depth_vis = (np.clip(depth_pred / 0.10, 0, 1) * 255).astype(np.uint8)
        depth_vis = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
        stem = Path(ds.images[i]).stem
        cv2.imwrite(str(visdir / f"{stem}_pred.png"), rgb)
        cv2.imwrite(str(visdir / f"{stem}_depth.png"), depth_vis)
        if has_abs:
            abs_vis = (np.clip(abs_pred / cfg["data"]["abs_depth_max_m"], 0, 1)
                       * 255).astype(np.uint8)
            cv2.imwrite(str(visdir / f"{stem}_absdepth.png"),
                        cv2.applyColorMap(abs_vis, cv2.COLORMAP_JET))
        n += 1
    print(f"[test] wrote per-sample visuals for {n} images -> {visdir}")


if __name__ == "__main__":
    run_test()