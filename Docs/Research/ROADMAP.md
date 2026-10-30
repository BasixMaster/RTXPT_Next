# Roadmap: B0–B16 and B10 sampling branches

## Current status — 2026-10-30

**B10 is partially implemented; B11 is not active.** The latest [duplication-reduction ablation](B10_DUPLICATION_HISTORY.md) completes 6 GPU activation/count cases, 18 quality sequences (1,152 frames) and 18 uncapped timing processes across Room, Convergence and Kitchen. Averaged-image MSE improves in the original scenes with individual-frame/perceptual tradeoffs. Startup reliability remains unresolved; no full PT++ promotion is claimed.

The [comparison overview](COMPARISON_OVERVIEW.md) includes both duplication policies beside B10, with performance, quality and pictures. Earlier [queue-history gates](B10_QUEUE_HISTORY.md), [Gaussian pairing](B10_GAUSSIAN_PAIRING.md) and [B9 measurements](B9_RESULTS.md) remain inspectable.

## Your B10+ roadmap

The integer sequence is cumulative: each version B11–B16 adds its named technique to the preceding version. B10.75/.50/.25 are sampling-budget branches of B10, not replacements for B11–B16. B0–B9 definitions and every historical source/data identity remain unchanged.

| Version | Your cumulative definition | Current status / implementation gate |
|---|---|---|
| **B10** | **Full PT++** | Partial. Duplication comparison complete; unified-lighting renderer, dual motion and broader validation pending. |
| **B10.75** | B10 with **0.75 spp** | Planned sampling branch; reuse RTXPT 1.9 native sub-sampling mode 1. |
| **B10.50** | B10 with **0.50 spp** | Planned sampling branch; reuse RTXPT 1.9 native sub-sampling mode 2. |
| **B10.25** | B10 with **0.25 spp** | Planned sampling branch; reuse RTXPT 1.9 native sub-sampling mode 3. |
| **B11** | B10 + **Compatibility-Guided Neighbor Selection active** | Planned after B10; integrate the selector, storage, sharing and normalization. |
| **B12** | B11 + **Stochastic Pairwise MIS** | Planned after B11; validate proposal support and combined weights. |
| **B13** | B12 + **ReSTIR LoD** | Planned after B12; validate geometry correspondence and shift Jacobians. |
| **B14** | B13 + **ReSTIR BDPT with LW version** | Planned after B13; preserve the requested LW designation and specify its exact scope before implementation. |
| **B15** | B14 + **ReSTIR PG** | Planned after B14; validate guiding proposals, training cost and replay. |
| **B16** | B15 + **Multi-Layer Reservoir Splatting** | Planned after B15; validate layer/visibility ownership and accumulation. |

## Implementation order and acceptance gates

1. **Finish B10:** follow PT++ and the authors' supplement closely. The [unified RIS/PSS oracle](B10_UNIFIED_LIGHTING.md) passes eight exact tests, but primary NEE/full-path unification is not yet implemented in the renderer. Add the paper's dual-motion recovery and complete broader reuse, motion/reset/resize and combined-preset validation.
2. **Paper-native unification:** full B10 gives the PT reservoir direct and all indirect paths and replaces standalone DI/GI shading in that preset. Preserve B8's short-GI/long-PT split as a control. A hybrid retaining short GI separately is an explicitly labelled adaptation, not a full reproduction of §6.1.
3. **Then activate B11:** use the documented CGNS selector and preserve geometry-only selection assumptions. Resolve independent neighbor choices, reciprocal sharing, queue ownership and valid normalization before claiming activation. See [B11 integration](B11_INTEGRATION.md).
4. **Integrate B12–B16 in order:** retain every preceding control and validate each combined estimator before the next technique. Planned definitions are not implementation or measurement claims.
5. **Validate sampling branches after B10:** RTXPT 1.9 already supplies the three native sampling rates. Reuse that mechanism; integrate sparse reservoir initialization, proposal weights, temporal history and reconstruction. The existing ReSTIR sub-sampling guard must not simply be removed.

## Source guidance and comparisons

