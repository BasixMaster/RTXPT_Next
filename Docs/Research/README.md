# Basix Pathtracing · RTXPT1.9 baseline and B-series roadmap

Final accepted basis, checked2026-10-28: **RTXPT1.9 renderer and its original scene assets.** The repository is named RTXPT_Next. B0 retains its original RTXDI3.0 runtime. B1 adopts runtime3.1 for the existing DI/GI passes. `External/RTXDI-SDK` remains reference-only.

| Version | Short algorithm overview | Current status |
|---|---|---|
| RTXPT1.9 baseline (B0 alias) | RTXPT native PT + RTXDI 3.0 DI/GI | Exact upstream renderer303b408, runtimea14e079 and Assets a56be4e; preserved baseline |
| B1 | RTXPT native PT + RTXDI 3.1 DI/GI | Migration implemented at `7010bb4`; [B1 results](B1_RESULTS.md) |
| B2 | RTXPT + ReSTIR DI + ReSTIR PT; GI is an alternative indirect mode | Static opaque checkpoint at `de9fe651`; broader validation pending, not promoted |
| B3 | B2 DI + ReSTIR PT + footprint/initial-only roulette | Scoped activation checkpoint; wider scene validation remains pending |
| B4 | Remaining PT++ estimator and scheduling techniques | Starts after B3 is preserved; individual oracles and ablations before a combined preset |

These labels describe available paths; every result also states the actual active configuration. Historical Convergence/Kitchen B0/B1 tests used DI + GI. The current opaque-room controls use B0/B1 native PT with DI/GI off versus B2 DI + ReSTIR PT, GI off. Read the [algorithm overview and extended scene policy](ALGORITHM_VARIANTS.md) before comparing them. The branch `baseline/rtxpt-1.9` and tag `rtxpt-1.9-baseline` point to the exact upstream baseline, distinct from documentation commits on main. Do not benchmark a moving main branch as an unnamed baseline.

## Start here

- [B0–B4 algorithm overview and mandatory scene coverage](ALGORITHM_VARIANTS.md)
- [Corrected B2 comparison and limitations](B2_RESULTS.md)
- [B3 measured activation results](B3_RESULTS.md)
- [B3 PT++ activation and ablation status](B3_IMPLEMENTATION.md)
- [B4 remaining PT++ implementation gates](B4_IMPLEMENTATION.md)
- [NVIDIA engineering whitepapers and next profiling steps](NVIDIA_WHITEPAPERS.md)
- [First B1 results and limitations](B1_RESULTS.md)
- [B2 integration and B3 PT++ implementation status](B2_IMPLEMENTATION.md)
- [Implementation roadmap](ROADMAP.md)
- [Version comparison and capture protocol](BENCHMARK_VERSIONS.md)
- [Image quality metrics](QUALITY_METRICS.md)
- [RTXDI3.1 reference PT++ audit](PTPP_AUDIT.md)
- [Architecture](ARCHITECTURE.md), [RTXDI vs RTXPT](RTXDI_VS_RTXPT.md), [scene compatibility](SCENE_COMPATIBILITY.md)
- [Seven focus papers A](FOCUSED_A.md), [focus papers B](FOCUSED_B.md), [all20 catalog](PAPER_CATALOG.md), [breadth notes](BREADTH.md)
- [Validation](VALIDATION.md), [source terms](SOURCES_AND_RIGHTS.md), [research map](RESEARCH_MAP.md)
- [Offline searchable study](index.html), [structured evidence](evidence/index.html), [verification](verification.json)

## Summary and lessons learned

RTXDI is sampling machinery; RTXPT is a renderer consuming it. RTXPT1.9 uses RTXDI3.0, while the linked SDK3.1 reference implements only part of PT++. B1 aligns the existing DI/GI APIs; it does not activate new PT capabilities. B2 integrates the ReSTIR PT path; B3 exposes and extends PT++ one mechanism at a time. The RTXDI3.1 PT baseline already inherits some PT++ machinery, which is recorded rather than counted as a new B3 gain. Preserve source pins, scene/camera identity and reference settings across every comparison. Report quality, complete-frame time and VRAM together. Reported paper gains are not measurements of this project.


## Documentation changes

- 2026-10-28: Added short algorithm labels for each variant and required original Convergence/Kitchen plus controlled-scene comparisons; B3 development started without a performance claim.
- 2026-10-28: Shared image preview opens pictures in place, supports keyboard activation, and closes with Escape or Close while restoring focus. The central HTML template and Documenter guidance share the same behavior.
