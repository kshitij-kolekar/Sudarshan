"""Lightweight multi-task architecture.

RGB -> MobileNetV3-Small encoder -> lightweight FPN decoder (5 levels)
   |-> Segmentation head  (binary pothole logits, full resolution)
   |-> Depth head         (cavity depth in metres via scaled sigmoid, full res)
   |-> Dimension head     (normalized physical quantities, mask-attention pooled)
   |-> Volume head        (auxiliary direct volume regression, NOT primary)

Design choices:
  - MobileNetV3-Small: ~1M-param-class model, edge-friendly (Jetson Nano class),
    ImageNet-pretrained via torchvision
    (MobileNet_V3_Small_Weights.IMAGENET1K_V1).
  - A 5-level FPN (strides 2/4/8/16/32) uses the whole pretrained encoder and
    keeps a stride-2 branch so segmentation/depth boundaries stay usable.
  - Dimension head uses mask-weighted pooling so regression focuses on the
    pothole region instead of the whole frame.
  - Depth is bounded to [0, clip] with a scaled sigmoid to avoid unbounded
    outliers flowing into the geometry module.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision


class ConvBnReLU(nn.Sequential):
    def __init__(self, cin, cout, k=3, s=1, p=None):
        p = p if p is not None else (k - 1) // 2
        super().__init__(
            nn.Conv2d(cin, cout, k, s, p, bias=False),
            nn.BatchNorm2d(cout),
            nn.ReLU(inplace=True),
        )


class MobileNetV3Backbone(nn.Module):
    """MobileNetV3 encoder split into 5 levels at strides 2/4/8/16/32.

    Segment boundaries were verified empirically against the actual
    torchvision feature graph (not assumed).
    """

    NIV = {
        "mobilenetv3_small": {
            "segments": [(0, 1), (1, 2), (2, 4), (4, 9), (9, 12)],
            "channels": [16, 16, 24, 48, 96],
            "strides": [2, 4, 8, 16, 32],
        },
        "mobilenetv3_large": {
            "segments": [(0, 2), (2, 4), (4, 7), (7, 13), (13, 16)],
            "channels": [16, 24, 40, 112, 160],
            "strides": [2, 4, 8, 16, 32],
        },
    }

    def __init__(self, name="mobilenetv3_small", pretrained=True):
        super().__init__()
        assert name in self.NIV, name
        if name == "mobilenetv3_small":
            weights = (torchvision.models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
                       if pretrained else None)
            v3 = torchvision.models.mobilenet_v3_small(weights=weights)
        else:
            weights = (torchvision.models.MobileNet_V3_Large_Weights.IMAGENET1K_V1
                       if pretrained else None)
            v3 = torchvision.models.mobilenet_v3_large(weights=weights)
        self.pretrained_source = str(weights) if pretrained else "random-init"
        feats = list(v3.features.children())
        segs = self.NIV[name]["segments"]
        self.stages = nn.ModuleList(
            [nn.Sequential(*feats[a:b]) for a, b in segs])
        self.out_channels = self.NIV[name]["channels"]

    def forward(self, x):
        outs = []
        f = x
        for stage in self.stages:
            f = stage(f)
            outs.append(f)
        return outs   # [s2, s4, s8, s16, s32]


class FPN(nn.Module):
    """Top-down FPN over N encoder levels (finest -> coarsest order)."""

    def __init__(self, in_channels, dh=64):
        super().__init__()
        self.laterals = nn.ModuleList(
            [ConvBnReLU(c, dh, 1, 1, p=0) for c in in_channels])
        self.refine = ConvBnReLU(dh, dh, 3, 1)
        self.out_ch = dh

    def forward(self, feats):
        lats = [lat(f) for lat, f in zip(self.laterals, feats)]  # fine->coarse
        p = lats[-1]
        for i in range(len(feats) - 2, -1, -1):
            p = lats[i] + F.interpolate(p, size=lats[i].shape[-2:],
                                        mode="nearest")
        p1 = self.refine(p)          # finest, stride 2
        return p1, lats[-1]          # (finest, coarsest lateral)


class MultiTaskNet(nn.Module):
    """RGB-only multi-task model: segmentation + cavity depth + dimensions."""

    def __init__(self, cfg):
        super().__init__()
        mcfg = cfg["model"]
        self.backbone = MobileNetV3Backbone(mcfg["backbone"],
                                            mcfg.get("pretrained", True))
        self.fpn = FPN(self.backbone.out_channels)

        dh = self.fpn.out_ch
        self.seg_head = nn.Sequential(ConvBnReLU(dh, 32, 3, 1),
                                      nn.Conv2d(32, 1, 1))
        self.depth_head = nn.Sequential(ConvBnReLU(dh, 32, 3, 1),
                                        nn.Conv2d(32, 1, 1), nn.Sigmoid())
        self.depth_clip = float(cfg["data"]["depth_clip_m"])

        # Stage 2.1: dense absolute metric depth head (metres, sigmoid-scaled).
        self.abs_enabled = bool(cfg["model"].get("abs_depth_head", True))
        if self.abs_enabled:
            self.abs_head = nn.Sequential(ConvBnReLU(dh, 32, 3, 1),
                                          nn.Conv2d(32, 1, 1), nn.Sigmoid())
        self.abs_depth_max = float(cfg["data"]["abs_depth_max_m"])

        n_dim = len(mcfg["dims"]) + len(mcfg["dims_aux"])
        in_feats = dh * 3
        self.dim_head = nn.Sequential(
            nn.Linear(in_feats, 128), nn.ReLU(inplace=True),
            nn.Dropout(0.2), nn.Linear(128, n_dim))
        self.vol_head = nn.Sequential(
            nn.Linear(in_feats, 128), nn.ReLU(inplace=True),
            nn.Dropout(0.2), nn.Linear(128, 1))

    def _pool_features(self, p1, pcoarse, attn):
        """Mask-attention weighted pooling + global pooling of two levels."""
        b = attn.size(0)
        ap = attn.reshape(b, -1).sum(dim=1, keepdim=True) + 1e-5
        attn_feat = (p1 * attn).sum(dim=(2, 3)) / ap
        glob1 = p1.mean(dim=(2, 3))
        glob4 = pcoarse.mean(dim=(2, 3))
        return torch.cat([attn_feat, glob1, glob4], dim=1)

    def forward(self, x):
        feats = self.backbone(x)
        p1, pcoarse = self.fpn(feats)
        h, w = x.shape[2], x.shape[3]

        seg_s2 = self.seg_head(p1)
        seg = F.interpolate(seg_s2, size=(h, w), mode="bilinear",
                            align_corners=False)

        depth_s2 = self.depth_head(p1)
        depth = F.interpolate(depth_s2, size=(h, w), mode="bilinear",
                              align_corners=False) * self.depth_clip

        abs_s2 = self.abs_head(p1) if self.abs_enabled else None
        if self.abs_enabled:
            abs_depth = F.interpolate(abs_s2, size=(h, w), mode="bilinear",
                                      align_corners=False) * self.abs_depth_max

        attn = torch.sigmoid(seg_s2.detach())          # stop-grad attention
        pool = self._pool_features(p1, pcoarse, attn)
        dims = self.dim_head(pool)                     # normalized units
        vol = self.vol_head(pool).squeeze(-1)          # normalized units
        out = {"seg": seg, "depth": depth, "dims": dims, "volume": vol}
        if self.abs_enabled:
            out["abs_depth"] = abs_depth
        return out

    def remove_abs_head(self):
        """Drop the absolute-depth head (for legacy Stage-2.0 checkpoints)."""
        if hasattr(self, "abs_head"):
            del self.abs_head
        self.abs_enabled = False

    def count_params(self):
        return sum(p.numel() for p in self.parameters())


def build_model(cfg):
    return MultiTaskNet(cfg)


def model_size_bytes(model):
    return sum(p.numel() * p.element_size() for p in model.parameters())