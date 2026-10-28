# First B0/B1 capture analysis

`analyze_captures.py` reads the existing RTXPT1.9 CSV schema and PNG screenshots. It does not launch the renderer or fabricate missing whole-frame/GPU results. Python3.10+ is required. GPU CSV analysis uses the standard library; PNG analysis/tests need NumPy and Pillow (available in the host's bundled Python). The optional `--flip` adapter calls an already-installed official `flip-evaluator` package. It never installs one silently.

## Scope that must be preserved

The upstream `Rtxpt/SampleCommon/PathTracePerfLog.h` writes `buildMs`, `compactionMs`, and `fillMs`. `AdvancedSample.cpp:221,285–286` wraps the path-trace prepass and fill; the subsequent RTXDI calls are at316/319. **The CSV excludes RTXDI DI/GI passes.** It is insufficient to measure the performance of the migrated DI/GI shaders or claim complete-renderer speedup. The tool labels all timing summaries as partial logged-stage attribution. Full GPU critical-path timing requires additional verified instrumentation/profiling.

Each input CSV must be a separate process run, not an appended set of invocations. Pass an explicit half-open scene-time interval and verify it advances monotonically. Avoid screenshot-write timing: **only for a source-verified animation-enabled scene**, a sequence with record start10seconds, simulated60FPS and one captured frame can provide600warmup frames with no image writes; an interval such as `[4,10)` selects the final360pre-capture frames. Check the actual log and manifest rather than assuming all frames exist. Scene time is simulated time, not achieved throughput. Capture startup/loading/caches and history behavior require separate interpretation.

### Static-scene sequence pitfall found during the pilot

`Sample.cpp:1050–1074` advances scene time only when `EnableAnimations && RealtimeMode`; otherwise a disabled-update branch resets it to0. The initial convergence and kitchen scenes have animations disabled. Consequently, `captureSequence` can keep rendering indefinitely without reaching a positive `sequenceRecordStart`, even without `--stopAnimations`. Do not use the animated sequence template below as a static-scene completion harness. Protocolv2 deliberately uses this static property as a bounded unfocused-render guard. The partial-CSV analyzer rejects constant/resetting selected scene times for an advancing-sequence analysis, including a static `[0,1)` selection that would otherwise contain many frames while representing no progressing capture interval.

For accepted first static-scene timing, `run_timed.py` uses an active `captureSequence` guard: original static sceneTime stays0 and never reaches recordStart20, while `ShouldRenderUnfocused` remains true. The wrapper warms for45wall seconds, collects a15wall-second PID-filtered PresentMon trace, then deliberately terminates only its owned renderer. Validate zero PNG writes, sufficient rendered frames, actual render size and static sceneTime0. Do not add `--stopAnimations`, and reject original scenes with animation enabled. The initial non-capture attempt was invalid because unfocused rendering could stop; those runs are excluded. Keep image quality separate: use `captureSimple` at its source default64warmup frames, with a separately generated reference (initial convergence reference2048spp at exposure0; kitchen exposure2, matching `RegressionTesting-RUN.bat`). Wall-clock warmup and trace time are not simulated scene time and must be recorded independently. The runner owns actual launch/timing boundaries and external tool version; analyzers only process retained data.

## Commands

Run from the repository root with a Python environment containing the stated packages:

For the complete frozen static protocol, supply separately preserved Release binaries and the exact PresentMon executable identified in the protocol. Runs are strictly serialized. Existing directories are resumed only after manifest, CSV hash, PID/swapchain, static coverage, scene and executable checks; incomplete runs must be retained under a separately named excluded diagnostic directory before retrying. Reported or ambiguous trace-loss diagnostics fail validation. PresentMon may require elevated trace privileges on the host; a denied trace is not an accepted sample.

```powershell
python -B Benchmarks/tools/run_protocol.py --baseline-exe C:/bench/B0/bin/Rtxpt.exe --candidate-exe C:/bench/B1/bin/Rtxpt.exe --presentmon C:/bench/tools/PresentMon-2.6.0-x64.exe --output C:/bench/runs --protocol Benchmarks/first-b1-protocol-v2.json
python -B Benchmarks/tools/summarize_protocol.py --runs C:/bench/runs --output C:/bench/analysis --protocol Benchmarks/first-b1-protocol-v2.json
```

These example absolute paths are placeholders for the user's preserved bundles. `summarize_protocol.py` requires all20 accepted runs, including each manifest, PresentMon log/CSV and partial perf CSV; it validates both scenes and reproduces run-level and paired-bootstrap summaries without executing the renderer. The raw partial perf data is coverage evidence only. Avoid any concurrent GPU workload while timing.

```powershell
python -B Benchmarks/tools/analyze_captures.py perf Benchmarks/runs/B0-r1.csv Benchmarks/runs/B0-r2.csv --label B0 --scene-start 4 --scene-end 10 --output Benchmarks/results/B0-partial.json
python -B Benchmarks/tools/analyze_captures.py perf Benchmarks/runs/B1-r1.csv Benchmarks/runs/B1-r2.csv --label B1 --scene-start 4 --scene-end 10 --output Benchmarks/results/B1-partial.json
python -B Benchmarks/tools/analyze_captures.py compare Benchmarks/results/B0-partial.json Benchmarks/results/B1-partial.json --output Benchmarks/results/B1-vs-B0-partial.json
python -B Benchmarks/tools/analyze_captures.py quality Benchmarks/runs/B0.png Benchmarks/runs/B1.png --relation regression --output Benchmarks/results/B1-vs-B0-display.json
python -B Benchmarks/tools/analyze_captures.py quality Benchmarks/runs/reference.png Benchmarks/runs/B1.png --relation accuracy_reference --flip --ppd 67 --output Benchmarks/results/B1-vs-reference-display.json
python -B -m unittest discover -s Benchmarks/tools -p "test_*.py" -v
```

Use five or more process runs for the planned confirmation protocol. Two are shown only for command brevity. The summary is a median of process-run medians, not a pooled frame median. It reports frame-distribution p95 within each run and the median of those p95s separately. A deterministic percentile bootstrap over run medians is supplied for three or more runs; its small-sample limits and independence assumptions remain material. Matching CSV columns cannot verify equal scene/camera/features/hardware; retain complete run manifests.

PNG metrics are decoded-RGB equality, changed-pixel fraction, encoded-sRGB RGB MSE/PSNR, and display-luma SMAPE100. Alpha is excluded. Equal pixels have mathematically infinite PSNR, encoded as `null` plus `psnr_identical_infinite=true` to keep valid JSON. Display-luma uses Rec.709 coefficients on encoded RGB; this is explicitly **not** HDR luminance or paper-exact radiometric SMAPE. A B0 regression image is a cross-version oracle, not converged truth. The optional official evaluator runs **LDR-FLIP**, records its package/native binary identity and PPD, and computes the full map before reducing any ROI. Official1.7 returns inactive HDR exposure defaults as `+inf` during LDR evaluation: the wrapper separates these under `inactive_hdr_parameters`, marks them not applicable and preserves the sentinels as strings. Active non-finite parameters, error maps or mean errors still fail. There is no substitute HDR-FLIP, MAPE, RelMSE, flicker, covariance or bias implementation here.

ROI masks are same-size image masks: nonzero grayscale pixels select the region. No resizing/cropping or denominator renormalization is hidden. Wrong dimensions, malformed/non-finite/negative timing data, empty windows, changed sampling settings and appended process logs fail explicitly. Synthetic tests verify formula and parser behavior only; their values must never enter renderer result tables.

## Activate the actual migrated path

`SampleUI.h:161–165` gates DI on UseNEE/realtime/UseReSTIRDI and GI on realtime/UseReSTIRGI; default DLSS-RR can disable both. For an isolated initial DI/GI comparison use `--overrideToRealtimeMode --useNEE 1 --useReSTIRDI 1 --useReSTIRGI 1 --realtimeAA 0 --standaloneDenoiser 0 --overrideSubSamplingMode 0 --overrideRadianceCacheMode 0 --realtimeSamplesPerPixel 1`, with fixed exposure/camera and matching source/scene pins. Those flags do not activate ReSTIR PT.

Example source-verified **animation-enabled-scene only** capture template (run from each preserved version root; create output folder first). First verify that the scene actually advances time; this template is not suitable for default static convergence/kitchen scenes:

```powershell
.\bin\Rtxpt.exe --scene bistro-programmer-art.scene.json --width 1920 --height 1080 --captureSequence --sequenceFPS 60 --sequenceWarmupStart 0 --sequenceRecordStart 10 --sequenceFrameCount 1 --overrideToRealtimeMode --useNEE 1 --useReSTIRDI 1 --useReSTIRGI 1 --realtimeAA 0 --standaloneDenoiser 0 --overrideSubSamplingMode 0 --overrideRadianceCacheMode 0 --realtimeSamplesPerPixel 1 --overrideAutoexposureOff --overrideExposureOffset 4 --disableFireflyFilters --disablePostProcessFilters --nonInteractive --capturePath "Benchmarks\runs\frame.png" --captureSuffix B0-r1 --perfLog "Benchmarks\runs\B0-r1.csv"
```

Sequence capture must not use `--stopAnimations`: the upstream manager asserts against that combination. It sets scene time at sequence start and fixed simulated delta thereafter. The image gets a numbered+versioned filename; the selected pre-image-write interval and subsequent single PNG are different evidence scopes. Verify animation/material/camera consistency and actual render dimensions before comparing. Frame-time sums are never converted to total FPS by these tools.

Official FLIP adapter API checked2026-10-28: [Python example](https://github.com/NVlabs/flip/blob/main/src/python/api_example.py), [API definition](https://github.com/NVlabs/flip/blob/main/src/flip_evaluator/flip_python_api.py). This project wrapper is independently written; no evaluator code is copied. Pin the installed evaluator version for actual measurements.

## PresentMon process-frame analysis

`presentmon_analysis.py` handles the separately captured PresentMon2.x process stream. The accepted static-scene runner uses the protocolv2 active-capture/no-image-write guard,45wall-second warmup then a15wall-second trace; analyze a preregistered last600eligible rows and drop the final16rows. Require enough frames rather than silently shortening the window. This selection also works for a verified animation-enabled sequence after separately checking its no-image-write interval; selection indices alone do not prove that condition.

```powershell
python -B Benchmarks/tools/presentmon_analysis.py summarize Benchmarks/runs/B0-r1-presentmon.csv Benchmarks/runs/B0-r2-presentmon.csv --label B0 --process-name Rtxpt.exe --last-n 600 --drop-tail 16 --output Benchmarks/results/B0-presentmon.json
python -B Benchmarks/tools/presentmon_analysis.py summarize Benchmarks/runs/B1-r1-presentmon.csv Benchmarks/runs/B1-r2-presentmon.csv --label B1 --process-name Rtxpt.exe --last-n 600 --drop-tail 16 --output Benchmarks/results/B1-presentmon.json
python -B Benchmarks/tools/presentmon_analysis.py compare Benchmarks/results/B0-presentmon.json Benchmarks/results/B1-presentmon.json --output Benchmarks/results/B1-vs-B0-presentmon.json
```

One processID and swapchain must remain after the process-name filter; otherwise specify `--process-id` and/or `--swapchain`. Generated frames are excluded when FrameType exists: default accepted types are Original/NotSet, with counts preserved. If another label is source-verified as application-rendered, declare it with `--allow-frame-type`; do not guess enum meanings. Missing FrameType leaves exclusion unverified. Missing/NA GPU or display values remain unavailable. The parser rejects an insufficient selection, non-finite/negative timings, incompatible selection policies, and differing observed API/sync/tearing/present-mode sets. Store the exact external tool checksum/version in each run manifest.

CPUFrameTime/FrameTime describes CPU frame cadence. GPUBusy measures target-process active-engine time; GPUTime includes its GPU wait interval. DisplayedTime describes display residence. These are distinct scopes; inverse GPUTime/GPUBusy is not total renderer FPS. Per-frame distributions and run-level summaries remain separate. Tail truncation is an explicit capture assumption, not proof that loading/readback or trace loss is absent. Verify selected row indices/times and manifests before using a result. Source: [official console schema](https://github.com/GameTechDev/PresentMon/blob/v2.3.0/README-ConsoleApplication.md#csv-columns); PresentMon2.6 `--v2_metrics` selects that metric family.
