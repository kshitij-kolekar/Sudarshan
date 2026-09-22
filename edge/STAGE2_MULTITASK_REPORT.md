# Stage-2 Report — RGB-Only Multi-Task Pothole Model

Status: **training + evaluation complete; STOPPED for user approval.**
No backend / frontend / database / Jetson integration was performed.
No report claims survey-grade accuracy.

---

## 1. What was built

A new, self-contained lightweight multi-task model at
`POTHOLE_TRAINING_DATASET/multitask_model/` that consumes **only an RGB
image** and produces:

| output | head | notes |
|---|---|---|
| pothole segmentation mask | seg head | BCE + Dice, full-resolution logits |
| cavity-depth map (m) | depth head | scaled sigmoid, bounded `[0, 0.30] m` |
| length, width, area, mean depth, p90 depth | dim head | mask-attention pooled |
| road-plane distance (m) = **scene scale** | dim head | new target (see §6) |
| volume (m3) | geometry module | primary; direct head is auxiliary |

The existing YOLOv8n-seg model was **not modified or retrained**
(`runs/segment/runs/pothole_v2/weights/best.pt`).

## 2. Architecture

```
RGB (512x384)
  -> MobileNetV3-Small encoder (ImageNet-pretrained, torchvision)
  -> lightweight 5-level FPN decoder (strides 2/4/8/16/32, 64 ch)
       |-> Segmentation head   (BCE + Dice)
       |-> Depth head          (cavity depth, scaled sigmoid)
       |-> Dimension head      (9 regression outputs, mask-attention pooled)
       |-> Volume head         (auxiliary direct regression)
```

- Parameters: **1.01 M** (4.03 MB fp32) — RTX-3050 / Jetson-Nano class.
- Pretrained source: `MobileNet_V3_Small_Weights.IMAGENET1K_V1`.
- Backbone stage boundaries were verified empirically against the actual
  torchvision feature graph.

## 3. Data and split

- Fixed split unchanged: **train 781 / val 97 / test 99** (valid rows
  778 / 96 / 99); only `valid == true` rows are used.
- Depth supervision: `targets_v2/{split}/*_cavity_depth.npy` (used only as a
  target; never a model input at inference).
- Depth-loss validity: pixels inside the GT mask **and** above the 3 mm noise
  floor.
- Normalization statistics (all 9 regression targets) computed on the
  **train split only** and stored in the checkpoint.

## 4. Training

- Input 512x384 (aspect-preserving 0.8x of 640x480 so metric geometry is
  consistent), AMP fp16, batch 16, AdamW, lr 1e-3, 2-epoch warmup + cosine,
  grad-clip 5.0, `workers=0`.
- Max 60 epochs, early-stop patience 15 → **stopped at epoch 45**.
- Best **validation seg IoU = 0.8120**.
- Checkpoints `checkpoints/best.pt` / `last.pt` include state_dict, optimizer,
  epoch, best score, target stats, full config and architecture metadata.

## 5. Final TEST metrics (RGB-only, n = 99)

Segmentation
- IoU 0.7912, Dice 0.8834, Precision 0.892, Recall 0.875

Depth (on GT-valid pixels)
- MAE **1.17 cm**, RMSE 1.55 cm, median abs error 0.90 cm

Dimension regression head (MAE / MAPE)
- length 0.187 m / 31.5 %
- width 0.083 m / 26.9 %
- area 0.1095 m2 / 57.9 %
- road-plane distance 0.164 m / **19.5 %**
- mean depth 0.63 cm, p90 depth 0.94 cm

Geometry-derived dimensions (predicted mask + plane + cavity depth, MAE)
- length 0.165 m, width 0.082 m, area 0.0983 m2
- mean depth 0.69 cm, p90 depth 1.10 cm

Volume
- **geometry-derived: MAE 3.780 L, MAPE 88.9 %**
- direct regression head (auxiliary): MAE 7.807 L

### Baseline cross-reference (NOT directly comparable)
YOLOv8n-seg (existing): maskP 0.912, maskR 0.944, mask-mAP50 0.970,
mask-mAP50-95 0.643. Those are detection/generalization mAP values; ours are
spatial per-pixel IoU/Dice at threshold 0.5. Shown for reference only.

## 6. Bug found and fixed during Stage 2