Use the Wyman papers, supplements/author code and NVIDIA documentation/reference implementations as the specification and integration basis. Record the relevant sections/equations and API/source locations; document paper-versus-SDK differences, approximations and adaptations. Preserve estimator support, PDFs/Jacobians, normalization, RNG and history semantics. [Project guidance](../../AGENTS.md) applies to all later work.

Each comparison includes original Convergence, original Kitchen and the controlled Room, with the actual active algorithm, raw/reference quality, convergence curves, pictures and repeated uncapped timing. Distinguish GPU busy from total latency/FPS, and fixed-frame convergence from equal-time or equal-quality gains. Preserve missing coverage, excluded failures, uncertainty and source/runtime/cap restoration evidence. Brightness fixes remain user-deferred; do not fit exposure or radiometric scale to hide error.

## Summary and lessons learned

The roadmap names target configurations. Current evidence validates scoped components and tradeoffs, not the entire future configuration. Keep B10 partial until its remaining mechanisms and integration gates pass, and keep B11–B16 planned until active implementations are validated.

## Legacy roadmap appendix

**The remainder is the retained planning history under the previous numbering.** In this appendix, old B1 is the `7010bb4` migration, old B2 is the B6/B7 PT foundation, old B3 is the GI-off B7 limited pilot, and old B4 remaining work now belongs to B10. Its old section labels and estimates are archival, not competing definitions of the canonical IDs. Source refs, links and measurements are preserved.

### Deliverable and version policy

B0 is preserved as the unchanged source/scene baseline. B1 runtime/API migration is implemented and built; first comparisons are documented in [B1 results](B1_RESULTS.md). B2 integration remains in progress and unpromoted. B3 PT++ development has started on `b3/ptpp-activation`; later research features remain planned. Every promoted B-version gets an immutable commit/tag, complete submodule manifest, executable/shader hashes, settings and result record. Keep RTXPT1.9 as a permanent comparator. Assign each later version only after its scoped feature and checks are complete; never relabel a changed build under an old result ID. The [variant overview](ALGORITHM_VARIANTS.md) provides short algorithm labels and distinguishes capabilities from measured configurations.

### Baseline milestone

Use exact upstream RTXPT1.9 source303b408 and its pinned Assets a56be4e, runtimea14e079. Capture untouched upstream real-time defaults and a separate strict/reference transport preset. Preserve upstream scene materials, cameras and lights. Build requirements are upstream's CMake4.1+, supported Visual Studio/SDK and downloaded dependencies; merely checking out source is not a successful build. Benchmark assets by the same pin in all versions. Choose target hardware/resolution/VRAM budgets before claims.

### B1: completed migration scope and later integration gates

Completed scope: runtime `a14e079`→`f12037f`, four host/UI compatibility files, unchanged DI/GI estimator path. Release builds and initial GPU runs succeeded. ReSTIR PT, CGNS activation, new PT++ behavior and the capabilities below were not implemented in B1. The list retains the wider integration plan; items4–6 are future gates.

1. Create a dedicated B1 development branch from the named RTXPT1.9 baseline with the research harness available.
2. Select owned runtime modification strategy; audit a14e079→f12037f changes. Reconcile renamed DI/GI APIs, parameter names and host/shader layouts. Keep a migration-only preset using the same baseline render path, so API migration can be separated from algorithm activation.
3. Build and regress existing DI/GI and primary/indirect light accounting before PT work. Preserve RTXPT's material and scene semantics.
4. If B1 enables ReSTIR PT, implement its application bridge and pass/resource lifecycle explicitly: path context calls, RNG/replay, emission/environment/NEE PDFs/MIS, ping-pong and preserved initial reservoirs, neighbor prepass, duplication maps and barriers.
5. Test raw transport before DLSS/NRD, SHaRC, PSR/transmission, sparse tracing and async modes. Preserve NEE-AT/cache baseline controls; do not count direct paths twice.
6. Benchmark existing3.1 footprint, history, roulette, CGNS and decorrelation choices independently. Some controls are present but off by default; history reduction is a biased heuristic.

Acceptance for broader future integration: all chosen capabilities are compiled, exercised and recorded; no unsupported mode silently falls through; baseline regressions, raw/reference tests and performance/quality/VRAM comparisons pass. If only runtime/API migration is complete, label that limited scope explicitly rather than claiming full PT integration. Effort estimate: roughly2–4 engineer-weeks after baseline/toolchain availability, with integration complexity uncertain.

