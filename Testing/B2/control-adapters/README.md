# Separate benchmark-control adapters for RTXPT1.9 and B1

`benchmark-controls.patch` adds **host controls only** to two separately named
source identities:

| Composite identity | Original root source |
|---|---|
| `RTXPT1.9+benchmark-controls-v1` | `303b408ab81790a5051abd7573830b7a4112eb8e` |
| `B1+benchmark-controls-v1` | `7010bb4cda80788eb13cd9ee6143eb2f52a5b6ee` |

These are not unchanged upstream binaries and are not replacements for the
frozen B0/B1 measurements. Every future result must record the original root
SHA **plus this patch's SHA-256**, executable hash, original dependency/Assets
pins and effective configuration. Do not label a patched executable simply
“unmodified RTXPT1.9” or mix its results into the initial B1 report.

## Added controls and unchanged scope

The patch changes exactly five host files: `CommandLine.h/.cpp`, `Sample.cpp`,
and `SampleUI.h/.cpp`. It adds:

- Explicit absolute scene JSON paths. A missing/non-JSON absolute path raises
  an error rather than falling back to another scene. Relative scene handling
  is unchanged.
- `--maxBounces` (clamped1..32) and `--maxDiffuseBounces` (clamped0..32), applied
  after the existing scene/preset settings. These control existing estimator
  parameters; they do not modify the bounce-classification algorithm.
- `--benchmarkUncapped`, which forces effective application VSync, FPS limiter,
  Reflex frame cap, Reflex mode and frame generation off, and renders while
  unfocused. The controls persist through scene/preset loading via effective
  getters. The first rendered frame logs the effective app state and bounce
  settings under `BENCHMARK_CONTROL_ADAPTER`.

All new overrides are inactive by default. There are no shader, estimator,
runtime-library, dependency, asset or material changes. The patch does not
implement ReSTIR PT, alter DI/GI selection, or add B2 algorithms.

“Uncapped” describes application-owned controls only. Inspect and record the
NVIDIA application profile, global cap, background cap, VSync policy and any
external overlay/capture limiter separately; do not claim that this patch
controls the driver or compositor. The simulated capture timestep is also
distinct from achieved frame cadence.

## Prepare isolated sources

From a workbench, with Python3.10+ and Git:

```powershell
python -B Testing/B2/control-adapters/prepare_controls.py --source-repo . --output-root C:/chosen/workbench
```

Choose a new output root if `controls-B0` or `controls-B1` already exists. The
tool refuses to overwrite snapshots. It archives each pinned root with newline
conversion disabled, initializes a private Git index at the original root SHA,
and applies the same patch after `git apply --check`. Read-only Git object
alternates reference the source repository, so keep it available while using
the snapshots. The input checkout, prior baseline checkout and existing binary
bundles are not edited. Original submodule directories remain uninitialized;
populate exact pins explicitly before any later build.

`manifest.json` records the patch hash, before/after hashes of all five changed
files, all unchanged shader-source hashes and original root gitlinks. The
preparation check verified164 `.hlsl`/`.hlsli` files unchanged in each snapshot
and no other root-file changes. Both composite snapshots subsequently built
successfully as Visual Studio2022 x64 Release D3D12 targets. Their executable
hashes and workbench log paths are recorded in the manifest. CPU compilation
used two compiler/shader workers and serial build targets; shared dependencies
and Assets retained the original pinned versions. Build scheduling changes were
confined to generated project files. **Neither composite was executed on a GPU
as part of this control-build preparation.**

After both builds, all500 recorded artifacts in the preserved B0 bundle and
all483 in the preserved B1 bundle still matched their original hashes. These
checks include compiled shaders and DLLs as well as the original executables.

A future launch can use the already-existing renderer switches together with:

```text
--scene C:/chosen/workbench/opaque.scene.json --maxBounces 3 --maxDiffuseBounces 3 --benchmarkUncapped
```

Use a separately preserved executable/output directory for each composite
identity, verify actual first-frame settings and raw/profiler completeness,
then compare B0+controls/B1+controls/B2 under one newly frozen protocol. The
first B1 report remains historical evidence for its original binaries/settings.
