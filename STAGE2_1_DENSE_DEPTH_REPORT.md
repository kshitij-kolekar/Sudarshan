# STAGE 2.1 — Dense Absolute Metric Depth Head (Evaluation & Ablation Report)

**Date:** 2026-09-21 · **Split:** train 778 / val 96 / test 99 (unchanged) · **Input:** RGB-only
**Hardware:** RTX 3050 4GB, CUDA 12.6, torch 2.14.0+cu126 · **Model:** MobileNetV3-Small + FPN, **1.03M params, 4.11 MB fp32**

---

## 1. Overview & goal

Stage 2.0 (Model A) derived physical pothole geometry from a **predictive cavity
head + a scalar road-plane-distance head** (`plane_dist_m`), which supplies the
metric scene scale. Stage 2.1 replaces the scalar scale with a **dense absolute
metric depth head**: the model predicts a per-pixel depth map in metres, a robust
road plane is **fitted from that predicted depth**, and length / width / area /
cavity depth / volume are computed by intersecting the pothole footprint with the
plane.

**Stated success criterion:** *does dense absolute depth reduce plane-distance
error and improve physical geometry/volume over Model A?*

**Short answer: No.** Dense absolute depth is learned (MAE ≈ 19.7–19.9 cm,
MAPE ≈ 18.6–20.5 %) but the fitted road plane is **not** more accurate than the
trained scalar head, and plane-fit volume/cavity are worse than Model A. Details,
numbers and the (technical) reasons are below.

---

## 2. Task & supervision

* Supervision targets (evaluation only — **never model inputs**):
  - `depths/<split>/*.npy` — original cleaned absolute depth, uint16 **mm**, scale 0.001 → metres.
  - `targets_v2/*_cavity_depth.npy` — cavity depth (mm, relative).
  - `targets_v2/*_mask.png` — GT pothole masks.
`dimension_targets_v2.csv` — physical labels (length/width/area/mean/p90/volume + `plane_dist_m` sidecar).
* Absolute-depth validity: exclude 0 / 65535 / non-finite / outside `[0.05, 5.0] m`
  (system-level stats: ~92 % of raw pixels are valid; p1≈0.3 m, p50≈0.85–1.05 m, p99≈2.4–2.5 m; >5 m is noise).
* Depth loss: SmoothL1 on **valid** pixels only + small edge-aware TV term
  (`abs_depth_grad_lambda=0.1`). No per-image normalization; target stays in metres.
* RGB-only inference. GT depth/mask loaded only post-hoc for scoring.

## 3. Method changes (Stage 2.1 vs 2.0)

| Area | Change |
|---|---|
| `model.py` | New dense absolute-depth head: `sigmoid`, scaled by `abs_depth_max_m=6.0`, output at input resolution (bilinear up). 2K extra params. Legacy checkpoints handled via `remove_abs_head()`. |
| `dataset.py` | Loads raw abs depth (`mm→m`), returns **8-tuple**: `(img, mask, cavity, cavity_valid, dims, vol, abs_depth, abs_valid)`. |
| `losses.py` | `abs_depth` loss (SmoothL1 on valid px, `lambda_abs_depth=2.0`) + optional gradient term; `cavity_depth` logged separately from `abs_depth`. |
| `geometry.py` | **Plane-fit path** `geometry_from_abs_depth()`: unproject pred depth → RANSAC road plane (exclude dilated mask, edge crop, out-of-range) → cavity = signed plane distance (pothole side positive), pothole area from per-pixel ray-plane footprints, length/width from PCA of projected footprint, volume = ∫(cavity·dA). Domain guards (plane distance 0.05–10 m, |n·rd|≥0.05, median-λ estimate) fail gracefully instead of emitting absurd numbers. Scalar path kept for Model A. |
| `validate.py / test.py` | Per-sample abs-depth bands (road/pothole, near≤1 m/far>1 m), MAE/RMSE/median/MAPE, fitted-plane distance MAE/MAPE, geo-failure count, `vol/(area·mean_depth)` sanity ratio. `test.py --ablate` runs Model A vs Model B. |
| `visualize_stage2_1.py` | 3×4 panels: RGB(+GT/Pred mask), GT/Pred abs depth, abs error, GT/Pred cavity, road-plane fit, GT/Pred geometry, sanity bars, metrics text. |

