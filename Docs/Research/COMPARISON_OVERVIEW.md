# B0–B16 and sampling-variant comparison overview

One row per registered Bx version and required scene, including the B10 sampling variants. **Unavailable means not measured, never zero.** Experimental checkpoints, overrides and ablations are kept in their detailed reports. B0 remains the unchanged RTXPT1.9 reference.

GPU busy is process GPU activity in milliseconds, not complete frame latency or an FPS estimate. Lower FLIP/MSE is better. Different cohorts are descriptive; check settings and sampling policies before calculating relative gains. Accepted current timing cohorts include app/NVIDIA/RTSS cap checks; unknown external limiters and background load remain limitations.

**B10 is partial:** unified finite/environment MIS and initial-only roulette have scoped diagnostic checks, but no accepted full-B10 performance/quality comparison. [B10 implementation and evidence](B10_UNIFIED_LIGHTING.md) · [Roadmap](ROADMAP.md).

[Research summary](RESEARCH_SUMMARY.md) · [Algorithm definitions](VERSION_MAPPING.md) · [Benchmark protocol](BENCHMARK_VERSIONS.md) · [Machine-readable data](comparison-overview.json)

## Controlled room — registered environment

Main rows use640×360,1spp,3/3 bounce limits unless the evidence status states a different development scope. Native controls retain their DI/MIS policies. Development pictures are illustrations, not accepted matched comparisons.

| Version | Algorithm | GPU busy ms ↓ | LDR-FLIP ↓ | HDR-FLIP ↓ | Picture | Evidence status |
|---|---|---:|---:|---:|---|---|
| **B0** | Unchanged RTXPT v1.9 reference: original defaults and dependencies | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B1** | v1.9 native PT + ReSTIR DI3.0; GI off | 1.283 | 0.121484 | Unavailable | [![B1 opaque-room representative capture](assets/registered-room/B1.png)](assets/registered-room/B1.png) | [measured](REGISTERED_ROOM_RESULTS.md) |
| **B2** | v1.9 native PT + ReSTIR DI3.0 + ReSTIR GI3.0 | 1.441 | 0.094603 | Unavailable | [![B2 opaque-room representative capture](assets/native-matrix/opaque-room-B2.png)](assets/native-matrix/opaque-room-B2.png) | [measured known caps verified](NATIVE_MATRIX_RESULTS.md) |
| **B3** | Native PT with RTXDI3.1 linked; DI/GI off | 0.805 | 0.116744 | Unavailable | [![B3 opaque-room representative capture](assets/native-matrix/opaque-room-B3.png)](assets/native-matrix/opaque-room-B3.png) | [measured known caps verified](NATIVE_MATRIX_RESULTS.md) |
| **B4** | Native PT + ReSTIR DI3.1; GI off | 1.289 | 0.121719 | Unavailable | [![B4 opaque-room representative capture](assets/registered-room/B4.png)](assets/registered-room/B4.png) | [measured](REGISTERED_ROOM_RESULTS.md) |
| **B5** | Native PT + ReSTIR DI3.1 + ReSTIR GI3.1 | 1.461 | 0.093961 | Unavailable | [![B5 opaque-room representative capture](assets/native-matrix/opaque-room-B5.png)](assets/native-matrix/opaque-room-B5.png) | [measured known caps verified](NATIVE_MATRIX_RESULTS.md) |
| **B6** | ReSTIR PT; DI/GI off | 1.419 | 0.073817 | 0.114122 | [![B6 opaque-room representative capture](assets/registered-room/B6.png)](assets/registered-room/B6.png) | [measured](REGISTERED_ROOM_RESULTS.md) |
| **B7** | ReSTIR PT + ReSTIR DI3.1; GI off | 1.539 | 0.066837 | 0.103801 | [![B7 opaque-room representative capture](assets/registered-room/B7.png)](assets/registered-room/B7.png) | [measured](REGISTERED_ROOM_RESULTS.md) |
| **B8** | B8 development: DI + approximate GI-short reuse + PT-long | Unavailable | Unavailable | Unavailable | [![B8 opaque-room representative capture](assets/b8-nvidia-gi/room-gi3.png)](assets/b8-nvidia-gi/room-gi3.png) | [development not accepted](B8_STAGED_IMPLEMENTATION.md) |
| **B9** | B9 on B8: GI reuse + footprint/roulette | Unavailable | Unavailable | Unavailable | [![B9 opaque-room representative capture](assets/b9-on-b8/room-B9.png)](assets/b9-on-b8/room-B9.png) | [development not accepted](B9_RESULTS.md) |
| **B10** | B10: Full PT++ (partial integration) | Unavailable | Unavailable | Unavailable | No eligible capture | [development not accepted](B10_UNIFIED_LIGHTING.md) |
| **B10.75** | B10 full PT++ at0.75average spp | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B10.50** | B10 full PT++ at0.5average spp | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B10.25** | B10 full PT++ at0.25average spp | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B11** | B10 + Compatibility-Guided Neighbor Selection active | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B12** | B11 + Stochastic Pairwise MIS | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B13** | B12 + ReSTIR LoD | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B14** | B13 + ReSTIR BDPT with LW version | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B15** | B14 + ReSTIR PG | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B16** | B15 + Multi-Layer Reservoir Splatting | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |

