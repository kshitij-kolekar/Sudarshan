"""Multi-task loss functions (Stage 2.1).

L_total = lambda_seg * L_seg
        + lambda_abs_depth * (L_abs_depth + abs_depth_grad_lambda * L_grad)
        + lambda_depth     * L_cavity_depth
        + lambda_dim       * L_dim
        + lambda_volume    * L_volume

  L_seg        = BCEWithLogits + Dice  (foreground/background imbalance)
  L_abs_depth  = SmoothL1 on VALID absolute-depth pixels (documented range, m)
  L_grad       = masked spatial gradient (TV) on valid abs-depth px (opt.)
  L_cavity_depth = SmoothL1 on VALID pothole cavity pixels (mask & > noise floor)
  L_dim        = SmoothL1 on the required normalized physical quantities
  L_volume     = SmoothL1 on normalized auxiliary volume regression

Each component is returned separately for logging.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


def dice_loss(logits, target, smooth=1.0):
    prob = torch.sigmoid(logits)
    num = 2.0 * (prob * target).sum() + smooth
    den = prob.sum() + target.sum() + smooth
    return 1.0 - num / den


def masked_smooth_l1(pred, target, valid, beta=1.0, reduction="mean"):
    """SmoothL1 over pixels where valid == 1."""
    if not bool(valid.any()):
        return pred.sum() * 0.0
    return F.smooth_l1_loss(pred[valid > 0], target[valid > 0],
                            reduction=reduction, beta=beta)


def masked_depth_grad(pred, valid, beta=0.1):
    """Mean L1 of the spatial gradient of `pred` on pixels whose 2x1 / 1x2
    neighbourhood is valid. Acts as a mild smoothness/edge-aware prior so the
    road surface stays locally planar without washing out real edges."""
    dx = (pred[..., 1:] - pred[..., :-1]).abs()
    dy = (pred[..., 1:, :] - pred[..., :-1, :]).abs()
    vx = valid[..., 1:] * valid[..., :-1]
    vy = valid[..., 1:, :] * valid[..., :-1, :]
    s = 0.0
    n = 0
    if bool(vx.any()):
        s = s + F.smooth_l1_loss(dx[vx > 0], torch.zeros_like(dx[vx > 0]),
                                 reduction="mean", beta=beta)
        n = n + 1
    if bool(vy.any()):
        s = s + F.smooth_l1_loss(dy[vy > 0], torch.zeros_like(dy[vy > 0]),
                                 reduction="mean", beta=beta)
        n = n + 1
    return s if n == 0 else s / n


class MultiTaskLoss(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        l = cfg["loss"]
        self.lambda_seg = float(l["lambda_seg"])
        self.lambda_depth = float(l["lambda_depth"])
        self.lambda_abs_depth = float(l["lambda_abs_depth"])
        self.lambda_dim = float(l["lambda_dim"])
        self.lambda_volume = float(l["lambda_volume"])
        self.seg_bce_w = float(cfg["model"]["seg_weight_bce"])
        self.seg_dice_w = float(cfg["model"]["seg_weight_dice"])
        self.abs_grad_lambda = float(cfg["model"]["abs_depth_grad_lambda"])
        self.smooth_beta = 1.0

    def forward(self, out, batch, aux_required):
        """out: {'seg','depth','abs_depth','dims','volume'}
        batch: (img, mask, cavity, cavity_valid, dims, vol, abs_depth, abs_valid)."""
        (_, mask_gt, cavity_gt, valid_cav, dims_gt, vol_gt,
         abs_gt, valid_abs) = batch

        # ---- segmentation ----
        seg_logits = out["seg"]
        bce = F.binary_cross_entropy_with_logits(
            seg_logits, mask_gt, reduction="mean")
        dice = dice_loss(seg_logits, mask_gt)
        seg_loss = self.seg_bce_w * bce + self.seg_dice_w * dice

        # ---- absolute metric depth (valid pixels only) ----
        abs_pred = out["abs_depth"]
        abs_loss = masked_smooth_l1(abs_pred, abs_gt, valid_abs,
                                    beta=self.smooth_beta)
        if self.abs_grad_lambda > 0.0:
            abs_loss = abs_loss + self.abs_grad_lambda * masked_depth_grad(
                abs_pred, valid_abs)

        # ---- cavity depth over VALID pothole pixels only ----
        cavity_loss = masked_smooth_l1(out["depth"], cavity_gt, valid_cav,
                                       beta=self.smooth_beta)

        # ---- dimension loss on REQUIRED quantities (first N) ----
        n_req = aux_required
        dims_pred = out["dims"][:, :n_req]
        dims_gt_r = dims_gt[:, :n_req]
        dim_loss = F.smooth_l1_loss(dims_pred, dims_gt_r, reduction="mean")

        # ---- auxiliary direct volume regression (normalized) ----
        vol_loss = F.smooth_l1_loss(out["volume"], vol_gt.squeeze(-1),
                                    reduction="mean")

        total = (self.lambda_seg * seg_loss
                 + self.lambda_abs_depth * abs_loss
                 + self.lambda_depth * cavity_loss
                 + self.lambda_dim * dim_loss
                 + self.lambda_volume * vol_loss)

        return {
            "total": total,
            "seg": seg_loss,
            "abs_depth": abs_loss,
            "cavity_depth": cavity_loss,
            "dim": dim_loss,
            "volume": vol_loss,
        }