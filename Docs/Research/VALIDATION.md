**Current project context (2026-10-28):** RTXPT1.9 with its original scenes is the immutable B0 baseline. B1 at `7010bb4cda80788eb13cd9ee6143eb2f52a5b6ee` applies the RTXDI3.1 runtime/API migration to the existing DI/GI path. It does not add a ReSTIR PT renderer or activate PT++/CGNS features. `External/RTXDI-SDK` remains reference-only. See [B1 results](B1_RESULTS.md) for measured scope and limitations. B2+ remain planned.

# Validation and benchmark plan

## Current verification boundary

B1 changes the active RTXDI runtime dependency plus four host/UI files for API compatibility. Both baseline and B1 Release builds succeeded. Initial GPU timing and display-image comparisons are recorded in [B1 results](B1_RESULTS.md). Reviewed paper algorithms are not newly integrated, and these measurements do not establish unbiasedness or HDR estimator correctness. The receipt distinguishes structural validation from actual measured evidence.

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
