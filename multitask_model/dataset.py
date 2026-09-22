"""Dataset: RGB image + GT segmentation mask + GT cavity-depth + GT dims.

The 640x480 input is resized (aspect-preserving) to the configured [W, H].
All spatial transforms (resize / affine / flip) are applied IDENTICALLY to
image, mask and depth so metric relationships are preserved.  Intensity
augmentations (brightness/contrast/saturation/blur/noise) affect the RGB
image ONLY.

The GT cavity-depth map (targets_v2/*_cavity_depth.npy) is used as depth
supervision.  Validity for the depth loss:
    - only pixels WITHIN the GT pothole mask
    - and with cavity depth above the configured noise floor (3 mm)
Anything else is background / invalid and is IGNORED by the depth loss.
"""
from __future__ import annotations

import random
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from torchvision.transforms import functional as F

import utils as U

IMG_MEAN = torch.tensor([0.485, 0.456, 0.406])
IMG_STD = torch.tensor([0.229, 0.224, 0.225])


class MultiTaskPotholeDataset(Dataset):
    def __init__(self, cfg, split: str, use_aug: bool = True):
        self.cfg = cfg
        self.split = split
        self.use_aug = use_aug
        self.root = Path(cfg["data"]["root"])
        self.W, self.H = cfg["data"]["image_size"]
        self.noise_floor = cfg["data"]["depth_noise_floor_m"]
        self.depth_clip = cfg["data"]["depth_clip_m"]

        df = U.load_targets_df(self.root)
        df = df[df["valid"] == True]                       # noqa: E712
        df = df[df["split"] == split] if split != "full" else df
        df = df.sort_values("image").reset_index(drop=True)

        self.images = df["image"].tolist()
        self.masks = df["mask_path"].tolist()
        self.depth_targets = df["depth_target_path"].tolist()
        self.raw_depth_paths = df["depth"].tolist()

        self.abs_depth_min, self.abs_depth_max = \
            cfg["data"]["abs_depth_valid_range_m"]
        self.abs_depth_clamp = float(cfg["data"]["abs_depth_max_m"])

        dim_cols = list(cfg["model"]["dims"])
        aux_cols = list(cfg["model"]["dims_aux"])
        self.dim_cols = dim_cols
        self.aux_cols = aux_cols
        self.dim_values = df[dim_cols + aux_cols].to_numpy(np.float64)
        self.volume_values = df["volume_m3"].to_numpy(np.float64)

        self.cfg_dim_stats = None   # set by caller (train-split statistics)
        self.cfg_vol_stats = None

    def __len__(self):
        return len(self.images)

    def _load(self, i):
        img = cv2.imread(str(self.root / self.images[i]))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mask = cv2.imread(str(self.root / self.masks[i]), cv2.IMREAD_GRAYSCALE)
        mask = (mask > 127).astype(np.uint8)
        depth = np.load(self.root / self.depth_targets[i]).astype(np.float32)
        abs_depth = np.load(self.root / self.raw_depth_paths[i]).astype(np.float32)
        abs_depth = abs_depth / 1000.0                       # mm -> m
        return img, mask, depth, abs_depth

    def _to_tensors(self, img, mask, depth, abs_depth):
        img_t = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
        mask_t = torch.from_numpy(mask).float().unsqueeze(0)
        depth_t = torch.from_numpy(np.clip(depth, 0.0, self.depth_clip)).float().unsqueeze(0)
        abs_t = torch.from_numpy(abs_depth).float().unsqueeze(0)
        return img_t, mask_t, depth_t, abs_t

    def _resize(self, img, mask, depth, abs_depth):
        img = F.resize(img, (self.H, self.W), F.InterpolationMode.BILINEAR)
        mask = F.resize(mask, (self.H, self.W), F.InterpolationMode.NEAREST)
        depth = F.resize(depth, (self.H, self.W), F.InterpolationMode.NEAREST)
        abs_depth = F.resize(abs_depth, (self.H, self.W),
                             F.InterpolationMode.NEAREST)
        return img, mask, depth, abs_depth

    def _rand_affine(self, img, mask, depth, abs_depth):
        aug = self.cfg["augmentation"]
        angle = random.uniform(-aug["rot_deg"], aug["rot_deg"])
        s0, s1 = aug["scale"]
        scale = random.uniform(s0, s1)
        tx = random.uniform(-aug["translate"], aug["translate"]) * self.W
        ty = random.uniform(-aug["translate"], aug["translate"]) * self.H
        interp = [
            F.InterpolationMode.BILINEAR,
            F.InterpolationMode.NEAREST,
            F.InterpolationMode.NEAREST,
            F.InterpolationMode.NEAREST,
        ]
        outs = []
        for t, itp in zip((img, mask, depth, abs_depth), interp):
            outs.append(F.affine(t, angle=angle, translate=(tx, ty),
                                 scale=scale, shear=0.0, interpolation=itp))
        return outs[0], outs[1], outs[2], outs[3]

    def _intensity(self, img):
        aug = self.cfg["augmentation"]
        img = F.adjust_brightness(img, random.uniform(1 - aug["brightness"],
                                                     1 + aug["brightness"]))
        img = F.adjust_contrast(img, random.uniform(1 - aug["contrast"],
                                                   1 + aug["contrast"]))
        img = F.adjust_saturation(img, random.uniform(1 - aug["saturation"],
                                                     1 + aug["saturation"]))
        if random.random() < aug["blur_p"]:
            k = random.choice([3, 5])
            img = F.gaussian_blur(img, (k, k))
        if random.random() < aug["noise_p"]:
            img = img + torch.randn_like(img) * 0.02
        return img.clamp(0.0, 1.0)

    def __getitem__(self, i):
        img, mask, depth, abs_depth = self._load(i)
        img_t, mask_t, depth_t, abs_t = self._to_tensors(img, mask, depth,
                                                         abs_depth)
        img_t, mask_t, depth_t, abs_t = self._resize(img_t, mask_t, depth_t,
                                                     abs_t)

        if self.use_aug:
            if random.random() < self.cfg["augmentation"]["hflip_p"]:
                img_t = F.hflip(img_t)
                mask_t = F.hflip(mask_t)
                depth_t = F.hflip(depth_t)
                abs_t = F.hflip(abs_t)
            img_t, mask_t, depth_t, abs_t = self._rand_affine(
                img_t, mask_t, depth_t, abs_t)
            img_t = self._intensity(img_t)

        img_t = F.normalize(img_t, list(IMG_MEAN), list(IMG_STD))

        # cavity-depth validity: inside GT mask AND above the noise floor
        valid = (mask_t >= 0.5) & (depth_t > self.noise_floor)

        # absolute-depth validity: inside the documented useful range
        abs_t = abs_t.clamp(0.0, self.abs_depth_clamp)
        valid_abs = ((abs_t >= self.abs_depth_min)
                     & (abs_t <= self.abs_depth_max))

        dims = torch.from_numpy(self.dim_values[i]).float()
        vol = torch.tensor([self.volume_values[i]], dtype=torch.float32)
        return img_t, mask_t, depth_t, valid.float(), dims, vol, abs_t, valid_abs.float()

    # ------------------------------------------------------------------
    def set_dim_stats(self, stats: dict):
        """Apply train-split normalization stats to stored targets."""
        from utils import zscore, zscore1d
        n = self.dim_values.shape[0]
        if n:
            self.dim_values = zscore(self.dim_values, stats["dims"])
            self.volume_values = zscore1d(self.volume_values, stats["volume"])


def build_loaders(cfg, train_stats=None):
    """Create train/val/test loaders with workers from config (0 on Windows)."""
    from torch.utils.data import DataLoader

    tr = MultiTaskPotholeDataset(cfg, "train", use_aug=True)
    assert train_stats is not None, "train-split statistics required"
    tr.set_dim_stats(train_stats)
    va = MultiTaskPotholeDataset(cfg, "val", use_aug=False)
    va.set_dim_stats(train_stats)
    te = MultiTaskPotholeDataset(cfg, "test", use_aug=False)
    te.set_dim_stats(train_stats)

    workers = int(cfg["data"].get("workers", 0))
    make = lambda ds: DataLoader(
        ds, batch_size=int(cfg["train"]["batch_size"]),
        shuffle=(ds.split == "train"), num_workers=workers, drop_last=False,
    )
    return make(tr), make(va), make(te)