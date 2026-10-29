**Current project context (2026-10-29):** [Canonical B0–B10 and legacy crosswalk](VERSION_MAPPING.md) govern project labels. B0 preserves unchanged RTXPT1.9 original defaults and pins. Legacy migration `7010bb4` is not canonical B1; its native/DI/DI+GI configurations map to B3/B4/B5. The PT-only/DI+PT foundation maps to B6/B7; old-B2 checkpoint `de9fe651` is B7. The GI-off old-B3 pilot is a B7 limited-feature ablation, not B9. B8 requires valid GI/PT sharing; B9/B10 depend on it, and full remaining PT++ work belongs to B10. The SDK stays reference-only. Preserve legacy measurements/IDs; historical original-scene DI+GI rows map to B2/B5 with cap coverage unverified.

# Validation and benchmark plan

## Current verification boundary

The legacy migration source7010bb4 changed the runtime dependency and four host/UI compatibility files; its Release build and the preserved RTXPT1.9 build succeeded. The [retained legacy B1 report](B1_RESULTS.md) contains historical DI+GI observations now mapped to canonical B2/B5. Subsequent [B7 opaque evidence](B2_RESULTS.md) and [GI-off limited-feature ablations](B3_RESULTS.md) are separate scoped GPU checkpoints, not full-paper or original-scene validation. Structural receipts, builds, activation diagnostics and estimator/quality evidence remain distinct.

## Experiment contract

Each capture records repository + child SHAs, dirty state, executable/shader hashes, scene/assets/license/version, camera path/shutter/aperture, render/output resolution, bounce cap, roulette policy, sample counts, seed, warmup/capture frames, GPU/VRAM, CPU, driver, OS, backend, denoiser/DLSS version and all approximation switches. Keep raw HDR radiance, guides, masks and complete timing/memory counters. Repeat with independent seeds; choose repeat count from pilot variability rather than presenting a single fortunate run.

Reference images must use independent high-spp sampling at matching transport/camera/bounce settings with cache termination, clamping, denoising and reuse biases disabled. Check reference convergence and uncertainty. Use exact finite-domain tests for estimator accounting and independent geometric cases for Jacobians; matching another renderer image alone cannot validate a faulty common estimator.

## Metrics

Report linear-HDR relative error with declared denominator safeguards, SMAPE and a perceptual metric such as FLIP under fixed display/exposure. Include temporal covariance/flicker, ghosting/recovery after disocclusion and lighting changes, and regional errors for glossy edges, glass/caustics and newly visible pixels. Report raw and reconstructed outputs separately. Preserve energy/long-run-mean tests for bias; denoising can hide it.

Measure complete GPU frame time and per-pass timestamps including neighbor/cell construction, guide fitting, cache updates, replay, barriers, reconstruction and copies. Include warmup, median and p95, CPU time, VRAM resident/peak, bytes per reservoir/domain, rays, successful shifts, queue/cell occupancy and overflow counts. For async compute, use critical-path timestamps rather than summing overlapping passes. Report display/render sizes and subsampling explicitly.

Compare both fixed complete-frame time and fixed error, sweeping sample/neighbor counts. Report a Pareto curve over time, error and VRAM instead of a single universal winner. Suggested initial product constraints (to be chosen before GPU runs): target GPU classes, render resolution, allowable memory overhead and frame-time budget. No numeric product target is assumed here.

## Scene and failure matrix

| Case | Required checks |
|---|---|
| Diffuse interior/window, many emissives | Guiding startup/adaptation, light sampling/NEE partition and cache control. |
| Glossy foliage/thin geometry | CGNS boundary/radius, footprint failures, covariance and rejected shifts. |
| Mirrors, nested glass, rough glass | PSR/guide ownership, transmission PDFs, BDPT bug and long temporal energy drift. |
| Fast camera/animated occluder/light | Disocclusion masks, stale history, lighting recovery, screen entry and camera cuts. |
| Geometry LoD transitions | UV validity/inverse consistency, area-Jacobian reciprocity, instance reuse and versioning. |
| DOF/motion blur/sparse rendering | Explicit support gates; preserve unbiased canonical fallback; multi-layer remains disabled. |
| Resize/restart/device/backend change | Reservoir and guiding invalidation, resource recreation, deterministic replay and no stale binding. |
| Empty/overflow cells and queues | Zero support, repeated selections, multiplicity, all-domain canonical accounting and bounded-memory fallback. |

## Focused acceptance gates

SPMIS: enumerate discrete domains including zero contributions and duplicate selections, then compare repeated means with full pairwise evaluation and exact expectation. CGNS: ensure selection depends only on permitted sample-independent geometry; compare matched radius before tuning radius. Guiding: integrate mixture PDF numerically, validate histogram draws and replay with retained models, test eviction/camera cuts. Splatting: validate collisions, canonical/backward terms, active domains, overflow and uncovered pixels. LoD: analytic mappings and inverse/area ratios before transition images. BDPT: technique partition, forward/reverse measures and rough-glass long-run regression before caustic quality claims.

## Reproduction and regression deliverables

P0 produces scene/config manifests, exact commands, raw captures, a metrics script and a machine-readable results table. Every new experiment must preserve baseline output and reject unsupported combinations explicitly. Run only changed behavior's relevant checks; broaden after failures or new unresolved risks. Record failed, skipped and unavailable checks with reasons. No generated pass flag can substitute for an actual shader build or GPU run.

## Canonical numbering and evidence boundary —2026-10-29

Legacy source/report labels remain intact: old B1 migration source7010bb4 maps by active mode to B3/B4/B5; old B2 DI+PT maps to B7; old B3 limited GI-off pilot is a B7 ablation, not B9. The [canonical crosswalk](VERSION_MAPPING.md) supersedes earlier planning labels. B8 sharing needs a valid partition/MIS before B9/B10 can claim it. Historical original-scene old-B0/old-B1 DI+GI rows map to B2/B5 with unverified cap coverage; do not pool them with cap-verified throughput. Current comparisons require actual modes, cap receipts, original-scene coverage and separate simulated-time/throughput labels.
