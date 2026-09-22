# Physical Target Generation (v2) — Final Report

Generated: 2026-09-18
Dataset root: `D:\drone\POTHOLE_TRAINING_DATASET`
Reference paper: Yurdakul & Tasdemir, *An Enhanced YOLOv8 Model for Real-Time and Accurate
Pothole Detection and Measurement*, arXiv:2505.04207 (PothRGBD, captured with Intel RealSense D415).

---

## 1. Existing files and scripts inspected, and their role

| File | Role / conclusion |
|---|---|
| `generate_pothole_physical_targets.py` | Old target-generation script that produced `dimension_targets.csv`. **Two root-cause bugs found** (see section 7): inverted cavity-sign convention plus inconsistent area/volume definitions. The module executes the whole pipeline at import time and cannot be imported safely, so v2 reimplements it independently. |
| `dimension_targets.csv` | Old output: OK 542 / FAILED_GEOMETRY 435; volume inconsistent with area x mean depth (typical 1e-5 m³ vs 0.0009 m³). Values are not trustworthy. **Not modified.** |
| `depth_verification.csv` | Depth-quality metadata (uint16, shape (480,640), 10 files contain 65535, 248 files max>5000, median_positive 279–3118). |
| `dataset_report.csv` / `unmatched_images.csv` | Produced by the public-dataset split script; describe key mapping and the 781/97/99 split. |
| `measurement_validation_v3.py`, `verify_pothole_depth_dataset.py` | Old validation scripts; use the same (old, sign-broken) conventions. Reference only. |
| `tests/*`, `depth_diagnostic.py`, `pothole_volume_test*.py` | Old geometry/volume test scripts based on the buggy sign convention; limited value. |
| `prepare_pothole_dataset.py` (in public dataset) | Data-prep script (split 781/97/99, key normalization). |
| Temp diagnostics (`C:\Users\DELL\AppData\Local\Temp\opencode\diag_planes.py`, `diag_old2.py`) | Reproduced and located the old sign bug; fitted correct planes for 60 samples (all pothole regions on the far side). |

**On Phase-2 3D ground truth**: this dataset has **no** independent second-stage 3D-scan ground truth;
physical quantities can only be derived from RGB + label + depth. That is the fundamental constraint of this rebuild.

## 2. Files modified / created

| File | Description |
|---|---|
| `generate_pothole_physical_targets_v2.py` | **New.** Main pipeline: depth cleaning → GT-mask rasterization → RANSAC road plane → cavity depth → length/width/area/depth/volume → sanity gates → CSV + per-sample artifacts. All configuration in a documented header block. |
| `dimension_targets_v2.csv` | **New.** Supervision table for 973 valid samples (includes all required columns). |
| `targets_v2/{train,val,test}/…_mask.png`, `…_cavity_depth.npy` | **New.** 973x (mask + cavity-depth map in metres). |
| `target_validation/` (27 panels) | **New.** Phase 13 visualization: each panel = RGB+GT mask / raw depth (pseudo-color) / cavity depth (pseudo-color) / measurement text. Includes largest, smallest, deepest, shallowest, and the 4 failed samples. |
| `target_statistics.txt` | **New.** Phase 14 dataset-level statistics. |
| `summarize_targets_v2.py`, `visualize_targets_v2.py` | **New.** Reproducible stats and visualization scripts. |
| `dimension_targets.csv`, `targets/` (old artifacts) | **Not modified**, kept for reference. |

## 3. Dataset scale and structure

- Images: `images/train 781`, `val 97`, `test 99` (977 total).
- Labels: YOLO segmentation polygons (normalized coords, class 0 = Potholes), `labels/{split}/{stem}.txt`.
- Depth: `depths/{split}/{stem}.npy`, uint16, (480,640), units mm (see section 4).
- Triplets complete (image/label/depth 1:1:1); no sample lacks depth.
- No second-stage 3D-scan ground truth exists (see note in section 1); all targets are derived from RGB + GT label + depth.

## 4. Depth / physical-conversion assumptions (explicit: evidence-backed, not a published fact)

