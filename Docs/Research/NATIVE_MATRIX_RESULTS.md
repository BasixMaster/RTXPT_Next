# Native comparison completion: B2, B3 and B5

Measured2026-10-29. **27quality captures and27accepted timing processes** cover three native configurations on original Convergence, original Kitchen and the separately identified registered-environment room. All original native shaders, executable controls and dependency pins remain unchanged. These runs complete current native coverage; they do not implement or validate ReSTIR PT on the original scenes.

[All B0–B10 versions, metrics and pictures](COMPARISON_OVERVIEW.md) · [Canonical mapping](VERSION_MAPPING.md)

## Performance and quality

| Scene | Version / algorithm | GPU busy ms ↓ | CPU cadence ms | LDR-FLIP ↓ | Display MSE ↓ |
|---|---|---:|---:|---:|---:|
| convergence | B2: native PT + DI/GI3.0 | 4.5099 | 4.5787 | 0.243459 | 0.018561 |
| convergence | B3: native PT, DI/GI off; runtime3.1 | 2.5654 | 2.5284 | 0.375281 | 0.087760 |
| convergence | B5: native PT + DI/GI3.1 | 4.5447 | 4.5870 | 0.243522 | 0.018563 |
| kitchen | B2: native PT + DI/GI3.0 | 5.3698 | 5.3773 | 0.352840 | 0.032410 |
| kitchen | B3: native PT, DI/GI off; runtime3.1 | 3.2579 | 3.2430 | 0.382364 | 0.071514 |
| kitchen | B5: native PT + DI/GI3.1 | 5.4207 | 5.4346 | 0.351458 | 0.032223 |
| opaque-room | B2: native PT + DI/GI3.0 | 1.4412 | 1.5218 | 0.094603 | 0.003519 |
| opaque-room | B3: native PT, DI/GI off; runtime3.1 | 0.8048 | 0.9305 | 0.116744 | 0.013356 |
| opaque-room | B5: native PT + DI/GI3.1 | 1.4607 | 1.5537 | 0.093961 | 0.003471 |

Each GPU value is the median of three process medians. GPU busy measures process engine activity, not full critical-path frame latency or renderer FPS. This is a separate acquisition cohort from B1/B4 and B6/B7. No across-cohort statistical equivalence, general speedup, equal-time or equal-quality speedup is established. Native DI/GI retain their original approximation settings.

## Scenes, controls and quality reference

Convergence and Kitchen preserve original scene files, cameras, materials and1280×720,1spp,total/diffuse14/2. Exposure is0/2 respectively. The room uses the separately identified zero-intensity registered environment fixture at640×360,1spp,3/3. AA, standalone denoiser, cache, subsampling and post/firefly filters are disabled. Three process restarts are not independent Monte Carlo seeds. The unmodified native simple-capture history behavior is retained.

B2 uses the303b408 RTXPT1.9 base/runtime3.0 with native-controls-v2 adapter4e380f9 and executable6db074d. B3/B5 use migration7010bb4/runtime3.1 with adapter13d023f and executable68cab907. Frozen source/build/cache receipts verify actual DI/GI/PT flags before and after each accepted run; no shader estimator change was made to these controls. B0 original defaults remain a separate preserved reference, not replaced by B3 or a raw preset.

LDR-FLIP uses official evaluator1.7 atPPD67 on stored sRGB PNGs. Display MSE is encoded RGB error, not linear-HDR error. Original-scene finite4096spp reference PNG hashes and2048spp discrepancy are retained in the previous native report. The room uses the same separate finite8192spp native reference as the registered-room report. Native original-shader controls do not export linear HDR or explicit independent seeds. No candidate exposure/brightness normalization is applied.

## Timing isolation and recovery

Each process uses45s warm-up and15s PresentMon. Selection retains the last600 eligible process/swapchain rows after dropping16. Variant order rotates each repetition. Every accepted timing verifies app controls, fresh matching NVIDIA foreground/background caps0 and forced-off VSync, observed SyncInterval0, read-only RTSS boundaries, frozen identities, no reported ETW loss and no image writes. All27temporary driver scopes were restored and verified. Other external limiters, background GPU work and unlocked clocks remain outside exclusive control. CPU-heavy quality analysis and the renderer build started only after all timing processes completed.

The first preparation attempt froze the shared R31 cache before warming its GI permutation. The identity guard rejected the subsequent B3 launch after the cache changed. It is excluded and retained locally; no timing sample was accepted from it. The fresh accepted suite warms all mode/scene combinations before freezing all identities.

## Representative pictures

Process1 is shown for every configuration, without selecting a favorable image. Click to enlarge; Escape closes the shared preview.

### convergence

| B2: native PT + DI/GI3.0 | B3: native PT; DI/GI off | B5: native PT + DI/GI3.1 |
|---|---|---|
| [![B2 convergence](assets/native-matrix/convergence-B2.png)](assets/native-matrix/convergence-B2.png) | [![B3 convergence](assets/native-matrix/convergence-B3.png)](assets/native-matrix/convergence-B3.png) | [![B5 convergence](assets/native-matrix/convergence-B5.png)](assets/native-matrix/convergence-B5.png) |

