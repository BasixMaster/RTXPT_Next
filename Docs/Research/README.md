# Basix Pathtracing · RTXPT1.9 baseline and B-series roadmap

Final accepted basis, checked2026-10-28: **RTXPT1.9 renderer and its original scene assets.** The repository is named RTXPT_Next. `External/RTXDI-SDK` links RTXDI3.1 as a source reference for future work; it does not change the baseline runtime.

| Version | Meaning | Current status |
|---|---|---|
| RTXPT1.9 baseline (B0 alias) | Exact upstream renderer303b408, runtimea14e079, Assets a56be4e | Source baseline and original scenes checked out; no local rendering results |
| B1 | Adopt RTXDI3.1 with compatible renderer integration | Planned; not implemented |
| B2 and later | Isolated, measured optimizations and paper-based extensions | Planned; not implemented |

User-selected scope for this pass: baseline, research and roadmap first. No renderer/shader algorithm implementation or benchmark result is claimed. The branch `baseline/rtxpt-1.9` and tag `rtxpt-1.9-baseline` point to the exact upstream baseline, distinct from documentation commits on main. Do not benchmark a moving main branch as an unnamed baseline.

## Start here

- [Implementation roadmap](ROADMAP.md)
- [Version comparison and capture protocol](BENCHMARK_VERSIONS.md)
- [Image quality metrics](QUALITY_METRICS.md)
- [RTXDI3.1 reference PT++ audit](PTPP_AUDIT.md)
- [Architecture](ARCHITECTURE.md), [RTXDI vs RTXPT](RTXDI_VS_RTXPT.md), [scene compatibility](SCENE_COMPATIBILITY.md)
- [Seven focus papers A](FOCUSED_A.md), [focus papers B](FOCUSED_B.md), [all20 catalog](PAPER_CATALOG.md), [breadth notes](BREADTH.md)
- [Validation](VALIDATION.md), [source terms](SOURCES_AND_RIGHTS.md), [research map](RESEARCH_MAP.md)
- [Offline searchable study](index.html), [structured evidence](evidence/index.html), [verification](verification.json)

## Summary and lessons learned

RTXDI is sampling machinery; RTXPT is a renderer consuming it. RTXPT1.9 uses RTXDI3.0, while the linked SDK3.1 reference implements only part of PT++. B1 must align APIs and explicitly integrate desired runtime capabilities. B2+ should change one major estimator/scheduling mechanism at a time. Preserve source pins, scene/camera identity and reference settings across every comparison. Report quality, complete-frame time and VRAM together. Reported paper gains are not measurements of this project.
