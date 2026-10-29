# Algorithm overview: canonical B0–B10

**Current numbering:** use [the canonical mapping and legacy crosswalk](VERSION_MAPPING.md). B0 retains unchanged RTXPT 1.9 defaults and pins; it is not defined by the raw native-only control.

| ID | Short algorithm overview | Active modes / gate |
|---|---|---|
| B0 | Unchanged RTXPT 1.9 reference | Original defaults and pins. |
| B1 | Native PT + DI 3.0 | GI/ReSTIR PT off; original-scene quality/timing measured. |
| B2 | Native PT + DI 3.0 + GI 3.0 | ReSTIR PT off; all three native scene rows freshly measured. |
| B3 | Native PT / runtime 3.1 | DI/GI/ReSTIR PT off; all three native scene rows freshly measured. |
| B4 | Native PT + DI 3.1 | GI/ReSTIR PT off; original-scene quality/timing measured. |
| B5 | Native PT + DI 3.1 + GI 3.1 | ReSTIR PT off; all three native scene rows freshly measured. |
| B6 | ReSTIR PT | DI/GI off; native direct/fallback ownership remains explicit. |
| B7 | ReSTIR PT + DI 3.1 | GI off; measured static opaque checkpoint. |
| B8 | ReSTIR PT + DI 3.1 + GI 3.1 | Disjoint initial-GI development executes; full GI reuse and acceptance pending. |
| B9 | B8 + limited PT++ | GI-initial-only footprint/roulette ablation executes; complete B8/B9 pending. |
| B10 | B8 + full remaining PT++ | Adjacent reciprocal-pair/vector GPU pilot executes; full PT++ and acceptance pending. |

B1/B4 native-DI comparisons are measured on original scenes and the registered room; B6/B7 room timing and history sweeps are also measured. The 0.803 ms control is a B0 native-control raw preset, separate from original defaults; the 0.806 ms migrated native control is B3 with DI/GI off. The old-B2 checkpoint `de9fe651` maps to B7. The old-B3 pilot `a7428c8` maps to B7 plus limited ablations, **not B9**. Stored refs/data IDs and numbers are preserved.

The original ReSTIR PT paper's §9.3 adjusted sample counts for approximately equal time; the current fixed-1spp room pilot is not that comparison. Keep equal-time/quality sweeps pending until measured. Existing runtime PT++ mechanisms are inherited, not newly counted as B9 gains.

## Legacy numbering appendix

The following retained overview and scene requirements were written under the previous IDs. Interpret every B1–B4 occurrence in this appendix through [VERSION_MAPPING.md](VERSION_MAPPING.md); it is not a second current version definition. Required original-scene identities and missing-coverage statements remain applicable to their mapped algorithms.

Version identifies the code; the algorithm label identifies the rendering configuration used in a particular result. Always show both. RTXPT supplies the renderer, materials and native path tracer; ReSTIR DI, GI and PT are selectable sampling paths within it.

## Short variant labels

| Variant | Short algorithm overview | Available paths and contribution ownership | Current evidence |
|---|---|---|---|
| B0 / RTXPT 1.9 | **RTXPT native PT + RTXDI 3.0 DI/GI** | Native path tracing, optional ReSTIR DI for direct light and ReSTIR GI for indirect light. No ReSTIR PT integration. | Preserved upstream source/assets. Historical Convergence/Kitchen comparison used DI + GI; the later opaque-room control used native PT with DI/GI off. |
| B1 | **RTXPT native PT + RTXDI 3.1 DI/GI** | Same rendering paths as B0, with the runtime/API migration. No new ReSTIR PT estimator was activated by B1. | Historical Convergence/Kitchen comparison used DI + GI; the later opaque-room control used native PT with DI/GI off. |
| B2 | **RTXPT + ReSTIR DI + ReSTIR PT** | Adds path-reservoir initial sampling, temporal/spatial reuse and mid-path reconnection. DI may own direct light while ReSTIR PT owns indirect light. GI remains selectable as an alternative indirect estimator; GI and PT are not added together. | Corrected static opaque checkpoint at `de9fe651`; measured preset is DI + ReSTIR PT, GI off. Broader validation is pending; B2 is not promoted. |
| B3 | **B2 DI + ReSTIR PT + isolated PT++ activations** | Retains B2's direct/indirect partition while PT++ mechanisms are enabled or added one at a time. First work targets footprint reconnection and initial-generation-only roulette; replay roulette remains off. | Development in progress on `b3/ptpp-activation`; no B3 quality/performance claim follows from this overview. Remaining paper mechanisms are assigned to B4. |
| B4 | **Remaining PT++ integration, after B3** | Planned replay compaction, paired spatial reuse, unified direct/indirect PT reservoirs, duplication reduction, vector-weight shading and dual-motion disocclusion recovery, each separately ablated. | User-assigned next stage; no B4 implementation or measurement claim. |

