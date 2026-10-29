# Prefix-throughput clamp: calibrated negative result

**2026-10-29.** The inherited upper clamp is not supported as the explanation of the remaining brightness discrepancy in these sampled frames. A synthetic GPU control verified the diagnostic, but all eight restored-shader physical captures had no packed weights above one. The legacy default remains unchanged.

[Unified comparison](COMPARISON_OVERVIEW.md) · [DI reuse isolation](DI_REUSE_ISOLATION.md) · [Evidence index](https://github.com/BasixMaster/RTXPT_Next/blob/b3/ptpp-activation/Benchmarks/development/2026-10-29-prefix-throughput-probe/index.json)

## Hypothesis and controlled interface

`PathTracerSurfaceBridgeDonut.hlsli` exports dominant-surface prefix weights through `Pack_R11G11B10_FLOAT(saturate(path.GetThp()))`. DI/GI shading multiplies its estimated contribution by these weights. A value above one could be clipped, but source inspection alone did not establish that such values occur here.

The new diagnostic option `--preserveGBufferThroughput 0/1` retains the old clamp by default. Mode 1 removes the upper clamp at one, while retaining the nonnegative lower bound and existing packing/finite upper clamp. It is not full-float transport. The capture wrapper exposes `--preserve-gbuffer-throughput 0/1` and `--capture-gbuffer-throughput`; omitted preserve mode is verified as `0`. Canonical-default labels cannot silently enable this ablation.

The control occupies existing constant-buffer padding. Packed surface/PT reservoir layouts and the existing Throughput texture stay unchanged. Staging allocation, GPU idle wait and file writes occur only when diagnostic capture is requested; no runtime or memory improvement is claimed.

## Capture and calibration validation

The packed texture is saved separately from radiance PFMs. Its header is `RTXPTTHP`, followed by little-endian uint32 version 1, width, height and pixelBytes 4; rows are tightly packed top-to-bottom. RGB uses the existing low-red R11G11B10 layout. These numbers are prefix weights, not image brightness.

The actual C++ mapped writer passed an independent golden-byte fixture covering padded rows, byte order, row order and invalid inputs. The Python decoder passed independent numeric channel/subnormal/layout fixtures. A temporary synthetic shader then injected **[2,0.5,4]** into positive exported prefixes. The GPU capture recovered that vector exactly, establishing a positive control for values above one and the producer/packing/readback/decoder path.

The synthetic source was restored byte-for-byte in a `finally` block and copied back into the runtime source tree. Physical shader permutations were warmed again, then source/executable/cache identities were frozen for the eight formal captures. Synthetic radiance is excluded from physical pictures, quality comparisons and performance measurements. The export retains separate synthetic and physical source patches/manifests.

## Original-scene observations

Original Convergence and Kitchen materials/cameras,1280×720, 14/2 total/diffuse bounces, 1 spp, 64 history frames, seed 0. B4 uses native PT+DI 3.1; B7 uses guarded full-prefix ReSTIR PT+DI 3.1,GI off, terminal-only connections, roulette off, age rejection off,spatial 1/1. Both use DI temporal+spatial, strict DI, MIP0, legacy material packing, AA/reconstruction/cache/post/firefly filters off.

|Scene|Variant|Default / preserve max packed component|Default / preserve pixels above one|Packed prefix arrays equal|
|---|---|---:|---:|---|
|Convergence|B4|1.0 / 1.0|0 / 0|Yes|
|Convergence|B7|1.0 / 1.0|0 / 0|Yes|
|Kitchen|B4|1.0 / 1.0|0 / 0|Yes|
|Kitchen|B7|1.0 / 1.0|0 / 0|Yes|

All eight physical radiance PFMs were finite and all formal artifact/setting checks passed. The four default/preserve prefix arrays were bit-identical. Full radiance arrays varied between process launches, as observed in earlier studies; they are not paired realizations and those differences are not presented as an effect or improvement from this switch.

## Physical pictures

Representative seed 0 physical renders only. Click to enlarge; Escape closes the shared preview. Separate-process lighting/sample variation remains; do not infer a quality gain from an individual pair.

|Scene / variant|Omitted legacy default|Preserve above one|
|---|---|---|
|Convergence / B4|<a href="assets/prefix-throughput/convergence-B4-omitted-default-s0.png"><img src="assets/prefix-throughput/convergence-B4-omitted-default-s0.png" width="300" alt="Physical convergence B4 omitted-default"></a>|<a href="assets/prefix-throughput/convergence-B4-preserve1-s0.png"><img src="assets/prefix-throughput/convergence-B4-preserve1-s0.png" width="300" alt="Physical convergence B4 preserve1"></a>|
|Convergence / B7|<a href="assets/prefix-throughput/convergence-B7-omitted-default-s0.png"><img src="assets/prefix-throughput/convergence-B7-omitted-default-s0.png" width="300" alt="Physical convergence B7 omitted-default"></a>|<a href="assets/prefix-throughput/convergence-B7-preserve1-s0.png"><img src="assets/prefix-throughput/convergence-B7-preserve1-s0.png" width="300" alt="Physical convergence B7 preserve1"></a>|
|Kitchen / B4|<a href="assets/prefix-throughput/kitchen-B4-omitted-default-s0.png"><img src="assets/prefix-throughput/kitchen-B4-omitted-default-s0.png" width="300" alt="Physical kitchen B4 omitted-default"></a>|<a href="assets/prefix-throughput/kitchen-B4-preserve1-s0.png"><img src="assets/prefix-throughput/kitchen-B4-preserve1-s0.png" width="300" alt="Physical kitchen B4 preserve1"></a>|
|Kitchen / B7|<a href="assets/prefix-throughput/kitchen-B7-omitted-default-s0.png"><img src="assets/prefix-throughput/kitchen-B7-omitted-default-s0.png" width="300" alt="Physical kitchen B7 omitted-default"></a>|<a href="assets/prefix-throughput/kitchen-B7-preserve1-s0.png"><img src="assets/prefix-throughput/kitchen-B7-preserve1-s0.png" width="300" alt="Physical kitchen B7 preserve1"></a>|

## Reproduction and limits

Use a fresh output directory and append `--capture-gbuffer-throughput` to a realtime DI/DI+PT raw-HDR capture. Leave preserve mode omitted for the legacy control, or append `--preserve-gbuffer-throughput 1` for the range probe. The wrapper records the effective setting and checks the packed output. The native fixture builds independently with `cmake -S Benchmarks/native-throughput-test -B build-throughput-test`, followed by build and CTest. The exported orchestration scripts expect the workspace `work/` and `outputs/RTXDI_Next` layout; adapt local toolchain/build paths explicitly.

This is one seed, two static scenes, two variants and selected final frames. It measures packed values, not original float32 prefixes; a value slightly above one could round to one. It does not establish a general bound for other scenes, PSR states, materials, motion or earlier history frames. Packing quantization and other DI integration approximations remain separate questions.

No larger clamp-quality study was launched after this negative result, and no FLIP or speedup improvement is claimed from the snapshots. No new presentation timing was attempted; the previous empty-trace issue still awaits the requested desktop/display clarification. B8 sharing and B9/B10 PT++ remain pending.

## Summary and lessons learned

A suspected energy-loss mechanism needs observed inputs, not just a suspicious source clamp. The calibrated capture detects above-one weights, while the physical samples do not contain them after packing. The default and preserve packed arrays agree exactly in the four observed pairs. This candidate does not explain the existing sampled brightness discrepancy and is not promoted as a quality enhancement.

The next focused audit is DI proposal/PDF support consistency. The standalone DI BRDF callback rejects the lower hemisphere, while its PDF callback can evaluate the full BSDF domain. Whether that mismatch reaches nonzero target/visibility in these scenes is unmeasured; no fix or causal attribution is claimed here.

## Changes

- 2026-10-29: Added opt-in packed-prefix capture, independent native/decoder fixtures, a synthetic GPU positive control and eight restored-shader physical/default observations. Legacy clamping remains the default.
