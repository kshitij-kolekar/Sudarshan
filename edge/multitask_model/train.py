"""Training driver for the RGB-only multi-task model.

Usage:
    python train.py                          # full training
    python train.py --epochs 90              # override epochs
    python train.py --limit 24 --epochs 3    # smoke test on a small subset

Checkpoints (best.pt / last.pt) include: model state, optimizer, scheduler,
epoch, best validation score, target-normalization statistics (train-split
only), full config and architecture metadata.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).parent))

import dataset as D
import geometry as G
import losses as L
import model as M
import utils as U
import validate as V


def build_model_safe(cfg):
    """Try pretrained backbone; fall back to random init with a printed note."""
    try:
        return M.build_model(cfg)
    except Exception as e:                    # download/weight-load failure
        print(f"[train] pretrained weights unavailable ({e}); "
              f"falling back to random-init backbone.")
        cfg["model"]["pretrained"] = False
        return M.build_model(cfg)


def cosine_warmup_schedule(epoch, warmup, total, base_lr, eta_min):
    if warmup > 0 and epoch < warmup:
        return base_lr * (epoch + 1) / warmup
    t = (epoch - warmup) / max(1, total - warmup)
    t = min(max(t, 0.0), 1.0)
    return eta_min + 0.5 * (base_lr - eta_min) * (1 + np.cos(np.pi * t))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--limit", type=int, default=None,
                    help="limit train (and val) samples (smoke test)")
    ap.add_argument("--resume", type=str, default=None)
    ap.add_argument("--tag", type=str, default="")
    ap.add_argument("--no-amp", action="store_true")
    args = ap.parse_args()

    cfg = U.load_config(args.config)
    if args.epochs:
        cfg["train"]["epochs"] = args.epochs
    use_amp = cfg["train"]["amp"] and not args.no_amp
    U.set_seed(cfg.get("seed", 42))
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[train] device={device} amp={use_amp}")

    # ------------------------------------------------------------------
    # Target-normalization statistics: TRAIN SPLIT ONLY.
    # ------------------------------------------------------------------
    root = Path(cfg["data"]["root"])
    df = U.load_targets_df(root)
    df = df[(df["valid"] == True) & (df["split"] == "train")]           # noqa:E712
    dim_cols = list(cfg["model"]["dims"]) + list(cfg["model"]["dims_aux"])
    stats = U.compute_target_stats(
        df[dim_cols].to_numpy(np.float64), df["volume_m3"].to_numpy(np.float64))
    print(f"[train] normalization stats: dims mean={np.round(stats['dims']['mean'],4)}")
    U.save_json({"target_stats": stats}, root / "multitask_model" / "outputs"
                / "target_stats.json")

    tr_ds = D.MultiTaskPotholeDataset(cfg, "train", use_aug=True)
    tr_ds.set_dim_stats(stats)
    va_ds = D.MultiTaskPotholeDataset(cfg, "val", use_aug=False)
    va_ds.set_dim_stats(stats)

    if args.limit:
        from torch.utils.data import Subset
        tr_ds = Subset(tr_ds, list(range(min(args.limit, len(tr_ds)))))
        va_ds = Subset(va_ds, list(range(min(args.limit, len(va_ds)))))
    workers = int(cfg["data"].get("workers", 0))
    bs = int(cfg["train"]["batch_size"])
    tr_loader = torch.utils.data.DataLoader(tr_ds, batch_size=bs, shuffle=True,
                                            num_workers=workers, drop_last=True)
    va_loader = torch.utils.data.DataLoader(va_ds, batch_size=bs, shuffle=False,
                                            num_workers=workers)

    # ------------------------------------------------------------------
    model = build_model_safe(cfg).to(device)
    n_params = model.count_params()
    print(f"[train] {cfg['model']['backbone']} params={n_params/1e6:.2f}M "
          f"size={M.model_size_bytes(model)/1e6:.2f}MB (fp32 weights)")

    optim = torch.optim.AdamW(model.parameters(),
                              lr=cfg["train"]["base_lr"],
                              weight_decay=cfg["train"]["weight_decay"])
    epochs = int(cfg["train"]["epochs"])
    warmup = int(cfg["train"]["warmup_epochs"])
    eta_min = float(cfg["train"]["cosine_eta_min"])
    base_lr = float(cfg["train"]["base_lr"])
    sched = None   # epoch-based LambdaLR increments below

    start_epoch = 0
    best_score = -1.0
    if args.resume:
        ck = U.load_checkpoint(Path(args.resume))
        model.load_state_dict(ck["state_dict"])
        optim.load_state_dict(ck["optimizer"])
        start_epoch = ck.get("epoch", 0) + 1
        best_score = ck.get("best_score", -1.0)
        print(f"[train] resumed from {args.resume} at epoch {start_epoch}")

    criterion = L.MultiTaskLoss(cfg)
    n_req = len(cfg["model"]["dims"])

    scaler = torch.amp.GradScaler("cuda") if use_amp and device == "cuda" else None
    amp_ctx = (lambda: torch.amp.autocast("cuda", dtype=torch.float16)) \
        if use_amp and device == "cuda" else contextlib.nullcontext()

    out_dir = Path(cfg.get("outputs_dir", str(Path(__file__).parent / "outputs")))
    ckpt_dir = Path(cfg.get("checkpoint_dir", str(Path(__file__).parent / "checkpoints")))
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / ("train_log" + (f"_{args.tag}" if args.tag else "") + ".csv")
    log_file = open(log_path, "w", newline="", encoding="utf-8")
    log_writer = csv.writer(log_file)
    log_writer.writerow(["epoch", "seg_loss", "abs_depth_loss", "cavity_loss",
                         "dim_loss", "vol_loss", "total_loss", "lr",
                         "seg_iou", "seg_dice", "cavity_mae_cm",
                         "abs_depth_mae_cm", "plane_dist_mae_m",
                         "dim_mae_length_m", "dim_mae_width_m",
                         "dim_mae_area_m2", "vol_reg_mae_L", "vol_geo_mae_L",
                         "time_s"])

    U.save_json({"params": n_params, "size_bytes": M.model_size_bytes(model),
                 "arch": cfg["model"]["backbone"],
                 "pretrained_source": getattr(model.backbone,
                                              "pretrained_source", "?"),
                 "resolution": cfg["data"]["image_size"],
                 "batch_size": bs, "amp": use_amp},
                out_dir / "train_meta.json")

    patience = int(cfg["train"]["early_stop_patience"])
    no_improve = 0
    best_lr = base_lr

    for epoch in range(start_epoch, epochs):
        lr = cosine_warmup_schedule(epoch, warmup, epochs, base_lr, eta_min)
        for pg in optim.param_groups:
            pg["lr"] = lr

        model.train()
        t0 = time.time()
        aggr = {k: 0.0 for k in ["total", "seg", "abs_depth", "cavity_depth",
                                 "dim", "volume"]}
        n_batch = 0
        for i, batch in enumerate(tr_loader):
            batch = [t.to(device) for t in batch]
            img = batch[0]
            optim.zero_grad(set_to_none=True)
            with amp_ctx():
                out = model(img)
                lossd = criterion(out, batch, n_req)
                total = lossd["total"]
            if scaler is not None:
                scaler.scale(total).backward()
                scaler.unscale_(optim)
                torch.nn.utils.clip_grad_norm_(model.parameters(),
                                               cfg["train"]["max_grad_norm"])
                scaler.step(optim)
                scaler.update()
            else:
                total.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(),
                                               cfg["train"]["max_grad_norm"])
                optim.step()
            for k in aggr:
                aggr[k] += float(lossd[k].detach()) / len(tr_loader)
            n_batch += 1
            if i % int(cfg["train"]["log_every"]) == 0:
                print(f"  e{epoch} b{i}/{len(tr_loader)} "
                      f"seg={aggr['seg']:.4f} abs={aggr['abs_depth']:.4f} "
                      f"cav={aggr['cavity_depth']:.4f} "
                      f"dim={aggr['dim']:.4f} ttl={aggr['total']:.4f}")

        # ---- validation ----
        res = V.validate(model, va_loader, cfg, stats, device)
        mem = (torch.cuda.memory_allocated() / 1e6 if device == "cuda" else 0)
        dt = time.time() - t0
        print(f"[ep{epoch}] seg_iou={res['seg_iou']:.4f} dice={res['seg_dice']:.4f} "
              f"cav={res['depth_mae_cm']:.2f}cm "
              f"abs={res.get('abs_depth_mae_cm', float('nan')):.2f}cm "
              f"plane={res.get('plane_dist_mae_m', res['dim_mae_plane_dist_m']):.3f}m "
              f"vol_geo={res['vol_geo_mae_L']:.2f}L "
              f"gpu={mem:.0f}MB t={dt:.0f}s")

        log_writer.writerow([epoch, aggr["seg"], aggr["abs_depth"],
                             aggr["cavity_depth"], aggr["dim"], aggr["volume"],
                             aggr["total"], lr,
                             res["seg_iou"], res["seg_dice"],
                             res["depth_mae_cm"],
                             res.get("abs_depth_mae_cm", float("nan")),
                             res.get("plane_dist_mae_m", float("nan")),
                             res["dim_mae_length_m"], res["dim_mae_width_m"],
                             res["dim_mae_area_m2"], res["vol_reg_mae_L"],
                             res["vol_geo_mae_L"], dt])
        log_file.flush()

        # ---- save checkpoints ----
        U.save_checkpoint(ckpt_dir / cfg["train"]["checkpoint_last"],
                          model, optim, None, epoch, best_score, stats, cfg,
                          extra={"has_abs_depth": model.abs_enabled})
        if res["seg_iou"] > best_score:
            best_score = res["seg_iou"]
            no_improve = 0
            U.save_checkpoint(ckpt_dir / cfg["train"]["checkpoint_best"],
                              model, optim, None, epoch, best_score, stats, cfg,
                              extra={"has_abs_depth": model.abs_enabled})
            print(f"  * best updated: val seg_iou={best_score:.4f}")
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"[train] early stopping at epoch {epoch}")
                break

    log_file.close()
    print(f"[train] done. best val seg_iou={best_score:.4f}")
    print(f"[train] log:    {log_path}")
    print(f"[train] best:   {ckpt_dir / cfg['train']['checkpoint_best']}")
    print(f"[train] last:   {ckpt_dir / cfg['train']['checkpoint_last']}")


if __name__ == "__main__":
    main()