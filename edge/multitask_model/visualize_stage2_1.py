"""Stage 2.1 panel visualization (PREDICTED / GT pairs).

Loads MODEL B (dense absolute-depth head), runs RGB-ONLY inference over a
split, and writes one PNG panel per sample (>= 20 by default) with:
  RGB+GT contour | RGB+pred contour | GT abs depth | pred abs depth
  abs error      | GT cavity        | pred cavity (plane-fit) | road plane
  GT geometry    | pred geometry    | sanity bars               | metrics text

Usage:
    python visualize_stage2_1.py --checkpoint checkpoints/best.pt
        [--split test] [--count 20] [--out outputs/panel_vis]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))

import dataset as D
import geometry as GE
import model as M
import utils as U

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
except Exception as e:                      # pragma: no cover
    print(f"[viz] matplotlib unavailable ({e}) - cannot render panels")
    sys.exit(1)


def _unz(dd, stats):
    return U.unzscore(dd, stats["dims"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--checkpoint", default="checkpoints/best.pt")
    ap.add_argument("--split", default="test")
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--out", default="outputs/panel_vis")
    args = ap.parse_args()

    cfg = U.load_config(args.config)
    ckpt = U.load_checkpoint(Path(args.checkpoint))
    has_abs = any(k.startswith("abs_head") for k in ckpt["state_dict"])
    assert has_abs, "visualize requires a MODEL B checkpoint (abs depth head)"

    ds = D.MultiTaskPotholeDataset(cfg, args.split, use_aug=False)
    ds.set_dim_stats(ckpt["target_stats"])

    model = M.build_model(cfg)
    model.load_state_dict(ckpt["state_dict"], strict=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()

    W, H = cfg["data"]["image_size"]
    thr = cfg["inference"]["mask_threshold"]
    noise = cfg["data"]["depth_noise_floor_m"]
    abs_max = float(cfg["data"]["abs_depth_max_m"])
    plane_idx = cfg["model"]["dims"].index("plane_dist_m")
    required = cfg["model"]["dims"]

    name = "length_m", "width_m", "area_m2", "mean_depth_m", "p90_depth_m"
    out_d = Path(args.out)
    out_d.mkdir(parents=True, exist_ok=True)

    n = min(args.count, len(ds))
    print(f"[viz] split={args.split} samples={n}")
    for i in range(n):
        img_t, mask_gt, depth_gt, cav_valid, dims, vol, abs_gt, abs_valid = ds[i]
        rgb = ((img_t * torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
                + torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)).clamp(0, 1)
               .permute(1, 2, 0).numpy())
        with torch.no_grad():
            out = model(img_t.unsqueeze(0).to(device))
        seg_prob = torch.sigmoid(out["seg"]).cpu().squeeze().numpy()
        mask_pred = (seg_prob > thr)
        abs_pred = out["abs_depth"].cpu().squeeze().numpy()
        dims_pred = _unz(out["dims"].cpu().numpy(), ckpt["target_stats"])[0]
        vol_pred = U.unzscore1d(out["volume"].cpu().numpy(),
                                ckpt["target_stats"]["volume"])[0]

        geo = GE.geometry_from_abs_depth(seg_prob, abs_pred, cfg, W, H,
                                         thr, noise)
        ok = geo["success"]
        cav_pred = geo["cavity_map"] if ok else np.zeros((H, W), np.float32)

        dims_orig = U.unzscore(dims.numpy(), ckpt["target_stats"]["dims"])[0]
        vol_orig = U.unzscore1d(vol.numpy(), ckpt["target_stats"]["volume"])
        a_gt = np.array([dims_orig[0], dims_orig[1], dims_orig[2],
                         dims_orig[3] * 100.0, dims_orig[4] * 100.0,
                         vol_orig[0] * 1000.0])
        a_pr = np.array([geo["length_m"], geo["width_m"], geo["area_m2"],
                         geo["mean_depth_m"] * 100.0,
                         geo["p90_depth_m"] * 100.0,
                         geo["volume_m3"] * 1000.0])
        a_pr = np.where(np.isfinite(a_pr), a_pr, 0.0)

        abs_err = np.abs(abs_pred - abs_gt.numpy().squeeze()) * 100.0
        valid_e = (abs_valid.numpy().squeeze() > 0)

        vmin_m, vmax_m = 0.0, abs_max
        cav_vmax = 6.0

        fig, axs = plt.subplots(3, 4, figsize=(18, 13.5))
        aa = axs.ravel()
        cm = "turbo"

        def _contour(im, mask, color):
            im = im.copy()
            cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(im, cnts, -1, color, 2)
            return im

        rgbc_gt = _contour((rgb * 255).astype(np.uint8), mask_gt.numpy().squeeze(),
                           (0, 255, 0))
        rgbc_pr = _contour((rgb * 255).astype(np.uint8), mask_pred.astype(np.uint8),
                           (0, 200, 255))
        aa[0].imshow(rgbc_gt); aa[0].set_title("RGB + GT mask")
        aa[1].imshow(rgbc_pr); aa[1].set_title("RGB + pred mask")
        aa[2].imshow(abs_gt.numpy().squeeze(), vmin=vmin_m, vmax=vmax_m, cmap=cm)
        aa[2].set_title("GT absolute depth [m]")
        aa[3].imshow(abs_pred, vmin=vmin_m, vmax=vmax_m, cmap=cm)
        aa[3].set_title("Pred absolute depth [m]")

        err_show = np.where(valid_e, abs_err, np.nan)
        im4 = aa[4].imshow(err_show, cmap=cm)
        aa[4].set_title("Abs depth error [cm]")
        plt.colorbar(im4, ax=aa[4], fraction=0.046)
        aa[5].imshow(depth_gt.numpy().squeeze() * 100.0, vmin=0, vmax=cav_vmax,
                     cmap="jet")
        aa[5].set_title("GT cavity depth [cm]")
        aa[6].imshow(cav_pred * 100.0, vmin=0, vmax=cav_vmax, cmap="jet")
        aa[6].set_title("Pred cavity (plane-fit) [cm]")

        if ok:
            intri = GE.effective_intrinsics(cfg, W, H)
            n_ = geo["plane_n"]
            crop = int(cfg["geometry"]["edge_crop"])
            gy, gx = np.mgrid[crop:H - crop:5, crop:W - crop:5]
            du_ = (gx.astype(np.float64) - intri["cx"]) / intri["fx"]
            dv_ = (gy.astype(np.float64) - intri["cy"]) / intri["fy"]
            nrd = n_[0] * du_ + n_[1] * dv_ + n_[2]
            with np.errstate(divide="ignore", invalid="ignore"):
                lam = np.where(np.abs(nrd) < 1e-6, np.nan,
                               -geo["plane_d"] / nrd)
            pp = (np.isfinite(lam)) & (lam > 0) & (lam <= abs_max)
            plane_mask = np.zeros((H, W), np.uint8)
            plane_mask[gy[pp], gx[pp]] = 1
            rgb_pl = (rgb * 255).astype(np.uint8)
            rgb_pl[plane_mask > 0] = (0, 255, 0)
            aa[7].imshow(rgb_pl)
            aa[7].set_title(f"Road plane fit nz={n_[2]:.2f} "
                            f"plane={geo['plane_dist_m']:.2f}m")
        else:
            aa[7].imshow(rgb)
            aa[7].set_title("Road plane fit: FAILED")

        names = ["L [m]", "W [m]", "A [m2]", "meanD [cm]", "p90D [cm]",
                 "Vol [L]"]
        x = np.arange(len(names))
        wdt = 0.38
        lm = 1e-9
        a_gt_s = np.where(a_gt > 0, np.log10(np.maximum(a_gt, lm)), -8)
        a_pr_s = np.where(a_pr > 0, np.log10(np.maximum(a_pr, lm)), -8)
        aa[8].bar(x - wdt / 2, a_gt_s, wdt, label="GT")
        aa[9].bar(x - wdt / 2, a_pr_s, wdt, label="Pred")
        aa[8].set_xticks(x, names); aa[8].set_xticklabels(names, rotation=45)
        aa[8].set_ylabel("log10 scale"); aa[8].legend(); aa[8].set_title("GT geometry")
        aa[9].set_xticks(x, names); aa[9].set_xticklabels(names, rotation=45)
        aa[9].set_ylabel("log10 scale"); aa[9].legend(); aa[9].set_title("Pred geometry")

        aa[10].bar(x, a_pr_s - a_gt_s, color="salmon")
        aa[10].axhline(0, color="k", lw=0.5)
        aa[10].set_xticks(x, names); aa[10].set_xticklabels(names, rotation=45)
        aa[10].set_title(f"Pred-GT (log)   sanity V/(A*mean)="
                         f"{geo['volume_m3']/(geo['area_m2']*geo['mean_depth_m']) if ok and geo['mean_depth_m']>0 and geo['area_m2']>0 and geo['volume_m3']>0 else float('nan'):.2f}")

        info = (f"succ={ok}  n_px={geo['n_pixels']}\n"
                f"GT:  L={a_gt[0]:.2f} W={a_gt[1]:.2f} A={a_gt[2]:.4f} "
                f"mD={a_gt[3]:.1f} pD={a_gt[4]:.1f} V={a_gt[5]:.2f}\n"
                f"PR:  L={a_pr[0]:.2f} W={a_pr[1]:.2f} A={a_pr[2]:.4f} "
                f"mD={a_pr[3]:.1f} pD={a_pr[4]:.1f} V={a_pr[5]:.2f}\n"
                f"plane dist: GT={dims_orig[5]:.3f}m  "
                f"pred(fit)={geo['plane_dist_m']:.3f}m\n"
                f"abs depth MAE(valid)={float(np.nanmean(err_show)):.1f} cm")
        aa[11].axis("off")
        aa[11].text(0.02, 0.98, info, va="top", ha="left", family="monospace",
                    fontsize=9)

        for a in aa:
            a.set_adjustable("box")
        fig.tight_layout()
        stem = Path(ds.images[i]).stem
        path = out_d / f"{args.split}_{i:03d}_{stem}.png"
        fig.savefig(path, dpi=110)
        plt.close(fig)
        print(f"  [{i+1}/{n}] {stem}  succ={ok}")
    print(f"[viz] panels -> {out_d}")


if __name__ == "__main__":
    main()