- **Unit assumption = millimetres (0.001 m per count)**, evidence-backed rather than published:
  1. RealSense D400-family depth frames default to millimetres (depth_scale = 0.001);
  2. Road-surface medians 279–3118 (dataset-wide median ~850). Interpreted as mm, that places the camera ~0.85 m above the road, consistent with the handheld collection rig; interpreted as 0.1 mm the camera would sit 8–9 m high, which is implausible;
  3. Cavity depths relative to the fitted plane: median ~2.5 cm, p90 median ~3.7 cm, consistent with the paper's reported range (~4–6 cm) and depth accuracy (±0.24 cm).
- **Uncertainty (documented in config header and statistics file)**: the paper does not publish the per-device depth scale. If the true scale differs, every metric scales linearly (length, area quadratically); conclusions unchanged. A single constant `DEPTH_SCALE_TO_METERS` makes this easy to re-derive later.
- **Camera intrinsics (provisional)**: `fx=fy=597.5, cx=319.5, cy=239.5` (D415 defaults, consistent with existing project code); **calibration not published**. These imply HFOV 56.3°, VFOV 43.8°, slightly narrower than the D415 datasheet depth FOV (65°x40°). Therefore **length/area-type metrics are calibration-dependent, not survey-grade**; depth and volume are far less sensitive to focal-length error.

## 5. Road-plane estimation (RANSAC)

- Road candidates: valid-depth points inside the pothole bbox expanded by 180 px, with the GT mask dilated (41x41 kernel) excluded; falls back to the full image if the window is too small; outer 8 px edge cropped.
- Depth cleaning: 0 / 65535 / non-finite / <0.10 m / >3.0 m treated as invalid (<0.10 m below D415 reliable min-Z; >3.0 m can only be non-road background).
- RANSAC: 400 iterations, 3-point samples, 2 cm threshold; sampled road points capped at 25000.
- Plane refinement: 2 SVD least-squares re-estimations on inliers.
- **Normal-orientation convention (the core fix)**: normal forced to `n_z > 0` (away from the camera, into the scene). For on-plane points, `n·p + d = 0`; the positive side is the side farther from the camera = the pothole-cavity side. Cavity depth = `max(signed, 0)`. The old script used `max(-signed, 0)`, measuring the camera-side offset — so the 542 "OK" samples measured the near-side bulge rather than cavity depth, and the 435 FAILED ones (pothole genuinely on the far side) were clamped to zero.
- Acceptance: inliers >= 400, inlier ratio >= 0.40, |n_z| >= 0.35; otherwise `plane_fit_failed`.
- Fit quality (valid samples): inlier ratio min 0.579, median 1.000; median inliers 25000.

In-plane distances are the per-point absolute `|p·n + d|`; GT-mask pixels are kept strictly separated from road candidates via the dilated exclusion.

## 6. Length / width / area / depth / volume computation

- **Per-pixel plane footprint (projected area, incidence-corrected)**:
  `pixel_area = λ²·|rd| / (fx·fy·|n·rd|)` with `rd=((u-cx)/fx,(v-cy)/fy,1)` and `λ = -d/(n·rd)` the ray/plane intersection parameter. `area_m2 = Σ pixel_area` over valid-depth mask pixels.
- **Length / width (PCA + robust quantiles)**: valid mask points projected onto the plane → principal axis; length = 2nd-to-98th percentile span on that axis, width = same on the perpendicular; `length >= width` enforced. No raw x/y extreme-range measurement, to resist single-point noise.
- **Depth statistics**: computed only over positive-cavity pixels (`cavity = max(signed, 0) > 3 mm noise floor`, far side): mean/median/p90/p99/max.
- **Volume**: `volume_m3 = Σ cavity_i · pixel_area_i` (cavity x footprint integral over positive-cavity pixels).
- **Self-consistency**: `volume/(area x mean_depth)` = cavity fill fraction (expected <= 1). Valid samples: p05/median/p95 = 0.80/0.96/1.01, tight and consistent — the old "volume inconsistency" came from the sign bug plus differing area/volume scopes.

## 7. Invalid-sample gating (sanity checks) and final counts

