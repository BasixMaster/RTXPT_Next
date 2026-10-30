# Canonical B0–B16 and sampling variants: legacy result mapping

User-confirmed numbering, 2026-10-29. **B0 is the unchanged RTXPT 1.9 reference with its original defaults and dependency/scene pins.** It is not redefined as a native-only raw preset. Every result shows a canonical variant, actual active modes and immutable source/settings identity.

## Canonical algorithm table

| ID | Short algorithm overview | Configuration and evidence boundary |
|---|---|---|
| **B0** | **Unchanged RTXPT 1.9 reference** | Original upstream defaults; source `303b408ab81790a5051abd7573830b7a4112eb8e`, RTXDI 3.0 `a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6`, Assets `a56be4ed65029d2733fd02f00f4027ffd541eda8`. A raw control with overrides is separately labelled. |
| **B1** | **RTXPT native PT + DI 3.0** | DI on; GI and ReSTIR PT off. Original-scene DI quality and cap-verified timing measured. |
| **B2** | **RTXPT native PT + DI 3.0 + GI 3.0** | DI/GI on; ReSTIR PT off. Fresh original-scene and registered-room quality and cap-verified timing are measured. |
| **B3** | **RTXPT native PT / runtime 3.1** | DI/GI/ReSTIR PT off. Fresh native-only results cover all three required scenes; they are not a ReSTIR direct-light baseline. |
| **B4** | **RTXPT native PT + DI 3.1** | DI on; GI and ReSTIR PT off. Original-scene DI quality and cap-verified timing measured; priority comparator to B1 and B7. |
| **B5** | **RTXPT native PT + DI 3.1 + GI 3.1** | DI/GI on; ReSTIR PT off. Fresh original-scene and registered-room quality and cap-verified timing are measured. |
| **B6** | **ReSTIR PT / DI and GI off** | Separate DI/GI estimators off; existing native direct/fallback terms remain until explicitly replaced by a unified-lighting partition. No complete extended-scene benchmark is claimed. |
| **B7** | **ReSTIR PT + DI 3.1** | DI direct plus PT indirect; GI off. Corrected static opaque checkpoint `de9fe651`; original-scene gates remain unresolved. |
| **B8** | **ReSTIR PT + DI 3.1 + GI 3.1** | NVIDIA non-directional GI temporal/spatial reuse executes on disjoint GI-short/PT-long domains. Full-resolution static quality is measured with mixed results; uncapped timing measured; canonical validation remains pending. |
| **B9** | **B8 + limited PT++** | B8 NVIDIA GI reuse retained: footprint/initial roulette in Room, full-prefix roulette-only original-scene ablations. Eight GPU checks pass; replicated quality and uncapped timing measured; original-scene footprint unsupported. The historical GI-off pilot is not B9. |
| **B10** | **B8 + full remaining PT++** | Gaussian reciprocal-pair/vector GPU development executes. Simultaneous multi-neighbor reuse, replay queues, remaining mechanisms and full validation remain pending. No complete-paper implementation claim. |

## Extended roadmap and sampling branches

Confirmed2026-10-30; B0–B9 and legacy evidence IDs remain unchanged. Future variants remain unmeasured until implemented and exercised.

| Version | Your cumulative definition | Current status / implementation gate |
|---|---|---|
| **B10** | **Full PT++** | Partial. Duplication comparison complete; finite RIS/PSS MIS active; environment/composition, dual motion and broader validation pending. |
| **B10.75** | B10 with **0.75 spp** | Planned sampling branch; reuse RTXPT 1.9 native sub-sampling mode 1. |
| **B10.50** | B10 with **0.50 spp** | Planned sampling branch; reuse RTXPT 1.9 native sub-sampling mode 2. |
| **B10.25** | B10 with **0.25 spp** | Planned sampling branch; reuse RTXPT 1.9 native sub-sampling mode 3. |
| **B11** | B10 + **Compatibility-Guided Neighbor Selection active** | Planned after B10; integrate the selector, storage, sharing and normalization. |
| **B12** | B11 + **Stochastic Pairwise MIS** | Planned after B11; validate proposal support and combined weights. |
| **B13** | B12 + **ReSTIR LoD** | Planned after B12; validate geometry correspondence and shift Jacobians. |
| **B14** | B13 + **ReSTIR BDPT with LW version** | Planned after B13; preserve the requested LW designation and specify its exact scope before implementation. |
| **B15** | B14 + **ReSTIR PG** | Planned after B14; validate guiding proposals, training cost and replay. |
| **B16** | B15 + **Multi-Layer Reservoir Splatting** | Planned after B15; validate layer/visibility ownership and accumulation. |

Fractional rates reuse RTXPT1.9 sub-sampling. Its current ReSTIR guard remains in place until sparse-reservoir/history and weighting integration is validated. [Execution roadmap](ROADMAP.md).

## Legacy crosswalk: preserve evidence identities

Old B1 meant a dependency migration, old B2 meant the PT bridge and old B3 meant two PT++ activations. Frozen filenames, tags, data IDs, branch names and figures keep those strings. **They are legacy labels, not the canonical IDs above.** No old numerical value or executable is renamed to imply a new measurement.

