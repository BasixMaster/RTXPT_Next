# Preserved RTXPT1.9 native benchmark controls v2

The patch applies directly to upstream `303b408ab81790a5051abd7573830b7a4112eb8e` and changes five host/CLI/UI files. Native shader sources, estimator logic, RTXDI3.0 `a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6` and Assets `a56be4ed65029d2733fd02f00f4027ffd541eda8` remain unchanged. `manifest.json` records before/after source hashes and the exact patch hash. The measured local adapter commit is a separate composite identity; it is not the original upstream binary.

Create a separate checkout at the base and populate its exact submodule pins. Verify `git apply --check rtxpt19-host-controls.patch`, then apply the patch. Build using the upstream documented toolchain. Supply these verified, unquoted preprocessor token values to the compiler through the build configuration:

```text
RTXPT_BENCHMARK_ROOT_PIN=303b408ab81790a5051abd7573830b7a4112eb8e
RTXPT_BENCHMARK_RUNTIME_PIN=a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6
```

The adapter refuses compilation without both definitions and logs a `NATIVE_CONTROLS_CONTRACT revision=2` receipt. Record the new executable and warmed shader hashes. Do not assume identical binary hashes across toolchain versions.

The adapter exposes absolute scene paths, existing bounce limits and application uncapping, renders while unfocused, and adds effective transport/provenance receipts. It does **not** add raw-HDR export, ReSTIR PT, independent-seed controls or the modern PT bridge's exact-MIS/filter overrides. PNG quality is supported; HDR metrics remain unavailable for this binary.

Use `Benchmarks/tools/run_native_pt_only.py --help` for the fixed three-scene/three-repeat PT-only cohort. Provide the separately built native control, PresentMon2.6.0 and the shipped NVAPI/RTSS helpers. The output must be outside the public repository because it includes local recovery state and device telemetry. Timing uses45s warmup plus30s measurement, schedules no image capture, and restores the owned temporary NVIDIA profile after each process. Keep the desktop active and display connected. RTSS is checked read-only; unsupported or active limiters fail validation.

This runner labels the configuration **B0/raw-native-control**: native PT and NEE on, ReSTIR DI/GI/PT off. It does not redefine B0's original defaults. B1/B2 separately enable DI3.0 and DI+GI3.0. See `Docs/Research/VERSION_MAPPING.md` for the canonical numbering.