### B2: ReSTIR PT integration

B2 integrates the RTXDI3.1 ReSTIR PT application bridge, path generation/replay, host passes, resources, synchronization and final shading into RTXPT. Keep original DI+GI available; add a DI+PT configuration with PT owning indirect illumination. A configuration combining GI and PT must define disjoint contributions or valid MIS; do not add both indirect estimates. The UI and command line must report actual mode selection and reject unsupported combinations.

The new pipeline reuses RTXPT's scene/material/light semantics and history/reset rules. Preserve B0 and B1. RTXDI3.1 already contains packed reservoirs, forced NEE reconnection and optional PT++ mechanisms; therefore B2 is an integrated3.1 reference path, not a recreation of the untouched2022 implementation. Record inherited mechanisms, chosen defaults and approximation controls in every manifest.

Acceptance: real shaders compile; initial, temporal and spatial PT paths execute; camera cuts/resize/mode switches reset history; reference/finite-value checks pass; unsupported reconstruction/cache/material modes fail visibly or use a documented validated fallback. No source-presence or stub is a completed integration. Track current work in [B2/B3 implementation status](B2_IMPLEMENTATION.md). An initial build may take hours; complete integration and validation are a multi-day effort with material/replay complexity uncertain.

### B3: footprint and initial-only roulette checkpoint

B3 activates and independently measures the inherited footprint/inverse-footprint reconnection policy and initial-generation-only Russian roulette. Preserve B2's fixed-threshold/no-roulette policy as a same-executable control, while retaining the immutable B2 artifacts separately. Keep original-scene coverage gaps explicit. See [B3 implementation](B3_IMPLEMENTATION.md).

### B4: remaining PT++ mechanisms

After B3 is finished and preserved, continue with reciprocal paired reuse, explicit replay compaction, unified direct/indirect PT reservoirs, vector-weight shading, duplication-based confidence reduction and dual-motion disocclusion recovery. Audit remaining described micro-optimizations without counting inherited packing or forced NEE twice. Each mechanism needs an independent oracle and an isolated GPU ablation before a combined preset. See [B4 implementation gates](B4_IMPLEMENTATION.md).

CGNS remains a separate paper and neighbor policy. Duplication reduction is deliberately biased and stays separate from strict reference settings. Preserve B0–B3 and all mandatory original-scene comparison rows; no paper speedup is assumed.

### B5 and later: research-backed candidates

The order below is proposed and may change after measured results. Each should be isolated before stacking; assign B3/B4/etc only when the actual scope is chosen.

| Candidate | Key interface and dependency | Acceptance / stop gate | Rough effort |
|---|---|---|---|
| Stochastic pairwise MIS | Alternative spatial estimator; immutable bounded reuse cells, all-domain canonical accounting, multiplicity and inverse selection probability | Exact discrete-domain oracle first; include cell-build/sort cost; stop if fresh samples win at equal time. Resolve official archive code terms before copying. | 2–4 weeks |
| ReSTIR PG | Initial proposals + model fitting + full mixture PDF + versioned replay | Diffuse-first; BSDF fallback, model eviction/startup/adaptation tests; measured bandwidth/VRAM budget. Paper's separate DI/no-roulette assumptions require validation. | 3–6 weeks |
| Reservoir splatting → multi-layer | Temporal candidate generation, canonical/backup/backward MIS and active-domain compaction | Single-layer correctness precedes2layer pinhole/no-motion-blur mode; collisions, overflow, disocclusion and scene-entry tests. | 3–6+ weeks |
| Geometry-LoD reuse | UV-space correspondence/BVH, both primary+reconnection mapping and area Jacobians | Consistent UV assets, inverse mapping and one LoD/object/frame. Reject undefined maps; per-ray LoD remains unsupported. | 3–6 weeks |
| Lightweight caustics → full BDPT | Technique-aware path reservoirs, forward/reverse PDFs, light tracing/cache and recursive MIS | Fix/reproduce rough-glass UCW bug; prove no double count, bound memory/queues; full BDPT optional if quality/time/VRAM justify it. | 4–8+ weeks |