| Retained legacy identity | Actual algorithm / scope | Canonical interpretation |
|---|---|---|
| `rtxpt-1.9-baseline` / `baseline/rtxpt-1.9`, source `303b408` | Unchanged upstream source/assets/defaults reference | B0 reference. |
| `B1_RESULTS.md`, old B0 DI+GI rows | Native PT + DI 3.0 + GI 3.0, original Convergence/Kitchen | B2 historical observations; cap coverage unverified. |
| Legacy tag `B1`, source `7010bb4cda80788eb13cd9ee6143eb2f52a5b6ee` | Runtime/API migration to 3.1; actual mode depends on each result | Retained source identity, **not canonical B1**. DI+GI rows map to B5; native-only rows map to B3. |
| `B1_RESULTS.md`, old B1 DI+GI rows | Native PT + DI 3.1 + GI 3.1, original Convergence/Kitchen | B5 historical observations; cap coverage unverified. |
| Opaque-room old B0 native control, GPU busy 0.803 ms | Upstream source plus benchmark-controls-v1; DI/GI off and raw overrides | **B0 native-control preset**, separate from unchanged B0 defaults. Not canonical B1, whose DI is on. |
| Opaque-room old B1 native control, GPU busy 0.806 ms | Migrated source plus benchmark-controls-v1; DI/GI off | B3 native-control observation. Not canonical B4, whose DI is on. |
| Old B2 checkpoint `de9fe651903f203327830e7361ac4237e00d508c`, GPU busy 1.519 ms | DI 3.1 + ReSTIR PT, GI off, static opaque room | B7 scoped development evidence. |
| Old B3 footprint/roulette pilot, `a7428c8`, branch `b3/ptpp-activation`, dataset `2026-10-28-b3-activation` | B7 partition, GI off, four fixed/footprint/roulette settings | B7 limited-feature ablation. **Not B9**, because B8 sharing was absent. |
| Old `B4_IMPLEMENTATION.md` remaining-PT++ plan | Design/oracle gates; no measured full port | Remaining work belongs to B10; retained filename preserves links. |

## Inherited PT++ is not a new B9 gain

Runtime 3.1 already supplies 64-byte PT reservoirs, forced terminal NEE reconnection and optional footprint/history/roulette machinery. Source presence is not execution. The historical GI-off pilot wired footprint and initial-only roulette and measured isolated effects; it did not implement reciprocal pairing, explicit replay compaction, unified primary direct/indirect reservoirs, all-candidate vector shading or dual-motion disocclusion recovery. Duplication reduction needs its actual producer/lifecycle and remains deliberately biased. Record inherited mechanisms rather than counting them again. CGNS is a separate paper and is not reciprocal pairing.

## Fair comparisons and paper context

Matched **B1 versus B4** native-PT-plus-DI captures and the registered-room B4/B7 comparison are now measured. The legacy 0.806 ms native control had DI off and cannot establish the native PT+DI3.1 baseline's cost or quality; use the new measured DI-on controls.

The referenced original ReSTIR PT paper's §9.3 uses approximately equal-time comparisons with adjusted sample counts. Our fixed-1spp opaque-room pilot is a different experiment. Add measured sample/candidate sweeps and quality-versus-cost curves before comparable equal-time/equal-quality conclusions; do not transplant paper speedups.

Every canonical variant retains visible original Convergence, original Kitchen and owned opaque-room rows. Preserve scene/material/camera identities and show missing, unsupported and historical-unverified-cap cases. The PT foundation's transmission/medium and original 14/2 binding diffuse-budget gates are not removed by renumbering or planned B8 sharing.

## Summary and lessons learned

Canonical IDs separate runtime, DI/GI/PT combination and PT++ scope. Legacy evidence stays intact under this crosswalk. Correct B8 sharing must precede B9/B10 claims, and missing native-DI baselines require measurements rather than inference from DI-off controls.

## Changes

- 2026-10-29: Applied user-confirmed B0–B10 numbering without changing historical references or numeric results.

Canonical update2026-10-29: [B1/B4 native-DI quality and cap-verified timing](CANONICAL_NATIVE_DI_RESULTS.md) retains12 original-scene captures and links12 accepted cap-verified timing runs; initial missing-trace attempts remain excluded.

Current scoped measurements: [registered-room B1/B4/B6/B7 comparison](REGISTERED_ROOM_RESULTS.md) includes30quality captures,12timing processes and explicit history settling; [native original-scene report](CANONICAL_NATIVE_DI_RESULTS.md) now includes12accepted timing processes. B6/B7 original-scene support and B8–B10 remain pending.

Current native coverage: [fresh B2/B3/B5 original-scene and room results](NATIVE_MATRIX_RESULTS.md) adds27quality captures and27cap-verified timing processes. [The unified B0–B10 overview](COMPARISON_OVERVIEW.md) includes all versions, current metrics and representative pictures; historical cohorts remain separate.

Current development: [B8–B10 staged implementation](B8_STAGED_IMPLEMENTATION.md) records the NVIDIA GI approximation, full-resolution original-scene checks and64-frame quality sequences. Earlier limited PT++ ablations retain their initial-only GI scope; remaining B10 mechanisms and canonical acceptance remain pending. Brightness fixes are deferred.

Current timing checkpoint2026-10-29: [Gaussian versus adjacent pair/vector development](B10_GAUSSIAN_PAIRING.md#frozen-adjacent-versus-gaussian-timing) completes18cap-verified processes over all three scenes. Small descriptive timing differences and mixed quality do not promote full B10. Explicit replay compaction remains next; brightness fixes remain deferred.

Fresh requested control: [RTXPT1.9 PT-only override](NATIVE_MATRIX_RESULTS.md#fresh-rtxpt19-pt-only-override) now has9cap-verified timing processes and9PNG captures across Room and original Convergence/Kitchen. Native PT/NEE on, DI/GI off; original B0 defaults remain preserved. HDR export is unsupported in that unchanged binary.

Latest scoped checkpoint2026-10-29: [one-neighbor spatial replay queue](B10_GAUSSIAN_PAIRING.md#replay-compaction--active-implementation-checkpoint) passes11captured-frame exact GPU oracles and2queue-disabled regressions. Queue timing, full multi-frame histories, temporal queues, simultaneous multi-neighbor reuse and remaining B10 mechanisms are pending. No full PT++ or speedup claim.
