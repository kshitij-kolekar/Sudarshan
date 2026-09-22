"""RGB-ONLY inference demo.

Usage:
    python inference.py --image path/to/image.jpg [--checkpoint ...]

Only the RGB image is required - no depth file is loaded as input.
The model predicts segmentation, cavity depth, and physical dimensions.

IMPORTANT SCIENTIFIC LIMITATION (printed with every result):
    * Measurements are MODEL PREDICTIONS.
    * They are "geometry-derived supervision"-style estimates and are
      "calibration-dependent metric estimates" - NOT survey-grade ground truth.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torchvision.transforms.functional as F

sys.path.insert(0, str(Path(__file__).parent))

import dataset as D
import geometry as GE
import model as M
import utils as U


def load_image(path: str, W: int, H: int):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    t = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
    t = F.resize(t, (H, W), F.InterpolationMode.BILINEAR)
    t = F.normalize(t, list(D.IMG_MEAN), list(D.IMG_STD))
    return img, t.unsqueeze(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--config", default=str(Path(__file__).parent / "config.yaml"))
    ap.add_argument("--checkpoint",
                    default=str(Path(__file__).parent / "checkpoints" / "best.pt"))
    ap.add_argument("--out", default=None, help="output annotated image path")
    args = ap.parse_args()

    cfg = U.load_config(args.config)
    ckpt = U.load_checkpoint(Path(args.checkpoint))
    model = M.build_model(cfg)
    has_abs = any(k.startswith("abs_head") for k in ckpt["state_dict"])
    if not has_abs:
        model.remove_abs_head()
    model.load_state_dict(ckpt["state_dict"], strict=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()

    W, H = cfg["data"]["image_size"]
    threshold = cfg["inference"]["mask_threshold"]
    noise = cfg["data"]["depth_noise_floor_m"]

    img_rgb, t = load_image(args.image, W, H)
    with torch.no_grad():
        out = model(t.to(device))

    seg_prob = torch.sigmoid(out["seg"]).cpu().squeeze().numpy()
    depth_pred = out["depth"].cpu().squeeze().numpy()
    dims_pred = U.unzscore(
        out["dims"].cpu().numpy(), ckpt["target_stats"]["dims"])[0]
    vol_aux = U.unzscore1d(
        out["volume"].cpu().numpy(), ckpt["target_stats"]["volume"])[0]

    mask = (seg_prob > threshold).astype(np.uint8)
    conf = float(seg_prob[mask > 0].mean()) if mask.any() else 0.0
    if has_abs and mask.any():
        abs_depth = out["abs_depth"].cpu().squeeze().numpy()
        geo = GE.geometry_from_abs_depth(seg_prob, abs_depth, cfg, W, H,
                                         threshold, noise)
    else:
        plane_idx = cfg["model"]["dims"].index("plane_dist_m")
        plane_pred = float(dims_pred[plane_idx])
        geo = GE.predict_geometry(seg_prob, depth_pred, plane_pred, cfg, W, H,
                                  threshold, noise)

    # Normalize resized intrinsics for displaying original-res coordinates
    xs, ys = np.where(mask > 0)
    if len(xs) > 0:
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        bbox = (int(x0), int(y0), int(x1 - x0 + 1), int(y1 - y0 + 1))
    else:
        bbox = None

    print("\n============================================")
    print(" RGB-ONLY MULTI-TASK INFERENCE RESULT")
    print("============================================")
    if conf == 0:
        print(" No pothole detected (max mask prob below threshold).")
        print(" (measurements are MODEL PREDICTIONS; calibration-dependent)")
        return
    print("Pothole: P001")
    print(f"Confidence: {conf:.2f}")
    print(f"Length:    {geo['length_m']*100:.1f} cm")
    print(f"Width:     {geo['width_m']*100:.1f} cm")
    print(f"Area:      {geo['area_m2']*1e4:.1f} cm^2")
    print(f"Mean Depth:{geo['mean_depth_m']*100:.1f} cm")
    print(f"P90 Depth: {geo['p90_depth_m']*100:.1f} cm")
    if has_abs and mask.any():
        print(f"Plane Dist:{geo['plane_dist_m']:.2f} m  (road plane fitted "
              f"from predicted absolute depth)")
    else:
        print(f"Plane Dist:{plane_pred:.2f} m  (predicted camera-to-road scale)")
    print(f"Volume:    {geo['volume_m3']*1000:.2f} L  "
          f"(geometry-derived; direct head={vol_aux*1000:.2f} L)")
    print("--------------------------------------------")
    print("These are MODEL PREDICTIONS.")
    print("Physical values are geometry-derived, calibration-dependent")
    print("metric estimates - NOT survey-grade ground truth.")
    print("============================================\n")

    # ---- annotated output ----
    if args.out:
        rgb_out = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR).copy()
        if bbox is not None:
            cv2.rectangle(rgb_out, (bbox[0], bbox[1]),
                          (bbox[0] + bbox[2], bbox[1] + bbox[3]),
                          (0, 255, 0), 2)
        conts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(rgb_out, conts, -1, (0, 200, 255), 2)
        lines = [
            f"P001  conf={conf:.2f}",
            f"L={geo['length_m']*100:.1f}cm  W={geo['width_m']*100:.1f}cm",
            f"A={geo['area_m2']*1e4:.0f}cm2  V={geo['volume_m3']*1000:.2f}L",
            f"meanD={geo['mean_depth_m']*100:.1f}cm  p90D={geo['p90_depth_m']*100:.1f}cm",
        ]
        y = 20
        for ln in lines:
            cv2.putText(rgb_out, ln, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255, 255, 255), 1, cv2.LINE_AA)
            y += 18
        cv2.imwrite(args.out, rgb_out)
        print(f"Annotated image saved -> {args.out}")


if __name__ == "__main__":
    main()