### kitchen

| B2: native PT + DI/GI3.0 | B3: native PT; DI/GI off | B5: native PT + DI/GI3.1 |
|---|---|---|
| [![B2 kitchen](assets/native-matrix/kitchen-B2.png)](assets/native-matrix/kitchen-B2.png) | [![B3 kitchen](assets/native-matrix/kitchen-B3.png)](assets/native-matrix/kitchen-B3.png) | [![B5 kitchen](assets/native-matrix/kitchen-B5.png)](assets/native-matrix/kitchen-B5.png) |

### opaque-room

| B2: native PT + DI/GI3.0 | B3: native PT; DI/GI off | B5: native PT + DI/GI3.1 |
|---|---|---|
| [![B2 opaque-room](assets/native-matrix/opaque-room-B2.png)](assets/native-matrix/opaque-room-B2.png) | [![B3 opaque-room](assets/native-matrix/opaque-room-B3.png)](assets/native-matrix/opaque-room-B3.png) | [![B5 opaque-room](assets/native-matrix/opaque-room-B5.png)](assets/native-matrix/opaque-room-B5.png) |

## Evidence and remaining coverage

Public-safe raw captures, metric JSON, timing traces, effective settings, frozen identities, exclusion note and driver restoration receipts are retained in `Benchmarks/development/2026-10-29-native-matrix-completion`. The unified overview preserves every missing B0–B10/scene row. Native variable-history convergence, reconstructed output, motion/disocclusion, renderer-exclusive memory and equal-time/error sweeps remain pending. ReSTIR PT original-scene support is being developed separately; a native result does not establish PT compatibility.

## Summary and lessons learned

Fresh cap-verified measurements replace the need to rely on historical cap-unverified B2/B5 observations. The configurations have different cost/quality tradeoffs; dependency migration alone establishes no general improvement. Preserve actual DI/GI/PT activation and finite-reference scope beside every value. The shared-cache guard correctly rejected an unstable setup before it entered the accepted cohort.

## Changes

- 2026-10-29: Completed B2/B3/B5 quality and performance coverage for all three required scenes; retained all earlier evidence unchanged.

## Fresh RTXPT1.9 PT-only override

**B0/raw-native-control** uses preserved1.9 source303b408 plus the host-only benchmark-controls-v2 adapter4e380f9, RTXDI3.0 a14e079 and original Assets a56be4e. Native PT and NEE remain on; effective receipts confirm ReSTIR DI/GI/PT all off. It does not replace B0 original defaults or the B2 DI+GI configuration. Native shaders are unchanged.

|Scene|GPU busy ms|CPU cadence ms|Display-FLIP|Display MSE|
|---|---:|---:|---:|---:|
|opaque-room|0.8307|0.8743|0.121162|0.0139288|
|convergence|2.5172|2.4667|0.372227|0.0866742|
|kitchen|3.2427|3.2611|0.376870|0.0691566|

Nine timing processes pass frozen source/executable/501shader-cache identities, no image writes, complete traces with no reported loss, application/NVIDIA/RTSS cap boundaries and per-process verified restoration. Protocol:45s warmup plus30s measurement, last600 Original/NotSet process/swapchain rows minus final16, three process repeats per scene. GPU busy and CPU cadence are separate metrics; no inverse-GPU-busy FPS is inferred.

Nine PNG quality captures use three process restarts; no independent-seed claim. Original Convergence/Kitchen remain1280x720,14/2, exposure0/2. Room is640x360,4/4, separate from earlier3/3 native-room results. Native MIS/filter policies remain unchanged and differ from strict modern PT development settings. Quality is descriptive against the documented finite native references, not an isolated algorithm-version gain.

**HDR-FLIP and linear MSE are unavailable:** the preserved executable has no raw-HDR exporter. An initial unsupported-HDR preflight failed without an image or timing; it remains excluded. The subsequent supported PNG cohort is separate. No transport or renderer-source workaround was applied.

|Room|Original Convergence|Original Kitchen|
|---|---|---|
|[![B0 PT-only Room](assets/native-pt-only/opaque-room.png)](assets/native-pt-only/opaque-room.png)|[![B0 PT-only Convergence](assets/native-pt-only/convergence.png)](assets/native-pt-only/convergence.png)|[![B0 PT-only Kitchen](assets/native-pt-only/kitchen.png)](assets/native-pt-only/kitchen.png)|

[Sanitized captures, quality, timing, cap/restoration receipts and exclusions](../../Benchmarks/development/2026-10-29-fresh-b0-pt-only/README.md). [Exact portable five-file native adapter patch](../../Testing/native-controls-v2/README.md) and the shipped PT-only runner support reproduction; toolchain versions may change executable hashes.

The comparison overview shows this control in its own supplemental table so original B0 defaults retain their identity. Brightness fixes remain deferred.
