# B10 development: Gaussian reciprocal pairing on the GPU

Three Gaussian-scale reciprocal tables now execute on the GPU, with frame-wide integer flips, rotations and offsets. The renderer selects **one table per frame** and retains the existing one-neighbor pair-MIS/vector estimator. This extends the [adjacent-pair pilot](B10_PAIRED_PILOT.md); it does not implement simultaneous three-neighbor reuse or complete PT++. Brightness work remains deferred.

## Implementation and controls

`--ptGaussianPairingValidation true` requires the explicit paired-spatial development path. The previous adjacent policy remains the default/control. Table-policy changes invalidate PT history and recreate the corresponding resources. Original scenes, materials, baseline refs and submodules are unchanged.

The application independently implements the [PT++ paper's section3 link-shuffle construction](https://cwyman.org/papers/i3d26_ReSTIRPT++.pdf): duplicated link IDs, alternating offset2×2 shuffles, race-free CPU pair resolution and signed periodic offsets. Its three deterministic tables have sizes254,230 and210, with declaredσ16. They use `RG32_SINT`, eight bytes per entry, totaling **1,292,128 bytes**. The inactive legacy/adjacent path binds an eight-byte dummy resource. This is not the paper's compact16-bit storage; packing remains a separate optimization.

| Table size | Entries | Measured RMS x | Measured RMS y | Mean radial distance |
|---|---:|---:|---:|---:|
| 254 | 64,516 | 15.904 | 16.052 | 20.020 |
| 230 | 52,900 | 15.949 | 15.868 | 19.909 |
| 210 | 44,100 | 16.015 | 16.155 | 20.164 |

These are finite generated-table moments, consistent with the declared scale, not a formal statistical proof of normality. A native C++ fixture tests the actual producer, deterministic bytes, reciprocal/non-self links and radial bounds. An independent NumPy validator checks the payload and matrix-conjugated frame transforms, including negative coordinates and tile seams. An adjacent-table negative control fails the Gaussian-scale gate.

The shader uses the **same global transform for every pixel in a frame**, then applies its inverse after table lookup. It preserves reciprocity across periodic tiles. Out-of-view links retain the original pixel estimate; they are not clamped into other pairs. Pair ownership now uses the full linear pixel index, allowing partners on different rows. The disabled policy has an explicit branch around table access, protecting the dummy-resource control path. Final captures exercise both policies; the Gaussian packed PT state is byte-identical before/after this guard at the same frame index. Separate-process HDR totals differ beginning at DI, so this does not establish whole-image equality. Cohort and final-guard source/cache identities are archived separately.

## GPU and boundary gates

GPU readback of all three tables is byte-identical to the native producer in every diagnostic run: SHA256 `661e8fddc377bef59f419be9377492473b27aef082af943e630b9cc2652f00dc`. The shader also checks reverse links and records nonlocal pair use, proving that the new policy executes rather than retaining adjacent offsets.

| Diagnostic | Resolution | Material-compatible pairs | Fallback pixels | Directed shifts |
|---|---|---:|---:|---:|
| Odd-height room | 176×91 | 1,161 | 13,694 | 1,319 |
| Room cap1 | 640×360 | 44,530 | 141,340 | 0 |
| Room cap2 | 640×360 | 44,530 | 141,340 | 0 |
| Room cap4 | 640×360 | 44,837 | 140,726 | 49,123 |
| Original Convergence | 1280×720 | 310,275 | 301,050 | 244,410 |
| Original Kitchen | 1280×720 | 280,570 | 360,460 | 41,042 |
| Room, temporal + limited PT++ | 640×360 | 44,837 | 140,726 | 88,829 |

All seven diagnostics have zero reverse-link failures and zero nonfinite vector/positive-weight reservoir outputs. Every output pixel is accounted for by **2×pairs + fallback pixels**; directed shifts never exceed two per eligible pair. Empty sources require no trace. Positive-weight PT paths retain light-inclusive length≥4, and cap1/2 PT-long output remains exactly zero.

The combined temporal/footprint/0.8-survival run recorded210,046 initial roulette tests and zero replay roulette tests. The first odd-height run measured6,384 nonlocal in-view pairs and a maximum squared link distance4,360. These are work/activation counters, not GPU timings.

GI remains initial-only. The original scenes use their original14/2 total/diffuse limits under the existing full-prefix replay guard. The room uses cap4/4. All diagnostics retain raw same-frame component captures locally.

## Quality: mixed result, not promoted

Two64-frame **640×360** room sequences compare adjacent versus Gaussian pairing under the same one-neighbor/vector-shading configuration, DI initial sampling, GI-short initial sampling and PT spatial-only reuse. The native reference is2048spp at cap4/4. These are single sequences without independent process/seed replication.

| Policy | Mean frame linear RGB MSE | Mean frame HDR-FLIP | Mean frame display-FLIP | MSE of64-frame mean |
|---|---:|---:|---:|---:|
| Adjacent reciprocal pair | 0.0393616 | 0.160266 | 0.098267 | 0.000494731 |
| One transformed Gaussian table per frame | 0.0412007 | 0.159373 | 0.096257 | 0.000521918 |

Gaussian pairing raises mean frame RGB MSE by about **4.7%**, while the two FLIP measures decrease slightly. It remains an experimental tradeoff. Broader links also encounter more surface/boundary rejection; this cohort does not establish their causal contribution. The paper's simultaneous multiple-neighbor configuration is still absent, and no general quality or speed improvement is inferred.

The following original-resolution captures are single1spp images after eight warm-up frames, **not accumulated8spp** and not temporal-reuse results:

| Scene | Linear RGB MSE | HDR-FLIP | Display-FLIP |
|---|---:|---:|---:|
| Convergence | 2.95359 | 0.536508 | 0.351035 |
| Kitchen | 0.899919 | 0.752397 | 0.406308 |

They use the preserved4096-spp native references with matching scene hashes, dimensions, exposure and14/2 budgets. Their substantial remaining error is visible; they are development coverage, not scene acceptance or a bias/convergence proof. No brightness adjustment is applied.

Official `flip-evaluator1.7` computes raw HDR and actual renderer-PNG metrics. Each reference fixes its own ppd67/ACES exposure sweep once for all associated candidates; display-FLIP uses sRGB/ppd67. Per-frame hashes, evaluator identity and fixed parameters are retained. These640×360 results are a new cohort and must not be numerically merged with the earlier176×90 pilot.

| Room640×360 | Original Convergence1280×720 | Original Kitchen1280×720 |
|---|---|---|
| ![Gaussian room development](assets/b10-gaussian/room.png) | ![Gaussian Convergence development](assets/b10-gaussian/convergence.png) | ![Gaussian Kitchen development](assets/b10-gaussian/kitchen.png) |

## Remaining implementation and comparison work

Explicit replay compaction is next: preserve cheap-shift work, compact actual pixel–neighbor replay requests, retain capacity/overflow handling, dispatch the compacted queue, and compare complete output/history against the direct schedule under identical inputs. All passes, barriers and queues must count toward performance and memory.

Also pending: simultaneous multi-neighbor paired reuse, unified primary direct/indirect ownership, duplication-map production, dual-motion recovery and general secondary-radiance reevaluation for GI reuse. Full B8/B9/B10 acceptance still needs replicated quality, motion/reset tests, convergence/equal-time comparisons and accepted total-frame timing.

Application cap receipts show vsync, limiter, reflex cap and frame generation off. No new driver/RTSS-audited total timing or FPS result is accepted here. Table-generation time, shader work counters and capture duration are not substituted for it.

## Summary and lessons learned

Reciprocity survived native generation, GPU upload, frame transforms, tile boundaries and full-resolution scene dispatch. The one-neighbor room result demonstrates why MSE and perceptual metrics must both remain visible: the new policy trades them rather than uniformly improving quality. Preserve the adjacent control and isolate scheduling next, before attributing any performance gain to Gaussian pairing or full PT++.

[Sanitized evidence and reproduction](../../Benchmarks/development/2026-10-29-gaussian-pairing/README.md) includes table bytes, source/executable identities, GPU counters, selected raw HDR, official metrics and exclusions. Large reservoir snapshots/raw sequences remain locally retained with hashes. The final identity is post-cohort; this is not represented as a pre-frozen timing experiment.

The bounded Release build, native CTest fixture and **207 Python tests** pass. These checks do not establish full PT++ or canonical acceptance.
