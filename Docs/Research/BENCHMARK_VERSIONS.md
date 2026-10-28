# Version comparison protocol for Basix Pathtracing / RTXPT_Next

This chapter defines the general comparison contract. The initial B1 migration and bounded capture/timing tools are now implemented; the first measured subset and its explicit gaps are in [B1 results](B1_RESULTS.md). The final repository basis is **RTXPT 1.9 at the root**, including its Assets scene repository. The current RTXDI 3.0 runtime integration is the baseline. B1 applies runtime3.1 to the existing DI/GI path; the separate optional SDK checkout remains a reference and does not establish PT integration.

## Immutable experiment versions

| ID | Exact source basis / planned scope | Comparison |
| --- | --- | --- |
| B0 | NVIDIA RTXPT 1.9 source commit `303b408ab81790a5051abd7573830b7a4112eb8e`, retained as tag `rtxpt-1.9-baseline` and branch `baseline/rtxpt-1.9`; existing `External/Rtxdi` gitlink `a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6`; Assets gitlink `a56be4ed65029d2733fd02f00f4027ffd541eda8` | Preserve original rendering behavior, feature defaults and binaries. |
| B1 | `7010bb4cda80788eb13cd9ee6143eb2f52a5b6ee`: RTXDI3.1 runtime/API update and necessary compatibility fixes; runtime `f12037fa8e97ebc08e9e3edfd2de528ed1772a4b` | B1 vs B0 isolates the version update. Merely adding `External/RTXDI-SDK` is insufficient. |
| B2 | Future single immutable commit: audited PT++ baseline and required ReSTIR PT host integration, if absent after B1 | B2 vs B1; document already-shipped PT++ components to avoid counting them twice. |
| B3+ | One named technique/ablation per immutable commit, then separately named combinations: compatible neighbors, stochastic MIS, single/multi-layer splatting, guiding, geometry LoD and BDPT | Each vs its immediate parent and B0/B1; combination vs each constituent. Do not pool builds with different estimator settings. |

The fork setup merge `c5b1569cf6eff2eb7fb85f1a47fc48722c254345` preserves prior remote history while switching the root to RTXPT; it is not NVIDIA's B0 source revision. Assign no invented SHA to a future version. Before each run, resolve full root/submodule SHAs, save clean/dirty status, compiler/CMake/DXC/SDK versions and configuration, and hash the executable, shader files and relevant DLLs. A version name or mutable branch is not an experiment identity. Preserve B0 and B1 executable bundles separately; this sample normally emits to `bin`, so sequential rebuilds can overwrite the comparison binary. Build configuration is Release for all performance comparisons; validation/debug runs are a separate result class.

## Fixed scene and rendering contract

Keep Assets at `a56be4ed65029d2733fd02f00f4027ffd541eda8` for every version. Record all scene JSON, glTF, material, texture, environment and camera-path hashes, plus any local Assets modifications. A gitlink does not describe local dirty scene changes. Do not silently refresh Assets between builds.

Use the main `Rtxpt` executable, not `IntroSample`, for these comparisons. The latter has a different hybrid rendering architecture. Start with the upstream regression scenes `bistro-programmer-art.scene.json`, `convergence-test.scene.json` and `kitchen-with-test-stuff.scene.json`; inspect the exact pinned assets before assigning claimed scene properties. Add named diagnostic camera/scene variants for thin geometry and moving disocclusion, glossy transport, small lights/indirect-only rooms, lens/shutter integration, LoD transitions and specular caustics when those techniques reach their gates. Preserve any new diagnostic scene variant as a separate immutable asset/configuration identity.

For every matched pair fix output resolution **and internal render resolution**, camera position/direction/up, projection/FOV, aperture, focus distance, shutter integration, scene time, animation/skin state, lights, environment, materials, path depth, roulette, texture sampling, SER/OMM state, reservoir settings/history limits, radiance cache, sample budget, reconstruction DLL/model/mode, async queue scheduling, exposure, firefly filters and post filters. Explicitly disable frame generation for timing; generated FPS is not renderer throughput. Do not assume that equal window dimensions imply equal DLSS render resolution. Keep SHaRC off in the isolated unbiased/sampling track, then test a separately labelled product configuration with SHaRC and reconstruction enabled identically across versions.