<details><summary>Coverage and missing-data reasons</summary>

- **B0:** Unchanged original reference preserved. Separate raw-native control data exists; original-default benchmark is not replaced by it
- **B1:** Explicit separate zero-intensity registered environment fixture, same owned model/materials/camera; preserve prior no-env data separately. Three timing repeats; native3quality processes or modern3seed history sweep.
- **B2:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B3:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B4:** Explicit separate zero-intensity registered environment fixture, same owned model/materials/camera; preserve prior no-env data separately. Three timing repeats; native3quality processes or modern3seed history sweep.
- **B5:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B6:** Explicit separate zero-intensity registered environment fixture, same owned model/materials/camera; preserve prior no-env data separately. Three timing repeats; native3quality processes or modern3seed history sweep.
- **B7:** Explicit separate zero-intensity registered environment fixture, same owned model/materials/camera; preserve prior no-env data separately. Three timing repeats; native3quality processes or modern3seed history sweep.
- **B8:** NVIDIA non-directional GI reuse: 640x360 cap4/4,64-frame static quality measured; mixed results. Scoped timing is shown separately when available; no canonical promotion.
- **B9:** Eight GPU diagnostics passed; 640x360 cap4/4 snapshot shown. Three-seed64-frame quality and uncapped timing in progress. Original-scene footprint remains unsupported; no promotion.
- **B10:** Full B10 comparison pending. Component diagnostics, captures and ablations are available in the detailed B10 reports; no eligible full-version picture or performance/quality result yet.
- **B10.75:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B10.50:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B10.25:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B11:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B12:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B13:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B14:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B15:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B16:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.

</details>

## Original Convergence

1280×720,1spp,14/2 bounce limits, exposure0. Original materials and camera preserved.

| Version | Algorithm | GPU busy ms ↓ | LDR-FLIP ↓ | HDR-FLIP ↓ | Picture | Evidence status |
|---|---|---:|---:|---:|---|---|
| **B0** | Unchanged RTXPT v1.9 reference: original defaults and dependencies | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B1** | v1.9 native PT + ReSTIR DI3.0; GI off | 3.796 | 0.341609 | Unavailable | [![B1 convergence representative capture](assets/canonical-native-di/convergence-B1.png)](assets/canonical-native-di/convergence-B1.png) | [measured](CANONICAL_NATIVE_DI_RESULTS.md) |
| **B2** | v1.9 native PT + ReSTIR DI3.0 + ReSTIR GI3.0 | 4.510 | 0.243459 | Unavailable | [![B2 convergence representative capture](assets/native-matrix/convergence-B2.png)](assets/native-matrix/convergence-B2.png) | [measured known caps verified](NATIVE_MATRIX_RESULTS.md) |
| **B3** | Native PT with RTXDI3.1 linked; DI/GI off | 2.565 | 0.375281 | Unavailable | [![B3 convergence representative capture](assets/native-matrix/convergence-B3.png)](assets/native-matrix/convergence-B3.png) | [measured known caps verified](NATIVE_MATRIX_RESULTS.md) |
| **B4** | Native PT + ReSTIR DI3.1; GI off | 3.772 | 0.341623 | Unavailable | [![B4 convergence representative capture](assets/canonical-native-di/convergence-B4.png)](assets/canonical-native-di/convergence-B4.png) | [measured](CANONICAL_NATIVE_DI_RESULTS.md) |
| **B5** | Native PT + ReSTIR DI3.1 + ReSTIR GI3.1 | 4.545 | 0.243522 | Unavailable | [![B5 convergence representative capture](assets/native-matrix/convergence-B5.png)](assets/native-matrix/convergence-B5.png) | [measured known caps verified](NATIVE_MATRIX_RESULTS.md) |
| **B6** | ReSTIR PT; DI/GI off | Unavailable | 0.300663 | 0.453476 | [![B6 convergence representative capture](assets/finite-shift-guard/convergence-B6.png)](assets/finite-shift-guard/convergence-B6.png) | [Guarded quality measured; timing pending †](FINITE_SHIFT_GUARD.md) |
| **B7** | ReSTIR PT + ReSTIR DI3.1; GI off | Unavailable | 0.222129 | 0.333817 | [![B7 convergence representative capture](assets/finite-shift-guard/convergence-B7.png)](assets/finite-shift-guard/convergence-B7.png) | [Guarded quality measured; timing pending †](FINITE_SHIFT_GUARD.md) |
| **B8** | B8 development: DI + approximate GI-short reuse + PT-long | Unavailable | Unavailable | Unavailable | [![B8 convergence representative capture](assets/b8-nvidia-gi/convergence-gi3.png)](assets/b8-nvidia-gi/convergence-gi3.png) | [development not accepted](B8_STAGED_IMPLEMENTATION.md) |
| **B9** | B9 on B8: GI reuse + full-prefix roulette-only ablation | Unavailable | Unavailable | Unavailable | [![B9 convergence representative capture](assets/b9-on-b8/convergence-B9.png)](assets/b9-on-b8/convergence-B9.png) | [development not accepted](B9_RESULTS.md) |
| **B10** | B10: Full PT++ (partial integration) | Unavailable | Unavailable | Unavailable | No eligible capture | [development not accepted](B10_UNIFIED_LIGHTING.md) |
| **B10.75** | B10 full PT++ at0.75average spp | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B10.50** | B10 full PT++ at0.5average spp | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B10.25** | B10 full PT++ at0.25average spp | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B11** | B10 + Compatibility-Guided Neighbor Selection active | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B12** | B11 + Stochastic Pairwise MIS | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B13** | B12 + ReSTIR LoD | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B14** | B13 + ReSTIR BDPT with LW version | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B15** | B14 + ReSTIR PG | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B16** | B15 + Multi-Layer Reservoir Splatting | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |

