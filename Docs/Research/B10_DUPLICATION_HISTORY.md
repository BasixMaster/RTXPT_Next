# B10 development: duplication-based temporal history reduction

## Summary and lessons learned

The application now implements a real duplication-map producer and connects the previous frame's counts to RTXDI3.1 temporal history reduction. **Six64-frame GPU cases pass**, with the feature on/off across Room, original Convergence and original Kitchen. All three enabled maps match an independent CPU count oracle exactly, and temporal reuse reads nonzero counts. The feature is an opt-in, deliberately biased B10 development mode; **full B10 and B11 remain incomplete**.

The extended quality cohort is incomplete: fourteen eligible64-frame sequences are preserved, with four original-scene cases still missing. Startup failures with exit code `0xC0000409` occurred with the feature both enabled and disabled. No performance cohort started, and no quality or speed improvement is claimed. The cause is unresolved; these failures are not evidence that the duplication estimator caused the crash.

## Implementation

`ComputeDuplicationMap.hlsl` counts other pixels sharing the selected reservoir's nonzero sample ID in a17×17 neighborhood. A16×16 compute group loads a32×32 shared tile including its radius8 halo. Bounds checks exclude out-of-view taps; empty IDs are ignored; the center is excluded; counts are capped at255 to match the supplied RTXDI3.1 map's range. This integrates the supplied behavior into the application; it is not a new paper algorithm.

The integer map has its own buffer and bindingu27, separate from the vector-shading/CGNS scratch storage. Temporal reuse consumes the previous completed map. The producer runs after current final resampling, with UAV barriers before subsequent use. Resource/history resets clear the map; the disabled path binds a minimum-size dummy and dispatches no producer. Changing reduction settings invalidates PT history. Static startup/history is tested; moving-camera, resize and interactive reset stress remain pending.

`--pt-duplication-history-validation` selects the development feature in the capture tool. It uses the existing SDK temporal reduction strength0.5 and keeps spatial duplication/decorrelation controls disabled. Standalone strict controls keep the feature off. The queue diagnostics retain sticky sequence failures in slots92–95; four new map counters occupy96–99.

The count oracle validates exactly what the GPU produced, using independently decoded final packed reservoir IDs and weights. Each enabled case also rejects a one-count corruption in memory. This establishes producer and consumer activation, not correctness of the underlying transport estimator or an unbiasedness result for a deliberately biased history cap.

## GPU gates

| Case | Resolution | Nonzero current-map pixels | Maximum current count | Temporal map reads | Nonzero temporal reads |
|---|---:|---:|---:|---:|---:|
| Room on |177×91|1,196|6|8,645|1,166|
| Convergence on |1280×720|158,104|59|752,110|157,727|
| Kitchen on |1280×720|222,571|25|808,152|222,554|

Disabled controls have zero map production and reads. All six cases compare64queued-history frames with zero packed reservoir/RGB scheduling mismatches or overflow:384frames total. Final map counts and temporal reads refer to different frames by design. Room uses footprint reconnection; original scenes retain full-prefix replay. Both policies retain B8 GI3, DI reuse, paired Gaussian spatial reuse, initial-only roulette0.8 and one neighbor.

[Exact statistics and scope](../../Benchmarks/development/2026-10-30-duplication-history/diagnostics.json) · [Source overlay](../../Benchmarks/development/2026-10-30-duplication-history/source.json) · [Excluded attempts](../../Benchmarks/development/2026-10-30-duplication-history/excluded-attempts.json)

## Quality, performance and remaining work

The requested extended comparison is three seeds47/1019/4093 × two policies × three scenes ×64frames. An initial capture stopped when the system volume filled. Its partial data is retained; the fresh cohort writes to a separately approved volume. Thirteen captures completed there, and one additional capture was independently reverified after its workbench wrapper failed to import a postprocessing module. The original failed files and wrapper error are retained. Repeated original-scene startup failures then prevented completion. None are silently substituted or counted as valid frames.

Portable tools now include `run_b10_duplication_sequences.py`, `evaluate_b10_duplication_sequences.py` and `duplication_contract.py`. The evaluator supports an explicit case index for separately acquired continuation captures, verifies frozen reference hashes and uses the existing HDR/LDR-FLIP settings. It must not publish a full three-seed comparison from the current incomplete cohort. Timed runs support explicit replay-queue and duplication controls; uncapped driver/RTSS receipts and restoration remain mandatory when timing resumes.

Next: diagnose startup reliability, complete the missing quality cases, then evaluate convergence/FLIP and matched repeated timing. Remaining full PT++ work still includes unified primary direct/indirect reservoirs, dual-motion recovery and broader temporal/multiple-neighbor scheduling. The [B11 integration requirements](B11_INTEGRATION.md) remain unchanged. Brightness investigation stays deferred.

Changelog:2026-10-30 — integrated and validated duplication producer/temporal consumer; preserved incomplete quality and startup failures; no promotion.