Estimates are engineering planning ranges for one experienced graphics engineer, not paper results or delivery promises. Dependencies, assets and hardware can dominate. The phases are not additive calendar commitments.

### Compatibility policy

Multi-layer paper excludes DOF/motion blur and off-screen history; leave these modes disabled for that technique until separately derived. Geometry-LoD paper assumes one per-object LoD per frame. CGNS's sample-independent geometric heuristic cannot acquire reservoir/luminance-dependent inputs while retaining its original proof. Stochastic MIS+CGNS needs explicit joint selection probabilities/support. PG's changing proposal models must not invalidate replay. Full BDPT and radiance cache termination need an explicit contribution partition. These are estimator gates, not cosmetic settings.

### Comparison and promotion

Every new variant requires visible rows for original Convergence, original Kitchen and the owned opaque room. Keep original assets, cameras and materials; show unsupported/missing cases with reasons rather than omitting them or silently changing scene semantics. Include a short actual algorithm label beside each variant result: native PT, DI + GI, or DI + ReSTIR PT with GI off. Include quality-versus-frames/samples/time curves as well as warmed-up quality and timing; absent convergence measurements remain pending. The historical B1 two-scene results have unverified cap coverage and must remain separate from newly cap-verified runs. See the [extended comparison contract](ALGORITHM_VARIANTS.md#extended-comparison-coverage).

For RTXPT1.9/B1/B2+ report raw and reconstructed image-quality metrics, complete-frame GPU median/p95, VRAM, temporal behavior and reference error. Run equal-time and equal-quality sweeps; do not multiply paper speedups from unrelated hardware/baselines. Measure all added preprocessing, replay, fitting, barriers and reconstruction costs. B1 versus RTXPT1.9 establishes update cost/benefit; B2 versus B1 isolates optimization benefit; B2 versus original shows cumulative change. Keep unsuccessful/scene-specific variants and reasons inspectable.


### Current B2 checkpoint

[Corrected static opaque B2 results](B2_RESULTS.md) now include active reconnection census, matched HDR validation and fresh three-process native-control comparisons with cap receipts. B2 remains unpromoted; original material/medium coverage, binding diffuse limits, motion, temporal/reconstruction metrics and wider scene coverage remain acceptance gates. B3 is not activated by this checkpoint.


### NVIDIA engineering guidance

The [NVIDIA whitepaper review](NVIDIA_WHITEPAPERS.md) adds immediate per-signal/pass profiling and later SER/OMM/tracing-model ablations. CLAS/PTLAS remains a separate geometry-scalability branch with explicit Agility SDK/HLSL/driver capability gates; it is not a substitute for ReSTIR-LoD's estimator/Jacobian work. Source-reported case-study gains are not RTXPT Next measurements.

Current native coverage: [fresh B2/B3/B5 original-scene and room results](NATIVE_MATRIX_RESULTS.md) adds27quality captures and27cap-verified timing processes. [The unified B0–B10 overview](COMPARISON_OVERVIEW.md) includes all versions, current metrics and representative pictures; historical cohorts remain separate.

Current timing checkpoint2026-10-29: [Gaussian versus adjacent pair/vector development](B10_GAUSSIAN_PAIRING.md#frozen-adjacent-versus-gaussian-timing) completes18cap-verified processes over all three scenes. Small descriptive timing differences and mixed quality do not promote full B10. Explicit replay compaction remains next; brightness fixes remain deferred.

Fresh requested control: [RTXPT1.9 PT-only override](NATIVE_MATRIX_RESULTS.md#fresh-rtxpt19-pt-only-override) now has9cap-verified timing processes and9PNG captures across Room and original Convergence/Kitchen. Native PT/NEE on, DI/GI off; original B0 defaults remain preserved. HDR export is unsupported in that unchanged binary.

Latest scoped checkpoint2026-10-29: [one-neighbor spatial replay queue](B10_GAUSSIAN_PAIRING.md#replay-compaction--active-implementation-checkpoint) passes11captured-frame exact GPU oracles and2queue-disabled regressions. Queue timing, full multi-frame histories, temporal queues, simultaneous multi-neighbor reuse and remaining B10 mechanisms are pending. No full PT++ or speedup claim.
