# Basix Pathtracing project guidance

Root basis is RTXPT1.9 including its original Assets pin. `baseline/rtxpt-1.9` and `rtxpt-1.9-baseline` identify unchanged upstream303b408. B1 means future RTXDI3.1 integration updates; B2+ means measured isolated optimizations. `External/RTXDI-SDK` is reference-only until an explicit integration is implemented. Preserve original SDK/component licenses.

Read Docs/Research/README.md, ROADMAP.md, PTPP_AUDIT.md and Benchmarks/versions.json. Distinguish source inspection, planned work, active features and measured results. Paper numbers and synthetic metric tests are not local renderer results. Baseline runtime External/Rtxdi remainsa14e079 until the B1 implementation task.

Changes inside submodules require explicit ownership and reachable child commits. Preserve exact baseline and scene pins for comparisons. Document estimator PDFs/Jacobians/RNG and bias controls; validate raw HDR before reconstruction, then quality, total timing, VRAM and temporal behavior. Exclude paper caches, credentials and private host telemetry from exports.
