# Roadmap: RTXPT1.9 → B1 → B2 and later

## Deliverable and version policy

B0 is preserved as the unchanged source/scene baseline. B1 runtime/API migration is implemented and built; first comparisons are documented in [B1 results](B1_RESULTS.md). B2 integration is in progress; B3 PT++ and the later research features remain planned. Every promoted B-version gets an immutable commit/tag, complete submodule manifest, executable/shader hashes, settings and result record. Keep RTXPT1.9 as a permanent comparator. Assign each later version only after its scoped feature and checks are complete; never relabel a changed build under an old result ID.

## Baseline milestone

Use exact upstream RTXPT1.9 source303b408 and its pinned Assets a56be4e, runtimea14e079. Capture untouched upstream real-time defaults and a separate strict/reference transport preset. Preserve upstream scene materials, cameras and lights. Build requirements are upstream's CMake4.1+, supported Visual Studio/SDK and downloaded dependencies; merely checking out source is not a successful build. Benchmark assets by the same pin in all versions. Choose target hardware/resolution/VRAM budgets before claims.

## B1: completed migration scope and later integration gates

Completed scope: runtime `a14e079`→`f12037f`, four host/UI compatibility files, unchanged DI/GI estimator path. Release builds and initial GPU runs succeeded. ReSTIR PT, CGNS activation, new PT++ behavior and the capabilities below were not implemented in B1. The list retains the wider integration plan; items4–6 are future gates.

1. Create a dedicated B1 development branch from the named RTXPT1.9 baseline with the research harness available.
2. Select owned runtime modification strategy; audit a14e079→f12037f changes. Reconcile renamed DI/GI APIs, parameter names and host/shader layouts. Keep a migration-only preset using the same baseline render path, so API migration can be separated from algorithm activation.
3. Build and regress existing DI/GI and primary/indirect light accounting before PT work. Preserve RTXPT's material and scene semantics.
4. If B1 enables ReSTIR PT, implement its application bridge and pass/resource lifecycle explicitly: path context calls, RNG/replay, emission/environment/NEE PDFs/MIS, ping-pong and preserved initial reservoirs, neighbor prepass, duplication maps and barriers.
5. Test raw transport before DLSS/NRD, SHaRC, PSR/transmission, sparse tracing and async modes. Preserve NEE-AT/cache baseline controls; do not count direct paths twice.
6. Benchmark existing3.1 footprint, history, roulette, CGNS and decorrelation choices independently. Some controls are present but off by default; history reduction is a biased heuristic.

Acceptance for broader future integration: all chosen capabilities are compiled, exercised and recorded; no unsupported mode silently falls through; baseline regressions, raw/reference tests and performance/quality/VRAM comparisons pass. If only runtime/API migration is complete, label that limited scope explicitly rather than claiming full PT integration. Effort estimate: roughly2–4 engineer-weeks after baseline/toolchain availability, with integration complexity uncertain.

## B2: ReSTIR PT integration

B2 integrates the RTXDI3.1 ReSTIR PT application bridge, path generation/replay, host passes, resources, synchronization and final shading into RTXPT. Keep original DI+GI available; add a DI+PT configuration with PT owning indirect illumination. A configuration combining GI and PT must define disjoint contributions or valid MIS; do not add both indirect estimates. The UI and command line must report actual mode selection and reject unsupported combinations.

The new pipeline reuses RTXPT's scene/material/light semantics and history/reset rules. Preserve B0 and B1. RTXDI3.1 already contains packed reservoirs, forced NEE reconnection and optional PT++ mechanisms; therefore B2 is an integrated3.1 reference path, not a recreation of the untouched2022 implementation. Record inherited mechanisms, chosen defaults and approximation controls in every manifest.

Acceptance: real shaders compile; initial, temporal and spatial PT paths execute; camera cuts/resize/mode switches reset history; reference/finite-value checks pass; unsupported reconstruction/cache/material modes fail visibly or use a documented validated fallback. No source-presence or stub is a completed integration. Track current work in [B2/B3 implementation status](B2_IMPLEMENTATION.md). An initial build may take hours; complete integration and validation are a multi-day effort with material/replay complexity uncertain.

## B3: PT++ activation and missing mechanisms

B3 separately activates validated footprint/history/roulette controls inherited from the runtime and implements the audited missing mechanisms: reciprocal spatial pairing, unified primary direct/indirect reservoirs, explicit replay compaction, all-candidate vector-weight shading and the paper's dual-motion-vector disocclusion handling. Preserve one toggle/ablation per mechanism before a combined preset. Do not assign a paper-equivalence label to unverified micro-optimizations.