## 4. Training configuration & run

`epochs=60, early_stop_patience=15, batch=16, base_lr=1e-3 (cosine, warmup 2), AdamW wd=1e-4,
AMP, cudnn.benchmark, workers=0`. **Early-stopped at epoch 25** (best val seg IoU 0.8018 @ ep10).

Training curves: `outputs/train_curves_stage21.png` · per-epoch log: `outputs/train_log.csv`
(val seg IoU 0.8018 @ ep10; cavity 1.10 cm → 1.04 cm; abs depth 45→19 cm; plane 0.41→0.15 m).
GPU peak ≈ 175 MB allocated.

## 5. Final Model B test metrics (RGB-only, test n=99; checkpoint `checkpoints/best.pt` @ ep10)

| Metric | Value |
|---|---|
| Segmentation IoU / Dice / P / R | 0.7649 / 0.8668 / 0.865 / 0.869 |
| Cavity depth MAE / RMSE / medAbs | 1.22 / 1.61 / 1.00 cm |
| **Absolute depth MAE / RMSE / medAbs / MAPE** | **19.90 / 28.79 / 15.04 cm / 20.5 %** |
| abs-depth MAPE (computed) | 20.5 % |
| Geo failures (plane fit failed / absurd) | 0 / 99 |
| Volume sanity `V/(A·mean_depth)` mean / median | 0.690 / 0.683 |

## 6. Absolute-depth banded analysis (best.pt, test)

| Band | MAE [cm] |
|---|---|
| Road (non-pothole valid px) | 20.11 |
| Pothole px | 19.32 |
| Near (GT ≤ 1 m) | 13.53 |
| Farther (GT > 1 m) | 29.04 |

Road and pothole error are similar (~20 cm); near range is better, far range worse.
Pothole ~19 cm vs pothole size scale ≈ 2.7 cm mean depth means the plane is heavily
noise-limited. `last.pt` (ep25): abs MAE 19.67 cm, RMSE 27.88, MAPE 18.6 % — plateaus, more training does not fix it.

## 7. Ablation — Model A vs Model B (RGB-only, test n=99)

| Metric | Model A (scalar plane, ep-∞ best) | Model B (dense abs-depth) `best.pt` | Model B `last.pt` (ep25) |
|---|---|---|---|
| Seg IoU | **0.7912** | 0.7649 | 0.7687 |
| Seg Dice | **0.8834** | 0.8668 | 0.8692 |
| Cavity MAE [cm] | **1.17** | 1.22 | 1.13 |
| Abs-depth MAE [cm] | — | 19.90 | 19.67 |
| **Plane distance MAE [m]** | **0.164** (scalar head) | 0.175 (fitted) | 0.168 (fitted) |
| Plane distance MAPE [%] | 19.5 | 19.2 | 16.1 |
| Geo length MAE [m] | **0.165** | 0.207 | 0.191 |
| Geo width MAE [m] | **0.082** | 0.125 | 0.096 |
| Geo area MAE [m²] | **0.0983** | 0.1242 | 0.1180 |
| Geo mean/cavity depth MAE [cm] | **0.69** | 5.23 | 5.16 |
| **Geometry volume MAE [L]** | **3.78** | 9.46 | 6.66 |
| Geometry volume MAPE [%] | **88.9** | 287.0 | 188.3 |
| Direct volume reg MAE [L] | 7.81 | 7.85 | 7.13 |
| Model size [M params] | 1.01 | 1.03 | 1.03 |

**Model A wins on 9/10 comparable metrics.** Plane-distance MAE is NOT reduced (0.175/0.168 m vs 0.164 m);
volume MAE is ~1.8–2.5× worse; cavity-from-plane is biased ~2× deep; segmentation slightly worse.

## 8. Baseline (YOLOv8n-seg) cross-reference