Trigger conditions (all configurable in the header):
- `depth_outlier` (2 samples): pixels above the 30 cm hard plausibility cap exceed 30% of positive-cavity pixels, or mean/p90/p99/max depth > 0.5 m. Both rejected samples show ±12–20 cm scale signed anomalies in the mask region — genuine depth artifacts.
- `plane_fit_failed` (2 samples): insufficient inliers / low ratio / |n_z| < 0.35 (fits an oblique wall / strongly curved surface).
- Other gates (not triggered by this dataset): `missing_depth / insufficient_road_points / insufficient_pothole_points / invalid_polygon / insufficient_cavity_depth / pothole_depth_coverage_low / non_positive_area / non_positive_volume / non_positive_dimension / dimensions_out_of_range / suspicious_volume`.
- Also enforced: min mask 20 px, min valid depth in mask 30 px, min positive-cavity pixels 20, `pothole_depth_coverage >= 0.05`; length/width <= 10 m, area <= 50 m², volume <= 10 m³.

**Final: 973 valid / 977 (99.6%)**; train 778/781, val 96/97, test 99/99. The 4 rejected samples keep their rows with `valid=false` and a `failure_reason`; no rows deleted.

## 8. Final measurement ranges / typical values (valid samples)

| Metric | min | p25 | median | p75 | max |
|---|---|---|---|---|---|
| length (m) | 0.076 | 0.345 | 0.513 | 0.735 | 2.263 |
| width (m) | 0.051 | 0.208 | 0.306 | 0.437 | 1.553 |
| area (m²) | 0.004 | 0.071 | 0.137 | 0.276 | 1.990 |
| mean_depth (cm) | 0.47 | 1.78 | 2.46 | 3.38 | 9.23 |
| p90_depth (cm) | 0.63 | 2.61 | 3.71 | 5.12 | 16.14 |
| max_depth (clipped 0.30 m) (cm) | 0.75 | 3.17 | 4.41 | 6.20 | 30.0 (p95 ≈ 9.46) |
| volume (L) | 0.02 | 1.19 | 3.19 | 8.28 | 77.08 |

Typical pothole: ~0.51 m long x 0.31 m wide x 0.137 m² x 2.46 cm mean depth ≈ 3.2 L.
The old median volume ≈ 1e-5 m³ artifact is gone: `volume/(area x mean_depth)` median is now 0.96.

## 9. Suitability for training + suggested model output representation

- **Suitable for training**: 973 valid samples across train/val/test, self-consistent metrics (volume consistent, planes fit cleanly, cavity distribution within the paper's range), usable as physical supervision for a model that takes **RGB only**.
- Volume is not recommended as a primary regression target (noise amplification, insensitive for small potholes). Recommended representations:
  1. **Multi-task regression**: length, width, area, depth (mean/max) as free quantities; volume as an auxiliary/consistency term;
  2. **Two-stage**: segmentation (or keypoints) → compute first-order physical quantities from the predicted mask (area, aspect ratio), avoiding numerically ill-conditioned end-to-end regression of tiny volumes;
  3. Represent depth with both `mean_depth` and `p90_depth` for robustness.
- **Data-leakage rule (Phase 15)**: every target derives only from that sample's own RGB + GT label + depth; no cross-sample / cross-split information; the split is unchanged (train samples only for training, val for validation, test only for final evaluation); no model was trained; the test set did not feed any fitting besides well-documented threshold choices. Per-sample artifacts (mask + cavity map) are kept in `targets_v2/` for future "predict-the-depth-map consistency" training.

## 10. Exact file list (created or modified)

Created (this report; all under `D:\drone\POTHOLE_TRAINING_DATASET\`):
1. `generate_pothole_physical_targets_v2.py` (main pipeline)
2. `dimension_targets_v2.csv` (973 valid + 4 failed rows)
3. `target_statistics.txt`
4. `visualize_targets_v2.py`
5. `summarize_targets_v2.py`
6. `target_validation/` (27 panel PNGs)
7. `targets_v2/train|val|test/` (973 x 2 artifacts: `*_mask.png`, `*_cavity_depth.npy`)

Not modified: `dimension_targets.csv`, `targets/`, any application code, any model or training script; no model trained.

---

### Key residual caveats
- Intrinsics are D415 default approximations, **not published calibration** → treat length/area-type values as relative/calibration-consistent.
- Depth units "mm" are a strong inference, not stated verbatim in the paper → if the true scale differs, all metrics scale linearly.