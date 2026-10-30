# B10 development: replay queue history validation

**Latest B10 checkpoint:** [duplication temporal history](B10_DUPLICATION_HISTORY.md) now has6GPU on/off gates/384frames, exact map counts and active nonzero prior-map reads. Quality14of18sequences; startup reliability prevents timing. Full B10/B11 remain incomplete.

## Summary and lessons learned

The spatial replay queue now preserves its actual output as the next frame's history while comparing every packed reservoir word and RGB shading bit against the direct scheduling control. Five static GPU cases cover **272 compared frames** with zero scheduling mismatches or overflow. A deliberately injected early mismatch remains detectable after later clean frames. This closes a diagnostic gap; **full B10 and B11 are not complete**. No new speedup or image-quality improvement is claimed.

Previously the direct oracle overwrote the queued output and left its own state as history. Its frame-local counters also forgot failures before the captured frame. The comparison now restores the queue's exact saved output, accumulates sequence coverage and keeps sticky failure flags until a PT history reset. No tolerance, reservoir repacking or brightness correction is applied.

## GPU evidence

| Case | Resolution | Compared frames | Queue state / RGB mismatches | Overflow |
|---|---:|---:|---:|---:|
| Room, adjacent reciprocal pairs | 177×91 | 64 | 0 / 0 | 0 |
| Room, Gaussian reciprocal pairs | 177×91 | 64 | 0 / 0 | 0 |
| Room, thin image and bounce cap1 | 176×1 | 16 | 0 / 0 | 0 |
| Original Convergence, Gaussian pairs | 1280×720 | 64 | 0 / 0 | 0 |
| Original Kitchen, Gaussian pairs | 1280×720 | 64 | 0 / 0 | 0 |

All cases use B8's NVIDIA non-directional GI approximation with reuse active and the limited initial-only roulette probability0.8. Room uses footprint reconnection; original scenes retain full-prefix replay because mid-path reconnection is still unsupported there. They use one spatial neighbor, DI/PT temporal+spatial reuse, static cameras and seed47. These are development combinations, not canonical full PT++ measurements. The five final-frame HDR stage payloads in each case are finite. Per-frame comparisons validate scheduling equivalence, not the underlying transport estimator's mean.

[Portable summary and exact statistics](../../Benchmarks/development/2026-10-30-queue-history/summary.json) · [Source and executable identities](../../Benchmarks/development/2026-10-30-queue-history/source-identity.json)

## Failure and boundary checks

The successful negative fixture changes only the oracle's saved comparison value on its third compared frame. The actual queued estimator state remains untouched. At capture, frame-local mismatches are zero but the sticky reservoir-failure flag is1; the sequence contract rejects the run. The fixture restores and rebuilds the original shader in a finally block, and records its restored hash.

Two earlier negative attempts are retained as excluded: a source edit did not reach the copied runtime shader, then a sampling-frame3 trigger failed to fire inside the compared chronology. Neither establishes failure detection. The third-comparison fixture does. A requested1×1 run rendered176×1 because of the window's minimum width; the requested-dimension gate rejected it. The176×1 follow-up is labelled with its actual dimensions. There is no claimed1×1 GPU result.

[Negative fixture receipt](../../Benchmarks/development/2026-10-30-queue-history/fault-sequence-third/receipt.json) · [Excluded attempts](../../Benchmarks/development/2026-10-30-queue-history/excluded-attempts.json)

The benchmark-tool suite passes **234 tests**, including missing sequence receipts, insufficient coverage and each sticky failure after a clean final frame. The portable runner is `Benchmarks/tools/run_queue_history_validation.py`; give it a new `--output` directory and optionally select a `--case`. It disables application caps for diagnostic captures. These captures do not establish driver-cap clearance or performance; timed tests still require the existing external-cap audit and complete pass costs.

## Remaining B10 gates

This is still a one-neighbor **spatial** queue. Temporal/multiple-neighbor scheduling, moving cameras/occluders, reset/resize stress and queue-only timing remain pending. Full PT++ also needs unified primary direct/indirect reservoir ownership, real duplication-map history reduction, paper-specific dual-motion recovery and the remaining scoped optimization audit. Inherited packing/forced NEE are not newly implemented gains. B10.75/.50/.25 retain the native RTXPT1.9 sampling definitions but sparse reservoir initialization/reconstruction is not activated.

The next integration requirements are recorded in [B11 integration](B11_INTEGRATION.md). Brightness investigation remains deferred at the user's request.

Changelog: 2026-10-30 — added preserved queue-history output, sequence counters, negative fixture and three-scene evidence.