CGNS is a separate paper, even though supplied by3.1. Keep CGNS and reciprocal pairing as alternative neighbor policies unless a compatible joint selection/weighting derivation is validated. Duplication-based history reduction is deliberately biased and remains a distinct preset from correctness/reference controls. Measure complete work, quality, temporal behavior and memory against B2, B1 and B0. No2–3× speedup over RTXPT is assumed from the paper.

## B4 and later: research-backed candidates

The order below is proposed and may change after measured results. Each should be isolated before stacking; assign B3/B4/etc only when the actual scope is chosen.

| Candidate | Key interface and dependency | Acceptance / stop gate | Rough effort |
|---|---|---|---|
| Stochastic pairwise MIS | Alternative spatial estimator; immutable bounded reuse cells, all-domain canonical accounting, multiplicity and inverse selection probability | Exact discrete-domain oracle first; include cell-build/sort cost; stop if fresh samples win at equal time. Resolve official archive code terms before copying. | 2–4 weeks |
| ReSTIR PG | Initial proposals + model fitting + full mixture PDF + versioned replay | Diffuse-first; BSDF fallback, model eviction/startup/adaptation tests; measured bandwidth/VRAM budget. Paper's separate DI/no-roulette assumptions require validation. | 3–6 weeks |
| Reservoir splatting → multi-layer | Temporal candidate generation, canonical/backup/backward MIS and active-domain compaction | Single-layer correctness precedes2layer pinhole/no-motion-blur mode; collisions, overflow, disocclusion and scene-entry tests. | 3–6+ weeks |
| Geometry-LoD reuse | UV-space correspondence/BVH, both primary+reconnection mapping and area Jacobians | Consistent UV assets, inverse mapping and one LoD/object/frame. Reject undefined maps; per-ray LoD remains unsupported. | 3–6 weeks |
| Lightweight caustics → full BDPT | Technique-aware path reservoirs, forward/reverse PDFs, light tracing/cache and recursive MIS | Fix/reproduce rough-glass UCW bug; prove no double count, bound memory/queues; full BDPT optional if quality/time/VRAM justify it. | 4–8+ weeks |

Estimates are engineering planning ranges for one experienced graphics engineer, not paper results or delivery promises. Dependencies, assets and hardware can dominate. The phases are not additive calendar commitments.

## Compatibility policy

Multi-layer paper excludes DOF/motion blur and off-screen history; leave these modes disabled for that technique until separately derived. Geometry-LoD paper assumes one per-object LoD per frame. CGNS's sample-independent geometric heuristic cannot acquire reservoir/luminance-dependent inputs while retaining its original proof. Stochastic MIS+CGNS needs explicit joint selection probabilities/support. PG's changing proposal models must not invalidate replay. Full BDPT and radiance cache termination need an explicit contribution partition. These are estimator gates, not cosmetic settings.

## Comparison and promotion

For RTXPT1.9/B1/B2+ report raw and reconstructed image-quality metrics, complete-frame GPU median/p95, VRAM, temporal behavior and reference error. Run equal-time and equal-quality sweeps; do not multiply paper speedups from unrelated hardware/baselines. Measure all added preprocessing, replay, fitting, barriers and reconstruction costs. B1 versus RTXPT1.9 establishes update cost/benefit; B2 versus B1 isolates optimization benefit; B2 versus original shows cumulative change. Keep unsuccessful/scene-specific variants and reasons inspectable.


## Current B2 checkpoint

[Corrected static opaque B2 results](B2_RESULTS.md) now include active reconnection census, matched HDR validation and fresh three-process native-control comparisons with cap receipts. B2 remains unpromoted; original material/medium coverage, binding diffuse limits, motion, temporal/reconstruction metrics and wider scene coverage remain acceptance gates. B3 is not activated by this checkpoint.


## NVIDIA engineering guidance

The [NVIDIA whitepaper review](NVIDIA_WHITEPAPERS.md) adds immediate per-signal/pass profiling and later SER/OMM/tracing-model ablations. CLAS/PTLAS remains a separate geometry-scalability branch with explicit Agility SDK/HLSL/driver capability gates; it is not a substitute for ReSTIR-LoD's estimator/Jacobian work. Source-reported case-study gains are not RTXPT Next measurements.