<details><summary>Coverage and missing-data reasons</summary>

- **B0:** Unchanged original reference preserved. Separate raw-native control data exists; original-default benchmark is not replaced by it
- **B1:** Original scene/material/camera retained;3quality and3timing process repetitions/configuration
- **B2:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B3:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B4:** Original scene/material/camera retained;3quality and3timing process repetitions/configuration
- **B5:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B6:** Five-seed1280x720 matched MIP0 quality; finite zero-Jacobian targets prevent invalid MIS propagation. Guarded replay-first transport; original scene/material/camera14/2. Throughput and general stability acceptance pending.
- **B7:** Five-seed1280x720 matched MIP0 quality; finite zero-Jacobian targets prevent invalid MIS propagation. Guarded replay-first transport; original scene/material/camera14/2. Throughput and general stability acceptance pending.
- **B8:** NVIDIA non-directional GI reuse: 1280x720 cap14/2,64-frame static quality measured; mixed results. Scoped timing is shown separately when available; no canonical promotion.
- **B9:** Eight GPU diagnostics passed; 1280x720 cap14/2 snapshot shown. Three-seed64-frame quality and uncapped timing in progress. Original-scene footprint remains unsupported; no promotion.
- **B10:** Full B10 comparison pending. Component diagnostics, captures and ablations are available in the detailed B10 reports; no eligible full-version picture or performance/quality result yet.
- **B10.75:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B10.50:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B10.25:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B11:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B12:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B13:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B14:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B15:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B16:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.

</details>

## Original Kitchen

1280×720,1spp,14/2 bounce limits, exposure2. Original materials and camera preserved.