The first trained model produced near-zero metric areas/volumes. Root cause:
`geometry.py` used the **cavity depth (~cm)** as the pixel-footprint scene
scale, but Stage-1 area/volume use the **camera-to-road-plane distance
(~1 m)**:

```
wrong:   pixel_area = cavity_depth^2 * |rd| / (fx*fy)      -> ~1000x too small
correct: pixel_area = z_plane^2     * |rd| / (fx*fy)
```

Fix: the model now additionally predicts a per-sample **road-plane distance**
(`plane_dist_m`). It is derived once as `mean(Z_raw - cavity)` over the mask
(`prepare_plane_distance.py` → `targets_v2/plane_dist_v2.csv`, 973 rows),
supervised by the regression head, and consumed by `geometry.py`.
Length/width are now computed from a metric road-plane point cloud
(`X = du*z_plane`, `Y = dv*z_plane`), not from cavity-depth coordinates.

Validation of the corrected geometry against Stage-1 targets (using GT
mask + GT cavity + GT plane distance, test split): ratio of new/Stage-1 values
— length 0.97, width 0.94, area 0.92, volume 0.91. The residual ~10 % is the
cost of using a single scalar plane distance instead of a per-pixel fitted
plane.

Effect on volume (test, RGB-only): MAE **8.21 L → 3.78 L**, MAPE
**99.8 % → 88.9 %**.

## 7. How to run

```bash
# from multitask_model/
python prepare_plane_distance.py     # one-off (already run)
python train.py                      # full training
python test.py --checkpoint checkpoints/best.pt --save
python inference.py --image <rgb.jpg> --out outputs/annotated.png
```

## 8. Scientific limitations (do not overstate)

- All physical values are **model predictions** and **calibration-dependent
  metric estimates**, NOT survey-grade ground truth.
- Physical targets are geometry-derived supervision from GT mask + GT depth +
  camera geometry, not manually measured values.
- Intrinsics are provisional D415 defaults (`fx=fy=597.5, cx=319.5, cy=239.5`
  @ 640x480); the PothRGBD paper does not publish per-device calibration.
- Depth units assumed millimetres (evidence-based; see Stage-1 report).
- **Volume remains the weakest metric (MAPE ~89 %).** Main error sources:
  (a) monocular scene-scale error (~20 % MAPE on plane distance, squared into
  area), (b) segmentation-boundary error, (c) cavity-depth error, and (d) a
  fronto-parallel assumption that ignores road-plane tilt. Domain shift vs
  drone imagery is expected and not yet addressed.
- Baseline comparison is cross-reference only; the two metric families are not
  equivalent.

## 9. Recommended next steps (awaiting approval)

1. **Dense road-plane depth head** (per-pixel plane depth supervised by
   `Z_raw - cavity`) instead of a single scalar — expected to remove most of
   the remaining scalarization/scale error and materially improve volume.
2. Predict `log(plane_dist)` and/or up-weight the plane-distance loss.
3. Report per-sample uncertainty and add a confidence/abstain threshold.
4. Only after approval: backend/frontend integration and drone-domain
   fine-tuning.

## 10. Files (Stage-2)

| path | role |
|---|---|
| `multitask_model/config.yaml` | hyper-parameters/paths (dims now 9, includes `plane_dist_m`) |
| `multitask_model/dataset.py` | synced image/mask/depth loading + augmentation |
| `multitask_model/model.py` | MobileNetV3-Small + 5-level FPN + heads |
| `multitask_model/losses.py` | BCE+Dice, masked depth, dim/volume losses |
| `multitask_model/geometry.py` | predicted mask+plane+depth -> metrics |
| `multitask_model/train.py` / `validate.py` / `test.py` / `inference.py` | pipeline |
| `multitask_model/prepare_plane_distance.py` | builds `targets_v2/plane_dist_v2.csv` |
| `targets_v2/plane_dist_v2.csv` | scene-scale target (NEW) |
| `multitask_model/checkpoints/best.pt`, `last.pt` | trained weights |
| `multitask_model/outputs/` | logs, `target_stats.json`, `test_results.*`, `test_vis/` |

## 11. Explicit STOP

Per the Stage-2 instructions, work stops here for review. The existing
YOLOv8n-seg model and the Stage-1 targets/`dimension_targets_v2.csv` are
untouched. Awaiting approval before any further modelling or integration.
