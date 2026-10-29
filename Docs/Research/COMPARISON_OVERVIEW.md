# B0–B10 comparison overview

All eleven canonical versions appear below for each required scene. Performance, quality and representative pictures share the same row. **Not measured means unavailable, never zero.** B0 remains the unchanged RTXPT1.9 reference; a raw native-control preset does not replace its original defaults.

GPU busy is process GPU activity in milliseconds, not complete frame latency or an FPS estimate. Lower FLIP/MSE is better. Rows from different cohorts are descriptive: settings and sampling policies must be checked before computing a relative gain. Known app/NVIDIA/RTSS cap boundaries were verified for accepted current timing cohorts; unknown external limiters and background load remain limitations.

[Machine-readable overview](comparison-overview.json) · [Algorithm definitions and identities](VERSION_MAPPING.md) · [Benchmark protocol](BENCHMARK_VERSIONS.md)

## Controlled room — registered environment

640×360,1spp,3/3 bounce limits; opaque-room-registered-env.scene.json. This is a distinct fixture from the legacy no-environment room. Native controls retain their DI/MIS policies; B6/B7 use their documented PT/strict-DI policies.

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
| **B8** | ReSTIR PT + ReSTIR DI3.1 + ReSTIR GI3.1 | Unavailable | Unavailable | Unavailable | No eligible capture | [unsupported](VERSION_MAPPING.md) |
| **B9** | B8 + limited PT++ | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B10** | B8 + full PT++ | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |

<details><summary>Coverage and missing-data reasons</summary>

- **B0:** Unchanged original reference preserved. Separate raw-native control data exists; original-default benchmark is not replaced by it
- **B1:** Explicit separate zero-intensity registered environment fixture, same owned model/materials/camera; preserve prior no-env data separately. Three timing repeats; native3quality processes or modern3seed history sweep.
- **B2:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B3:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B4:** Explicit separate zero-intensity registered environment fixture, same owned model/materials/camera; preserve prior no-env data separately. Three timing repeats; native3quality processes or modern3seed history sweep.
- **B5:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B6:** Explicit separate zero-intensity registered environment fixture, same owned model/materials/camera; preserve prior no-env data separately. Three timing repeats; native3quality processes or modern3seed history sweep.
- **B7:** Explicit separate zero-intensity registered environment fixture, same owned model/materials/camera; preserve prior no-env data separately. Three timing repeats; native3quality processes or modern3seed history sweep.
- **B8:** PT/GI contribution partition is not implemented; no combined execution or B9/B10 performance claimed
- **B9:** PT/GI contribution partition is not implemented; no combined execution or B9/B10 performance claimed
- **B10:** PT/GI contribution partition is not implemented; no combined execution or B9/B10 performance claimed

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
| **B8** | ReSTIR PT + ReSTIR DI3.1 + ReSTIR GI3.1 | Unavailable | Unavailable | Unavailable | No eligible capture | [unsupported](VERSION_MAPPING.md) |
| **B9** | B8 + limited PT++ | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B10** | B8 + full PT++ | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |

<details><summary>Coverage and missing-data reasons</summary>

- **B0:** Unchanged original reference preserved. Separate raw-native control data exists; original-default benchmark is not replaced by it
- **B1:** Original scene/material/camera retained;3quality and3timing process repetitions/configuration
- **B2:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B3:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B4:** Original scene/material/camera retained;3quality and3timing process repetitions/configuration
- **B5:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B6:** Five-seed1280x720 matched MIP0 quality; finite zero-Jacobian targets prevent invalid MIS propagation. Guarded replay-first transport; original scene/material/camera14/2. Throughput and general stability acceptance pending.
- **B7:** Five-seed1280x720 matched MIP0 quality; finite zero-Jacobian targets prevent invalid MIS propagation. Guarded replay-first transport; original scene/material/camera14/2. Throughput and general stability acceptance pending.
- **B8:** PT/GI contribution partition is not implemented; no combined execution or B9/B10 performance claimed
- **B9:** PT/GI contribution partition is not implemented; no combined execution or B9/B10 performance claimed
- **B10:** PT/GI contribution partition is not implemented; no combined execution or B9/B10 performance claimed

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
| **B8** | ReSTIR PT + ReSTIR DI3.1 + ReSTIR GI3.1 | Unavailable | Unavailable | Unavailable | No eligible capture | [unsupported](VERSION_MAPPING.md) |
| **B9** | B8 + limited PT++ | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |
| **B10** | B8 + full PT++ | Unavailable | Unavailable | Unavailable | No eligible capture | [pending](VERSION_MAPPING.md) |

