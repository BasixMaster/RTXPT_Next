# Versioned quality/performance comparisons

See [the capture/version protocol](../Docs/Research/BENCHMARK_VERSIONS.md), [quality metrics](../Docs/Research/QUALITY_METRICS.md) and [validation](../Docs/Research/VALIDATION.md). `versions.json` identifies the immutable baseline, migration-only B1 and future B2 variants. [First B1 results](../Docs/Research/B1_RESULTS.md) records the initial local timing/quality evidence and its limits. Do not populate metrics from paper tables or synthetic tests.


The [current B2 report](../Docs/Research/B2_RESULTS.md) separates the new native-PT control track from the earlier B1 DI/GI migration experiment. Its raw evidence is in development/2026-10-28-b2-static-opaque; three-process timings and finite-reference image scores are exploratory, not an equal-quality speedup claim.


The [algorithm overview](../Docs/Research/ALGORITHM_VARIANTS.md) and `comparison-matrix.json` identify the active algorithm per result and require original Convergence/Kitchen plus the controlled room for every variant. Unsupported rows remain visible. [B3 activation work](../Docs/Research/B3_IMPLEMENTATION.md) is in progress; the first ablations preserve B2's lighting partition and do not imply complete PT++ integration.