The short labels describe capabilities, not a promise that all named paths run in every capture. The command-line defaults request DI off and GI on; effective activation also depends on realtime/reconstruction settings. Benchmarks explicitly select and record their modes rather than relying on those defaults. An exact B0/B1 baseline remains distinct from its separately identified benchmark-control adapter.

## Labels required beside every result

Use a compact form such as **B1 · native PT · DI off / GI off**, **B1 · DI + GI**, or **B2 · DI + ReSTIR PT · GI off**. Include reuse modes, bounce limits, resolution, reconstruction/cache state and source/executable identity in the supporting receipt. A single table must not turn an available feature into a claim that it was exercised.

The current opaque-room table compares B0/B1 native PT against B2 DI + ReSTIR PT. It does not isolate only the runtime migration or compare the same indirect estimator across all versions. The earlier two-scene B0/B1 DI + GI experiment is a separate track, and its historical frame-cap coverage is unverified.

## Extended comparison coverage

Every new variant's comparison must include rows for **original Convergence**, **original Kitchen**, and the **owned opaque room**. Preserve pinned assets, original scene materials and camera identity. Run a capability preflight before expensive tests. An unsupported or missing case remains visible with its exact reason and next gate; do not silently substitute opaque materials, a different camera, or a different scene.

The original B1 comparison identifies Convergence as `Assets/convergence-test.scene.json` (SHA256 `c3afaa933c5084ba04f8e5100b64bb8b488ab312f4042849705a15e5bf5af549`, exposure 0) and Kitchen as `Assets/kitchen-with-test-stuff.scene.json` (SHA256 `2af5735fb02fc01badd83671641d54b7f1c69859c8c9bcdf335ca95d9daae552`, exposure 2), at 1280×720 and total/diffuse bounce limits 14/2 under Balanced. At the current B2 checkpoint, both original presets are unsupported by its transmission/material gate and binding diffuse-cap restriction. This is a coverage gap, not a measured B2 performance result. A cap3/3 or opaque-only derivative would be a separately labelled diagnostic, not the original-scene comparison.

For each scene/configuration, report timing, image quality and convergence as separate outcomes:

- Matched resolution, transport limits and reconstruction settings; actual DI/GI/PT modes and effective cap receipts.
- Raw HDR error and HDR-FLIP where supported, common display metrics where legacy builds cannot export HDR, finite-reference discrepancy and multiple seeds/processes.
- Quality versus accumulated frames/samples and elapsed time, including startup/history reset and steady state. Distinguish a convergence curve from a single warmed-up screenshot; report unavailable curves as pending.
- Process GPU busy and CPU cadence with repeated runs and tails; renderer memory and temporal/reconstruction coverage when measured. A GPU-busy ratio is not a time-to-equal-quality speedup.

Keep the old capped-or-unverified historical observations inspectable, but do not pool them with newly cap-verified throughput runs. One successful controlled scene does not satisfy this extended scene matrix.

## Summary and lessons learned

The version name alone did not explain which estimator ran. The algorithm label and scene-coverage matrix make the comparison assessable: B1 is the dependency migration, B2 adds path reuse, and B3 isolates PT++ changes. Report missing scenes and unmeasured convergence explicitly so a narrow checkpoint cannot be mistaken for general validation.

## Documentation changes

- 2026-10-28: Added per-variant algorithm labels and mandatory Convergence/Kitchen/opaque-room coverage for new comparisons.

Canonical update2026-10-29: [B1/B4 native-DI quality and cap-verified timing](CANONICAL_NATIVE_DI_RESULTS.md) retains12 original-scene captures and links12 accepted cap-verified timing runs; initial missing-trace attempts remain excluded.

Current scoped measurements: [registered-room B1/B4/B6/B7 comparison](REGISTERED_ROOM_RESULTS.md) includes30quality captures,12timing processes and explicit history settling; [native original-scene report](CANONICAL_NATIVE_DI_RESULTS.md) now includes12accepted timing processes. B6/B7 original-scene support and B8–B10 remain pending.

Current native coverage: [fresh B2/B3/B5 original-scene and room results](NATIVE_MATRIX_RESULTS.md) adds27quality captures and27cap-verified timing processes. [The unified B0–B10 overview](COMPARISON_OVERVIEW.md) includes all versions, current metrics and representative pictures; historical cohorts remain separate.
