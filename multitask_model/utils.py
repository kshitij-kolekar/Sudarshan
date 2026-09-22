"""Shared utilities: config, metrics, normalization stats, seeding."""
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml


def load_config(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_targets_df(root) -> pd.DataFrame:
    """Load the Stage-1 supervision table and merge the Stage-2 scene-scale
    target (`plane_dist_m`, road-plane distance in metres) by image name."""
    root = Path(root)
    df = pd.read_csv(root / "dimension_targets_v2.csv")
    plane_path = root / "targets_v2" / "plane_dist_v2.csv"
    if plane_path.exists():
        plane = pd.read_csv(plane_path)
        df = df.merge(plane[["image", "plane_dist_m"]], on="image", how="left")
    return df


def save_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=float)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ------------------------------------------------------------------
# Checkpoints
# ------------------------------------------------------------------
def save_checkpoint(path: Path, model, optimizer, scheduler, epoch, best_score,
                    target_stats, cfg, extra=None):
    data = {
        "state_dict": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": None if scheduler is None else scheduler.state_dict(),
        "epoch": epoch,
        "best_score": best_score,
        "target_stats": target_stats,
        "config": cfg,
        "model_size_params": model.count_params(),
        "arch": cfg["model"]["backbone"],
    }
    if extra:
        data.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(data, path)


def load_checkpoint(path: Path):
    return torch.load(path, map_location="cpu", weights_only=False)


# ------------------------------------------------------------------
# Normalization statistics - MUST be computed on TRAIN split only.
# Saved to disk so inference/test use the exact same values.
# ------------------------------------------------------------------
def compute_target_stats(dim_data: np.ndarray, vol_data: np.ndarray = None) -> dict:
    """Return normalized statistics; dims use z-score, volume uses z-score too."""
    stats = {}

    def _z(a):
        return {
            "mean": [float(x) for x in np.mean(a, axis=0)],
            "std": [float(x) for x in np.std(a, axis=0)],
        }

    stats["dims"] = _z(dim_data)
    if vol_data is not None:
        v = np.asarray(vol_data, dtype=np.float64)
        stats["volume"] = {
            "mean": float(np.mean(v)),
            "std": float(np.std(v)),
        }
    return stats


def zscore(arr, stats):
    return (arr - np.asarray(stats["mean"])[None, :]) / (
        np.asarray(stats["std"])[None, :] + 1e-8
    )


def unzscore(arr, stats):
    return arr * np.asarray(stats["std"])[None, :] + np.asarray(stats["mean"])[None, :]


def zscore1d(arr, stats):
    return (arr - stats["mean"]) / (stats["std"] + 1e-8)


def unzscore1d(arr, stats):
    return arr * stats["std"] + stats["mean"]


def shape_of_tensor(x) -> str:
    return str(tuple(x.shape)) if isinstance(x, torch.Tensor) else str(np.shape(x))


# ------------------------------------------------------------------
# Metric helpers (batched evaluation)
# ------------------------------------------------------------------
def iou_score(tp, fp, fn):
    denom = tp + fp + fn
    return tp / denom if denom > 0 else 0.0


def dice_score(tp, fp, fn):
    denom = 2 * tp + fp + fn
    return (2 * tp) / denom if denom > 0 else 0.0


def precision_recall(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return p, r


def seg_metrics(gt_mask, pred_mask):
    """gt/pred: flattened bool or 0/1 arrays of equal length."""
    gt = gt_mask.reshape(-1) > 0
    pr = pred_mask.reshape(-1) > 0
    tp = int(np.logical_and(gt, pr).sum())
    fp = int(np.logical_and(~gt, pr).sum())
    fn = int(np.logical_and(gt, ~pr).sum())
    return tp, fp, fn


def mae(y, yhat):
    return float(np.mean(np.abs(y - yhat)))


def rmse(y, yhat):
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def median_abs_err(y, yhat):
    return float(np.median(np.abs(y - yhat)))


def mape(y, yhat):
    m = np.abs(y) > 1e-12
    if not m.any():
        return float("nan")
    return float(np.mean(np.abs((y[m] - yhat[m]) / y[m]) * 100.0))


def masked_mae(y, yhat, valid):
    v = valid > 0
    return mae(y[v], yhat[v]) if v.any() else float("nan")