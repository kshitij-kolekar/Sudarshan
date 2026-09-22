# RGB-Only Multi-Task Pothole Model

Stage-2 model for the Drone Infrastructure Inspector pipeline.
It takes **only an RGB image** and outputs:

1. a binary pothole segmentation mask,
2. a monocular metric **cavity-depth** map (metres),
3. physical **length, width, area, mean depth, p90 depth**, a predicted
   **road-plane distance** (scene scale), and a **geometry-derived volume**
   (plus an auxiliary direct volume head).

The GT depth maps (`targets_v2/*_cavity_depth.npy` and the raw
`depths/{split}/*.npy` absolute maps in Stage 2.1) are **supervision targets**
only. They are never a model input at inference.

## Stage 2.1 — dense absolute metric depth head

`config.yaml: model.abs_depth_head: true` adds a dense absolute-depth head
(predicted in metres, `sigmoid * abs_depth_max_m`, supervised on the raw
cleaned depth maps at `[0.05, 5.0] m` valid range). `geometry.py` gained a
plane-fit path (`geometry_from_abs_depth`) that fits the road plane from
predicted depth and computes length/width/area/cavity/volume.

**Result (full evaluation in `../STAGE2_1_DENSE_DEPTH_REPORT.md`):** the dense
head learns abs depth to ~19-20 cm MAE (~20 % MAPE, bands: pothole 19.3 cm,
road 20.1 cm, near 13.5 cm, far 29.0 cm) but the **fitted** plane distance
(0.168-0.175 m) does **not** beat Model A's scalar head (0.164 m), and
plane-fit volume/geometry are worse (MAE 6.7-9.5 L vs 3.8 L). **Model A
(`checkpoints/stage2_modelA_best.pt`) remains the better geometry source.**
`test.py --ablate` reproduces the comparison; panels in `outputs/panel_vis_stage21/`.

## Architecture

```
RGB (512x384)
  -> MobileNetV3-Small encoder (ImageNet-pretrained, torchvision)
  -> lightweight FPN decoder (stride-2 branch, 64 ch)
       |-> Segmentation head   (BCE + Dice, full-res logits)
       |-> Depth head          (scaled sigmoid, 0..0.30 m cavity)
       |-> Abs-depth head      (dense metric depth, 0..6 m; Stage 2.1)
       |-> Dimension head      (mask-attention pooled MLP, normalized targets)
       |-> Volume head         (auxiliary direct regression)
```

Choice rationale: MobileNetV3-Small is small enough for an RTX 3050 4GB and in
the Jetson-Nano class; the FPN keeps a stride-2 branch so pothole boundaries are
usable; the dimension head is mask-focused via attention pooling.

Pretrained weights source: `torchvision.models.MobileNet_V3_Small_Weights.IMAGENET1K_V1`
(if unavailable, training falls back to random init and prints a warning).

## Data / split

Fixed split, never reshuffled: **train 781 / val 97 / test 99** (valid rows:
778 / 96 / 99). Only `valid == true` rows from `dimension_targets_v2.csv`.
Normalization statistics are computed on the **train split only** and stored in
the checkpoint.

- image: `images/{split}/*.jpg`
- GT mask: `targets_v2/{split}/*_mask.png`
- GT cavity depth: `targets_v2/{split}/*_cavity_depth.npy`
- scene scale: `targets_v2/plane_dist_v2.csv` (road-plane distance, metres;
  derived once from raw depth - cavity, no plane fitting)
- physical targets: `dimension_targets_v2.csv`

Depth loss validity: only pixels inside the GT mask **and** above the 3 mm noise
floor. Background / invalid pixels are ignored.

## Losses

```
L_total = lambda_seg * (BCE + Dice)
        + lambda_depth * SmoothL1(depth, only-valid px)
        + lambda_dim   * SmoothL1(normalized dims)
        + lambda_volume* SmoothL1(normalized volume)   # auxiliary
```

All lambdas are configurable in `config.yaml`; each component is logged
separately.

## Volume is geometric, not a regression

Predicted volume reported for evaluation/inference comes from the geometry
module:

```
volume = sum_i( cavity_depth_i * pixel_area_i )
pixel_area_i = z_plane^2 * |rd_i| / (fx * fy)     (fronto-parallel assumption)
```

where `z_plane` is the **predicted road-plane distance** (~metres), NOT the
cavity depth (~cm). The cavity depth supplies the depression; the plane distance
supplies the metric scene scale. Omitting `z_plane` (using the cavity depth
instead) makes areas/volumes ~1000x too small.

The direct volume head is auxiliary only and is compared against the
geometry-derived value.

## Scientific limitations (do not overstate)

- Physical targets are **geometry-derived supervision** from GT mask + GT depth
  + camera geometry - not manually measured ground truth.
- Intrinsics are provisional Intel RealSense D415 defaults
  (`fx=fy=597.5, cx=319.5, cy=239.5` at 640x480); the PothRGBD paper does not
  publish per-device calibration. All length/area/volume outputs are therefore
  **calibration-dependent metric estimates**, not survey-grade.
- Depth units assumed millimetres (evidence-based; see Stage-1 report).

## Domain shift (documented, not hidden)

PothRGBD was captured with an Intel RealSense D415-type setup. Drone imagery may
differ in camera height, viewpoint, focal length, lighting, motion blur, and
road appearance, causing domain shift. The architecture is plain image-in /
targets-out so future drone RGB data can be used for fine-tuning with the same
pipeline.

## Usage

```bash
# train (run from this folder)
python train.py
python train.py --epochs 90
python train.py --limit 24 --epochs 3        # smoke test

# validation / test (RGB-only)
python validate.py --checkpoint checkpoints/best.pt
python test.py --checkpoint checkpoints/best.pt --save

# RGB-only inference on any image
python inference.py --image D:\path\img.jpg --out outputs\annotated.jpg
```

`workers=0` is used by default (Windows DataLoader stability). Mixed precision
is enabled when `train.amp: true` and CUDA is available.

## Files

| file | role |
|---|---|
| `config.yaml` | all hyper-parameters and paths |
| `utils.py` | config, metrics, normalization stats, checkpoints |
| `dataset.py` | synchronized image/mask/depth loading + augmentation |
| `model.py` | MobileNetV3-Small + FPN + multi-task heads |
| `losses.py` | BCE+Dice, masked SmoothL1 depth, dim/volume losses |
| `geometry.py` | predicted mask+plane+depth -> physical metrics |
| `prepare_plane_distance.py` | derive `targets_v2/plane_dist_v2.csv` (one-off) |
| `train.py` | training loop, checkpoints, logging |
| `validate.py` | validation metrics |
| `test.py` | RGB-only final test + baseline comparison |
| `inference.py` | single-image RGB-only demo |
| `checkpoints/` | `best.pt`, `last.pt` |
| `outputs/` | logs, metadata, test visuals |