| Version | Algorithm | GPU busy ms ↓ | LDR-FLIP ↓ | HDR-FLIP ↓ | Picture | Evidence status |
|---|---|---:|---:|---:|---|---|
| **B0** | Unchanged RTXPT v1.9 reference: original defaults and dependencies | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B1** | v1.9 native PT + ReSTIR DI3.0; GI off | 4.455 | 0.386252 | Unavailable | [![B1 kitchen representative capture](assets/canonical-native-di/kitchen-B1.png)](assets/canonical-native-di/kitchen-B1.png) | [measured](CANONICAL_NATIVE_DI_RESULTS.md) |
| **B2** | v1.9 native PT + ReSTIR DI3.0 + ReSTIR GI3.0 | 5.370 | 0.352840 | Unavailable | [![B2 kitchen representative capture](assets/native-matrix/kitchen-B2.png)](assets/native-matrix/kitchen-B2.png) | [measured known caps verified](NATIVE_MATRIX_RESULTS.md) |
| **B3** | Native PT with RTXDI3.1 linked; DI/GI off | 3.258 | 0.382364 | Unavailable | [![B3 kitchen representative capture](assets/native-matrix/kitchen-B3.png)](assets/native-matrix/kitchen-B3.png) | [measured known caps verified](NATIVE_MATRIX_RESULTS.md) |
| **B4** | Native PT + ReSTIR DI3.1; GI off | 4.446 | 0.386295 | Unavailable | [![B4 kitchen representative capture](assets/canonical-native-di/kitchen-B4.png)](assets/canonical-native-di/kitchen-B4.png) | [measured](CANONICAL_NATIVE_DI_RESULTS.md) |
| **B5** | Native PT + ReSTIR DI3.1 + ReSTIR GI3.1 | 5.421 | 0.351458 | Unavailable | [![B5 kitchen representative capture](assets/native-matrix/kitchen-B5.png)](assets/native-matrix/kitchen-B5.png) | [measured known caps verified](NATIVE_MATRIX_RESULTS.md) |
| **B6** | ReSTIR PT; DI/GI off | Unavailable | 0.302520 | 0.546629 | [![B6 kitchen representative capture](assets/finite-shift-guard/kitchen-B6.png)](assets/finite-shift-guard/kitchen-B6.png) | [Guarded quality measured; timing pending †](FINITE_SHIFT_GUARD.md) |
| **B7** | ReSTIR PT + ReSTIR DI3.1; GI off | Unavailable | 0.249775 | 0.440491 | [![B7 kitchen representative capture](assets/finite-shift-guard/kitchen-B7.png)](assets/finite-shift-guard/kitchen-B7.png) | [Guarded quality measured; timing pending †](FINITE_SHIFT_GUARD.md) |
| **B8** | B8 development: DI + approximate GI-short reuse + PT-long | Unavailable | Unavailable | Unavailable | [![B8 kitchen representative capture](assets/b8-nvidia-gi/kitchen-gi3.png)](assets/b8-nvidia-gi/kitchen-gi3.png) | [development not accepted](B8_STAGED_IMPLEMENTATION.md) |
| **B9** | B9 on B8: GI reuse + full-prefix roulette-only ablation | Unavailable | Unavailable | Unavailable | [![B9 kitchen representative capture](assets/b9-on-b8/kitchen-B9.png)](assets/b9-on-b8/kitchen-B9.png) | [development not accepted](B9_RESULTS.md) |
| **B10** | B10: Full PT++ (partial integration) | Unavailable | Unavailable | Unavailable | No eligible capture | [development not accepted](B10_UNIFIED_LIGHTING.md) |
| **B10.75** | B10 full PT++ at0.75average spp | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B10.50** | B10 full PT++ at0.5average spp | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B10.25** | B10 full PT++ at0.25average spp | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B11** | B10 + Compatibility-Guided Neighbor Selection active | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B12** | B11 + Stochastic Pairwise MIS | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B13** | B12 + ReSTIR LoD | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B14** | B13 + ReSTIR BDPT with LW version | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B15** | B14 + ReSTIR PG | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B16** | B15 + Multi-Layer Reservoir Splatting | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |

<details><summary>Coverage and missing-data reasons</summary>

- **B0:** Unchanged original reference preserved. Separate raw-native control data exists; original-default benchmark is not replaced by it
- **B1:** Original scene/material/camera retained;3quality and3timing process repetitions/configuration
- **B2:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B3:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B4:** Original scene/material/camera retained;3quality and3timing process repetitions/configuration
- **B5:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B6:** Five-seed1280x720 matched MIP0 quality; finite zero-Jacobian targets prevent invalid MIS propagation. Guarded replay-first transport; original scene/material/camera14/2. Throughput and general stability acceptance pending.
- **B7:** Five-seed1280x720 matched MIP0 quality; finite zero-Jacobian targets prevent invalid MIS propagation. Guarded replay-first transport; original scene/material/camera14/2. Throughput and general stability acceptance pending.
- **B8:** NVIDIA non-directional GI reuse: 1280x720 cap14/2,64-frame static quality measured; mixed results. Scoped timing is shown separately when available; no canonical promotion.
- **B9:** Eight GPU diagnostics passed; 1280x720 cap14/2 snapshot shown. Three-seed64-frame quality and uncapped timing in progress. Original-scene footprint remains unsupported; no promotion.
- **B10:** Full B10 comparison pending. Component diagnostics, captures and ablations are available in the detailed B10 reports; no eligible full-version picture or performance/quality result yet.
- **B10.75:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B10.50:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B10.25:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B11:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B12:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B13:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B14:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B15:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.
- **B16:** User-confirmed roadmap; activation/integration and matched quality/performance evidence pending. No measurements inferred.

</details>

† Guarded original-scene B6/B7 quality uses five explicit seeds and matched MIP0 references. It is not unrestricted scene acceptance or a new throughput result. [Scene-support evidence](FINITE_SHIFT_GUARD.md).

## Detailed studies

[Unified lighting](B10_UNIFIED_LIGHTING.md) · [Replay queues](B10_QUEUE_HISTORY.md) · [Pairing and vector shading](B10_GAUSSIAN_PAIRING.md) · [Duplication history](B10_DUPLICATION_HISTORY.md) · [B9 ablations](B9_RESULTS.md) · [Native controls and overrides](NATIVE_MATRIX_RESULTS.md) · [DI reuse isolation](DI_REUSE_ISOLATION.md) · [Material precision](GBUFFER_PRECISION.md) · [Prefix throughput](PREFIX_THROUGHPUT.md)
