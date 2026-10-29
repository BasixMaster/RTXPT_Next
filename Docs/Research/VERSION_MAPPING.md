# Canonical B0–B10 variants and legacy result mapping

User-confirmed numbering, 2026-10-29. **B0 is the unchanged RTXPT 1.9 reference with its original defaults and dependency/scene pins.** It is not redefined as a native-only raw preset. Every result shows a canonical variant, actual active modes and immutable source/settings identity.

## Canonical algorithm table

| ID | Short algorithm overview | Configuration and evidence boundary |
|---|---|---|
| **B0** | **Unchanged RTXPT 1.9 reference** | Original upstream defaults; source `303b408ab81790a5051abd7573830b7a4112eb8e`, RTXDI 3.0 `a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6`, Assets `a56be4ed65029d2733fd02f00f4027ffd541eda8`. A raw control with overrides is separately labelled. |
| **B1** | **RTXPT native PT + DI 3.0** | DI on; GI and ReSTIR PT off. Original-scene DI quality and cap-verified timing measured. |
| **B2** | **RTXPT native PT + DI 3.0 + GI 3.0** | DI/GI on; ReSTIR PT off. Historical original-scene observations exist, with unverified cap coverage. |
| **B3** | **RTXPT native PT / runtime 3.1** | DI/GI/ReSTIR PT off. Raw native-control observations exist; they are not a ReSTIR direct-light baseline. |
| **B4** | **RTXPT native PT + DI 3.1** | DI on; GI and ReSTIR PT off. Original-scene DI quality and cap-verified timing measured; priority comparator to B1 and B7. |
| **B5** | **RTXPT native PT + DI 3.1 + GI 3.1** | DI/GI on; ReSTIR PT off. Historical original-scene observations exist, with unverified cap coverage. |
| **B6** | **ReSTIR PT / DI and GI off** | Separate DI/GI estimators off; existing native direct/fallback terms remain until explicitly replaced by a unified-lighting partition. No complete extended-scene benchmark is claimed. |
| **B7** | **ReSTIR PT + DI 3.1** | DI direct plus PT indirect; GI off. Corrected static opaque checkpoint `de9fe651`; original-scene gates remain unresolved. |
| **B8** | **ReSTIR PT + DI 3.1 + GI 3.1** | Planned shared configuration: requires disjoint GI/PT contributions or valid MIS. The present alternative-mode guard does not implement it. |
| **B9** | **B8 + limited PT++** | Planned footprint/inverse-footprint reconnection and initial-generation-only roulette on a validated B8 foundation. The existing GI-off pilot is not B9. |
| **B10** | **B8 + full remaining PT++** | Authorized future work, dependent on correct B8 sharing and individual correctness/feature/performance validation. No complete-paper implementation claim. |

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