YOLO (existing, NOT retrained): maskP 0.912, maskR 0.944, mAP50 0.970, mAP50-95 0.643 —
detection/generalization mAP, not directly comparable to per-pixel IoU/Dice. Shown for reference only.

## 9. Plane-fit geometry analysis (why it underperforms)

* **Cavity bias:** median absolute-depth error ~15 cm vs 5 cm RANSAC tolerance. The fitted
  plane sits "under" an asymmetric noisy point cloud; the pothole's far edge reads proportionally
  deeper → **mean cavity 5.2 cm vs GT ≈ 2.7 cm** (same sign for both best/last). This inflates volume.
* **Area inflation:** depth noise + predicted-mask boundary → footprint 0.124 m² vs GT 0.098 m².
* **Scale contention:** the dense head must solve a harder per-pixel problem over a 1 m scene
  (~19–20 cm MAE ≈ 20 % total error, far band 29 cm). The scalar head is trained *directly* on the
  mean plane distance — essentially free. Dense depth would need to be <~5 cm near the road to win.
* **Capacity:** 1.03 M params shared across seg+abs+cavity+dims; a larger/DFA backbone or
  explicit plane-consistency loss (plane + depth joint supervision) would be the natural fix.

## 10. Volume sanity check

Model A sanity ratio ≈ 0.997 (volume ≈ area·mean — its supervised cavity is uniform, so geometry
degenerates to that product). Model B ≈ 0.69 — closer to a physical bowl shape, but with biased
cavity and area → higher absolute error. No sample produced an absurd volume
(all 99 plane fits passed the 0.05–10 m guard). Failures aren't hidden: `geo_failure_count` and
sanity ratios are logged per epoch in `outputs/train_log.csv`.

## 11. Verdict on the success criterion

**Dense absolute depth does NOT reduce plane-distance error and does NOT improve volume/geometry
for this lightweight RGB-only model.** The per-pixel depth error (~20 cm) is too large relative to
both the road-plane tolerance and the pothole depth scale (~3 cm). The previous scalar plane
distance remains the better scene-scale source on this dataset/architecture. Model B's one genuine
gain is a more physical cavity *shape* (sanity ≈ 0.69), but absolute volume accuracy is worse.

## 12. Limitations

* Provisional D415 intrinsics (fx=fy=597.5, cxcy=319.5/239.5 @640×480), not per-scene calibrated.
* 1.03 M-param capacity was intentionally kept (4 GB GPU); absolute-depth quality is capacity-limited.
* Early stop keys on seg IoU, not depth; `last.pt` was ~equal on abs depth (19.7 cm).
* Depth targets are the original cleaned maps (subjective/dataset-specific); see Stage-2 report.

## 13. Visualization

`outputs/panel_vis_stage21/` — 20 test-sample panels (RGB+GT/pred mask, GT/pred abs depth,
abs error, GT/pred cavity, road-plane fit overlay, GT/pred geometry bars, metrics text), plus
`outputs/test_vis_{modelA,modelB}` from `test.py --save`, and training curves (section 4).

## 14. Reproducibility

```
python train.py                        # Model B (best.pt / last.pt) — early-stopped ep25
python test.py --ablate                # Model A vs Model B on test
python test.py --checkpoint checkpoints/last.pt --split test
python visualize_stage2_1.py --split test --count 20 --out outputs/panel_vis_stage21
python inference.py --image <path>     # RGB-only demo (plane-fit path auto-selected)
```
Config: `multitask_model/config.yaml` (`data.abs_depth_*`, `loss.lambda_abs_depth`, `geometry.*`).
Checkpoints: `checkpoints/stage2_modelA_best.pt` (A), `checkpoints/best.pt` (B best),
`checkpoints/last.pt` (B last).

## 15. Recommendation / STOP

Keep **Model A** as the deployed geometry source (better plane distance, area, cavity and volume).
Stage 2.1 demonstrated (and quantified) that a dense absolute-depth head does not pay off at this
capacity; if scene-scale accuracy is a priority, the next step would be a larger depth-competent
backbone + plane-consistency supervision — out of scope here. **Stopping before any backend /
frontend / database / Jetson integration, per instructions.**