## Source-verified capture controls

These controls were inspected in `Rtxpt/SampleCommon/CommandLine.cpp`, `CaptureScriptManager.cpp/.h`, `PathTracePerfLog.h`, `Testing/RegressionTesting-GENERATE.bat`, `SequenceDisocclusionLag.bat` and `SequenceWeightBoost.bat` at B0.

| Control | Verified meaning / limit |
| --- | --- |
| `--captureSimple --capturePath` | One image after default 64 warmup frames. In reference mode waits for accumulation completion. The 64-frame default is in the manager header, not an exposed CLI warmup option. |
| `--captureSequence --sequenceFPS --sequenceWarmupStart --sequenceRecordStart --sequenceFrameCount` | Fixed simulated scene timestep and named time interval. Warmup frame count is calculated from the start-time difference. `sequenceWarmupStart < sequenceRecordStart` is required; avoid `--stopAnimations` with sequence capture. Older names in help prose are not accepted option names. |
| `--captureSuffix` | Adds a version suffix to captured image names. Sequence files receive numbered names such as `frame_000_B0.png`. |
| `--cameraPosDirUp` | Nine comma-separated values; quote as one argument, especially when invoking batch scripts. Camera UI can copy the values. |
| `--realtimeAA 0` / `3` | None / DLSS-RR. Set `--standaloneDenoiser 0` for a no-reconstruction capture. |
| `--overrideRadianceCacheMode 0` / `1` | Disabled / SHaRC. |
| `--overrideSubSamplingMode 0` | Disable sub-1spp subsampling. Keep the same mode across paired baselines; evaluate subsampling separately. |
| `--overrideDLSSMode 6` | DLAA. Verify actual internal resolution and supported mode at runtime. Other enumerated modes are listed in CommandLine.cpp. |
| `--perfLog <csv>` | Appends per-frame GPU timings for path-tracing build/compaction/fill only. Rows include scene time and render dimensions; incomplete timer rows are flushed on capture exit. This is not a complete-frame timer and omits other passes/reconstruction. |
| `--nonInteractive` | Suppresses input-requiring dialogs. A window is still required; `--noWindow` is explicitly rejected. |

There is no source-verified general command-line random-seed selector in the inspected parser. Record that independent-seed control is missing rather than fabricating a flag or calling repeated deterministic captures independent Monte Carlo trials. If seed scheduling is added later, first define and verify it as a separately versioned benchmark facility, consistently available to all compared builds.

## Exact upstream examples, for later execution

Use each version's preserved `bin/Rtxpt.exe` with its `bin` directory as the working directory. The wrapper resolves absolute output paths; relative template paths must be adjusted accordingly. The commands below use only inspected B0 flags. Create each output directory beforehand. These are **image validation templates**, not complete performance benchmarks.

Raw here means the unreconstructed captured display image, with no AA or denoiser. The current PNG path is tonemapped sRGB; it is **not linear HDR radiance**.

```powershell
.\bin\Rtxpt.exe --scene bistro-programmer-art.scene.json --width 1920 --height 1080 --stopAnimations --captureSimple --overrideRadianceCacheMode 0 --useNEE 1 --NEEType 2 --useReSTIRDI 0 --useReSTIRGI 0 --standaloneDenoiser 0 --overrideAutoexposureOff --overrideExposureOffset 4 --disablePostProcessFilters --overrideToRealtimeMode --realtimeSamplesPerPixel 1 --realtimeAA 0 --disableFireflyFilters --overrideSubSamplingMode 0 --nonInteractive --capturePath "Testing\Benchmark-B0\bistro-raw.png" --captureSuffix B0
```

For the matched reconstructed display capture, replace `--realtimeAA 0` with `--realtimeAA 3 --overrideDLSSMode 6`; keep all other features and sample settings unchanged. Confirm actual runtime reconstruction/internal resolution before accepting the comparison.

The source-tested upstream regression script also generates 1spp and 32spp images with and without DLSS-RR and a 16384spp reference, followed by an external OptiX denoiser. Its 32spp and reference commands do not explicitly disable the firefly filter. Do not call that entire set a pure unbiased/linear-radiance test; align filtering explicitly for estimator evaluation and preserve the undenoised reference.

