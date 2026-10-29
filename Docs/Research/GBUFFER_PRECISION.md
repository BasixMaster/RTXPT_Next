# GBuffer material precision: controlled DI brightness test

**2026-10-29: mixed results; legacy packing remains the default.** Material rounding improves Convergence B7 reference agreement but does not explain the remaining Kitchen DI deficit. It stays an opt-in diagnostic, separate from the earlier zero-Jacobian MIS bug fix.

[Unified comparison](COMPARISON_OVERVIEW.md) · [Finite-shift fix](FINITE_SHIFT_GUARD.md) · [Evidence index](https://github.com/BasixMaster/RTXPT_Next/blob/b3/ptpp-activation/Benchmarks/development/2026-10-29-gbuffer-precision/index.json)

## Experiment and estimator boundary

One frozen renderer exposes `--roundedGBufferMaterials 0/1`; the wrapper uses `--rounded-gbuffer-materials 0/1`. Omission retains legacy truncation. A first-frame receipt verifies the actual mode. The switch reuses constant-buffer padding; packed surface and PT reservoir sizes/layouts are unchanged. The wrapper rejects combining rounded `1` with a canonical-default result label.

Mode1 follows the half-up-after-fp16 rounding and finite upper clamp already present in RTXPT's `PathTracer/Utils/Packing.hlsli`, retaining the GBuffer's high-red/low-blue bit order. It changes diffuse/specular colors, transmission and roughness/metallic/IOR reconstruction. It does not scale radiance or normalize image brightness. Double rounding and quantized BSDF changes mean this is not exact or unbiased material reconstruction.

Original Convergence and Kitchen materials/cameras, 1280×720, 14/2 total/diffuse bounces, 1 spp, 64 history frames, MIP0, strict DI, AA/reconstruction/cache/post/firefly filtering off. B4 is native PT+DI 3.1; B7 is guarded full-prefix ReSTIR PT+DI 3.1, GI off, roulette off, age rejection off, ordinary/boosted spatial 1/1. Five seeds 0/11/47/1019/4093; precision and scene order rotate by seed. Both precision settings use unchanged independent native 4096 spp references from the finite-shift study. Native primary policies differ between B4 and B7, so isolate the precision setting within each variant.

## Matched quality results

Signed luminance differences use raw linear HDR without brightness normalization. ± denotes sample standard error across five seeds, not an unbiasedness guarantee. FLIP columns are medians, using the prior study's evaluator 1.7, PPD67 and reference-derived exposure parameters.

|Scene|Variant|Legacy mean Y difference ± SE|Rounded mean Y difference ± SE|HDR-FLIP legacy → rounded ↓|LDR-FLIP legacy → rounded ↓|
|---|---|---:|---:|---:|---:|
|Convergence|B4|-0.370% ±0.430%|-0.270% ±0.359%|0.43186 → 0.43114|0.29489 → 0.29342|
|Convergence|B7|-0.351% ±0.074%|-0.037% ±0.061%|0.33360 → 0.33293|0.22160 → 0.22037|
|Kitchen|B4|-0.833% ±0.212%|-0.936% ±0.176%|0.58597 → 0.58601|0.32491 → 0.32434|
|Kitchen|B7|-1.062% ±0.326%|-1.114% ±0.319%|0.44106 → 0.44025|0.24984 → 0.24934|

Seed-paired differences compare separate process captures, not identical sampled paths. Full per-seed metrics and artifact receipts are retained.

|Scene|Variant|Rounded − legacy luminance change, percentage points ± SE|Mean HDR-FLIP change ± SE|
|---|---|---:|---:|
|Convergence|B4|+0.100 ±0.123|-0.000691 ±0.000220|
|Convergence|B7|+0.314 ±0.081|-0.000790 ±0.000353|
|Kitchen|B4|-0.103 ±0.223|+0.000421 ±0.000484|
|Kitchen|B7|-0.051 ±0.191|-0.000440 ±0.000348|

## Pictures

Representative seed0 images. Click to enlarge; Escape closes the shared preview.

|Scene / variant|Legacy truncation|Rounded materials|
|---|---|---|
|Convergence / B4|<a href="assets/gbuffer-precision/convergence-B4-r0-s0.png"><img src="assets/gbuffer-precision/convergence-B4-r0-s0.png" width="300" alt="convergence B4 rounded=0"></a>|<a href="assets/gbuffer-precision/convergence-B4-r1-s0.png"><img src="assets/gbuffer-precision/convergence-B4-r1-s0.png" width="300" alt="convergence B4 rounded=1"></a>|
|Convergence / B7|<a href="assets/gbuffer-precision/convergence-B7-r0-s0.png"><img src="assets/gbuffer-precision/convergence-B7-r0-s0.png" width="300" alt="convergence B7 rounded=0"></a>|<a href="assets/gbuffer-precision/convergence-B7-r1-s0.png"><img src="assets/gbuffer-precision/convergence-B7-r1-s0.png" width="300" alt="convergence B7 rounded=1"></a>|
|Kitchen / B4|<a href="assets/gbuffer-precision/kitchen-B4-r0-s0.png"><img src="assets/gbuffer-precision/kitchen-B4-r0-s0.png" width="300" alt="kitchen B4 rounded=0"></a>|<a href="assets/gbuffer-precision/kitchen-B4-r1-s0.png"><img src="assets/gbuffer-precision/kitchen-B4-r1-s0.png" width="300" alt="kitchen B4 rounded=1"></a>|
|Kitchen / B7|<a href="assets/gbuffer-precision/kitchen-B7-r0-s0.png"><img src="assets/gbuffer-precision/kitchen-B7-r0-s0.png" width="300" alt="kitchen B7 rounded=0"></a>|<a href="assets/gbuffer-precision/kitchen-B7-r1-s0.png"><img src="assets/gbuffer-precision/kitchen-B7-r1-s0.png" width="300" alt="kitchen B7 rounded=1"></a>|

## Validation and reproducibility

Release build and benchmark-tool checks passed. All 40 measured captures completed with requested precision receipts and renderer source/executable/shader checks before and after execution; all raw outputs were finite. A calculated CPU-port check exhausts31,744 nonnegative finite fp16 inputs per channel precision against an independently searched nearest-value oracle, with zero mismatches for the clamped fp16 domain. This is not a GPU shader-execution test or a guarantee about original fp32 materials.

The first warmup was excluded because the Boolean option enabled rounding despite false text. Its effective receipt rejected it before measurement. The option was changed to validated numeric 0/1 and a separate cohort started. An omitted-option GPU probe verified default 0. No measured failed launches were silently retried; this successful block does not resolve the previously observed intermittent native startup access violation.

After quality capture, a negative-option test exposed a modal Donut error dialog before noninteractive logging was enabled. The final CLI-only correction disables that dialog and enables console diagnostics for the invalid option. A second diagnostic caught missing console output; both attempts are retained. The final invalid-mode test exits promptly with its expected diagnostic. Two post-fix GPU smoke captures verify omitted/default 0 and opt-in 1, with shader identities equal to the measured cohort. Measured and final source patches/manifests are separate; the 40 quality scores are not reassigned to the later executable.

The export contains 40 PNG images, sanitized capture/settings/metric receipts, two selected Kitchen B7 raw PFMs, and exact renderer patches against parent `e0eeced`. Other raw images remain local. To reproduce orchestration, place exported scripts in the workspace `work/` directory beside `outputs/RTXDI_Next`, choose a fresh output name, and use the documented metric dependencies. For direct captures, append `--rounded-gbuffer-materials 0` or `1` to the matched B4/B7 commands in the finite-shift report and retain all other settings/references.

## Summary and lessons learned

Follow-up: [DI initial/temporal/spatial isolation](DI_REUSE_ISOLATION.md) keeps material rounding off and compares effective reuse modes without changing the renderer.

B7 Convergence mean luminance moved from−0.351% to−0.037%; its seed-paired change was+0.314percentage points ±0.081 SE. Kitchen B7 stayed near−1.1%, with a change of−0.051percentage points ±0.191 SE. Native B4 shows no consistent brightness improvement across scenes. This supports a scene-dependent precision effect, not a complete explanation of the remaining DI discrepancy.

B7 median HDR-FLIP improves slightly in both scenes. Kitchen B4 median HDR-FLIP is effectively unchanged and its mean per-seed HDR-FLIP change is positive. Lower absolute mean-brightness error alone would not establish better image quality. Keep legacy packing as the default and retain rounding as a named diagnostic ablation.

The remaining Kitchen discrepancy needs separate DI estimator/support and convergence checks; it is not an established PT++ benefit. The earlier zero-Jacobian NaN/MIS correction remains a separately demonstrated correctness fix.

**No new throughput result.** These captures wrote PNG/PFM data; process elapsed times are orchestration, not GPU performance. Canonical B0–B10 results and existing timings remain preserved. B8 sharing and B9/B10 PT++ are still pending.
