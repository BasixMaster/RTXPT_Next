# Algorithm overview: B0, B1, B2, B3 and B4

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