```powershell
.\bin\Rtxpt.exe --scene bistro-programmer-art.scene.json --width 1920 --height 1080 --stopAnimations --captureSimple --overrideRadianceCacheMode 0 --useNEE 1 --NEEType 2 --useReSTIRDI 0 --useReSTIRGI 0 --standaloneDenoiser 0 --overrideAutoexposureOff --overrideExposureOffset 4 --disablePostProcessFilters --disableFireflyFilters --overrideToReferenceMode --referenceSamplesPerPixel 16384 --realtimeAA 0 --nonInteractive --capturePath "Testing\Benchmark-B0\bistro-reference.png" --captureSuffix B0
```

This is a high-spp display-space reference template. Check convergence with a larger sample count and independent seed/reference route before treating its error floor as negligible. Reference mode and real-time mode can differ in enabled approximation/filtering; audit parity for each intended statistic. Scene-linear HDR export and strict mean/bias testing remain future instrumentation requirements, not capabilities proven by this PNG command.

The current disocclusion sequence is source-tested at 8 frames/15 simulated FPS after scene-time warmup from 4.0 to 5.82 seconds:

```powershell
.\bin\Rtxpt.exe --scene bistro-programmer-art.scene.json --width 1920 --height 1080 --propShowTags LagTestWallLamp --propCameraAttach SHIP_LagTestWallLamp --captureSequence --sequenceFrameCount 8 --sequenceFPS 15 --sequenceWarmupStart 4.0 --sequenceRecordStart 5.82 --useNEE 1 --NEEType 2 --useReSTIRDI 0 --useReSTIRGI 0 --realtimeSamplesPerPixel 1 --standaloneDenoiser 0 --realtimeAA 0 --overrideToRealtimeMode --overrideAutoexposureOff --overrideExposureOffset 4.0 --disableFireflyFilters --disablePostProcessFilters --nonInteractive --capturePath "Testing\Benchmark-B0\disocclusion.png" --captureSuffix B0 --perfLog "Testing\Benchmark-B0\disocclusion.csv"
```

Keep that sequence for visual regression, but its 8 frames are too short for a general steady-state performance result. A longer proposed run can use the same verified sequence controls with a preregistered interval and at least 600 recorded frames, checking animation looping and scene-time coverage. No new CLI benchmark facility is implied. ReSTIR PT and future paper switches are not present in these commands; B0's `useReSTIRDI`/`useReSTIRGI` switches must not be relabelled as PT.

## Warmup, timing and repeated runs

Separate first-use loading/shader compilation/OMM construction/cache initialization from steady state, retaining first-use costs as a distinct result. The simple-capture 64 frames are only an upstream default, not proof of convergence. For planned steady-state captures use an initial 240-frame interval at 60 simulated FPS, then at least 600 recorded frames; extend warmup if measured passes/cache occupancy have not stabilized. Test cold-start and history-reset behavior separately so warmup does not conceal instability or disocclusion lag.

Use at least five process-level repetitions per version/scene/configuration in randomized or balanced order, with GPU temperatures/clocks checked. Repeat the complete paired workload, not individual pixels treated as independent samples. Report the median of run-level medians and across-run confidence intervals; include frame-time p50/p95/p99, mean and standard deviation, sample count and run duration. When runs have correlated frames, compute uncertainty from run blocks or suitable block bootstraps, not a naive confidence interval over all frames. Preserve dropped frames, crashes and outliers with stated exclusion rules.

Use `perfLog` for attribution only. Add an external GPU timeline/profiler measurement of complete submitted-frame critical-path latency, plus CPU frame time and steady-state throughput in a no-image-write measurement interval. Screenshot readback/PNG writing may stall queues and alter CPU throughput; report capture timing separately. With asyncPrefix/async DLSS, summing per-pass durations can double-count overlap; report both individual durations and actual critical path. VSync/frame limit/window composition/Reflex state must be fixed and recorded. Debug layers, GPU validation and intrusive captures are disabled for final performance timing. The first benchmark uses an explicit bounded wrapper and the upstream static active-capture guard to keep rendering while unfocused without writing PNGs. See B1 results; this measures process GPU engine active time and CPU cadence, not a full critical-path profiler trace.