<details><summary>Coverage and missing-data reasons</summary>

- **B0:** Unchanged original reference preserved. Separate raw-native control data exists; original-default benchmark is not replaced by it
- **B1:** Original scene/material/camera retained;3quality and3timing process repetitions/configuration
- **B2:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B3:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B4:** Original scene/material/camera retained;3quality and3timing process repetitions/configuration
- **B5:** Fresh native-control cohort:3 quality processes and3 cap-verified timing processes; original shader estimator retained. Different acquisition cohort from B1/B4 and B6/B7.
- **B6:** Five-seed1280x720 matched MIP0 quality; finite zero-Jacobian targets prevent invalid MIS propagation. Guarded replay-first transport; original scene/material/camera14/2. Throughput and general stability acceptance pending.
- **B7:** Five-seed1280x720 matched MIP0 quality; finite zero-Jacobian targets prevent invalid MIS propagation. Guarded replay-first transport; original scene/material/camera14/2. Throughput and general stability acceptance pending.
- **B8:** PT/GI contribution partition is not implemented; no combined execution or B9/B10 performance claimed
- **B9:** PT/GI contribution partition is not implemented; no combined execution or B9/B10 performance claimed
- **B10:** PT/GI contribution partition is not implemented; no combined execution or B9/B10 performance claimed

</details>

† Original-scene B6/B7 quality uses five explicit seeds and new matched MIP0 references after the finite-MIS-target fix. This differs from retained native timing/quality cohorts; it is not a new throughput result or unrestricted scene acceptance. Native startup intermittency and the smaller DI-enabled residual remain. See the [scene-fix follow-up](FINITE_SHIFT_GUARD.md).

## Historical observations — different cohorts

These retained measurements remain useful context, but are excluded from the current tables’ numeric columns. Their settings, scene identity or cap evidence differ. Historical images are available through the linked reports; they are not substitutes for missing current captures.

| Canonical interpretation | Scene | GPU busy ms | LDR-FLIP | Scope and pictures |
|---|---|---:|---:|---|
| B2: native PT + DI/GI3.0 | Convergence | 4.4584 | 0.24355 | [Legacy migration cohort; caps unverified](B1_RESULTS.md) |
| B5: native PT + DI/GI3.1 | Convergence | 4.4530 | 0.24338 | [Legacy migration cohort; caps unverified](B1_RESULTS.md) |
| B2: native PT + DI/GI3.0 | Kitchen | 5.3398 | 0.35210 | [Legacy migration cohort; caps unverified](B1_RESULTS.md) |
| B5: native PT + DI/GI3.1 | Kitchen | 5.3591 | 0.35226 | [Legacy migration cohort; caps unverified](B1_RESULTS.md) |
| B0/raw-native-control, not original defaults | Legacy room, no registered environment | 0.803 | See report | [DI/GI off; different fixture](B2_RESULTS.md) |
| B3: native PT, DI/GI off | Legacy room, no registered environment | 0.806 | See report | [Different fixture](B2_RESULTS.md) |
| B7: ReSTIR PT + DI3.1 | Legacy room, no registered environment | 1.519 | See report | [Earlier checkpoint](B2_RESULTS.md) |

## Quality detail and convergence coverage

The JSON includes display MSE, available linear MSE and CPU cadence alongside each current result. [Registered-room history curves and finite-reference checks](REGISTERED_ROOM_RESULTS.md) cover B6/B7 at1,8,32,64 warm-up frames and three explicit seeds. These are separate1spp history-settling snapshots, not accumulated-spp convergence or time-to-equal-quality. Native captures use three process restarts without verified independent seeds. Original-scene native quality uses finite4096spp references; the room uses a separate finite8192spp native reference with discrepancy checks. HDR-FLIP is unavailable for native original-shader controls.

## Summary and lessons learned

The current registered-room comparison shows B7 costing19.4%more process GPU busy than B4 while lowering LDR-FLIP by45.1%. Original Convergence/Kitchen B1/B4 timing changes are below1%; they do not demonstrate a general speedup. B6/B7 now have corrected original-resolution five-seed quality evidence; native startup stability and new throughput remain pending. B8 GPU sharing and B9/B10 PT++ configurations remain pending; their rows stay visible until eligible measurements exist.

## Changes

- 2026-10-29: Added one generated overview with all33 version/scene rows, explicit missing coverage, representative images and retained historical cohort links.
