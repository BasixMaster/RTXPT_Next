# Basix Pathtracing · RTXPT1.9 baseline and B-series roadmap

**Current work:** completed pairing and fresh native PT-only results are in the [comparison overview](COMPARISON_OVERVIEW.md). [Replay compaction](B10_GAUSSIAN_PAIRING.md#replay-compaction--active-implementation-checkpoint) passes11captured-frame exact GPU oracles; queue timing/sequences and full B10 remain pending.

[B10 Gaussian GPU pairing and extended scene checks](B10_GAUSSIAN_PAIRING.md): full-resolution pictures, quality tradeoffs and18cap-verified adjacent/Gaussian timing runs; replay compaction remains next.

[B10 GPU paired/vector pilot](B10_PAIRED_PILOT.md): reciprocal shared shifts, separate vector shading and three-scene development evidence. Full PT++ remains pending.

[B8–B10 staged implementation and current GPU evidence](B8_STAGED_IMPLEMENTATION.md): disjoint initial-GI/PT-long foundation and limited PT++ ablation; full GI reuse and remaining B10 GPU mechanisms remain pending. Brightness work is deferred.

[Calibrated prefix-throughput investigation](PREFIX_THROUGHPUT.md): no clamp activation observed in the sampled packed weights; defaults unchanged.

[DI-stage isolation: initial sampling versus temporal/spatial reuse](DI_REUSE_ISOLATION.md).

[DI brightness follow-up: matched material-precision ablation](GBUFFER_PRECISION.md). Canonical defaults remain unchanged.

[**B0–B10 comparison overview: performance, quality and pictures**](COMPARISON_OVERVIEW.md) shows all eleven versions for each required scene, including missing or unsupported results.

[Scene-fix follow-up: finite MIS targets, five-seed quality and remaining limits](FINITE_SHIFT_GUARD.md).

User-confirmed numbering, 2026-10-29: **B0 is unchanged RTXPT 1.9 with its original defaults, renderer/dependency pins and scene assets.** The repository is RTXPT_Next. Read the [canonical B0–B10 mapping](VERSION_MAPPING.md); legacy files/tags/data IDs keep their earlier names and numeric results. `External/RTXDI-SDK` remains reference-only.

| Version | Short algorithm overview | Current status |
|---|---|---|
| B0 | Unchanged RTXPT 1.9 reference | Original defaults and source303b408/runtimea14e079/Assets a56be4e preserved |
| B1 | Native PT + DI 3.0; GI off | Original-scene and registered-room quality/timing measured |
| B2 | Native PT + DI 3.0 + GI 3.0 | Original-scene and registered-room quality/timing measured |
| B3 | Native PT / runtime 3.1; DI/GI off | Fresh native-only quality/timing measured on all three scenes |
| B4 | Native PT + DI 3.1; GI off | Original-scene and registered-room quality/timing measured |
| B5 | Native PT + DI 3.1 + GI 3.1 | Original-scene and registered-room quality/timing measured |
| B6 | ReSTIR PT; DI/GI off | Registered-room quality/timing/history measured; original scenes have guarded development images; quality acceptance pending |
| B7 | ReSTIR PT + DI 3.1; GI off | Scoped opaque checkpoint `de9fe651`; wider material/scene validation pending |
| B8 | ReSTIR PT + DI 3.1 + GI 3.1 | Disjoint initial-GI development executes; full GI reuse/acceptance pending |
| B9 | B8 + limited PT++ | GI-initial-only footprint/roulette development ablation executes; full B8/B9 pending |
| B10 | B8 + full remaining PT++ | Gaussian reciprocal-pair/vector GPU development executes; full PT++ pending |

Every result states its actual algorithm, settings and source identity. Historical old-B0/old-B1 Convergence/Kitchen DI+GI rows map to B2/B5. The old opaque-room comparison maps to a separately labelled B0 native-control raw preset, B3 native control and B7 DI+PT. Its DI-off0.806ms row is not a B4 native-DI comparator. New B1/B4 and room B4/B7 measurements now supply DI-on controls; equal-time sample sweeps remain pending. The branch `baseline/rtxpt-1.9` and tag `rtxpt-1.9-baseline` retain exact upstream source; a moving main branch is not an unnamed baseline.

## Start here

- [Canonical B0–B10 mapping and preserved legacy crosswalk](VERSION_MAPPING.md)
- [Algorithm overview and mandatory scene coverage](ALGORITHM_VARIANTS.md)
- [B7 opaque checkpoint: retained legacy B2 report](B2_RESULTS.md)
- [B7 limited-feature ablation: retained legacy B3 report](B3_RESULTS.md)
- [Legacy limited PT++ activation implementation](B3_IMPLEMENTATION.md)
- [B10 remaining PT++ gates: retained legacy B4 filename](B4_IMPLEMENTATION.md)
- [NVIDIA engineering whitepapers and next profiling steps](NVIDIA_WHITEPAPERS.md)
- [Historical B2/B5 DI+GI comparison: retained legacy B1 report](B1_RESULTS.md)
- [Legacy PT bridge implementation history, now B6/B7 foundation](B2_IMPLEMENTATION.md)
- [Implementation roadmap](ROADMAP.md)
- [Version comparison and capture protocol](BENCHMARK_VERSIONS.md)
- [Image quality metrics](QUALITY_METRICS.md)
- [RTXDI3.1 reference PT++ audit](PTPP_AUDIT.md)
- [Architecture](ARCHITECTURE.md), [RTXDI vs RTXPT](RTXDI_VS_RTXPT.md), [scene compatibility](SCENE_COMPATIBILITY.md)
- [Seven focus papers A](FOCUSED_A.md), [focus papers B](FOCUSED_B.md), [all20 catalog](PAPER_CATALOG.md), [breadth notes](BREADTH.md)
- [Validation](VALIDATION.md), [source terms](SOURCES_AND_RIGHTS.md), [research map](RESEARCH_MAP.md)
- [Offline searchable study](index.html), [structured evidence](evidence/index.html), [verification](verification.json)

## Summary and lessons learned

RTXDI is sampling machinery; RTXPT is the renderer. Canonical IDs now distinguish runtime3.0/3.1, actual DI/GI/PT modes and PT++ scope. B8 sharing must be correct before B9/B10 can claim it. Runtime3.1 already contains some PT++ machinery; record it as inherited. Preserve original scenes, source/settings identity and B0 defaults, and report quality, complete-frame timing, convergence and memory together. Paper speedups and historical DI-off controls do not replace matched native-DI/equal-time comparisons.


## Documentation changes

- 2026-10-29: Adopted canonical B0–B10 IDs with a legacy crosswalk; preserved all historical refs and numerical results.
- 2026-10-28: Added short algorithm labels for each variant and required original Convergence/Kitchen plus controlled-scene comparisons; B3 development started without a performance claim.
- 2026-10-28: Shared image preview opens pictures in place, supports keyboard activation, and closes with Escape or Close while restoring focus. The central HTML template and Documenter guidance share the same behavior.

Canonical update2026-10-29: [B1/B4 native-DI quality and cap-verified timing](CANONICAL_NATIVE_DI_RESULTS.md) retains12 original-scene captures and links12 accepted cap-verified timing runs; initial missing-trace attempts remain excluded.

Current scoped measurements: [registered-room B1/B4/B6/B7 comparison](REGISTERED_ROOM_RESULTS.md) includes30quality captures,12timing processes and explicit history settling; [native original-scene report](CANONICAL_NATIVE_DI_RESULTS.md) now includes12accepted timing processes. B6/B7 original-scene support and B8–B10 remain pending.

Current native coverage: [fresh B2/B3/B5 original-scene and room results](NATIVE_MATRIX_RESULTS.md) adds27quality captures and27cap-verified timing processes. [The unified B0–B10 overview](COMPARISON_OVERVIEW.md) includes all versions, current metrics and representative pictures; historical cohorts remain separate.

Fresh requested control: [RTXPT1.9 PT-only override](NATIVE_MATRIX_RESULTS.md#fresh-rtxpt19-pt-only-override) now has9cap-verified timing processes and9PNG captures across Room and original Convergence/Kitchen. Native PT/NEE on, DI/GI off; original B0 defaults remain preserved. HDR export is unsupported in that unchanged binary.