## Quality and efficiency comparisons

Use the paper-backed definitions and scope in [Quality metrics](QUALITY_METRICS.md) when selecting the final image/temporal metrics. Keep those source-specific metrics distinct from the general experiment controls below.

1. **Equal configuration / equal spp:** B0 vs B1 isolates SDK integration changes; preserve DI/GI/PT mode names accurately. Verify image equivalence and mean before attributing performance. Preserve both default-product and isolated-sampling tracks as separate tables.
2. **Equal time:** Sweep candidate/neighbor/sample counts in each version and compare error at matched complete GPU frame budgets. Do not compare one shader duration to a full reconstructed frame. Keep resolution, camera, reconstruction and bias settings identical.
3. **Equal quality:** Plot complete frame cost against a preregistered error threshold; report interpolated time-to-threshold only between measured settings, with uncertainty. Declare unattained thresholds instead of extrapolating a speedup.
4. **Raw / reconstructed:** Keep display PNG MSE/PSNR and FLIP labelled display-space. For estimator accuracy add verified linear-radiance HDR capture later and report RMSE/relative error, energy drift and long-run statistical mean. Reconstructed images get temporal/FLIP tests, not an unbiasedness claim. Save raw inputs and reconstruction configuration separately.
5. **Temporal:** Match scene-time indices; measure disocclusion recovery, flicker/temporal error, firefly tails and long-history correlation on animated camera/geometry/light sequences. Matching fixed FPS advances scene time; it does not mean the renderer attained that real FPS.
6. **Resources:** Report peak/local VRAM, reservoir bytes per pixel, guide-grid storage, rays/shifts per pixel, bandwidth/occupancy where measured, CPU time and loading/compilation cost. For LoD report geometry/AS cost and approximation error; for guiding include training updates; for splatting include collisions/layer overflow; for BDPT include light cache and MIS/replay cost.

The existing regression comparison script uses PSNR against per-image GOLD captures and color-coded historical drop thresholds. It is useful for regression triage, but is not a cross-version equal-quality benchmark or an unbiasedness oracle. Preserve GOLD images for every immutable configuration rather than overwriting the only baseline.

## Required run manifest and results table

Required manifest fields: version ID/root SHA; all recursive submodule SHAs; executable/shader/DLL hashes; Assets pin and dirty status; scene/camera/config hashes; full launch command; effective runtime feature state; OS/build; GPU exact model, VRAM, driver, power limit, clocks and temperature; CPU/RAM; compiler/DXC/CMake/toolchain; API; presentation/VSync/Reflex state; reconstruction model/DLL/mode/internal resolution; seeds or explicit seed-control gap; warmup/record interval; repetitions; measurement tools/version/scope; reference identity; output hashes; validation/errors/exclusions.

| Version pair | Scene/config | Raw or reconstructed | Frame p50/p95/p99 | Error / temporal metric | VRAM | Equal-time gain | Equal-quality gain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B1 vs B0 | Convergence and Kitchen,1280×720 isolated DI/GI | Unreconstructed display captures | [Measured scope](B1_RESULTS.md) | [Display-space metrics](B1_RESULTS.md) | Device-wide only | Not established | Not established |
| B2+ vs parent and B0/B1 | Pending implementation and manifest | Pending | Not measured | Not measured | Not measured | Not measured | Not measured |

Initial hardware: RTX4090/24GiB, driver617.42, Ryzen7 5800X3D, Windows10. Full first-run details and measured configuration are in B1 results; paper hardware does not substitute for this machine.

## Summary and lessons learned

RTXPT already supplies repeatable screenshot/sequence controls and limited GPU-pass CSV logging. Those are sufficient to preserve visual regression inputs, but do not establish full-frame performance, independent-seed statistics or linear HDR estimator correctness. Keep B0 immutable, isolate the B1 runtime/API update, then add one research change per B2+ identity. Publish gains only after complete-frame, paired-configuration experiments; paper-reported speedups and generated FPS do not substitute for these measurements.
